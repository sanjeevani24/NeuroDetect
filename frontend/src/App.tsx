import { useState } from "react";

import { AppShell } from "./components/ui/AppShell";
import { AssessmentProgress, type AssessmentStage } from "./components/ui/AssessmentProgress";
import { CompletionState, ErrorState, InstructionCard, LoadingState } from "./components/ui/States";
import { PrimaryButton, SecondaryButton } from "./components/ui/buttons";
import { MemoryGame } from "./games/memory/MemoryGame";
import { MMSEGame } from "./games/mmse/MMSEGame";
import { NBackGame } from "./games/nback/NBackGame";
import { ApiError, createAssessmentSession } from "./services/api";

const ASSESSMENT_ID_PLACEHOLDER = "REPLACE_WITH_REAL_ASSESSMENT_ID";
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

type SessionStatus = "idle" | "creating" | "error";

/**
 * MVP shell: the Memory Recall game expects an existing assessment_id.
 * In this milestone there is no assessment-creation UI yet — the id is
 * read from the URL query string (?assessment_id=...) or falls back to a
 * placeholder for local development against a seeded Supabase row.
 */
function getAssessmentId(): string {
  const params = new URLSearchParams(window.location.search);
  return params.get("assessment_id") ?? ASSESSMENT_ID_PLACEHOLDER;
}

function getInitialStage(): AssessmentStage {
  const params = new URLSearchParams(window.location.search);
  const game = params.get("game");
  if (game === "nback") return "nback";
  if (game === "memory") return "memory";
  return "mmse";
}

function syncAssessmentIdInUrl(assessmentId: string, stage: AssessmentStage) {
  const params = new URLSearchParams(window.location.search);
  params.set("assessment_id", assessmentId);
  params.set("game", stage === "memory" ? "memory" : "mmse");
  window.history.replaceState({}, "", `${window.location.pathname}?${params.toString()}`);
}

function AppHeader({
  currentStage,
  completedStages,
}: {
  currentStage: AssessmentStage;
  completedStages: AssessmentStage[];
}) {
  return (
    <div className="app-header">
      <div className="app-header__brand">
        <div className="app-header__mark" aria-hidden="true" />
        <div>
          <p className="app-header__eyebrow">NEURODETECT</p>
          <h1>Cognitive Assessment Platform</h1>
        </div>
      </div>
      <div className="app-header__progress">
        <span className="app-header__label">Assessment</span>
        <AssessmentProgress currentStage={currentStage} completedStages={completedStages} />
      </div>
    </div>
  );
}

function StartScreen({
  onStart,
  hasExistingAssessment,
  isCreating,
}: {
  onStart: () => void;
  hasExistingAssessment: boolean;
  isCreating: boolean;
}) {
  return (
    <div className="start-screen">
      <section className="hero-card">
        <p className="hero-card__eyebrow">Structured Cognitive Assessment</p>
        <h2>Memory, attention, language, and executive function in one guided session.</h2>
        <p className="hero-card__body">
          A structured assessment of memory, attention, language and executive function.
        </p>
        <div className="hero-card__actions">
          <PrimaryButton type="button" onClick={onStart} disabled={isCreating}>
            {isCreating
              ? "Creating Session..."
              : hasExistingAssessment
                ? "Resume Assessment"
                : "Start Assessment"}
          </PrimaryButton>
          <SecondaryButton type="button" disabled>
            {hasExistingAssessment ? "Secure session active" : "A new secure session will be created"}
          </SecondaryButton>
        </div>
      </section>

      <div className="overview-grid">
        <InstructionCard
          title="Assessment overview"
          message="The current prototype begins with MMSE, followed by Memory Recall, using one shared assessment session."
        />
        <InstructionCard
          title="Estimated duration"
          message="Plan for approximately 12 to 18 minutes for the currently implemented stages."
        />
        <InstructionCard
          title="What to expect"
          message="You will answer orientation prompts, short language tasks, structured recall tasks, and guided interactions."
        />
        <InstructionCard
          title="Privacy note"
          message="Responses are captured for research-oriented feature extraction. This prototype does not provide a medical diagnosis."
        />
      </div>
    </div>
  );
}

function App() {
  const [assessmentId, setAssessmentId] = useState(getAssessmentId);
  const hasValidAssessmentId = UUID_PATTERN.test(assessmentId);
  const [started, setStarted] = useState(false);
  const [stage, setStage] = useState<AssessmentStage>(getInitialStage);
  const [completedStages, setCompletedStages] = useState<AssessmentStage[]>([]);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>("idle");
  const [sessionError, setSessionError] = useState<string | null>(null);

  async function startAssessment() {
    if (hasValidAssessmentId) {
      setStarted(true);
      return;
    }

    setSessionStatus("creating");
    setSessionError(null);

    try {
      const session = await createAssessmentSession();
      setAssessmentId(session.assessment_id);
      syncAssessmentIdInUrl(session.assessment_id, stage);
      setStarted(true);
      setSessionStatus("idle");
    } catch (error) {
      setSessionStatus("error");
      setSessionError(error instanceof ApiError ? String(error.detail ?? error.message) : "Failed to create session.");
    }
  }

  function completeStage(nextStage?: AssessmentStage) {
    setCompletedStages((prev) => {
      if (prev.includes(stage)) return prev;
      return [...prev, stage];
    });
    if (nextStage) {
      setStage(nextStage);
      if (UUID_PATTERN.test(assessmentId)) {
        syncAssessmentIdInUrl(assessmentId, nextStage);
      }
      return;
    }
    setStage("trail");
  }

  return (
    <AppShell
      header={<AppHeader currentStage={stage} completedStages={completedStages} />}
      footer={<p className="app-footer__text">Secure assessment session</p>}
    >
      {sessionStatus === "creating" ? (
        <LoadingState
          title="Creating assessment session"
          message="Preparing a new secure assessment session for this participant."
        />
      ) : sessionStatus === "error" ? (
        <ErrorState
          title="We could not create an assessment session"
          message={sessionError ?? "Please try again."}
          action={
            <PrimaryButton type="button" onClick={() => void startAssessment()}>
              Retry session creation
            </PrimaryButton>
          }
        />
      ) : !started ? (
        <StartScreen
          onStart={() => void startAssessment()}
          hasExistingAssessment={hasValidAssessmentId}
          isCreating={false}
        />
      ) : !hasValidAssessmentId ? (
        <ErrorState
          title="Assessment session missing"
          message="Open the app with a real assessment_id in the URL before starting. Example: ?assessment_id=11111111-1111-1111-1111-111111111111"
        />
      ) : stage === "mmse" ? (
        <MMSEGame assessmentId={assessmentId} onComplete={() => completeStage("memory")} />
      ) : stage === "memory" ? (
        <MemoryGame assessmentId={assessmentId} onComplete={() => completeStage("nback")} />
      ) : stage === "nback" ? (
        <NBackGame assessmentId={assessmentId} onComplete={() => completeStage("naming")} />
      ) : (
        <CompletionState
          title="Current milestone complete"
          message="MMSE, Memory Recall, and N-Back have been completed in this prototype session."
        />
      )}
    </AppShell>
  );
}

export default App;
