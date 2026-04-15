export type CefrLevel = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";

export interface HighlightedWord {
  text: string;
  highlight?: CefrLevel;
}

export interface ChunkMetric {
  label: string;
  value: number;
}

export interface ConversationChunk {
  topic: string;
  words: HighlightedWord[];
  metrics: ChunkMetric[];
}

export interface LessonData {
  id: number;
  name: string;
  chunks: ConversationChunk[];
}

function w(text: string, highlight?: CefrLevel): HighlightedWord {
  return highlight ? { text, highlight } : { text };
}

export const lessonsData: LessonData[] = [
  {
    id: 1,
    name: "Lesson 1",
    chunks: [
      {
        topic: "Greetings",
        words: [
          w("Hello"), w("teacher,"), w("how"), w("are"), w("you?"),
          w("I'm"), w("very"), w("good,"), w("thanks.", "A1"),
          w("I"), w("had"), w("a"), w("fantastic", "A2"), w("time"),
          w("with"), w("my"), w("friends"), w("last"), w("night."),
        ],
        metrics: [
          { label: "Fluency", value: 78 },
          { label: "Accuracy", value: 65 },
          { label: "Complexity", value: 42 },
        ],
      },
      {
        topic: "Daily routine",
        words: [
          w("I"), w("study", "A1"), w("English"), w("every"), w("day."),
          w("My"), w("friend"), w("who"), w("teaches", "A2"), w("us"),
          w("is"), w("kind."), w("She"), w("helped", "A2"), w("me"),
          w("learn"), w("many"), w("new"), w("words."),
          w("The"), w("conference", "B1"), w("was"), w("hard", "C1"),
          w("but"), w("I"), w("learned", "A1"), w("a"), w("lot.", "B2"),
        ],
        metrics: [
          { label: "Fluency", value: 82 },
          { label: "Accuracy", value: 71 },
          { label: "Complexity", value: 58 },
        ],
      },
      {
        topic: "Hobbies & interests",
        words: [
          w("My"), w("friend"), w("loves"), w("to"), w("play"),
          w("soccer."), w("She"), w("is"), w("an"), w("artist", "B1"),
          w("who"), w("paints"), w("beautiful", "A1"), w("flowers"),
          w("in"), w("the"), w("garden."), w("The"), w("blooming", "B2"),
          w("flowers"), w("were"), w("displayed", "C2"), w("at"),
          w("a"), w("concert.", "A2"), w("She"), w("is"),
          w("quite", "B1"), w("talented.", "B1"),
        ],
        metrics: [
          { label: "Fluency", value: 88 },
          { label: "Accuracy", value: 74 },
          { label: "Complexity", value: 67 },
        ],
      },
      {
        topic: "Describing people",
        words: [
          w("The"), w("woman"), w("who"), w("lives", "B2"), w("next"),
          w("to"), w("me"), w("is"), w("a"), w("doctor."),
          w("She"), w("has"), w("a"), w("dog"), w("that"),
          w("barks", "B2"), w("loudly.", "B1"), w("I"), w("admire", "B1"),
          w("her"), w("the"), w("most.", "A2"), w("She"), w("is"),
          w("a"), w("fascinating", "B2"), w("person."),
        ],
        metrics: [
          { label: "Fluency", value: 72 },
          { label: "Accuracy", value: 80 },
          { label: "Complexity", value: 73 },
        ],
      },
    ],
  },
  {
    id: 2,
    name: "Lesson 2",
    chunks: [
      {
        topic: "Motivation",
        words: [
          w("After"), w("our"), w("class", "A1"), w("I"), w("wanted", "A1"),
          w("to"), w("prepare", "A2"), w("some"), w("of"), w("it."),
          w("Yeah,"), w("I'm"), w("learning", "A1"), w("a"),
          w("lot", "B2"), w("because"), w("I"), w("speak", "B2"),
          w("Spanish", "B1"), w("and"), w("English."),
        ],
        metrics: [
          { label: "Fluency", value: 68 },
          { label: "Accuracy", value: 62 },
          { label: "Complexity", value: 55 },
        ],
      },
      {
        topic: "Learning strategies",
        words: [
          w("I"), w("told", "B2"), w("them"), w("I"), w("didn't"),
          w("know"), w("if"), w("I"), w("would"), w("be"),
          w("confident", "B1"), w("but"), w("I"), w("tried", "A2"),
          w("to"), w("practice.", "A1"), w("Now"), w("I"),
          w("understand", "B1"), w("that"), w("it"), w("takes"),
          w("time.", "B1"),
        ],
        metrics: [
          { label: "Fluency", value: 75 },
          { label: "Accuracy", value: 69 },
          { label: "Complexity", value: 61 },
        ],
      },
      {
        topic: "Reflection",
        words: [
          w("I"), w("think", "A1"), w("the"), w("lack", "C2"),
          w("of"), w("practice"), w("was"), w("the"), w("problem."),
          w("But"), w("now"), w("I"), w("started", "B1"),
          w("speaking", "B2"), w("more"), w("and"), w("I"), w("feel"),
          w("perfect", "C2"), w("about"), w("my"), w("ability.", "B1"),
        ],
        metrics: [
          { label: "Fluency", value: 80 },
          { label: "Accuracy", value: 76 },
          { label: "Complexity", value: 70 },
        ],
      },
    ],
  },
  {
    id: 3,
    name: "Lesson 3",
    chunks: [
      {
        topic: "Travel plans",
        words: [
          w("I"), w("would"), w("like"), w("to"), w("travel", "A2"),
          w("to"), w("many"), w("countries."), w("My"), w("dream"),
          w("is"), w("to"), w("visit", "A1"), w("the"),
          w("ancient", "B2"), w("cities"), w("of"), w("Europe."),
        ],
        metrics: [
          { label: "Fluency", value: 85 },
          { label: "Accuracy", value: 78 },
          { label: "Complexity", value: 60 },
        ],
      },
      {
        topic: "Food & culture",
        words: [
          w("The"), w("restaurant", "A1"), w("was"), w("incredible.", "B1"),
          w("I"), w("tasted", "A2"), w("the"), w("traditional"),
          w("cuisine", "C1"), w("and"), w("it"), w("was"),
          w("absolutely", "B1"), w("delicious.", "A2"), w("The"),
          w("atmosphere", "B2"), w("felt"), w("authentic.", "C1"),
        ],
        metrics: [
          { label: "Fluency", value: 90 },
          { label: "Accuracy", value: 82 },
          { label: "Complexity", value: 75 },
        ],
      },
    ],
  },
  { id: 4, name: "Lesson 4", chunks: [] },
  { id: 5, name: "Lesson 5", chunks: [] },
  { id: 6, name: "Lesson 6", chunks: [] },
];
