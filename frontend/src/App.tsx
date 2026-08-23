import { useEffect, useMemo, useState, type FormEvent } from "react";

import { AppShell } from "./components/ui/AppShell";
import { AssessmentProgress, type AssessmentProgressStep } from "./components/ui/AssessmentProgress";
import { CompletionState, ErrorState, InstructionCard, LoadingState } from "./components/ui/States";
import { PrimaryButton, SecondaryButton } from "./components/ui/buttons";
import { BostonNamingGame } from "./games/boston-naming/BostonNamingGame";
import { MemoryGame } from "./games/memory/MemoryGame";
import { MMSEGame } from "./games/mmse/MMSEGame";
import { NBackGame } from "./games/nback/NBackGame";
import { TrailMakingGame } from "./games/trail-making/TrailMakingGame";
import {
  ApiError,
  completeMentalHealthScreening,
  createAssessmentSession,
  getAssessmentSession,
  type AssessmentSession,
  type GAD7Answers,
  type MentalHealthCompletionResult,
  type PHQ9Answers,
} from "./services/api";

const SESSION_STORAGE_KEY = "neurodetect.active_assessment_id";
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const TOP_LEVEL_STEPS: AssessmentProgressStep[] = [
  { id: "mental-health", label: "Mental Health" },
  { id: "cognitive", label: "Cognitive Assessment" },
  { id: "speech", label: "Speech Assessment" },
  { id: "results", label: "Results" },
];

const COGNITIVE_STEPS: AssessmentProgressStep[] = [
  { id: "mmse", label: "MMSE" },
  { id: "memory", label: "Memory Recall" },
  { id: "nback", label: "N-Back" },
  { id: "boston-naming", label: "Boston Naming" },
  { id: "trail-making", label: "Trail Making" },
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
  if (session.current_stage === "RESULTS") {
    completed.add("speech");
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
    case "speech":
      return "speech";
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
        title: "AI-Assisted Multimodal Cognitive Assessment",
        subtitle: "A structured assessment combining mental-health screening, cognitive tasks, and speech-based analysis.",
      };
    case "patient":
      return {
        title: "Patient Information",
        subtitle: "Collect the required participant details before creating the secure assessment session.",
      };
    case "mental-health":
      return {
        title: "Mental Health Screening",
        subtitle: "PHQ-9 and GAD-7 screening questionnaires for the last two weeks.",
      };
    case "cognitive":
      return {
        title: "Cognitive Assessment Overview",
        subtitle: "The existing cognitive assessment page, preserved and moved after PHQ-9 and GAD-7.",
      };
    case "speech":
      return {
        title: "Speech Assessment",
        subtitle: "Continue the same assessment session into the speech stage using the existing assessment ID.",
      };
    case "results":
      return {
        title: "Final Results",
        subtitle: "Assessment outputs are gathered here before the later fusion layer combines them.",
      };
    default:
      return {
        title: "Cognitive Assessment Platform",
        subtitle: "Shared assessment session across all stages.",
      };
  }
}

function AppHeader({ title, subtitle, currentStage, completedStages }: AppHeaderProps) {
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
      <div className="app-header__progress">
        <span className="app-header__label">Assessment</span>
        <AssessmentProgress
          currentStage={currentStage}
          completedStages={completedStages}
          steps={TOP_LEVEL_STEPS}
        />
      </div>
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
        <p className="hero-card__eyebrow">NEURODETECT</p>
        <h2>AI-Assisted Multimodal Cognitive Assessment</h2>
        <p className="hero-card__body">
          A structured assessment combining mental-health screening, cognitive tasks, and speech-based analysis.
        </p>
        <div className="hero-card__actions">
          <PrimaryButton type="button" onClick={onStart}>
            Start Assessment
          </PrimaryButton>
          {hasSavedAssessment ? (
            <SecondaryButton type="button" onClick={onResume} disabled={resumeStatus === "loading"}>
              {resumeStatus === "loading" ? "Resuming..." : "Resume Assessment"}
            </SecondaryButton>
          ) : null}
          {hasSavedAssessment ? (
            <SecondaryButton type="button" onClick={onStartNew}>
              Start New Assessment
            </SecondaryButton>
          ) : null}
        </div>
        {resumeError ? <p className="inline-error">{resumeError}</p> : null}
      </section>

      <section className="hero-card hero-card--section">
        <div className="section-copy">
          <p className="hero-card__eyebrow">About the Assessment</p>
          <h3>One continuous research-oriented assessment flow</h3>
          <p className="hero-card__body">
            The assessment combines structured screening, cognitive performance tasks, and speech-based analysis in one
            continuous session. It is designed for assessment, screening, and research use rather than standalone diagnosis.
          </p>
        </div>
        <div className="overview-grid">
          <InstructionCard
            title="Mental Health Screening"
            message="PHQ-9 and GAD-7 screen depressive and anxiety symptoms over the previous two weeks."
          />
          <InstructionCard
            title="Cognitive Assessment"
            message="MMSE, Memory Recall, N-Back, Boston Naming, and Trail Making capture different aspects of cognitive performance."
          />
          <InstructionCard
            title="Speech Assessment"
            message="A speech-based assessment contributes an additional signal to the multimodal assessment."
          />
          <InstructionCard
            title="Final Analysis"
            message="The different assessment components are combined later into the overall assessment output."
          />
        </div>
      </section>
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
    if (!/^\d+$/.test(values.age) || Number(values.age) <= 0) nextErrors.age = "Age must be a positive integer.";
    if (!values.sex.trim()) nextErrors.sex = "Sex is required.";
    if (!/^\d+$/.test(values.education_years) || Number(values.education_years) < 0) {
      nextErrors.education_years = "Education years must be a non-negative integer.";
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
        <p className="hero-card__eyebrow">Patient Information</p>
        <h2>Collect the minimum required participant details.</h2>
        <p className="hero-card__body">
          All four fields are required before the secure assessment session can be created.
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
          <span>Education Years</span>
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
            {submitStatus === "submitting" ? "Creating secure assessment..." : "Continue"}
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
        <p className="hero-card__eyebrow">Mental Health Screening</p>
        <h2>{section === "phq9" ? "PHQ-9" : "GAD-7"}</h2>
        <p className="hero-card__body">
          The following questions ask about how you have been feeling over the last two weeks. These are screening
          questionnaires and are not presented as diagnoses.
        </p>
      </div>

      <div className="questionnaire-card__body">
        <div className="question-meta">
          <span>{section === "phq9" ? "PHQ-9" : "GAD-7"}</span>
          <span>
            Question {questionIndex + 1} of {totalQuestions}
          </span>
        </div>
        <h3>How often have you been bothered by the following problem over the last 2 weeks?</h3>
        <p className="questionnaire-card__question">{questions[questionIndex]}</p>

        <fieldset className="questionnaire-options">
          <legend className="sr-only">Response options</legend>
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
                {option.value} - {option.label}
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
                ? "Complete Screening"
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
        <p className="hero-card__eyebrow">NEURODETECT</p>
        <h2>Cognitive Assessment Platform</h2>
        <p className="hero-card__body">
          This preserved overview page now appears after patient information and mental-health screening.
        </p>
        <div className="overview-list">
          <span>ASSESSMENT</span>
          <strong>✓ MMSE</strong>
          <strong>✓ Memory Recall</strong>
          <strong>✓ N-Back</strong>
          <strong>✓ Boston Naming</strong>
          <strong>• Trail Making</strong>
        </div>
        <div className="hero-card__actions">
          <PrimaryButton type="button" onClick={onResume}>
            {session.current_stage === "COGNITIVE" ? "Start Cognitive Assessment" : "Resume Assessment"}
          </PrimaryButton>
          <SecondaryButton type="button" onClick={onStartNew}>
            Start New Assessment
          </SecondaryButton>
        </div>
      </section>

      <section className="hero-card hero-card--section">
        <div className="section-copy">
          <p className="hero-card__eyebrow">Cognitive Progress</p>
          <h3>Continue the existing game sequence without changing game logic.</h3>
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

function SpeechScreen({ assessmentId, onContinue }: { assessmentId: string; onContinue: () => void }) {
  return (
    <section className="hero-card">
      <p className="hero-card__eyebrow">Speech Assessment</p>
      <h2>Continue with the same assessment session.</h2>
      <p className="hero-card__body">
        The speech stage uses the same assessment ID: <strong>{assessmentId}</strong>. No new patient or assessment is
        created here.
      </p>
      <div className="hero-card__actions">
        <PrimaryButton type="button" onClick={onContinue}>
          Continue to Results
        </PrimaryButton>
      </div>
    </section>
  );
}

function ResultsScreen({ session }: { session: AssessmentSession | null }) {
  return (
    <div className="page-stack">
      <CompletionState
        title="Assessment flow completed"
        message="Patient information, mental-health screening, and the existing cognitive stages now share one continuous assessment session."
      />
      <section className="hero-card hero-card--section">
        <div className="section-copy">
          <p className="hero-card__eyebrow">Fusion</p>
          <h3>Stored outputs are ready for the later fusion layer.</h3>
          <p className="hero-card__body">
            The later fusion stage can combine Model 1, PHQ/GAD outputs, and additional signals without creating a new
            assessment ID.
          </p>
        </div>
        {session ? (
          <div className="session-summary">
            <p>
              <strong>Assessment ID:</strong> {session.assessment_id}
            </p>
            <p>
              <strong>Participant:</strong> {session.full_name}
            </p>
          </div>
        ) : null}
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
  }

  useEffect(() => {
    if (!routeNeedsAssessment(route)) {
      setLoadStatus("idle");
      setLoadError(null);
      return;
    }
    if (!UUID_PATTERN.test(route.assessmentId)) {
      setLoadStatus("error");
      setLoadError("Assessment session is invalid. Please return home and start from the patient information step.");
      return;
    }

    setLoadStatus("loading");
    setLoadError(null);
    void loadSession(route.assessmentId)
      .then(() => setLoadStatus("idle"))
      .catch((error) => {
        setLoadStatus("error");
        setLoadError(error instanceof ApiError ? String(error.detail ?? error.message) : "Unable to load assessment.");
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
          message="Checking the current assessment stage and restoring the participant session."
        />
      );
    }

    if (loadStatus === "error" && routeNeedsAssessment(route)) {
      return (
        <ErrorState
          title="Unable to load assessment session"
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
        return <TrailMakingGame assessmentId={route.assessmentId} onComplete={() => navigate({ kind: "speech", assessmentId: route.assessmentId })} />;
      case "speech":
        return <SpeechScreen assessmentId={route.assessmentId} onContinue={() => navigate({ kind: "results", assessmentId: route.assessmentId })} />;
      case "results":
        return <ResultsScreen session={session} />;
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
  ]);

  return (
    <AppShell
      header={
        <AppHeader
          title={headerCopy.title}
          subtitle={headerCopy.subtitle}
          currentStage={getTopLevelCurrentStage(route)}
          completedStages={completedTopStages}
        />
      }
      footer={<p className="app-footer__text">One assessment session, one patient, one assessment ID.</p>}
    >
      {content}
    </AppShell>
  );
}

export default App;
