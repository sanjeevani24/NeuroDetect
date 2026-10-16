import { useEffect, useMemo, useState, type FormEvent } from "react";

import { AppShell } from "./components/ui/AppShell";
import { AssessmentSources } from "./components/ui/AssessmentSources";
import { ModelEvaluation } from "./components/ui/ModelEvaluation";
import { AssessmentProgress, type AssessmentProgressStep } from "./components/ui/AssessmentProgress";
import { CompletionState, ErrorState, LoadingState } from "./components/ui/States";
import { PrimaryButton, SecondaryButton } from "./components/ui/buttons";
import { BostonNamingGame } from "./games/boston-naming/BostonNamingGame";
import { MemoryGame } from "./games/memory/MemoryGame";
import { MMSEGame } from "./games/mmse/MMSEGame";
import { NBackGame } from "./games/nback/NBackGame";
import { TrailMakingGame } from "./games/trail-making/TrailMakingGame";
import {
  getAssessmentResults,
  ApiError,
  completeMentalHealthScreening,
  createAssessmentSession,
  getAssessmentSession,
  predictModel1,
  type AssessmentResults,
  type AssessmentSession,
  type GAD7Answers,
  type MentalHealthCompletionResult,
  type PHQ9Answers,
} from "./services/api";

const SESSION_STORAGE_KEY = "neurodetect.active_assessment_id";
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const TOP_LEVEL_STEPS: AssessmentProgressStep[] = [
  { id: "mental-health", label: "How you feel" },
  { id: "cognitive", label: "Memory & thinking" },
  { id: "results", label: "Results" },
];

const COGNITIVE_STEPS: AssessmentProgressStep[] = [
  { id: "mmse", label: "Everyday questions" },
  { id: "memory", label: "Memory Recall" },
  { id: "nback", label: "Letter matching" },
  { id: "boston-naming", label: "Name the pictures" },
  { id: "trail-making", label: "Connect the circles" },
];

const PHQ9_QUESTIONS = [
  "Little interest or pleasure in doing things",
  "Feeling down, depressed, or hopeless",
  "Trouble falling or staying asleep, or sleeping too much",
  "Feeling tired or having little energy",
  "Poor appetite or overeating",
  "Feeling bad about yourself - or that you are a failure or have let your family down",
  "Trouble concentrating on things, such as reading the newspaper or watching television",
  "Moving or speaking so slowly that other people could have noticed? Or the opposite - being so fidgety or restless that you have been moving around a lot more than usual",
  "Thoughts that you would be better off dead or of hurting yourself in some way",
] as const;

const GAD7_QUESTIONS = [
  "Feeling nervous, anxious or on edge",
  "Not being able to stop or control worrying",
  "Worrying too much about different things",
  "Trouble relaxing",
  "Being so restless that it is hard to sit still",
  "Becoming easily annoyed or irritable",
  "Feeling afraid as if something awful might happen",
] as const;

const RESPONSE_OPTIONS = [
  { value: 0, label: "Not at all" },
  { value: 1, label: "Several days" },
  { value: 2, label: "More than half the days" },
  { value: 3, label: "Nearly every day" },
] as const;

type Route =
  | { kind: "home" }
  | { kind: "patient" }
  | { kind: "mental-health"; assessmentId: string }
  | { kind: "cognitive"; assessmentId: string }
  | { kind: "mmse"; assessmentId: string }
  | { kind: "memory"; assessmentId: string }
  | { kind: "nback"; assessmentId: string }
  | { kind: "boston-naming"; assessmentId: string }
  | { kind: "trail-making"; assessmentId: string }
  | { kind: "speech"; assessmentId: string }
  | { kind: "results"; assessmentId: string }
  | { kind: "not-found" };

type LoadStatus = "idle" | "loading" | "error";

interface AppHeaderProps {
  title: string;
  subtitle: string;
  currentStage: string;
  completedStages: string[];
  showProgress: boolean;
}

interface HomeScreenProps {
  hasSavedAssessment: boolean;
  resumeStatus: "idle" | "loading";
  resumeError: string | null;
  onStart: () => void;
  onResume: () => void;
  onStartNew: () => void;
}

interface PatientFormValues {
  full_name: string;
  age: string;
  sex: string;
  education_years: string;
}

interface PatientInformationScreenProps {
  submitStatus: "idle" | "submitting";
  submitError: string | null;
  onSubmit: (values: PatientFormValues) => Promise<void>;
}

interface MentalHealthScreenProps {
  assessmentId: string;
  submitStatus: "idle" | "submitting";
  submitError: string | null;
  onComplete: (result: MentalHealthCompletionResult) => Promise<void>;
}

interface CognitiveOverviewProps {
  session: AssessmentSession;
  onResume: () => void;
  onStartNew: () => void;
}

function formatSeverityLabel(value: string | null | undefined): string {
  if (!value) return "Unavailable";
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((part) => part[0].toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function formatAssessmentError(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    if (error.status === 400 || error.status === 404) {
      return "Assessment not found.";
    }
    return typeof error.detail === "string" ? error.detail : fallback;
  }
  return fallback;
}

function parseRoute(pathname: string): Route {
  const trimmed = pathname.replace(/\/+$/, "") || "/";
  if (trimmed === "/") return { kind: "home" };
  if (trimmed === "/patient") return { kind: "patient" };

  const match = trimmed.match(
    /^\/assessment\/([^/]+)\/(mental-health|cognitive|mmse|memory|nback|boston-naming|trail-making|speech|results)$/
  );
  if (!match) return { kind: "not-found" };

  const assessmentId = decodeURIComponent(match[1]);
  const section = match[2];
  return { kind: section as Route["kind"], assessmentId } as Route;
}

function routeToPath(route: Route): string {
  switch (route.kind) {
    case "home":
      return "/";
    case "patient":
      return "/patient";
    case "mental-health":
    case "cognitive":
    case "mmse":
    case "memory":
    case "nback":
    case "boston-naming":
    case "trail-making":
    case "speech":
    case "results":
      return `/assessment/${encodeURIComponent(route.assessmentId)}/${route.kind}`;
    default:
      return "/";
  }
}

function routeForStage(stage: AssessmentSession["current_stage"], assessmentId: string): Route {
  switch (stage) {
    case "PHQ_GAD":
      return { kind: "mental-health", assessmentId };
    case "COGNITIVE":
      return { kind: "cognitive", assessmentId };
    case "MMSE":
      return { kind: "mmse", assessmentId };
    case "MEMORY":
      return { kind: "memory", assessmentId };
    case "NBACK":
      return { kind: "nback", assessmentId };
    case "BOSTON_NAMING":
      return { kind: "boston-naming", assessmentId };
    case "TRAIL_MAKING":
      return { kind: "trail-making", assessmentId };
    case "SPEECH":
      return { kind: "speech", assessmentId };
    case "RESULTS":
      return { kind: "results", assessmentId };
    default:
      return { kind: "patient" };
  }
}

function normalizeCompletedStages(session: AssessmentSession | null): string[] {
  if (!session) return [];
  const completed = new Set<string>();
  if (session.completed_stages.includes("PHQ_GAD")) completed.add("mental-health");
  if (
    session.completed_stages.includes("MMSE") &&
    session.completed_stages.includes("MEMORY") &&
    session.completed_stages.includes("NBACK") &&
    session.completed_stages.includes("BOSTON_NAMING") &&
    session.completed_stages.includes("TRAIL_MAKING")
  ) {
    completed.add("cognitive");
  }
  return [...completed];
}

function getTopLevelCurrentStage(route: Route): string {
  switch (route.kind) {
    case "cognitive":
    case "mmse":
    case "memory":
    case "nback":
    case "boston-naming":
    case "trail-making":
      return "cognitive";
    case "results":
      return "results";
    default:
      return "mental-health";
  }
}

function getHeaderCopy(route: Route): { title: string; subtitle: string } {
  switch (route.kind) {
    case "home":
      return {
        title: "Your memory and wellbeing check",
        subtitle: "Simple questions. Clear instructions. One step at a time.",
      };
    case "patient":
      return {
        title: "About you",
        subtitle: "A few details before we begin.",
      };
    case "mental-health":
      return {
        title: "How you feel",
        subtitle: "Choose the answer that feels closest to your experience.",
      };
    case "cognitive":
      return {
        title: "Memory and thinking",
        subtitle: "Follow the instructions for each activity and do your best.",
      };
    case "results":
      return {
        title: "Your results",
        subtitle: "A summary of your answers and activities.",
      };
    default:
      return {
        title: "Memory and thinking",
        subtitle: "Follow the instructions for this activity.",
      };
  }
}

function AppHeader({ title, subtitle, currentStage, completedStages, showProgress }: AppHeaderProps) {
  return (
    <div className="app-header">
      <div className="app-header__brand">
        <div className="app-header__mark" aria-hidden="true" />
        <div>
          <p className="app-header__eyebrow">NEURODETECT</p>
          <h1>{title}</h1>
          <p className="app-header__subtitle">{subtitle}</p>
        </div>
      </div>
      {showProgress ? <div className="app-header__progress">
        <AssessmentProgress
          currentStage={currentStage}
          completedStages={completedStages}
          steps={TOP_LEVEL_STEPS}
        />
      </div> : null}
    </div>
  );
}

function HomeScreen({
  hasSavedAssessment,
  resumeStatus,
  resumeError,
  onStart,
  onResume,
  onStartNew,
}: HomeScreenProps) {
  return (
    <div className="page-stack">
      <section className="hero-card hero-card--landing">
        <h2>Welcome. Let’s take it one step at a time.</h2>
        <p className="hero-card__body">
          Answer a few questions about how you feel, then try some memory and thinking activities. We’ll explain each activity before you begin.
        </p>
        <div className="hero-card__actions">
          <PrimaryButton type="button" onClick={hasSavedAssessment ? onResume : onStart} disabled={resumeStatus === "loading"}>
            {resumeStatus === "loading" ? "Opening your assessment…" : hasSavedAssessment ? "Continue my assessment" : "Let’s begin"}
          </PrimaryButton>
          {hasSavedAssessment ? (
            <SecondaryButton type="button" onClick={onStartNew} disabled={resumeStatus === "loading"}>
              Start a new assessment
            </SecondaryButton>
          ) : null}
        </div>
        {resumeError ? <p className="inline-error">{resumeError}</p> : null}
      </section>

      <p className="welcome-note">Find a quiet, comfortable place before you begin. This assessment is a screening tool and does not provide a diagnosis.</p>
    </div>
  );
}

function PatientInformationScreen({
  submitStatus,
  submitError,
  onSubmit,
}: PatientInformationScreenProps) {
  const [values, setValues] = useState<PatientFormValues>({
    full_name: "",
    age: "",
    sex: "",
    education_years: "",
  });
  const [errors, setErrors] = useState<Partial<Record<keyof PatientFormValues, string>>>({});

  function updateField(field: keyof PatientFormValues, value: string) {
    setValues((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  }

  function validate(): boolean {
    const nextErrors: Partial<Record<keyof PatientFormValues, string>> = {};
    if (!values.full_name.trim()) nextErrors.full_name = "Full name is required.";
    if (!/^\d+$/.test(values.age) || Number(values.age) <= 0) nextErrors.age = "Please enter your age in whole years.";
    if (!values.sex.trim()) nextErrors.sex = "Sex is required.";
    if (!/^\d+$/.test(values.education_years) || Number(values.education_years) < 0) {
      nextErrors.education_years = "Please enter a whole number, or 0 if none.";
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validate()) return;
    await onSubmit(values);
  }

  return (
    <section className="form-card">
      <div className="form-card__intro">
        <h2>A little about you</h2>
        <p className="hero-card__body">
          Please fill in all four fields, then choose Continue.
        </p>
      </div>
      <form className="form-grid" onSubmit={(event) => void handleSubmit(event)}>
        <label className="form-field">
          <span>Full Name</span>
          <input
            value={values.full_name}
            onChange={(event) => updateField("full_name", event.target.value)}
            autoComplete="name"
          />
          {errors.full_name ? <span className="field-error">{errors.full_name}</span> : null}
        </label>

        <label className="form-field">
          <span>Age</span>
          <input
            inputMode="numeric"
            value={values.age}
            onChange={(event) => updateField("age", event.target.value)}
          />
          {errors.age ? <span className="field-error">{errors.age}</span> : null}
        </label>

        <label className="form-field">
          <span>Sex</span>
          <select value={values.sex} onChange={(event) => updateField("sex", event.target.value)}>
            <option value="">Select</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
            <option value="Prefer not to say">Prefer not to say</option>
          </select>
          {errors.sex ? <span className="field-error">{errors.sex}</span> : null}
        </label>

        <label className="form-field">
          <span>Years of education</span>
          <span className="field-hint">Total years at school and college. Enter 0 if none.</span>
          <input
            inputMode="numeric"
            value={values.education_years}
            onChange={(event) => updateField("education_years", event.target.value)}
          />
          {errors.education_years ? <span className="field-error">{errors.education_years}</span> : null}
        </label>

        {submitError ? <p className="inline-error">{submitError}</p> : null}

        <div className="form-actions">
          <PrimaryButton type="submit" disabled={submitStatus === "submitting"}>
            {submitStatus === "submitting" ? "Getting ready…" : "Continue"}
          </PrimaryButton>
        </div>
      </form>
    </section>
  );
}

function MentalHealthScreen({
  assessmentId,
  submitStatus,
  submitError,
  onComplete,
}: MentalHealthScreenProps) {
  const [localSubmitting, setLocalSubmitting] = useState(false);
  const [section, setSection] = useState<"phq9" | "gad7">("phq9");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [requiredError, setRequiredError] = useState<string | null>(null);
  const [phq9, setPhq9] = useState<Partial<PHQ9Answers>>({});
  const [gad7, setGad7] = useState<Partial<GAD7Answers>>({});

  const questions = section === "phq9" ? PHQ9_QUESTIONS : GAD7_QUESTIONS;
  const totalQuestions = questions.length;
  const answerKey = `q${questionIndex + 1}` as keyof PHQ9Answers & keyof GAD7Answers;
  const selectedValue = section === "phq9" ? phq9[answerKey] : gad7[answerKey];

  function setAnswer(value: number) {
    setRequiredError(null);
    if (section === "phq9") {
      setPhq9((prev) => ({ ...prev, [answerKey]: value }));
    } else {
      setGad7((prev) => ({ ...prev, [answerKey]: value }));
    }
  }

  function goNext() {
    if (selectedValue === undefined) {
      setRequiredError("Please select one response before continuing.");
      return;
    }
    if (questionIndex < totalQuestions - 1) {
      setQuestionIndex((prev) => prev + 1);
      return;
    }
    if (section === "phq9") {
      setSection("gad7");
      setQuestionIndex(0);
      return;
    }
    void handleSubmit();
  }

  function goBack() {
    setRequiredError(null);
    if (questionIndex > 0) {
      setQuestionIndex((prev) => prev - 1);
      return;
    }
    if (section === "gad7") {
      setSection("phq9");
      setQuestionIndex(PHQ9_QUESTIONS.length - 1);
    }
  }

  async function handleSubmit() {
    const phqPayload = phq9 as PHQ9Answers;
    const gadPayload = gad7 as GAD7Answers;
    if (Object.keys(phqPayload).length !== 9 || Object.keys(gadPayload).length !== 7) {
      setRequiredError("Every PHQ-9 and GAD-7 question must be answered.");
      return;
    }

    setLocalSubmitting(true);
    try {
      const result = await completeMentalHealthScreening(assessmentId, {
        phq9: phqPayload,
        gad7: gadPayload,
      });
      await onComplete(result);
    } finally {
      setLocalSubmitting(false);
    }
  }

  return (
    <section className="questionnaire-card">
      <div className="questionnaire-card__intro">
        <h2>How have you been feeling?</h2>
      </div>

      <div className="questionnaire-card__body">
        <div className="question-meta">
          <span>{section === "phq9" ? "Your mood" : "Worry and relaxation"}</span>
          <span>
            Question {(section === "phq9" ? 0 : PHQ9_QUESTIONS.length) + questionIndex + 1} of {PHQ9_QUESTIONS.length + GAD7_QUESTIONS.length}
          </span>
        </div>
        <h3>How often have you been bothered by the following problem over the last 2 weeks?</h3>
        <p className="questionnaire-card__question">{questions[questionIndex]}</p>

        <fieldset className="questionnaire-options">
          <legend className="sr-only">{questions[questionIndex]}</legend>
          {RESPONSE_OPTIONS.map((option) => (
            <label
              key={option.value}
              className={`option-row ${selectedValue === option.value ? "is-selected" : ""}`}
            >
              <input
                type="radio"
                name={`${section}-${questionIndex}`}
                checked={selectedValue === option.value}
                onChange={() => setAnswer(option.value)}
              />
              <span>
                {option.label}
              </span>
            </label>
          ))}
        </fieldset>

        {requiredError ? <p className="inline-error">{requiredError}</p> : null}
        {submitError ? <p className="inline-error">{submitError}</p> : null}

        <div className="form-actions">
          <SecondaryButton type="button" onClick={goBack} disabled={section === "phq9" && questionIndex === 0}>
            Back
          </SecondaryButton>
          <PrimaryButton
            type="button"
            onClick={goNext}
            disabled={submitStatus === "submitting" || localSubmitting}
          >
            {submitStatus === "submitting" || localSubmitting
              ? "Saving screening..."
              : section === "gad7" && questionIndex === totalQuestions - 1
                ? "Continue to activities"
                : "Next"}
          </PrimaryButton>
        </div>
      </div>
    </section>
  );
}

function CognitiveOverviewScreen({ session, onResume, onStartNew }: CognitiveOverviewProps) {
  const completedGames = new Set(session.completed_stages);
  const currentGameStage =
    session.current_stage === "COGNITIVE" ? "mmse" : routeForStage(session.current_stage, session.assessment_id).kind;
  const cognitiveCompletedStages = [
    completedGames.has("MMSE") ? "mmse" : null,
    completedGames.has("MEMORY") ? "memory" : null,
    completedGames.has("NBACK") ? "nback" : null,
    completedGames.has("BOSTON_NAMING") ? "boston-naming" : null,
    completedGames.has("TRAIL_MAKING") ? "trail-making" : null,
  ].filter(Boolean) as string[];

  return (
    <div className="page-stack">
      <section className="hero-card">
        <h2>Next, a few simple activities</h2>
        <p className="hero-card__body">
          You’ll answer everyday questions, remember items, match letters, name pictures, and connect circles. Each activity starts with instructions.
        </p>
        <div className="hero-card__actions">
          <PrimaryButton type="button" onClick={onResume}>
            {session.current_stage === "COGNITIVE" ? "Start the activities" : "Continue my assessment"}
          </PrimaryButton>
          <SecondaryButton type="button" onClick={onStartNew}>
            Start New Assessment
          </SecondaryButton>
        </div>
      </section>

      <section className="hero-card hero-card--section">
        <div className="section-copy">
          <h3>Your activities</h3>
        </div>
        <AssessmentProgress
          currentStage={currentGameStage}
          completedStages={cognitiveCompletedStages}
          steps={COGNITIVE_STEPS}
        />
      </section>
    </div>
  );
}

function ResultsScreen({
  session,
  results,
  resultsStatus,
  resultsError,
  model1Status,
  model1Error,
  onRetryResults,
  onRetryModel1,
  onContinueAssessment,
  onReturnHome,
}: {
  session: AssessmentSession | null;
  results: AssessmentResults | null;
  resultsStatus: LoadStatus;
  resultsError: string | null;
  model1Status: "idle" | "loading" | "error";
  model1Error: string | null;
  onRetryResults: () => void;
  onRetryModel1: () => void;
  onContinueAssessment: () => void;
  onReturnHome: () => void;
}) {
  if (resultsStatus === "error") {
    return (
      <ErrorState
        title={resultsError === "Assessment not found." ? "Assessment not found" : "Unable to load assessment results."}
        message={resultsError ?? "Please try again."}
        action={
          resultsError === "Assessment not found." ? (
            <PrimaryButton type="button" onClick={onReturnHome}>
              Return Home
            </PrimaryButton>
          ) : (
            <PrimaryButton type="button" onClick={onRetryResults}>
              Retry
            </PrimaryButton>
          )
        }
      />
    );
  }

  if (resultsStatus === "loading" || !results) {
    return (
      <div className="page-stack">
        <LoadingState title="Loading your results…" message="Please wait while we prepare your summary." />
        <section className="hero-card hero-card--section results-skeleton" aria-hidden="true">
          <div className="results-skeleton__block" />
          <div className="results-skeleton__grid">
            <div className="results-skeleton__card" />
            <div className="results-skeleton__card" />
            <div className="results-skeleton__card" />
          </div>
        </section>
      </div>
    );
  }

  const cognitiveTasks = results.completed_components.filter((item) =>
    ["mmse", "memory", "nback", "boston_naming", "trail_making"].includes(item.key)
  );
  const showModel1Scale = typeof results.model1.score_scale_max === "number" && Number.isFinite(results.model1.score_scale_max);
  const showAssessmentCompleteBanner = results.status === "completed";
  const showAwaitingModel1Banner = results.status === "awaiting_model1";

  return (
    <div className="page-stack">
      <section className="hero-card hero-card--section">
        <div className="results-header">
          <div className="results-header__copy">
            <p className="hero-card__eyebrow">NEURODETECT</p>
            <h3>Your assessment summary</h3>
            <p className="hero-card__body">
              {showAssessmentCompleteBanner
                ? "Assessment Completed"
                : showAwaitingModel1Banner
                  ? "Activities complete — your score is not ready yet"
                  : "Assessment Incomplete"}
            </p>
          </div>
          <div className="session-summary">
            <p>
              <strong>Assessment ID:</strong> {results.assessment_short_id}
            </p>
            <p>
              <strong>Participant:</strong> {results.participant_name || session?.full_name || "Participant"}
            </p>
          </div>
        </div>
      </section>

      {showAssessmentCompleteBanner ? (
        <CompletionState title="Assessment Complete" message={results.completion_message} />
      ) : null}

      {showAwaitingModel1Banner ? (
        <ErrorState
          title="Your score is not ready yet"
          message="Your activities are complete. Choose Try again to prepare your score."
          action={
            <PrimaryButton type="button" onClick={onRetryModel1} disabled={model1Status === "loading"}>
              {model1Status === "loading" ? "Preparing your score…" : "Try again"}
            </PrimaryButton>
          }
        />
      ) : null}

      {results.status === "incomplete" ? (
        <section className="hero-card hero-card--section">
          <div className="section-copy">
            <p className="hero-card__eyebrow">Assessment Status</p>
            <h3>Assessment Incomplete</h3>
            <p className="hero-card__body">
              Continue the current assessment session to complete the remaining components before reviewing final results.
            </p>
          </div>
          <div className="results-checklist" role="list" aria-label="Assessment completion checklist">
            {results.completed_components.map((item) => (
              <div className="results-checklist__item" key={item.key} role="listitem">
                <span className={`results-checklist__marker ${item.completed ? "is-complete" : "is-pending"}`} aria-hidden="true">
                  {item.completed ? "OK" : "NO"}
                </span>
                <span>{item.label}</span>
                <strong>{item.completed ? "Completed" : "Pending"}</strong>
              </div>
            ))}
          </div>
          <div className="hero-card__actions">
            <PrimaryButton type="button" onClick={onContinueAssessment}>
              Continue Assessment
            </PrimaryButton>
          </div>
        </section>
      ) : null}

      <section className="hero-card hero-card--section">
        <div className="section-copy">
          <p className="hero-card__eyebrow">Cognitive Performance</p>
          <h3>Memory and thinking results</h3>
          <p className="hero-card__body">
            This score summarizes performance across the cognitive tasks included in this assessment.
          </p>
        </div>
        <div className="results-grid">
          <article className="results-card results-card--score">
            <p className="results-card__label">Cognitive Performance Score</p>
            <div className="results-card__score">
              {results.model1.available && results.model1.cognitive_performance_score !== null
                ? results.model1.cognitive_performance_score.toFixed(2)
                : "Unavailable"}
              {showModel1Scale && results.model1.cognitive_performance_score !== null ? (
                <span> / {results.model1.score_scale_max}</span>
              ) : null}
            </div>
          </article>

          <article className="results-card">
            <p className="results-card__label">Cognitive Tasks Completed</p>
            <div className="results-task-list" role="list" aria-label="Completed cognitive tasks">
              {cognitiveTasks.map((item) => (
                <div className="results-task-list__item" key={item.key} role="listitem">
                  <span aria-hidden="true">{item.completed ? "OK" : "NO"}</span>
                  <span>{item.label}</span>
                  <strong>{item.completed ? "Completed" : "Pending"}</strong>
                </div>
              ))}
            </div>
          </article>

          <details className="results-card results-card--details">
            <summary>Assessment Details</summary>
            <div className="results-details">
              <p>
                <strong>Model:</strong> {results.model1.model_name ?? "NeuroDetect Model 1"}
              </p>
              <p>
                <strong>Version:</strong> {results.model1.model_version ?? "1.0.0"}
              </p>
              <p>
                <strong>Features:</strong> {results.model1.feature_count ?? "Unavailable"}
              </p>
              <p>
                <strong>Type:</strong> {results.model1.model_type ?? "Cognitive performance regression"}
              </p>
            </div>
          </details>
        </div>
      </section>

      <ModelEvaluation evaluation={results.model1.evaluation} />

      {model1Status === "error" && model1Error ? (
        <ErrorState
          title="We couldn’t prepare your score"
          message="The score could not be regenerated from the stored cognitive task results. Please try again."
          action={
            <PrimaryButton type="button" onClick={onRetryModel1}>
              Try again
            </PrimaryButton>
          }
        />
      ) : null}

      <section className="hero-card hero-card--section">
        <div className="section-copy">
          <p className="hero-card__eyebrow">Mental Health Screening</p>
          <h3>Your mood and wellbeing</h3>
          <p className="hero-card__body">
            These questionnaires provide screening scores based on the responses provided during the assessment. They are
            not diagnostic results.
          </p>
        </div>
        <div className="results-grid results-grid--two">
          <article className="results-card">
            <p className="results-card__label">PHQ-9</p>
            <div className="results-card__score results-card__score--small">
              {results.mental_health.phq9.available && results.mental_health.phq9.score !== null
                ? `${results.mental_health.phq9.score} / ${results.mental_health.phq9.score_max}`
                : "Unavailable"}
            </div>
            <p>
              <strong>Severity:</strong> {formatSeverityLabel(results.mental_health.phq9.severity)}
            </p>
          </article>

          <article className="results-card">
            <p className="results-card__label">GAD-7</p>
            <div className="results-card__score results-card__score--small">
              {results.mental_health.gad7.available && results.mental_health.gad7.score !== null
                ? `${results.mental_health.gad7.score} / ${results.mental_health.gad7.score_max}`
                : "Unavailable"}
            </div>
            <p>
              <strong>Severity:</strong> {formatSeverityLabel(results.mental_health.gad7.severity)}
            </p>
          </article>
        </div>
        <p className="results-disclaimer">
          These screening scores are intended to provide an indication of symptom severity based on the questionnaire
          responses. They do not constitute a medical diagnosis.
        </p>
      </section>

    </div>
  );
}

function routeNeedsAssessment(route: Route): route is Exclude<Route, { kind: "home" | "patient" | "not-found" }> {
  return route.kind !== "home" && route.kind !== "patient" && route.kind !== "not-found";
}

function App() {
  const [route, setRoute] = useState<Route>(() => parseRoute(window.location.pathname));
  const [session, setSession] = useState<AssessmentSession | null>(null);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("idle");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [createStatus, setCreateStatus] = useState<"idle" | "submitting">("idle");
  const [createError, setCreateError] = useState<string | null>(null);
  const [screeningStatus, setScreeningStatus] = useState<"idle" | "submitting">("idle");
  const [screeningError, setScreeningError] = useState<string | null>(null);
  const [resumeStatus, setResumeStatus] = useState<"idle" | "loading">("idle");
  const [resumeError, setResumeError] = useState<string | null>(null);
  const [model1Status, setModel1Status] = useState<"idle" | "loading" | "error">("idle");
  const [model1Error, setModel1Error] = useState<string | null>(null);
  const [resultsStatus, setResultsStatus] = useState<LoadStatus>("idle");
  const [resultsError, setResultsError] = useState<string | null>(null);
  const [resultsData, setResultsData] = useState<AssessmentResults | null>(null);

  const headerCopy = getHeaderCopy(route);
  const completedTopStages = normalizeCompletedStages(session);

  useEffect(() => {
    const handlePopState = () => setRoute(parseRoute(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  async function loadSession(assessmentId: string) {
    const nextSession = await getAssessmentSession(assessmentId);
    setSession(nextSession);
    window.localStorage.setItem(SESSION_STORAGE_KEY, nextSession.assessment_id);
    return nextSession;
  }

  function navigate(nextRoute: Route, replace = false) {
    const path = routeToPath(nextRoute);
    if (replace) {
      window.history.replaceState({}, "", path);
    } else {
      window.history.pushState({}, "", path);
    }
    setRoute(nextRoute);
  }

  function clearAssessmentSession() {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    setSession(null);
    setModel1Status("idle");
    setModel1Error(null);
    setResultsStatus("idle");
    setResultsError(null);
    setResultsData(null);
  }

  useEffect(() => {
    if (!routeNeedsAssessment(route)) {
      setModel1Status("idle");
      setModel1Error(null);
      setResultsStatus("idle");
      setResultsError(null);
      setResultsData(null);
      return;
    }
    if (route.kind !== "results") {
      setModel1Status("idle");
      setModel1Error(null);
      setResultsStatus("idle");
      setResultsError(null);
      return;
    }
  }, [route]);

  useEffect(() => {
    if (!routeNeedsAssessment(route)) {
      setLoadStatus("idle");
      setLoadError(null);
      return;
    }
    if (!UUID_PATTERN.test(route.assessmentId)) {
      setLoadStatus("error");
      setLoadError("Assessment not found.");
      return;
    }

    setLoadStatus("loading");
    setLoadError(null);
    void loadSession(route.assessmentId)
      .then(() => setLoadStatus("idle"))
      .catch((error) => {
        setLoadStatus("error");
        setLoadError(formatAssessmentError(error, "Unable to load assessment session."));
      });
  }, [route]);

  async function handleCreateSession(values: PatientFormValues) {
    setCreateStatus("submitting");
    setCreateError(null);
    try {
      const nextSession = await createAssessmentSession({
        full_name: values.full_name.trim(),
        age: Number(values.age),
        sex: values.sex.trim(),
        education_years: Number(values.education_years),
      });
      setSession(nextSession);
      window.localStorage.setItem(SESSION_STORAGE_KEY, nextSession.assessment_id);
      navigate({ kind: "mental-health", assessmentId: nextSession.assessment_id });
    } catch (error) {
      setCreateError(error instanceof ApiError ? String(error.detail ?? error.message) : "Unable to create assessment.");
    } finally {
      setCreateStatus("idle");
    }
  }

  async function handleResumeAssessment() {
    const storedAssessmentId = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (!storedAssessmentId) return;
    setResumeStatus("loading");
    setResumeError(null);
    try {
      const nextSession = await loadSession(storedAssessmentId);
      navigate(routeForStage(nextSession.current_stage, nextSession.assessment_id));
    } catch (error) {
      clearAssessmentSession();
      setResumeError(error instanceof ApiError ? String(error.detail ?? error.message) : "Unable to resume assessment.");
    } finally {
      setResumeStatus("idle");
    }
  }

  async function handleMentalHealthComplete(result: MentalHealthCompletionResult) {
    setScreeningStatus("submitting");
    setScreeningError(null);
    try {
      await loadSession(result.assessment_id);
      navigate({ kind: "cognitive", assessmentId: result.assessment_id });
    } catch (error) {
      setScreeningError(error instanceof ApiError ? String(error.detail ?? error.message) : "Unable to continue.");
    } finally {
      setScreeningStatus("idle");
    }
  }

  async function runModel1Prediction(assessmentId: string): Promise<boolean> {
    setModel1Status("loading");
    setModel1Error(null);
    try {
      await predictModel1(assessmentId);
      setModel1Status("idle");
      return true;
    } catch (error) {
      setModel1Status("error");
      setModel1Error(error instanceof ApiError ? String(error.detail ?? error.message) : "Unable to run Model 1.");
      return false;
    }
  }

  async function loadResults(assessmentId: string) {
    setResultsStatus("loading");
    setResultsError(null);
    try {
      const nextResults = await getAssessmentResults(assessmentId);
      setResultsData(nextResults);
      setResultsStatus("idle");
      return nextResults;
    } catch (error) {
      setResultsData(null);
      setResultsStatus("error");
      setResultsError(formatAssessmentError(error, "Unable to load assessment results."));
      return null;
    }
  }

  function startNewAssessment() {
    clearAssessmentSession();
    navigate({ kind: "patient" });
  }

  function resumeCognitiveAssessment() {
    if (!session) return;
    if (session.current_stage === "COGNITIVE") {
      navigate({ kind: "mmse", assessmentId: session.assessment_id });
      return;
    }
    navigate(routeForStage(session.current_stage, session.assessment_id));
  }

  async function handleTrailMakingComplete(assessmentId: string) {
    const succeeded = await runModel1Prediction(assessmentId);
    if (!succeeded) {
      console.error("Model 1 inference failed after Trail Making completion.");
    }
    navigate({ kind: "results", assessmentId });
  }

  async function handleRetryModel1FromResults() {
    if (route.kind !== "results") return;
    const succeeded = await runModel1Prediction(route.assessmentId);
    if (succeeded) {
      await loadResults(route.assessmentId);
      await loadSession(route.assessmentId);
    }
  }

  useEffect(() => {
    if (route.kind !== "results") return;
    void loadResults(route.assessmentId);
  }, [route]);

  const content = useMemo(() => {
    if (route.kind === "not-found") {
      return (
        <ErrorState
          title="Page not found"
          message="This route is not part of the NeuroDetect assessment flow."
          action={
            <PrimaryButton type="button" onClick={() => navigate({ kind: "home" }, true)}>
              Return Home
            </PrimaryButton>
          }
        />
      );
    }

    if (loadStatus === "loading" && routeNeedsAssessment(route)) {
      return (
        <LoadingState
          title="Loading assessment session"
          message="Please wait while we open your assessment."
        />
      );
    }

    if (loadStatus === "error" && routeNeedsAssessment(route)) {
      return (
        <ErrorState
          title={loadError === "Assessment not found." ? "Assessment not found" : "Unable to load assessment session"}
          message={loadError ?? "Please restart the assessment from home."}
          action={
            <PrimaryButton type="button" onClick={() => navigate({ kind: "home" }, true)}>
              Return Home
            </PrimaryButton>
          }
        />
      );
    }

    switch (route.kind) {
      case "home":
        return (
          <HomeScreen
            hasSavedAssessment={Boolean(window.localStorage.getItem(SESSION_STORAGE_KEY))}
            resumeStatus={resumeStatus}
            resumeError={resumeError}
            onStart={() => navigate({ kind: "patient" })}
            onResume={() => void handleResumeAssessment()}
            onStartNew={startNewAssessment}
          />
        );
      case "patient":
        return (
          <PatientInformationScreen
            submitStatus={createStatus}
            submitError={createError}
            onSubmit={handleCreateSession}
          />
        );
      case "mental-health":
        return session ? (
          <MentalHealthScreen
            assessmentId={route.assessmentId}
            submitStatus={screeningStatus}
            submitError={screeningError}
            onComplete={handleMentalHealthComplete}
          />
        ) : null;
      case "cognitive":
        return session ? (
          <CognitiveOverviewScreen
            session={session}
            onResume={resumeCognitiveAssessment}
            onStartNew={startNewAssessment}
          />
        ) : null;
      case "mmse":
        return <MMSEGame assessmentId={route.assessmentId} onComplete={() => navigate({ kind: "memory", assessmentId: route.assessmentId })} />;
      case "memory":
        return <MemoryGame assessmentId={route.assessmentId} onComplete={() => navigate({ kind: "nback", assessmentId: route.assessmentId })} />;
      case "nback":
        return <NBackGame assessmentId={route.assessmentId} onComplete={() => navigate({ kind: "boston-naming", assessmentId: route.assessmentId })} />;
      case "boston-naming":
        return (
          <BostonNamingGame
            assessmentId={route.assessmentId}
            onComplete={() => navigate({ kind: "trail-making", assessmentId: route.assessmentId })}
          />
        );
      case "trail-making":
        return <TrailMakingGame assessmentId={route.assessmentId} onComplete={() => void handleTrailMakingComplete(route.assessmentId)} />;
      case "speech":
        navigate({ kind: "results", assessmentId: route.assessmentId }, true);
        return null;
      case "results":
        return (
          <ResultsScreen
            session={session}
            results={resultsData}
            resultsStatus={resultsStatus}
            resultsError={resultsError}
            model1Status={model1Status}
            model1Error={model1Error}
            onRetryResults={() => void loadResults(route.assessmentId)}
            onRetryModel1={() => void handleRetryModel1FromResults()}
            onContinueAssessment={() => {
              const nextStage = resultsData?.next_stage ?? session?.current_stage ?? "COGNITIVE";
              navigate(routeForStage(nextStage, route.assessmentId));
            }}
            onReturnHome={() => navigate({ kind: "home" }, true)}
          />
        );
      default:
        return null;
    }
  }, [
    createError,
    createStatus,
    loadError,
    loadStatus,
    resumeError,
    resumeStatus,
    route,
    screeningError,
    screeningStatus,
    session,
    model1Status,
    model1Error,
    resultsData,
    resultsStatus,
    resultsError,
  ]);

  return (
    <AppShell
      footer={<AssessmentSources />}
      header={
        <AppHeader
          title={headerCopy.title}
          subtitle={headerCopy.subtitle}
          currentStage={getTopLevelCurrentStage(route)}
          completedStages={completedTopStages}
          showProgress={route.kind !== "home" && route.kind !== "patient" && route.kind !== "not-found"}
        />
      }
    >
      {content}
    </AppShell>
  );
}

export default App;
