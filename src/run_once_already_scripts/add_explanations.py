"""
add_explanations.py

Adds a human-readable 'explanation' field to every rule in the 4 active
strategy JSON files. The explanation tells a teacher (in plain English)
what grammatical structure was detected and why it matters.

Run from repo root:
    python scripts/add_explanations.py
"""

from __future__ import annotations
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

STRATEGY_FILES = [
    REPO_ROOT / "grammar_parser" / "structures" / "strategy1_lexical_trigger.json",
    REPO_ROOT / "grammar_parser" / "structures" / "strategy2_nominal_pos.json",
    REPO_ROOT / "grammar_parser" / "structures" / "strategy3_verbal_morphology.json",
    REPO_ROOT / "grammar_parser" / "structures" / "strategy4_syntactic_structure.json",
]

# ---------------------------------------------------------------------------
# Explanations keyed by (category, guideword).
# guideword is matched after stripping leading/trailing whitespace.
# ---------------------------------------------------------------------------
EXPLANATIONS: dict[tuple[str, str], str] = {

    # ── STRATEGY 1: LEXICAL TRIGGER ─────────────────────────────────────────

    # MODALITY A2
    ("MODALITY", "FORM/USE: 'WILL BE ABLE TO'"): (
        "Future ability — 'will be able to' expresses capability in the future "
        "(e.g. 'I will be able to help you tomorrow')."
    ),
    ("MODALITY", "FORM/USE: AFTER 'IF', FUTURE SITUATIONS"): (
        "Conditional modal — modal verb in the main clause of an 'if' sentence, "
        "describing a possible outcome (e.g. 'If you come, I'll be happy')."
    ),
    ("MODALITY", "FORM/USE: MID POSITION, HEDGING OR EMPHASIS"): (
        "Modal adverb in mid-position — adverb placed between subject and main verb "
        "to soften or emphasise (e.g. 'I will probably go')."
    ),
    ("MODALITY", "FORM: 'BE' + 'SURE' + CLAUSE"): (
        "'Be sure' structure — expresses certainty or strong advice "
        "(e.g. 'Be sure to call me')."
    ),
    ("MODALITY", "FORM: AFFIRMATIVE"): (
        "Modal verb in a positive statement — use of can, could, will, would, "
        "should, must, etc. in affirmative form."
    ),
    ("MODALITY", "FORM: CLAUSE POSITION"): (
        "Modal verb inside a clause — modal verb appearing in a dependent or "
        "subordinate clause."
    ),
    ("MODALITY", "FORM: NEGATIVE"): (
        "Modal verb in negative — negated modal (can't, won't, shouldn't, etc.) "
        "to say something is not possible, allowed, or advisable."
    ),
    ("MODALITY", "FORM: QUESTIONS WITH 'LIKE'"): (
        "Modal question with 'like' — used to make polite invitations or ask "
        "about preferences (e.g. 'Would you like a coffee?')."
    ),
    ("MODALITY", "USE: ADVICE"): (
        "Giving advice — modal verb recommending a course of action "
        "(e.g. 'You should see a doctor')."
    ),
    ("MODALITY", "USE: IMAGINED SITUATIONS"): (
        "Hypothetical — modal used for imaginary or unreal situations "
        "(e.g. 'I would love to travel more')."
    ),
    ("MODALITY", "USE: OBLIGATION"): (
        "Expressing obligation — modal indicating something is required "
        "(e.g. 'You must wear a seatbelt')."
    ),
    ("MODALITY", "USE: OBLIGATION AND NECESSITY"): (
        "Obligation and necessity — modal expressing both a requirement and its "
        "urgency (e.g. 'You have to submit it today')."
    ),
    ("MODALITY", "USE: PERMISSION"): (
        "Permission — modal used to ask for or grant permission "
        "(e.g. 'Can I leave early?', 'You may go')."
    ),
    ("MODALITY", "USE: SUGGESTIONS"): (
        "Making a suggestion — modal proposing an action "
        "(e.g. 'We could try a different route')."
    ),
    ("MODALITY", "USE: SUGGESTIONS WITH 'IT WOULD BE'"): (
        "Indirect suggestion with 'it would be' — softened suggestion structure "
        "(e.g. 'It would be great to meet up')."
    ),
    ("MODALITY", "USE: WILLINGNESS, OFFERS"): (
        "Willingness and offers — 'will' expressing readiness or making an offer "
        "(e.g. 'I'll carry that for you')."
    ),
    ("MODALITY", "USE: WISHES AND PREFERENCES"): (
        "Wishes and preferences — modal expressing what one wants or prefers "
        "(e.g. 'I'd rather stay home', 'I'd love to go')."
    ),
    # MODALITY B1
    ("MODALITY", "USE: WILLINGNESS IN THE PAST"): (
        "Past willingness — 'would' describing readiness or refusal in a past "
        "situation (e.g. 'He wouldn't help me')."
    ),
    # MODALITY B2
    ("MODALITY", "FORM: 'SHOULD BE' + '-ING'"): (
        "'Should be' + continuous — describes what is expected to be happening "
        "right now (e.g. 'You should be studying')."
    ),
    # MODALITY C1
    ("MODALITY", "FORM/USE: 'MAY WELL'"): (
        "'May well' — expresses a strong possibility with a formal or hedged tone "
        "(e.g. 'He may well be right')."
    ),
    # MODALITY C2
    ("MODALITY", "FORM/USE: 'MAY AS WELL'"): (
        "'May as well' — suggests an action is the best option given the "
        "circumstances (e.g. 'We may as well leave now')."
    ),
    ("MODALITY", "FORM: 'MIGHT AS WELL'"): (
        "'Might as well' — resigned acceptance of the best available option "
        "(e.g. 'I might as well try')."
    ),
    ("MODALITY", "USE: WILLFULNESS OR DISAPPROVAL"): (
        "Expressing disapproval — 'will/would' to show annoyance at a repeated "
        "behaviour (e.g. 'He will keep interrupting')."
    ),

    # DISCOURSE MARKERS A2
    ("DISCOURSE MARKERS", "FORM/USE: 'AS YOU KNOW', ORGANISING, MARKING SHARED KNOWLEDGE"): (
        "'As you know' — signals information both speakers share, used to organise "
        "speech and avoid repetition."
    ),
    ("DISCOURSE MARKERS", "FORM/USE: 'SO', SUMMARISING, INFORMAL"): (
        "'So' as a connector — 'so' at the start of a turn to summarise, conclude, "
        "or introduce a topic shift."
    ),

    # NEGATION A2
    ("NEGATION", "FORM: PRONOUNS"): (
        "Negative pronouns — 'nobody', 'nothing', 'nowhere' express total negation "
        "without using 'not' (e.g. 'Nobody came')."
    ),
    # NEGATION B1
    ("NEGATION", "FORM: 'NOT', NON FINITE AND ELLIPTED CLAUSES"): (
        "Negating a non-finite clause — 'not' before an infinitive or participle "
        "(e.g. 'She told me not to worry', 'Not knowing what to do...')."
    ),
    # NEGATION B2
    ("NEGATION", "FORM/USE: 'NEITHER … NOR'"): (
        "'Neither … nor' — correlative structure negating two alternatives at once "
        "(e.g. 'Neither the food nor the service was good')."
    ),
    ("NEGATION", "FORM/USE: 'NEVER', INVERTED FRONT POSITION, FOCUS"): (
        "Fronted 'never' with inversion — 'never' moved to the front for emphasis, "
        "triggering subject-auxiliary inversion (e.g. 'Never have I seen such a mess')."
    ),
    ("NEGATION", "FORM: 'NEITHER OF', 'NONE OF' + PRONOUN"): (
        "'Neither of / none of' + pronoun — negative quantifier before a pronoun "
        "referring to a group (e.g. 'None of them arrived')."
    ),

    # ── STRATEGY 2: NOMINAL POS ──────────────────────────────────────────────

    # DETERMINERS A2
    ("DETERMINERS", "FORM: 'MANY' WITH PLURAL NOUNS, NEGATIVE"): (
        "'Not many' — negative quantifier for countable nouns expressing a small "
        "number (e.g. 'There aren't many people here')."
    ),
    ("DETERMINERS", "FORM: 'MUCH' WITH UNCOUNTABLE NOUNS, NEGATIVE"): (
        "'Not much' — negative quantifier for uncountable nouns expressing a small "
        "amount (e.g. 'There isn't much time')."
    ),
    ("DETERMINERS", "FORM: 'THESE'"): (
        "'These' — plural demonstrative pointing to things nearby "
        "(e.g. 'These books are mine')."
    ),
    ("DETERMINERS", "FORM: 'THOSE'"): (
        "'Those' — plural demonstrative pointing to things further away "
        "(e.g. 'Those shoes look great')."
    ),

    # PRONOUNS A2
    ("PRONOUNS", "FORM: 'MINE'"): (
        "'Mine' — first-person possessive pronoun replacing a noun phrase "
        "(e.g. 'That bag is mine')."
    ),
    ("PRONOUNS", "FORM: 'ONE'"): (
        "'One' — impersonal pronoun referring to people in general, or substituting "
        "for a previously mentioned noun (e.g. 'One never knows')."
    ),
    ("PRONOUNS", "FORM: 'THAT'"): (
        "'That' as demonstrative pronoun — replaces a noun already mentioned "
        "(e.g. 'I prefer that')."
    ),
    ("PRONOUNS", "FORM: 'YOURS' AS OBJECT"): (
        "'Yours' as object — second-person possessive pronoun used as the object "
        "(e.g. 'I took yours by mistake')."
    ),
    ("PRONOUNS", "FORM: NEGATIVE + 'ANYTHING'"): (
        "Negative 'anything' — 'not + anything' (or 'nothing') to express a "
        "complete absence (e.g. 'I don't know anything about it')."
    ),
    ("PRONOUNS", "USE: 'SOMETHING' IN VAGUE EXPRESSIONS"): (
        "'Something' in vague language — refers to an unspecified thing or softens "
        "a statement (e.g. 'There's something about this place')."
    ),

    # ADJECTIVES A2
    ("ADJECTIVES", "FORM: WITH DEGREE ADVERBS"): (
        "Adjective with degree adverb — intensifier or softener modifying an "
        "adjective (e.g. 'very big', 'quite interesting', 'rather cold')."
    ),

    # DETERMINERS B1
    ("DETERMINERS", "FORM: 'ANOTHER' |"): (
        "'Another' — determiner meaning 'one more' or 'a different one' "
        "(e.g. 'Can I have another coffee?')."
    ),

    # PRONOUNS B1
    ("PRONOUNS", "FORM: 'ONES'"): (
        "'Ones' — pronoun substituting for a plural noun already mentioned "
        "(e.g. 'The red ones are better')."
    ),
    ("PRONOUNS", "FORM: COMPARATIVE CLAUSES WITH 'MINE', 'YOURS'"): (
        "Possessive pronoun in comparisons — 'mine'/'yours' inside a comparative "
        "clause (e.g. 'Her score is higher than mine')."
    ),

    # ADVERBS B2
    ("ADVERBS", "FORM/USE: FRONT POSITION, INVERSION WITH 'NEVER'"): (
        "Fronted 'never' with inversion — 'never' at the front of a clause for "
        "emphasis, followed by auxiliary before subject "
        "(e.g. 'Never had I felt so tired')."
    ),

    # PRONOUNS B2
    ("PRONOUNS", "FORM: 'HERS' AS OBJECT"): (
        "'Hers' as object — third-person feminine possessive pronoun "
        "(e.g. 'I borrowed hers')."
    ),
    ("PRONOUNS", "FORM: 'OURS' AS OBJECT"): (
        "'Ours' as object — first-person plural possessive pronoun "
        "(e.g. 'They took ours by mistake')."
    ),
    ("PRONOUNS", "FORM: 'THEIRS' AS OBJECT"): (
        "'Theirs' as object — third-person plural possessive pronoun "
        "(e.g. 'We saw theirs first')."
    ),
    ("PRONOUNS", "FORM: COMPARATIVE CLAUSES WITH 'OURS', 'HERS'"): (
        "Possessive pronoun in comparisons — 'ours'/'hers' in a comparative "
        "structure (e.g. 'Their house is bigger than ours')."
    ),
    ("PRONOUNS", "USE: 'ITSELF', FOR EMPHASIS"): (
        "'Itself' for emphasis — reflexive pronoun stressing that no one else is "
        "involved (e.g. 'The problem solved itself')."
    ),
    ("PRONOUNS", "USE: 'YOURSELVES', FOR POLITENESS"): (
        "'Yourselves' for politeness — reflexive used to address a group in a "
        "welcoming way (e.g. 'Please help yourselves')."
    ),

    # DETERMINERS C1
    ("DETERMINERS", "FORM: 'EITHER', 'NEITHER' WITH SINGULAR NOUNS"): (
        "'Either'/'neither' with singular noun — used to choose between or exclude "
        "two options (e.g. 'Either option works', 'Neither side agreed')."
    ),

    # ADVERBS C2
    ("ADVERBS", "FORM/USE: FRONT POSITION, INVERSION, WITH 'HARDLY'"): (
        "Fronted 'hardly' with inversion — negative adverb 'hardly' in initial "
        "position triggers subject-auxiliary inversion "
        "(e.g. 'Hardly had she left when it started raining')."
    ),

    # PRONOUNS C2
    ("PRONOUNS", "FORM: 'HIS'"): (
        "'His' as standalone pronoun — masculine possessive pronoun used alone as a "
        "noun phrase (e.g. 'Is that jacket his?')."
    ),
    ("PRONOUNS", "FORM: OF 'THEIRS', 'HERS', 'HIS'"): (
        "Double possessive — possessive pronoun after 'of' to express one of several "
        "belonging to someone (e.g. 'a friend of hers', 'that idea of his')."
    ),

    # ── STRATEGY 3: VERBAL MORPHOLOGY ────────────────────────────────────────

    # PRESENT A2
    ("PRESENT", "FORM/USE: REAL AND IMAGINED SITUATIONS AFTER 'IF'"): (
        "Present simple in 'if' clauses — present tense in the condition of a real "
        "or likely conditional (e.g. 'If you need help, just ask')."
    ),

    # PAST A2
    ("PAST", "FORM/USE: TIME WITH 'FOR'"): (
        "Past with 'for' — verb indicating duration in the past, used with 'for' "
        "(e.g. 'I waited for an hour', 'She had been waiting for days')."
    ),
    ("PAST", "FORM/USE: WITH 'YET'"): (
        "Past with 'yet' — present perfect asking or stating whether something "
        "expected has happened (e.g. 'Have you finished yet?', 'She hasn't arrived yet')."
    ),
    ("PAST", "FORM: WITH 'WHEN'"): (
        "Past in 'when' clauses — past tense describing what happened at a specific "
        "time (e.g. 'I was reading when she called')."
    ),

    # PASSIVES A2
    ("PASSIVES", "FORM/USE: WITH 'BY' TO ADD INFORMATION"): (
        "Passive with 'by' — passive construction that identifies the agent "
        "(e.g. 'The book was written by Hemingway')."
    ),
    ("PASSIVES", "FORM: PAST SIMPLE, AFFIRMATIVE"): (
        "Simple past passive — describes something done to the subject in the past "
        "(e.g. 'The car was repaired')."
    ),

    # PAST B1
    ("PAST", "FORM/USE: AFTER 'IF' CLAUSES"): (
        "Past in hypothetical 'if' clauses — past tense used for imaginary or "
        "unreal conditions (e.g. 'If I had more time, I would...')."
    ),
    ("PAST", "FORM/USE: DURATION WITH 'SINCE'"): (
        "Past with 'since' — present perfect indicating an ongoing situation that "
        "started at a point in the past (e.g. 'I've lived here since 2010')."
    ),
    ("PAST", "FORM/USE: WITH 'ALREADY'"): (
        "Past with 'already' — present perfect showing something happened before "
        "expected or earlier than usual (e.g. 'She has already left')."
    ),
    ("PAST", "FORM: AFFIRMATIVE"): (
        "Affirmative past tense — regular or irregular verb in the simple past, "
        "positive form (e.g. 'He walked', 'She went')."
    ),

    # PASSIVES B1
    ("PASSIVES", "FORM: 'GET' + '-ED'"): (
        "Get-passive — informal passive using 'get' instead of 'be' "
        "(e.g. 'He got fired last week')."
    ),
    ("PASSIVES", "FORM: INFINITIVE"): (
        "Passive infinitive — 'to be + past participle' as a passive construction "
        "(e.g. 'It needs to be fixed', 'She wants to be promoted')."
    ),
    ("PASSIVES", "USE: PRESENT CONTINUOUS, FUTURE REFERENCE"): (
        "Passive continuous with future reference — passive in present continuous "
        "to describe a planned upcoming event (e.g. 'The building is being renovated next year')."
    ),

    # PASSIVES B2
    ("PASSIVES", "FORM/USE: 'HAVE' + OBJ + '-ED', PROACTIVE PASSIVE"): (
        "Causative 'have' — 'have something done' means arranging for someone else "
        "to do something for you (e.g. 'I had my hair cut')."
    ),
    ("PASSIVES", "FORM: PAST SIMPLE NEGATIVE"): (
        "Negative past passive — 'was/were not + past participle' "
        "(e.g. 'The report wasn't submitted on time')."
    ),

    # PAST B2
    ("PAST", "FORM/USE: AFTER 'BECAUSE', EXPLANATIONS"): (
        "Past tense in 'because' clauses — past verb in a reason clause explaining "
        "why something happened (e.g. 'She left because she was tired')."
    ),
    ("PAST", "FORM/USE: AFTER 'IF ONLY' AND 'WISH', IMAGINED PAST"): (
        "'Wish'/'if only' + past — expressing regret or a wish to change a present "
        "or past situation (e.g. 'I wish I had more time', 'If only I had known')."
    ),
    ("PAST", "FORM/USE: WITH 'STILL'"): (
        "Past with 'still' — past perfect or simple past showing a situation "
        "continued into a past moment (e.g. 'She was still working at midnight')."
    ),

    # PASSIVES C1
    ("PASSIVES", "FORM/USE: SUMMARISING, EVALUATING WITH 'IT'."): (
        "Impersonal passive with 'it' — 'it is said/reported/believed that' to "
        "describe general opinion or formally attributed information "
        "(e.g. 'It is believed that the building dates from 1800')."
    ),

    # PAST C1
    ("PAST", "USE: FOR EMPHASIS, WITH 'DID'"): (
        "Emphatic 'did' — auxiliary 'did' added in a positive sentence for "
        "emphasis or to contradict a negative assumption "
        "(e.g. 'I did try my best!')."
    ),

    # PAST C2
    ("PAST", "FORM/USE: AFTER 'IF ONLY', IMAGINED PAST"): (
        "'If only' + past perfect — expressing strong regret about a past situation "
        "that cannot be changed (e.g. 'If only I had listened to her')."
    ),

    # VERBS A2
    ("VERBS", "FORM: 'ENJOY' + '-ING'"): (
        "'Enjoy' + gerund — verb 'enjoy' is always followed by a verb in -ing form "
        "(e.g. 'She enjoys painting', 'Do you enjoy cooking?')."
    ),
    ("VERBS", "FORM: 'THERE IS' + UNCOUNTABLE"): (
        "'There is' with uncountable noun — existential structure stating the "
        "existence of an uncountable thing (e.g. 'There is some water')."
    ),
    ("VERBS", "FORM: 'THERE IS/ARE' + A LOT OF"): (
        "'There is/are a lot of' — existential structure expressing a large quantity "
        "(e.g. 'There are a lot of people here')."
    ),
    ("VERBS", "FORM: AUXILIARY VERBS 'HAVE' AND 'DO'"): (
        "Auxiliary 'have'/'do' — helper verb forming questions, negatives, or "
        "perfect tenses (e.g. 'Does she know?', 'Have you seen it?')."
    ),
    ("VERBS", "FORM: LINKING + COMPLEMENT"): (
        "Linking verb with complement — verb like 'seem', 'become', 'appear' "
        "connecting the subject to a description (e.g. 'He seems tired')."
    ),
    ("VERBS", "FORM: LINKING VERBS + ADJECTIVE"): (
        "Linking verb + adjective — state verb followed by a describing adjective "
        "(e.g. 'She looks happy', 'It tastes good')."
    ),
    ("VERBS", "FORM: REPORTING VERBS + DIRECT OBJECT 'THAT'-CLAUSE"): (
        "Reporting verb + 'that' clause — verb of thinking/saying followed by a "
        "'that' clause (e.g. 'She told me that she was leaving')."
    ),
    ("VERBS", "FORM: VERB + 'TO'- INFINITIVE"): (
        "Verb + to-infinitive — verb followed by another verb in 'to + base form' "
        "(e.g. 'I want to go', 'She decided to stay')."
    ),
    ("VERBS", "FORM: VERB + PRONOUN + PARTICLE"): (
        "Separable phrasal verb — object pronoun placed between the verb and its "
        "particle (e.g. 'Turn it off', 'Pick them up')."
    ),
    ("VERBS", "FORM: VERBS + 'TO'-INFINITIVE OR + '-ING'"): (
        "Verb + infinitive or gerund — verb that can be followed by either "
        "'to + verb' or '-ing' form (e.g. 'start to run' / 'start running')."
    ),
    ("VERBS", "FORM: VERBS + DIRECT OBJECT CLAUSE WITHOUT 'THAT'"): (
        "Reporting verb without 'that' — verb of saying/thinking followed by a "
        "clause with no 'that' connector (e.g. 'I think you're right')."
    ),

    # FUTURE A2
    ("FUTURE", "FORM: AFFIRMATIVE WITH 'WILL'"): (
        "'Will' in positive statements — 'will + base verb' for future predictions "
        "or decisions (e.g. 'It will rain tomorrow')."
    ),
    ("FUTURE", "FORM: NEGATIVE 'WILL'"): (
        "'Won't' — 'will not/won't + base verb' for future negatives "
        "(e.g. 'She won't come')."
    ),
    ("FUTURE", "FORM: WITH 'WHEN'"): (
        "Future in 'when' clauses — present tense used in a 'when' clause that "
        "refers to the future (e.g. 'I'll call you when I arrive')."
    ),
    ("FUTURE", "USE: 'HOPE'"): (
        "'Hope' for the future — 'hope + present/future' to express a desired "
        "outcome (e.g. 'I hope it goes well')."
    ),
    ("FUTURE", "USE: FUTURE ARRANGEMENTS"): (
        "Arranged future — present continuous or 'going to' for fixed plans "
        "already organised (e.g. 'We are meeting tomorrow')."
    ),
    ("FUTURE", "USE: PLANS AND  INTENTIONS WITH 'WILL'"): (
        "Spontaneous plans with 'will' — 'will' for on-the-spot decisions or "
        "stated intentions (e.g. 'I'll help you with that')."
    ),
    ("FUTURE", "USE: REQUESTS WITH 'WILL'"): (
        "Requests with 'will' — 'will you...?' to make a request "
        "(e.g. 'Will you help me?')."
    ),
    ("FUTURE", "USE: WILLINGNESS WITH 'WILL'"): (
        "Willingness with 'will' — 'will' expressing voluntary agreement or offer "
        "(e.g. 'I'll do it', 'I will if you want')."
    ),

    # VERBS B1
    ("VERBS", "FORM: 'MAKE', 'LET' + INFINITIVE WITHOUT 'TO'"): (
        "'Make'/'let' + bare infinitive — causative or permissive verb followed by "
        "an object and a base-form verb "
        "(e.g. 'She made me laugh', 'Let me go')."
    ),
    ("VERBS", "FORM: 'THERE' + MODAL VERBS"): (
        "'There' with modal verb — existential structure using a modal "
        "(e.g. 'There must be a solution', 'There should be more options')."
    ),
    ("VERBS", "FORM: VERB + 'TO-' INFINITIVE"): (
        "B1 verb + to-infinitive — wider range of verbs followed by 'to + verb' "
        "(e.g. 'She refused to leave', 'He managed to escape')."
    ),
    ("VERBS", "FORM: VERBS + DIRECT OBJECT + 'TO' INFINITIVE"): (
        "Verb + object + to-infinitive — object placed before the infinitive "
        "(e.g. 'She asked him to stay', 'I want you to understand')."
    ),
    ("VERBS", "FORM: VERBS + PREPOSITIONAL PHRASE + 'THAT'-CLAUSE"): (
        "Verb + prepositional phrase + 'that' clause — complex reporting structure "
        "(e.g. 'He reminded me that I should call')."
    ),

    # FUTURE B1
    ("FUTURE", "FORM: NEGATIVE WITH 'WILL'"): (
        "Future negative B1 — 'will not/won't' in complex future contexts or with "
        "conditional nuance."
    ),
    ("FUTURE", "USE: 'BE GOING TO'"): (
        "'Going to' — 'be going to + verb' for plans, intentions, or predictions "
        "based on present evidence (e.g. 'It's going to rain')."
    ),
    ("FUTURE", "USE: FIXED PLANS WITH 'WILL'"): (
        "Confirmed future with 'will' — 'will' for decisions already made or "
        "firm commitments (e.g. 'I will be there at 8')."
    ),
    ("FUTURE", "USE: PREDICTIONS WITH 'WILL'"): (
        "Predictions with 'will' — 'will' to make predictions about the future "
        "(e.g. 'She will probably pass the exam')."
    ),

    # VERBS B2
    ("VERBS", "FORM: 'THERE' + VERBS WITH MODAL MEANING"): (
        "'There' + semi-modal — existential with a verb carrying modal meaning "
        "(e.g. 'There seems to be a problem', 'There happens to be one left')."
    ),
    ("VERBS", "FORM: 'TO'-INFINITIVE OR '-ING' FORM, MEANING"): (
        "Infinitive vs gerund — the same verb changes meaning depending on whether "
        "it is followed by 'to' or '-ing' "
        "(e.g. 'stop to think' vs 'stop thinking')."
    ),
    ("VERBS", "FORM: PREPOSITIONAL VERB, STRANDED PREPOSITION"): (
        "Stranded preposition — prepositional verb where the preposition is "
        "separated from its object, often at end of clause "
        "(e.g. 'the problem I was talking about')."
    ),

    # VERBS C1
    ("VERBS", "FORM: PHRASAL-PREPOSITIONAL VERB, STRANDED PREPOSITION"): (
        "Phrasal-prepositional verb — complex verb (verb + particle + preposition) "
        "with the preposition at the end of the clause "
        "(e.g. 'something to put up with')."
    ),

    # ── STRATEGY 4: SYNTACTIC STRUCTURE ─────────────────────────────────────

    # CLAUSES A2
    ("CLAUSES", "FORM/USE: 'LET'S', SUGGESTION"): (
        "'Let's' suggestion — 'let's + base verb' to propose doing something "
        "together (e.g. 'Let's go for a walk')."
    ),
    ("CLAUSES", "FORM: 'IF' + PRESENT SIMPLE"): (
        "Real conditional — 'if' + present simple in the condition clause, "
        "describing a genuine possibility (e.g. 'If you come early, we can chat')."
    ),
    ("CLAUSES", "FORM: DEFINING, OBJECT, WITH 'THAT'"): (
        "Defining relative clause with 'that' (object) — 'that' introduces a clause "
        "that identifies the noun, which is the object of the relative clause "
        "(e.g. 'the film that I watched')."
    ),
    ("CLAUSES", "FORM: DEFINING, OBJECT, WITH 'WHICH'"): (
        "Defining relative clause with 'which' (object) — 'which' identifies a "
        "thing that is the object of the relative clause "
        "(e.g. 'the car which I bought')."
    ),
    ("CLAUSES", "FORM: DEFINING, SUBJECT, WITH 'WHO'"): (
        "Defining relative clause with 'who' (subject) — 'who' introduces a clause "
        "identifying the person by what they do "
        "(e.g. 'the woman who called', 'the man who lives next door')."
    ),
    ("CLAUSES", "FORM: NEGATIVE DECLARATIVE WITH 'HAVE'"): (
        "Negative 'have' — 'don't/doesn't/didn't have' stating the absence of "
        "something (e.g. 'I don't have any money', 'She didn't have time')."
    ),

    # REPORTED SPEECH A2
    ("REPORTED SPEECH", "FORM: REPORTED STATEMENTS WITH 'SAY', PRONOUN SHIFT"): (
        "Reported speech with 'say' — converting direct speech to indirect using "
        "'say', with tense backshift and pronoun changes "
        "(e.g. 'He said he was tired')."
    ),
    ("REPORTED SPEECH", "FORM: REPORTED STATEMENTS WITH 'TELL', PRONOUN SHIFT"): (
        "Reported speech with 'tell' — converting direct speech using 'tell + person', "
        "with tense and pronoun backshift "
        "(e.g. 'She told me she would come')."
    ),

    # CLAUSES B1
    ("CLAUSES", "FORM/USE: 'DO', EMPHASIS"): (
        "Emphatic 'do' — auxiliary 'do/does/did' in an affirmative clause to add "
        "emphasis or contradict a prior statement "
        "(e.g. 'I do like your idea', 'She did warn us')."
    ),
    ("CLAUSES", "FORM/USE: 'LET ME', FOCUS"): (
        "'Let me' + focus — 'let me + verb' to introduce an offer, clarification, "
        "or example (e.g. 'Let me explain', 'Let me show you')."
    ),
    ("CLAUSES", "FORM/USE: 'RATHER THAN' + PHRASE"): (
        "'Rather than' contrast — shows preference or contrast between two options "
        "(e.g. 'She studied rather than going out')."
    ),
    ("CLAUSES", "FORM/USE: 'UNLESS', EXCEPTIONS"): (
        "'Unless' condition — negative conditional meaning 'except if' "
        "(e.g. 'I'll go unless it rains', 'Don't call unless it's urgent')."
    ),
    ("CLAUSES", "FORM/USE: 'WHEN', FOCUS"): (
        "'When' clause — temporal or focusing clause introduced by 'when' "
        "(e.g. 'When I was young, I loved climbing')."
    ),
    ("CLAUSES", "FORM: 'HOW' + ADJECTIVE"): (
        "'How + adjective' — exclamatory or embedded question structure "
        "(e.g. 'How strange!', 'I know how difficult it is')."
    ),
    ("CLAUSES", "FORM: 'TOO' + 'TO'-INFINITIVE"): (
        "'Too + to-infinitive' — 'too + adjective/adverb + to + verb' expresses "
        "that something is excessive and prevents an action "
        "(e.g. 'It's too heavy to lift')."
    ),
    ("CLAUSES", "FORM: SENSE VERBS + 'AS IF' OR 'AS THOUGH' + FINITE CLAUSE"): (
        "Sense verb + 'as if'/'as though' — linking verb followed by 'as if' or "
        "'as though' to describe an impression "
        "(e.g. 'It sounds as if something is wrong')."
    ),
    ("CLAUSES", "FORM: WITH 'WHERE', PLACE"): (
        "Relative clause with 'where' — 'where' modifies a place noun "
        "(e.g. 'the city where I grew up', 'the office where she works')."
    ),
    ("CLAUSES", "FORM: WITH 'WHOSE NAME'"): (
        "Relative clause with 'whose' — 'whose' introduces a clause showing "
        "possession or close relationship "
        "(e.g. 'the woman whose bag was stolen', 'the doctor whose name I forgot')."
    ),

    # FOCUS B1
    ("FOCUS", "FORM/USE: 'IT' + 'BE' ADJECTIVE + 'THAT' CLAUSE"): (
        "'It is + adjective + that' — structure emphasising the content of the "
        "'that' clause (e.g. 'It is important that you attend', "
        "'It is clear that she knows')."
    ),

    # CLAUSES B2
    ("CLAUSES", "FORM/USE: 'LET'S NOT', SUGGESTION"): (
        "'Let's not' — negative suggestion proposing to avoid doing something "
        "together (e.g. 'Let's not argue about this')."
    ),
    ("CLAUSES", "FORM: ADJECTIVE + 'ENOUGH' + 'TO'-INFINITIVE"): (
        "'Enough + to-infinitive' — 'adjective + enough + to' expresses that the "
        "degree is sufficient for an action "
        "(e.g. 'He is old enough to drive', 'Is it warm enough to swim?')."
    ),

    # FOCUS C1
    ("FOCUS", "FORM/USE: 'WHAT' CLEFT CLAUSE"): (
        "'What' cleft clause — 'What + clause + is/was + focus' puts special "
        "emphasis on a part of the message "
        "(e.g. 'What I need is a rest', 'What surprised me was her reaction')."
    ),

    # CLAUSES C2
    ("CLAUSES", "FORM/USE: NEGATIVE CLAUSE +  'NOR', FOCUS"): (
        "Negative + 'nor' — 'nor' following a negative clause for rhetorical "
        "emphasis or to add a further negative "
        "(e.g. 'I didn't like it, nor did she')."
    ),
    ("CLAUSES", "FORM/USE: NON-FINITE AFTER 'ALTHOUGH', 'THOUGH'"): (
        "Non-finite concessive — 'although'/'though' followed by a non-finite "
        "clause; formal and condensed concession "
        "(e.g. 'Although tired, she kept going')."
    ),
    ("CLAUSES", "FORM: 'AS IF' + NON-FINITE CLAUSE"): (
        "'As if' + non-finite — 'as if' followed by an infinitive or participle "
        "clause to describe an appearance or impression "
        "(e.g. 'She looked as if about to cry')."
    ),

    # QUESTIONS A2
    ("QUESTIONS", "FORM: AUXILIARY 'BE'"): (
        "Yes/no question with 'be' — question formed by moving 'is/are/was/were' "
        "before the subject (e.g. 'Is she coming?', 'Were they late?')."
    ),
    ("QUESTIONS", "FORM: AUXILIARY 'HAVE'"): (
        "Question with 'have' — question using 'have/has/had' in the perfect aspect "
        "(e.g. 'Have you seen it?', 'Has she arrived?')."
    ),
    ("QUESTIONS", "FORM: QUESTION TAGS"): (
        "Question tag — short question added at the end of a statement to seek "
        "confirmation or agreement (e.g. 'It's nice, isn't it?', 'You know him, don't you?')."
    ),
    ("QUESTIONS", "FORM: WITH AUXILIARY 'DO'"): (
        "Question with 'do' — question formed using 'do/does/did' as auxiliary "
        "(e.g. 'Do you know her?', 'Did they leave?')."
    ),
}


def _fallback(category: str, guideword: str) -> str:
    """Generate a basic explanation when no specific entry exists."""
    import re
    desc = re.sub(r"^(FORM/USE|FORM|USE):\s*", "", guideword).strip()
    if desc:
        desc = desc[0].upper() + desc[1:].lower()
    labels = {
        "MODALITY": "Modal verb", "NEGATION": "Negation",
        "DISCOURSE MARKERS": "Discourse marker", "CONJUNCTIONS": "Conjunction",
        "PREPOSITIONS": "Preposition", "PRONOUNS": "Pronoun",
        "DETERMINERS": "Determiner", "ADJECTIVES": "Adjective",
        "ADVERBS": "Adverb", "NOUNS": "Noun", "PAST": "Past tense",
        "PRESENT": "Present tense", "FUTURE": "Future",
        "PASSIVES": "Passive voice", "VERBS": "Verb",
        "CLAUSES": "Clause", "REPORTED SPEECH": "Reported speech",
        "FOCUS": "Focus / emphasis", "QUESTIONS": "Question",
    }
    label = labels.get(category, category.title())
    return f"{label} — {desc}."


def main() -> None:
    total_written = 0
    total_fallback = 0

    for path in STRATEGY_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for s in data["structures"]:
            key = (s["category"], s["guideword"].strip())
            if key in EXPLANATIONS:
                s["explanation"] = EXPLANATIONS[key]
                total_written += 1
            else:
                s["explanation"] = _fallback(s["category"], s["guideword"])
                total_fallback += 1
                print(f"  [fallback] {s['category']} | {s['guideword']!r}")
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{path.name}: {len(data['structures'])} rules written.")

    print(f"\nDone. {total_written} specific + {total_fallback} fallback explanations.")


if __name__ == "__main__":
    main()
