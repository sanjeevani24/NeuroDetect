export type MMSEPhase =
  | "INTRO"
  | "ORIENTATION"
  | "REGISTRATION"
  | "ATTENTION"
  | "LANGUAGE"
  | "DELAYED_RECALL"
  | "COMMAND"
  | "COMPLETION";

export interface MMSEState {
  phase: MMSEPhase;
  events: import("../telemetry/mmseEvents").MMSEEvent[];
  completed: boolean;
  startedAt: string | null;
}
