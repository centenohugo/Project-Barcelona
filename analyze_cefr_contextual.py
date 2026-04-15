"""
Clasifica por nivel CEFR (A1-C2) cada palabra del canal 0 (alumno) de una
transcripción Deepgram, desambiguando el SENTIDO de la palabra según su contexto.

Enfoque (inspirado en Kikuchi et al. 2026, arXiv:2510.18466):
1. Para cada token se toma una ventana de +-N palabras como contexto.
2. Se recuperan los sentidos (synsets de WordNet) candidatos para la palabra.
3. Se elige el synset cuya glosa es más similar al contexto (cosine similarity
   con embeddings de sentence-transformers/all-MiniLM-L6-v2).
4. Se mira el nivel CEFR del sense_key correspondiente en la CEFR-annotated
   WordNet publicada en Zenodo (10.5281/zenodo.17395388).

Se analizan todos los tokens del canal del alumno. Palabras sin synset en
WordNet (interjecciones, contracciones, números) se resuelven por whitelist
o fallback a cefrpy; los nombres propios se protegen con un umbral mínimo
de similitud para no asignarles niveles altos espurios.

Preparación única:
    pip install sentence-transformers nltk numpy cefrpy
    python -m nltk.downloader wordnet omw-1.4
    # Descargar y descomprimir:
    #   https://zenodo.org/records/17395388/files/CEFR-Annotated%20WordNet.zip
    # en resources/cefr_wordnet/

Uso:   python analyze_cefr_contextual.py <input.json> [--window 5]
Input: JSON Deepgram con results.channels[0].alternatives[0].words[].
Output: output/<Student-X>_<lesson-Y>_<NN>_contextual.json con
        - words[]: {start, end, word, confidence, cefr_level}
        - stats:   total_words, unique_words, cefr_distribution, unknown_words
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from cefrpy import CEFRAnalyzer
from nltk.corpus import wordnet as wn
from sentence_transformers import SentenceTransformer


MIN_WSD_SIMILARITY = 0.15  # umbral mínimo de similitud coseno para aceptar un synset


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

A2_WHITELIST = frozenset({"smartphone"})

DEFAULT_WORDNET_TSV = Path("resources/cefr_wordnet/data/wordnet_sensekey_cefr.tsv")


def _variants(word):
    yield word
    if word.endswith("'s"):
        yield word[:-2]
    if "'" in word:
        yield word.split("'", 1)[0]


def load_sensekey_cefr(path: Path) -> dict:
    """Carga el mapping sense_key -> 'A1'..'C2' desde el TSV de Zenodo."""
    mapping = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 2:
                mapping[parts[0]] = parts[1]
    return mapping


def synset_cefr_level(synset, sensekey_cefr: dict, target_word: str):
    """Devuelve el nivel CEFR del lemma del synset que coincida con target_word,
    o de cualquier lemma si no hay coincidencia exacta. None si no hay nivel."""
    target = target_word.lower()
    # Preferimos el lemma que coincide con la palabra tal cual fue transcrita.
    matched_lemmas = [l for l in synset.lemmas() if l.name().lower().replace("_", " ") == target]
    for l in matched_lemmas + [l for l in synset.lemmas() if l not in matched_lemmas]:
        level = sensekey_cefr.get(l.key())
        if level is not None:
            return level
    return None


def lemma_fallback_level(word: str, sensekey_cefr: dict, pos=None):
    """Último recurso: toma la menor CEFR entre todos los sentidos del lemma.
    Útil cuando la WSD falla o cuando ningún sense_key del synset elegido tiene nivel."""
    best = None
    for synset in wn.synsets(word, pos=pos) if pos else wn.synsets(word):
        for lemma in synset.lemmas():
            level = sensekey_cefr.get(lemma.key())
            if level is None:
                continue
            if best is None or LEVELS.index(level) < LEVELS.index(best):
                best = level
    return best


def build_classifier(sensekey_cefr: dict, window: int, model_name: str = "all-MiniLM-L6-v2"):
    print(f"[info] Cargando modelo {model_name}...", file=sys.stderr)
    model = SentenceTransformer(model_name)
    cefrpy_analyzer = CEFRAnalyzer()

    # Cache de embeddings de glosa por synset.name()
    gloss_cache: dict[str, np.ndarray] = {}

    def embed(texts):
        return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    def classify_token(tokens: list[str], i: int):
        word = tokens[i].lower()

        # 1. Whitelist + dígitos: tokens sin synset útil en WordNet.
        if word.isdigit():
            return "A1", "digit"
        for v in _variants(word):
            if v in A1_WHITELIST:
                return "A1", "whitelist"
            if v in A2_WHITELIST:
                return "A2", "whitelist"

        # 2. Buscar synsets candidatos (todas las POS) con variantes.
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

        # 3. Construir contexto con ventana +-N.
        lo = max(0, i - window)
        hi = min(len(tokens), i + window + 1)
        context = " ".join(tokens[lo:hi])

        # 3. Embed contexto + glosas y elegir el synset con mayor similitud.
        ctx_emb = embed([context])[0]
        missing = [s.name() for s in candidates if s.name() not in gloss_cache]
        if missing:
            new_embs = embed([wn.synset(n).definition() for n in missing])
            for n, e in zip(missing, new_embs):
                gloss_cache[n] = e
        gloss_embs = np.stack([gloss_cache[s.name()] for s in candidates])
        sims = gloss_embs @ ctx_emb  # coseno (ya normalizados)
        order = np.argsort(-sims)

        # 4. Si la mejor similitud supera el umbral, recorrer el ranking
        #    buscando el primer synset con CEFR conocido.
        if sims[order[0]] >= MIN_WSD_SIMILARITY:
            for idx in order:
                if sims[idx] < MIN_WSD_SIMILARITY:
                    break
                level = synset_cefr_level(candidates[idx], sensekey_cefr, used_variant)
                if level is not None:
                    return level, f"wsd:{candidates[idx].name()}"

        # 5. Fallbacks: lemma_fallback (cualquier sentido con nivel), luego
        #    cefrpy (word-level, no contextual), luego UNKNOWN.
        level = lemma_fallback_level(used_variant, sensekey_cefr)
        if level is not None:
            return level, "lemma_fallback"
        for v in _variants(word):
            lv = cefrpy_analyzer.get_average_word_level_CEFR(v)
            if lv is not None:
                return str(lv), "cefrpy"
        return "UNKNOWN", "none"

    return classify_token


def analyze(input_path: Path, window: int, wordnet_tsv: Path) -> dict:
    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)
    raw_words = data["results"]["channels"][0]["alternatives"][0]["words"]

    sensekey_cefr = load_sensekey_cefr(wordnet_tsv)
    classify_token = build_classifier(sensekey_cefr, window)

    tokens = [w.get("word", "").strip() for w in raw_words]

    words_out = []
    for i, w in enumerate(raw_words):
        token = tokens[i]
        if not token:
            continue
        level, _ = classify_token(tokens, i)
        words_out.append({
            "start": w["start"],
            "end": w["end"],
            "word": token,
            "confidence": w["confidence"],
            "cefr_level": level,
        })

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

    stats = {
        "total_words": total,
        "unique_words": len({it["word"] for it in words_out}),
        "cefr_distribution": distribution,
        "unknown_words": unknown_types,
    }
    return {"words": words_out, "stats": stats}


def main():
    parser = argparse.ArgumentParser(description="Contextual CEFR classifier.")
    parser.add_argument("input", help="Path to Deepgram JSON file")
    parser.add_argument("--window", type=int, default=5, help="Context window size (+-N tokens)")
    parser.add_argument("--wordnet-path", type=Path, default=DEFAULT_WORDNET_TSV,
                        help="Path to wordnet_sensekey_cefr.tsv")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not args.wordnet_path.exists():
        print(f"[error] No encuentro el fichero CEFR-WordNet en {args.wordnet_path}", file=sys.stderr)
        print("        Descarga y descomprime el ZIP de Zenodo (ver docstring).", file=sys.stderr)
        sys.exit(1)

    result = analyze(input_path, args.window, args.wordnet_path)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    parts = input_path.with_suffix("").parts[-3:]
    output_path = output_dir / ("_".join(parts) + "_contextual.json")

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Wrote {output_path}")
    print(f"  total_words={result['stats']['total_words']}  unique={result['stats']['unique_words']}")
    for lvl, d in result["stats"]["cefr_distribution"].items():
        print(f"  {lvl}: {d['count']} ({d['percent']}%)")


if __name__ == "__main__":
    main()
