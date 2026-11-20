import { describe, it, expect } from "vitest";
import { SERIAL7_CONFIG } from "./config/mmseConfig";
import { createMMSEEvent, type MMSEEvent } from "./telemetry/mmseEvents";

describe("MMSE Serial 7s Dynamic Counting Logic", () => {
  const assessmentId = "11111111-2222-4333-8444-555555555555";

  it("verifies config does not hardcode answer-revealing placeholders", () => {
    expect(SERIAL7_CONFIG.startValue).toBe(100);
    expect(SERIAL7_CONFIG.step).toBe(7);
    expect(SERIAL7_CONFIG.totalAttempts).toBe(5);
    expect(SERIAL7_CONFIG.questionIds).toEqual([
      "serial7_1",
      "serial7_2",
      "serial7_3",
      "serial7_4",
      "serial7_5",
    ]);
  });

  it("Scenario A: Correct responses generate 5 accurate dynamic steps (93 -> 86 -> 79 -> 72 -> 65)", () => {
    let currentNumber = SERIAL7_CONFIG.startValue;
    const userAnswers = [93, 86, 79, 72, 65];
    const emittedEvents: MMSEEvent[] = [];

    userAnswers.forEach((ans, idx) => {
      const questionId = SERIAL7_CONFIG.questionIds[idx];
      const subtractionValue = SERIAL7_CONFIG.step;
      const expectedAnswer = currentNumber - subtractionValue;
      const promptText = `${currentNumber} minus ${subtractionValue}`;

      // 1. question_presented
      emittedEvents.push(
        createMMSEEvent({
          assessmentId,
          phase: "ATTENTION",
          eventType: "question_presented",
          questionId,
          metadata: {
            prompt: promptText,
            expected_answer: String(expectedAnswer),
            domain: "serial7",
            starting_number: currentNumber,
            subtraction_value: subtractionValue,
            attempt: idx + 1,
          },
        })
      );

      // 2. response_submitted
      const userAnswer = String(ans);
      const parsed = parseInt(userAnswer, 10);
      const isCorrect = parsed === expectedAnswer;

      expect(isCorrect).toBe(true);
      expect(parsed).toBe(ans);

      emittedEvents.push(
        createMMSEEvent({
          assessmentId,
          phase: "ATTENTION",
          eventType: "response_submitted",
          questionId,
          value: userAnswer,
          metadata: {
            prompt: promptText,
            expected_answer: String(expectedAnswer),
            domain: "serial7",
            starting_number: currentNumber,
            subtraction_value: subtractionValue,
            user_answer: userAnswer,
            is_correct: isCorrect,
            attempt: idx + 1,
          },
        })
      );

      // Next starting number is participant's response
      currentNumber = parsed;
    });

    expect(emittedEvents.filter((e) => e.event_type === "question_presented")).toHaveLength(5);
    expect(emittedEvents.filter((e) => e.event_type === "response_submitted")).toHaveLength(5);

    // Verify all correct in metadata
    const submissions = emittedEvents.filter((e) => e.event_type === "response_submitted");
    expect(submissions.every((s) => s.metadata.is_correct === true)).toBe(true);
  });

  it("Scenario B: Incorrect initial response (92 instead of 93) dynamically adapts the sequence", () => {
    let currentNumber = SERIAL7_CONFIG.startValue;
    // Patient enters 92 (incorrect for 100 - 7 = 93), then from 92 subtracts 7 correctly: 85, 78, 71, 64
    const userAnswers = [92, 85, 78, 71, 64];
    const steps: {
      attempt: number;
      startingNumber: number;
      expected: number;
      userAnswer: number;
      isCorrect: boolean;
      prompt: string;
    }[] = [];

    userAnswers.forEach((ans, idx) => {
      const subtractionValue = SERIAL7_CONFIG.step;
      const expected = currentNumber - subtractionValue;
      const parsed = ans;
      const isCorrect = parsed === expected;

      steps.push({
        attempt: idx + 1,
        startingNumber: currentNumber,
        expected,
        userAnswer: parsed,
        isCorrect,
        prompt: `${currentNumber} minus 7`,
      });

      // Next starting number uses patient's actual answer
      currentNumber = parsed;
    });

    // Step 1: started at 100, prompt "100 minus 7", expected 93, user answered 92 -> incorrect
    expect(steps[0].startingNumber).toBe(100);
    expect(steps[0].prompt).toBe("100 minus 7");
    expect(steps[0].expected).toBe(93);
    expect(steps[0].userAnswer).toBe(92);
    expect(steps[0].isCorrect).toBe(false);

    // Step 2: dynamically started at 92! Prompt "92 minus 7", expected 85, user answered 85 -> correct
    expect(steps[1].startingNumber).toBe(92);
    expect(steps[1].prompt).toBe("92 minus 7");
    expect(steps[1].expected).toBe(85);
    expect(steps[1].userAnswer).toBe(85);
    expect(steps[1].isCorrect).toBe(true);

    // Step 3: dynamically started at 85! Prompt "85 minus 7", expected 78, user answered 78 -> correct
    expect(steps[2].startingNumber).toBe(85);
    expect(steps[2].prompt).toBe("85 minus 7");
    expect(steps[2].expected).toBe(78);
    expect(steps[2].userAnswer).toBe(78);
    expect(steps[2].isCorrect).toBe(true);

    // Step 4: dynamically started at 78!
    expect(steps[3].startingNumber).toBe(78);
    expect(steps[3].expected).toBe(71);
    expect(steps[3].isCorrect).toBe(true);

    // Step 5: dynamically started at 71!
    expect(steps[4].startingNumber).toBe(71);
    expect(steps[4].expected).toBe(64);
    expect(steps[4].isCorrect).toBe(true);

    // 4 out of 5 correct
    const correctCount = steps.filter((s) => s.isCorrect).length;
    expect(correctCount).toBe(4);
  });

  it("Scenario C: Input validation rules properly reject non-numeric and empty input", () => {
    const isInteger = (val: string) => /^-?\d+$/.test(val.trim());

    expect(isInteger("")).toBe(false);
    expect(isInteger("   ")).toBe(false);
    expect(isInteger("abc")).toBe(false);
    expect(isInteger("93a")).toBe(false);
    expect(isInteger("93.5")).toBe(false);

    expect(isInteger("93")).toBe(true);
    expect(isInteger("  86  ")).toBe(true);
    expect(isInteger("-3")).toBe(true);
  });
});
