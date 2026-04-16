"""
rule_mapping.py — Maps LanguageTool rule IDs to grammar categories and
Proficiency Dimensions (A/B/C/D).

Two-level classification:
  grammar_category  — medium-level, teacher-readable label
                      (e.g. "subject-verb agreement", "article use")
  super_category    — one of the four Proficiency Dimensions:
                        A  Sentence Architecture
                        B  Tense & Aspect Mastery
                        C  Nominal Precision
                        D  Modal & Functional Range
"""

from __future__ import annotations

# ── Super-category labels ─────────────────────────────────────────────────────
SUPER_CATEGORY_LABELS: dict[str, str] = {
    "A": "Sentence Architecture",
    "B": "Tense & Aspect Mastery",
    "C": "Nominal Precision",
    "D": "Modal & Functional Range",
}

# ── Rule-ID blacklist ─────────────────────────────────────────────────────────
# Rules that are stylistic, overly permissive, or not relevant for learner
# grammar assessment. Matches are dropped regardless of category.
BLACKLIST: frozenset[str] = frozenset({
    "SENT_START_CONJUNCTION",       # "And …" / "But …" — valid in speech
    "TOO_LONG_SENTENCE",            # purely stylistic
    "COMMA_PARENTHESIS_WHITESPACE", # punctuation/spacing
    "DOUBLE_PUNCTUATION",           # punctuation
    "WHITESPACE_RULE",              # typography
    "UNPAIRED_BRACKETS",            # punctuation
    "EN_QUOTES",                    # typography
    "CURRENCY",                     # typography
    "DASH_RULE",                    # punctuation
    "WORD_CONTAINS_UNDERSCORE",     # formatting
    "SENTENCE_FRAGMENT",            # overly broad in learner speech turns
})

# ── Explicit rule-ID → (grammar_category, dimension) ─────────────────────────
# Checked before the keyword fallback. Keys are exact rule_id strings.
RULE_ID_MAP: dict[str, tuple[str, str]] = {
    # ── Dimension B: Tense & Aspect ──────────────────────────────────────────
    "BEEN_PART_AGREEMENT":         ("verb form in perfect aspect", "B"),
    "HAS_TO_APPROVED_BY":          ("verb form after auxiliary", "B"),
    "HE_VERB_AGR":                 ("subject-verb agreement", "B"),
    "SHE_VERB_AGR":                ("subject-verb agreement", "B"),
    "I_VERB_AGR":                  ("subject-verb agreement", "B"),
    "IT_VERB_AGR":                 ("subject-verb agreement", "B"),
    "THEY_VERB_AGR":               ("subject-verb agreement", "B"),
    "WE_VERB_AGR":                 ("subject-verb agreement", "B"),
    "YOU_VERB_AGR":                ("subject-verb agreement", "B"),
    "DO_VBZ":                      ("subject-verb agreement", "B"),
    "HAVE_VBZ":                    ("subject-verb agreement", "B"),
    "BE_VBZ":                      ("subject-verb agreement", "B"),
    "THERE_S_MANY":                ("subject-verb agreement", "B"),
    "AGREEMENT_SENT_START":        ("subject-verb agreement", "B"),
    "DID_BASEFORM":                ("verb form after auxiliary", "B"),
    "DOES_BASEFORM":               ("verb form after auxiliary", "B"),
    "DO_BASEFORM":                 ("verb form after auxiliary", "B"),
    "AM_BASEFORM":                 ("verb form after auxiliary", "B"),
    "IS_BASEFORM":                 ("verb form after auxiliary", "B"),
    "ARE_BASEFORM":                ("verb form after auxiliary", "B"),
    "WAS_BASEFORM":                ("verb form after auxiliary", "B"),
    "WERE_BASEFORM":               ("verb form after auxiliary", "B"),
    "I_AM_VB":                     ("verb form after auxiliary", "B"),
    "TO_VBD":                      ("verb form after 'to'", "B"),
    "HAVE_PART_AGREEMENT":         ("verb form in perfect aspect", "B"),
    "INGS_APPLIED":                ("gerund vs infinitive", "B"),
    "EN_TENSE_1":                  ("incorrect verb tense", "B"),
    "PRESENT_PERFECT_SIMPLE_PAST": ("verb tense choice", "B"),
    "PAST_CONTINUOUS_ASPECT":      ("aspect choice", "B"),
    "INCORRECT_WORD_IN_CONTEXT":   ("incorrect verb form", "B"),
    "MORFOLOGIK_RULE_EN_US":       ("incorrect word form", "B"),  # often irregular verbs

    # ── Dimension C: Nominal Precision ───────────────────────────────────────
    "EN_A_VS_AN":                  ("article choice (a/an)", "C"),
    "EN_A_VS_AN_SENT_START":       ("article choice (a/an)", "C"),
    "THE_SUPERLATIVE":             ("article with superlative", "C"),
    "THE_OPENING":                 ("article omission", "C"),
    "MISSING_GENITIVE":            ("genitive form", "C"),
    "PRP_VBZ":                     ("pronoun-verb agreement", "C"),
    "IT_S_ITS":                    ("its vs it's", "C"),
    "ITS_THEIR":                   ("pronoun choice", "C"),
    "FEWER_LESS":                  ("quantifier choice", "C"),
    "MUCH_MANY":                   ("quantifier choice", "C"),
    "SOME_ANY":                    ("determiner choice", "C"),
    "THIS_THAT":                   ("demonstrative choice", "C"),
    "ADJECTIVE_ADVERB_CONFUSION":  ("adjective vs adverb", "C"),
    "MISSING_PREPOSITION":         ("missing preposition", "C"),
    "WRONG_PREPOSITION":           ("incorrect preposition", "C"),
    "PREPOSITION_VERB":            ("preposition after verb", "C"),
    "NOUN_VERB_CONFUSION":         ("noun vs verb form", "C"),
    "NON_STANDARD_PLURAL":         ("irregular plural", "C"),
    "DT_DT":                       ("double determiner", "C"),

    # ── Dimension A: Sentence Architecture ───────────────────────────────────
    "COMMA_SPLICE":                ("comma splice / run-on", "A"),
    "RUN_ON_SENTENCE":             ("run-on sentence", "A"),
    "MISSING_SUBJECT":             ("missing subject", "A"),
    "ENGLISH_WORD_REPEAT_RULE":    ("word repetition", "A"),
    "WORD_REPEAT_RULE":            ("word repetition", "A"),
    "ENGLISH_WORD_REPEAT_BEGINNING_RULE": ("phrase repetition", "A"),
    "MISSING_COMMA_AFTER_INTRODUCTORY_PHRASE": ("sentence punctuation", "A"),
    "RELATIVE_CLAUSE_COMMA":       ("relative clause structure", "A"),
    "FRAGMENT_TWO_TOKENS":         ("sentence fragment", "A"),
    "SUBJECTLESS":                 ("missing subject", "A"),
    "CONFUSION_RULE":              ("word confusion", "A"),

    # ── Dimension D: Modal & Functional Range ─────────────────────────────────
    "IF_WOULD":                    ("conditional structure", "D"),
    "WOULD_RATHER":                ("modal expression", "D"),
    "MODAL_VERB":                  ("modal verb form", "D"),
    "CONDITIONAL_IF":              ("conditional clause", "D"),
    "SUBJUNCTIVE_MOOD":            ("subjunctive form", "D"),
    "CANT_HELP_CANNOT":            ("modal expression", "D"),
    "BE_ABLE_TO":                  ("modal equivalent", "D"),
    "WOULD_LIKE_TO":               ("polite request form", "D"),
}

# ── Keyword patterns for fallback classification ──────────────────────────────
# Checked in order; first match wins. Format: (keyword_in_rule_id, category_label, dimension)
_KEYWORD_PATTERNS: list[tuple[str, str, str]] = [
    # Dimension D
    ("MODAL",        "modal verb use",          "D"),
    ("CONDITIONAL",  "conditional structure",   "D"),
    ("IF_WOULD",     "conditional structure",   "D"),
    ("WOULD_IF",     "conditional structure",   "D"),
    ("SUBJUNCTIVE",  "subjunctive form",        "D"),
    # Dimension B
    ("TENSE",        "verb tense",              "B"),
    ("VERB_FORM",    "verb form",               "B"),
    ("AGREEMENT",    "subject-verb agreement",  "B"),
    ("VBZ",          "subject-verb agreement",  "B"),
    ("VBD",          "incorrect past form",     "B"),
    ("PAST",         "past tense",              "B"),
    ("PERFECT",      "perfect aspect",          "B"),
    ("BEEN_",        "verb form in perfect",    "B"),
    ("PASSIVE",      "passive voice",           "B"),
    ("CONTINUOUS",   "continuous aspect",       "B"),
    ("GERUND",       "gerund vs infinitive",    "B"),
    ("INFINITIVE",   "infinitive form",         "B"),
    ("PART_",        "participle form",         "B"),
    ("THIRD_PERSON", "third person agreement",  "B"),
    ("IRREGULAR",    "irregular verb form",     "B"),
    # Dimension C
    ("ARTICLE",      "article use",             "C"),
    ("A_VS_AN",      "article choice (a/an)",   "C"),
    ("DETERMINER",   "determiner use",          "C"),
    ("PRONOUN",      "pronoun use",             "C"),
    ("POSSESSIVE",   "possessive form",         "C"),
    ("PREPOSIT",     "preposition use",         "C"),
    ("PLURAL",       "plural form",             "C"),
    ("SINGULAR",     "singular form",           "C"),
    ("NOUN",         "noun form",               "C"),
    ("ADJECTIVE",    "adjective use",           "C"),
    ("ADVERB",       "adverb use",              "C"),
    ("QUANTIFIER",   "quantifier use",          "C"),
    # Dimension A
    ("SENTENCE",     "sentence structure",      "A"),
    ("CLAUSE",       "clause structure",        "A"),
    ("COMMA_SPLICE", "comma splice",            "A"),
    ("RUN_ON",       "run-on sentence",         "A"),
    ("CONJUNCTION",  "conjunction use",         "A"),
    ("RELATIVE",     "relative clause",         "A"),
    ("WORD_ORDER",   "word order",              "A"),
    ("REPEAT",       "word/phrase repetition",  "A"),
    ("FRAGMENT",     "sentence fragment",       "A"),
]


def classify_rule(
    rule_id: str,
    category: str,
    rule_issue_type: str,
    message: str,
) -> tuple[str, str, str] | None:
    """
    Classify a LanguageTool match into (grammar_category, dim_code, dim_label).

    Returns None if the match should be discarded (blacklisted, not grammar, etc.).

    Parameters
    ----------
    rule_id         : m.rule_id
    category        : m.category  (e.g. 'GRAMMAR', 'TYPOS', 'STYLE')
    rule_issue_type : m.rule_issue_type  (e.g. 'grammar', 'misspelling', 'style')
    message         : m.message
    """
    # ── 1. Blacklist ──────────────────────────────────────────────────────────
    if rule_id in BLACKLIST:
        return None

    # ── 2. Explicit rule-ID lookup (before category filter) ──────────────────
    # Curated rules are trusted regardless of LT's category/issue_type label,
    # e.g. MORFOLOGIK_RULE_EN_US is tagged TYPOS/misspelling but is really
    # a wrong verb form. Explicit mapping wins unconditionally.
    if rule_id in RULE_ID_MAP:
        cat_label, dim = RULE_ID_MAP[rule_id]
        return cat_label, dim, SUPER_CATEGORY_LABELS[dim]

    # ── 3. Category filter — only real grammar errors ────────────────────────
    # Keep GRAMMAR category (covers most structural errors).
    # Keep TYPOS with issue_type='grammar' — these are typically wrong word
    # FORMS (irregular verbs, wrong participle) tagged as spelling by LT.
    if category == "GRAMMAR" and rule_issue_type == "grammar":
        pass  # include
    elif category == "TYPOS" and rule_issue_type == "grammar":
        pass  # include: wrong verb form flagged as spelling
    else:
        return None  # skip STYLE, PUNCTUATION, TYPOGRAPHY, pure spelling

    # ── 4. Keyword fallback on rule_id (unknown grammar rules) ──────────────────
    rule_upper = rule_id.upper()
    for keyword, cat_label, dim in _KEYWORD_PATTERNS:
        if keyword in rule_upper:
            return cat_label, dim, SUPER_CATEGORY_LABELS[dim]

    # ── 5. Message-based fallback ─────────────────────────────────────────────
    msg_lower = message.lower()
    if any(w in msg_lower for w in ("verb", "tense", "past", "perfect", "agreement")):
        return "verb/tense error", "B", SUPER_CATEGORY_LABELS["B"]
    if any(w in msg_lower for w in ("article", "determiner", "pronoun", "noun", "adjective")):
        return "nominal error", "C", SUPER_CATEGORY_LABELS["C"]
    if any(w in msg_lower for w in ("modal", "conditional", "would", "could", "should")):
        return "modal/conditional error", "D", SUPER_CATEGORY_LABELS["D"]

    # Default: treat unclassified grammar errors as Nominal Precision
    return "grammar error", "C", SUPER_CATEGORY_LABELS["C"]
