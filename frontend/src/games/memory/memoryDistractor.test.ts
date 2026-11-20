import { describe, it, expect } from "vitest";
import { DISTRACTOR_CONFIG } from "./config/memoryConfig";
import { createMemoryEvent } from "./telemetry/memoryEvents";

describe("Memory Distractor Counting Logic (Subtraction by 3)", () => {
  const assessmentId = "22222222-3333-4444-8555-666666666666";

  it("verifies config values and maxAttempts limit", () => {
    expect(DISTRACTOR_CONFIG.startValue).toBe(100);
    expect(DISTRACTOR_CONFIG.step).toBe(3);
    expect(DISTRACTOR_CONFIG.maxAttempts).toBe(5);
    expect(DISTRACTOR_CONFIG.prompt).toBe("Count backwards from 100 by 3s.");
  });

  it("Scenario A: Correct responses (97 -> 94 -> 91 -> 88 -> 85) across 5 attempts", () => {
    let currentNumber = DISTRACTOR_CONFIG.startValue;
    const userAnswers = [97, 94, 91, 88, 85];
    const steps: {
      attempt: number;
      startingNumber: number;
      expected: number;
      userAnswer: number;
      isCorrect: boolean;
    }[] = [];

    userAnswers.forEach((ans, idx) => {
      const expected = currentNumber - DISTRACTOR_CONFIG.step;
      const parsed = ans;
      const isCorrect = parsed === expected;

      steps.push({
        attempt: idx + 1,
        startingNumber: currentNumber,
        expected,
        userAnswer: parsed,
        isCorrect,
      });

      // Update currentNumber to participant's response
      currentNumber = parsed;
    });

    expect(steps).toHaveLength(5);
    expect(steps.every((s) => s.isCorrect)).toBe(true);
    expect(steps[0].startingNumber).toBe(100);
    expect(steps[0].expected).toBe(97);
    expect(steps[1].startingNumber).toBe(97);
    expect(steps[1].expected).toBe(94);
    expect(steps[4].startingNumber).toBe(88);
    expect(steps[4].expected).toBe(85);
  });

  it("Scenario B: Incorrect initial response (96 instead of 97) uses 96 as next starting number", () => {
    let currentNumber = DISTRACTOR_CONFIG.startValue;
    // Participant enters 96 (incorrect for 100 - 3 = 97), then from 96: 93, 90, 87, 84
    const userAnswers = [96, 93, 90, 87, 84];
    const events: ReturnType<typeof createMemoryEvent>[] = [];

    userAnswers.forEach((ans, idx) => {
      const expected = currentNumber - DISTRACTOR_CONFIG.step;
      const parsed = ans;
      const isCorrect = parsed === expected;
      const attempt = idx + 1;

      events.push(
        createMemoryEvent({
          assessmentId,
          phase: "DISTRACTOR",
          eventType: "response_submitted",
          value: String(ans),
          metadata: {
            starting_number: currentNumber,
            subtraction_value: DISTRACTOR_CONFIG.step,
            user_answer: String(ans),
            expected_answer: String(expected),
            is_correct: isCorrect,
            attempt,
            total_attempts: DISTRACTOR_CONFIG.maxAttempts,
          },
        })
      );

      // Next starting number is user's actual response!
      currentNumber = parsed;
    });

    // Check step 1: starting number 100, user answer 96, expected 97, is_correct false
    expect(events[0].metadata.starting_number).toBe(100);
    expect(events[0].metadata.user_answer).toBe("96");
    expect(events[0].metadata.expected_answer).toBe("97");
    expect(events[0].metadata.is_correct).toBe(false);

    // Check step 2: starting number 96! user answer 93, expected 93, is_correct true
    expect(events[1].metadata.starting_number).toBe(96);
    expect(events[1].metadata.user_answer).toBe("93");
    expect(events[1].metadata.expected_answer).toBe("93");
    expect(events[1].metadata.is_correct).toBe(true);

    // Check step 3: starting number 93! user answer 90, expected 90, is_correct true
    expect(events[2].metadata.starting_number).toBe(93);
    expect(events[2].metadata.expected_answer).toBe("90");
    expect(events[2].metadata.is_correct).toBe(true);

    // Check step 4: starting number 90! user answer 87, expected 87, is_correct true
    expect(events[3].metadata.starting_number).toBe(90);
    expect(events[3].metadata.expected_answer).toBe("87");
    expect(events[3].metadata.is_correct).toBe(true);

    // Check step 5: starting number 87! user answer 84, expected 84, is_correct true
    expect(events[4].metadata.starting_number).toBe(87);
    expect(events[4].metadata.expected_answer).toBe("84");
    expect(events[4].metadata.is_correct).toBe(true);

    // 4 out of 5 correct
    const correctCount = events.filter((e) => e.metadata.is_correct === true).length;
    expect(correctCount).toBe(4);
  });
});
