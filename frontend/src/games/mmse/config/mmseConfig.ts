export const ORIENTATION_QUESTIONS = [
  { id: "year", prompt: "What year is it?", expectedAnswer: "2026" },
  { id: "month", prompt: "What month is it?", expectedAnswer: "August" },
  { id: "date", prompt: "What is today's date?", expectedAnswer: "23" },
  { id: "day", prompt: "What day of the week is it?", expectedAnswer: "Sunday" },
  { id: "location", prompt: "What is the name of this assessment site?", expectedAnswer: "NeuroDetect Clinic" },
] as const;

export const REGISTRATION_WORDS = ["APPLE", "TABLE", "COIN"] as const;

export const SERIAL7_SEQUENCE = [
  { id: "serial7_1", prompt: "100 minus 7", expectedAnswer: "93" },
  { id: "serial7_2", prompt: "93 minus 7", expectedAnswer: "86" },
  { id: "serial7_3", prompt: "86 minus 7", expectedAnswer: "79" },
  { id: "serial7_4", prompt: "79 minus 7", expectedAnswer: "72" },
  { id: "serial7_5", prompt: "72 minus 7", expectedAnswer: "65" },
] as const;

export const LANGUAGE_TASKS = [
  { id: "naming", prompt: "Type the object name exactly as shown: PEN", expectedAnswer: "PEN" },
  {
    id: "repetition",
    prompt: 'Repeat this sentence exactly: "No ifs, ands, or buts."',
    expectedAnswer: "No ifs, ands, or buts.",
  },
  { id: "reading", prompt: 'Type the word "CLOSE" to confirm you read the instruction.', expectedAnswer: "CLOSE" },
  { id: "sentence", prompt: "Write a short sentence that includes the word patient.", expectedAnswer: "patient" },
] as const;

export const COMMAND_STEPS = [
  { id: "step_1", label: "Tap Left" },
  { id: "step_2", label: "Tap Center" },
  { id: "step_3", label: "Tap Right" },
] as const;
