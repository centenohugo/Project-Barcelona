"""
Contextual CEFR classifier (A1-C2) for each word, disambiguating word SENSE
by context.

Supports two input formats:
  1. Deepgram transcription JSON (results.channels[0].alternatives[0].words[])
  2. Paragraphs JSON (paragraphs[].sentences[].text) — auto-detected

Approach (inspired by Kikuchi et al. 2026, arXiv:2510.18466):
1. For each token, take a +-N word context window.
2. Retrieve candidate senses (WordNet synsets) for the word.
3. Pick the synset whose gloss is most similar to the context (cosine similarity
   with sentence-transformers/all-MiniLM-L6-v2 embeddings).
4. Look up the CEFR level of the corresponding sense_key in the CEFR-annotated
   WordNet published on Zenodo (10.5281/zenodo.17395388).

One-time setup:
    pip install sentence-transformers nltk numpy cefrpy
    python -m nltk.downloader wordnet omw-1.4
    # Download and extract:
    #   https://zenodo.org/records/17395388/files/CEFR-Annotated%20WordNet.zip
    # into resources/cefr_wordnet/

Usage:
    python analyze_cefr_contextual.py <input.json> [--window 5]

    # Deepgram format:
    python analyze_cefr_contextual.py Data/Student-1/lesson-1/01.json

    # Paragraphs format (processes all paragraphs, one output per paragraph):
    python analyze_cefr_contextual.py Data/format.json
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from cefrpy import CEFRAnalyzer
from nltk.corpus import wordnet as wn
from sentence_transformers import SentenceTransformer


MIN_WSD_SIMILARITY = 0.15  # minimum cosine similarity to accept a synset


LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2", "UNKNOWN"]

A1_WHITELIST = frozenset({
    "hello", "hi", "hey", "bye", "goodbye", "thanks", "please", "sorry",
    "yeah", "yep", "yes", "nope", "ok", "okay", "uh", "um", "oh", "ah",
    "hmm", "mhm", "wow",
    "don't", "doesn't", "didn't", "can't", "won't", "wouldn't", "couldn't",
    "shouldn't", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't",
    "hadn't", "i'm", "you're", "he's", "she's", "it's", "we're", "they're",
    "that's", "there's", "what's", "where's", "who's", "how's",
    "i've", "you've", "we've", "they've",
    "i'd", "you'd", "he'd", "she'd", "we'd", "they'd",
    "i'll", "you'll", "he'll", "she'll", "we'll", "they'll",
    "let's",
})

DEFAULT_WORDNET_TSV = Path("resources/cefr_wordnet/data/wordnet_sensekey_cefr.tsv")


def _variants(word):
    yield word
    if word.endswith("'s"):
        yield word[:-2]
    if "'" in word:
        yield word.split("'", 1)[0]


def load_sensekey_cefr(path: Path) -> dict:
    """Load the sense_key -> 'A1'..'C2' mapping from the Zenodo TSV."""
    mapping = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 2:
                mapping[parts[0]] = parts[1]
    return mapping


def synset_cefr_level(synset, sensekey_cefr: dict, target_word: str):
    """Return the CEFR level for the synset lemma matching target_word,
    or any lemma if no exact match. None if no level found."""
    target = target_word.lower()
    # Prefer the lemma that matches the transcribed word exactly
    matched_lemmas = [l for l in synset.lemmas() if l.name().lower().replace("_", " ") == target]
    for l in matched_lemmas + [l for l in synset.lemmas() if l not in matched_lemmas]:
        level = sensekey_cefr.get(l.key())
        if level is not None:
            return level
    return None


def lemma_fallback_level(word: str, sensekey_cefr: dict, pos=None):
    """Last resort: return the lowest CEFR level across all senses of the lemma.
    Used when WSD fails or the chosen synset's sense_key has no level."""
    best = None
    for synset in wn.synsets(word, pos=pos) if pos else wn.synsets(word):
        for lemma in synset.lemmas():
            level = sensekey_cefr.get(lemma.key())
            if level is None:
                continue
            if best is None or LEVELS.index(level) < LEVELS.index(best):
                best = level
    return best


def _lemmatize(word: str) -> str:
    """Lemmatize a word by trying all WordNet POS tags."""
    for pos in (wn.VERB, wn.NOUN, wn.ADJ, wn.ADV):
        lemma = wn.morphy(word, pos)
        if lemma and lemma != word:
            return lemma
    return word


def compute_synonym_groups(words_out: list) -> list:
    """Group words sharing the same synset that were expressed with ≥2 distinct lemmas.
    Filters out inflections of the same lemma (is/are, friend/friends)."""
    from collections import defaultdict
    synset_words: dict[str, dict] = defaultdict(lambda: {"words": set(), "lemmas": set(), "levels": set()})
    for w in words_out:
        src = w.get("source", "")
        if src.startswith("wsd:"):
            syn_name = src[4:]
            word_lower = w["word"].lower()
            synset_words[syn_name]["words"].add(word_lower)
            synset_words[syn_name]["lemmas"].add(_lemmatize(word_lower))
            synset_words[syn_name]["levels"].add(w["cefr_level"])

    groups = []
    for syn_name, info in sorted(synset_words.items()):
        if len(info["lemmas"]) >= 2:
            try:
                gloss = wn.synset(syn_name).definition()
            except Exception:
                gloss = ""
            groups.append({
                "synset": syn_name,
                "gloss": gloss,
                "words_used": sorted(info["words"]),
                "cefr_levels": sorted(info["levels"], key=lambda l: LEVELS.index(l)),
            })
    return groups


def compute_word_families(words_out: list) -> list:
    """Detect morphological word families using WordNet derivationally_related_forms()."""
    unique_words = {w["word"].lower() for w in words_out}
    word_levels = {}
    for w in words_out:
        wl = w["word"].lower()
        if wl not in word_levels:
            word_levels[wl] = w["cefr_level"]

    # Union-Find to cluster derivationally related words
    parent: dict[str, str] = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for word in unique_words:
        parent[word] = word
        for v in _variants(word):
            for synset in wn.synsets(v):
                # Only check lemmas matching the student's word
                for lemma in synset.lemmas():
                    if lemma.name().lower().replace("_", " ") != v:
                        continue
                    for related in lemma.derivationally_related_forms():
                        related_word = related.name().lower().replace("_", " ")
                        if related_word in unique_words and related_word != word:
                            parent.setdefault(related_word, related_word)
                            union(word, related_word)

    # Group by connected component
    from collections import defaultdict
    clusters: dict[str, set] = defaultdict(set)
    for word in unique_words:
        if word in parent:
            clusters[find(word)].add(word)

    families = []
    for members in clusters.values():
        if len(members) >= 2:
            sorted_members = sorted(members)
            levels = sorted(
                {word_levels[m] for m in members if m in word_levels},
                key=lambda l: LEVELS.index(l),
            )
            families.append({
                "family_root": sorted_members[0],
                "members_used": sorted_members,
                "cefr_levels": levels,
            })
    return sorted(families, key=lambda f: f["family_root"])


def compute_lexical_diversity(words_out: list, synonym_groups: list) -> dict:
    """Compute lexical diversity metrics (TTR, synonym variation, uniqueness by level)."""
    total = len(words_out)
    unique = len({w["word"].lower() for w in words_out})
    ttr = round(unique / total, 4) if total else 0.0

    # Unique-word ratio per CEFR level
    from collections import Counter, defaultdict
    level_total: Counter = Counter()
    level_unique: dict[str, set] = defaultdict(set)
    for w in words_out:
        lvl = w["cefr_level"]
        level_total[lvl] += 1
        level_unique[lvl].add(w["word"].lower())

    unique_ratio_by_level = {}
    for lvl in LEVELS:
        if level_total[lvl] > 0:
            unique_ratio_by_level[lvl] = round(
                len(level_unique[lvl]) / level_total[lvl], 4
            )

    return {
        "ttr": ttr,
        "synonym_variation_count": len(synonym_groups),
        "unique_ratio_by_level": unique_ratio_by_level,
    }


def build_classifier(sensekey_cefr: dict, window: int, model_name: str = "all-MiniLM-L6-v2"):
    print(f"[info] Loading model {model_name}...", file=sys.stderr)
    model = SentenceTransformer(model_name)
    cefrpy_analyzer = CEFRAnalyzer()

    # Gloss embedding cache keyed by synset.name()
    gloss_cache: dict[str, np.ndarray] = {}

    def embed(texts):
        return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    def classify_token(tokens: list[str], i: int):
        word = tokens[i].lower()

        # 1. Whitelist + digits: tokens without a useful WordNet synset
        if word.isdigit():
            return "A1", "digit"
        for v in _variants(word):
            if v in A1_WHITELIST:
                return "A1", "whitelist"

        # 2. Find candidate synsets (all POS) using word variants
        candidates = []
        used_variant = word
        for v in _variants(word):
            candidates = wn.synsets(v)
            if candidates:
                used_variant = v
                break

        if not candidates:
            for v in _variants(word):
                lv = cefrpy_analyzer.get_average_word_level_CEFR(v)
                if lv is not None:
                    return str(lv), "cefrpy"
            return "UNKNOWN", "no_synset"

        # 3. Build context from +-N token window
        lo = max(0, i - window)
        hi = min(len(tokens), i + window + 1)
        context = " ".join(tokens[lo:hi])

        # 3b. Embed context + glosses and pick the synset with highest similarity
        ctx_emb = embed([context])[0]
        missing = [s.name() for s in candidates if s.name() not in gloss_cache]
        if missing:
            new_embs = embed([wn.synset(n).definition() for n in missing])
            for n, e in zip(missing, new_embs):
                gloss_cache[n] = e
        gloss_embs = np.stack([gloss_cache[s.name()] for s in candidates])
        sims = gloss_embs @ ctx_emb  # cosine (already normalized)
        order = np.argsort(-sims)

        # 4. If best similarity exceeds threshold, walk the ranking
        #    looking for the first synset with a known CEFR level
        if sims[order[0]] >= MIN_WSD_SIMILARITY:
            for idx in order:
                if sims[idx] < MIN_WSD_SIMILARITY:
                    break
                level = synset_cefr_level(candidates[idx], sensekey_cefr, used_variant)
                if level is not None:
                    return level, f"wsd:{candidates[idx].name()}"

        # 5. Fallbacks: lemma_fallback (any sense with a level), then
        #    cefrpy (word-level, non-contextual), then UNKNOWN
        level = lemma_fallback_level(used_variant, sensekey_cefr)
        if level is not None:
            return level, "lemma_fallback"
        for v in _variants(word):
            lv = cefrpy_analyzer.get_average_word_level_CEFR(v)
            if lv is not None:
                return str(lv), "cefrpy"
        return "UNKNOWN", "none"

    return classify_token


def classify_words(raw_words: list[dict], classify_token) -> dict:
    """Classify a list of word dicts and compute stats. Format-agnostic.

    Each entry in raw_words must have at least {"word": str}.
    Optional: "start", "end", "confidence".
    """
    tokens = [w.get("word", "").strip() for w in raw_words]

    words_out = []
    for i, w in enumerate(raw_words):
        token = tokens[i]
        if not token:
            continue
        level, source = classify_token(tokens, i)
        entry = {
            "word": token,
            "confidence": w.get("confidence", 1.0),
            "cefr_level": level,
            "source": source,
        }
        if "start" in w:
            entry["start"] = w["start"]
        if "end" in w:
            entry["end"] = w["end"]
        words_out.append(entry)

    counts = Counter(item["cefr_level"] for item in words_out)
    total = len(words_out)
    distribution = {
        lvl: {
            "count": counts.get(lvl, 0),
            "percent": round(100 * counts.get(lvl, 0) / total, 2) if total else 0.0,
        }
        for lvl in LEVELS
    }
    unknown_types = sorted({it["word"] for it in words_out if it["cefr_level"] == "UNKNOWN"})

    synonym_groups = compute_synonym_groups(words_out)
    word_families = compute_word_families(words_out)
    lexical_diversity = compute_lexical_diversity(words_out, synonym_groups)

    stats = {
        "total_words": total,
        "unique_words": len({it["word"] for it in words_out}),
        "cefr_distribution": distribution,
        "unknown_words": unknown_types,
        "lexical_diversity": lexical_diversity,
        "synonym_groups": synonym_groups,
        "word_families": word_families,
    }

    return {"words": words_out, "stats": stats}


# ---------------------------------------------------------------------------
# Format: Deepgram
# ---------------------------------------------------------------------------


def analyze_deepgram(input_path: Path, window: int, wordnet_tsv: Path) -> dict:
    """Analyze a Deepgram transcription JSON (original format)."""
    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)
    raw_words = data["results"]["channels"][0]["alternatives"][0]["words"]

    sensekey_cefr = load_sensekey_cefr(wordnet_tsv)
    classify_token = build_classifier(sensekey_cefr, window)
    return classify_words(raw_words, classify_token)


# ---------------------------------------------------------------------------
# Format: Paragraphs JSON
# ---------------------------------------------------------------------------


_PUNCT_STRIP = re.compile(r'^[^\w]+|[^\w]+$')


def _tokenize_sentence(text: str) -> list[str]:
    """Split sentence text into word tokens, stripping surrounding punctuation."""
    tokens = []
    for raw in text.split():
        clean = _PUNCT_STRIP.sub("", raw)
        if clean:
            tokens.append(clean)
    return tokens


def load_paragraphs_format(path: Path) -> tuple[str, str, list[tuple[int, str, list[dict]]]]:
    """Load a paragraphs JSON and return (student, lesson, paragraphs_data).

    paragraphs_data is a list of (paragraph_id, label, raw_words) where
    raw_words follows the same dict format as Deepgram words.
    """
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    student = data["student"]
    lesson = data["lesson"]

    paragraphs_data = []
    for para in data["paragraphs"]:
        pid = para["paragraph_id"]
        label = para.get("label", "")
        raw_words = []
        for sent in para.get("sentences", []):
            for token in _tokenize_sentence(sent.get("text", "")):
                raw_words.append({"word": token, "confidence": 1.0})
        paragraphs_data.append((pid, label, raw_words))

    return student, lesson, paragraphs_data


def analyze_paragraphs(input_path: Path, window: int, wordnet_tsv: Path) -> dict:
    """Analyze a paragraphs-format JSON. Returns a single result dict.

    The output contains all words classified across all paragraphs, plus a
    per-paragraph breakdown in the "paragraphs" key.
    """
    student, lesson, paragraphs_data = load_paragraphs_format(input_path)

    sensekey_cefr = load_sensekey_cefr(wordnet_tsv)
    classify_token = build_classifier(sensekey_cefr, window)

    # Classify all words across all paragraphs as one flat token list
    # (so the context window can cross paragraph boundaries)
    all_raw_words = []
    paragraph_boundaries = []  # (start_idx, end_idx, pid, label)
    for pid, label, raw_words in paragraphs_data:
        start = len(all_raw_words)
        all_raw_words.extend(raw_words)
        end = len(all_raw_words)
        paragraph_boundaries.append((start, end, pid, label))

    result = classify_words(all_raw_words, classify_token)

    # Build per-paragraph breakdown from the classified words
    paragraphs_out = []
    for start, end, pid, label in paragraph_boundaries:
        para_words = result["words"][start:end]
        para_counts = Counter(w["cefr_level"] for w in para_words)
        para_total = len(para_words)
        para_dist = {
            lvl: {
                "count": para_counts.get(lvl, 0),
                "percent": round(100 * para_counts.get(lvl, 0) / para_total, 2) if para_total else 0.0,
            }
            for lvl in LEVELS
        }
        paragraphs_out.append({
            "paragraph_id": pid,
            "label": label,
            "total_words": para_total,
            "unique_words": len({w["word"] for w in para_words}),
            "cefr_distribution": para_dist,
        })

    result["student"] = student
    result["lesson"] = lesson
    result["paragraphs"] = paragraphs_out
    return result


# ---------------------------------------------------------------------------
# Format detection and CLI
# ---------------------------------------------------------------------------


def detect_format(input_path: Path) -> str:
    """Detect whether the input JSON is Deepgram or paragraphs format."""
    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)
    if "paragraphs" in data:
        return "paragraphs"
    return "deepgram"


def _print_result_summary(result: dict):
    """Print summary stats for a single analysis result."""
    print(f"  total_words={result['stats']['total_words']}  unique={result['stats']['unique_words']}")
    for lvl, d in result["stats"]["cefr_distribution"].items():
        print(f"  {lvl}: {d['count']} ({d['percent']}%)")

    ld = result["stats"]["lexical_diversity"]
    print(f"\n  Lexical diversity (TTR): {ld['ttr']}")
    print(f"  Synonym variation count: {ld['synonym_variation_count']}")
    for g in result["stats"]["synonym_groups"]:
        print(f"    synonym group: {g['words_used']} ({g['synset']}) -> {g['cefr_levels']}")
    if result["stats"]["word_families"]:
        print(f"  Word families found: {len(result['stats']['word_families'])}")
        for fam in result["stats"]["word_families"]:
            print(f"    family: {fam['members_used']} -> {fam['cefr_levels']}")


def main():
    parser = argparse.ArgumentParser(description="Contextual CEFR classifier.")
    parser.add_argument("input", help="Path to input JSON (Deepgram or paragraphs format)")
    parser.add_argument("--window", type=int, default=5, help="Context window size (+-N tokens)")
    parser.add_argument("--wordnet-path", type=Path, default=DEFAULT_WORDNET_TSV,
                        help="Path to wordnet_sensekey_cefr.tsv")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not args.wordnet_path.exists():
        print(f"[error] No encuentro el fichero CEFR-WordNet en {args.wordnet_path}", file=sys.stderr)
        print("        Descarga y descomprime el ZIP de Zenodo (ver docstring).", file=sys.stderr)
        sys.exit(1)

    fmt = detect_format(input_path)
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    if fmt == "paragraphs":
        print(f"[info] Detected paragraphs format", file=sys.stderr)
        result = analyze_paragraphs(input_path, args.window, args.wordnet_path)
        student = result["student"]
        lesson = result["lesson"]
        output_path = output_dir / f"{student}_{lesson}_contextual.json"
    else:
        result = analyze_deepgram(input_path, args.window, args.wordnet_path)
        parts = input_path.with_suffix("").parts[-3:]
        output_path = output_dir / ("_".join(parts) + "_contextual.json")

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Wrote {output_path}")
    _print_result_summary(result)


if __name__ == "__main__":
    main()
