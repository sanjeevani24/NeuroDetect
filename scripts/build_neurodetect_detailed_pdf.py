from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.doctemplate import BaseDocTemplate, Frame, PageTemplate


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "NeuroDetect_Detailed_Implementation_Report.pdf"

NAVY = colors.HexColor("#132B4F")
BLUE = colors.HexColor("#246AA7")
TEAL = colors.HexColor("#16847A")
GREEN = colors.HexColor("#2C8C63")
INK = colors.HexColor("#172235")
SLATE = colors.HexColor("#5E718A")
MIST = colors.HexColor("#EDF3F8")
PALE_BLUE = colors.HexColor("#DDEBF6")
PALE_GREEN = colors.HexColor("#DDF2E7")
PALE_ORANGE = colors.HexColor("#FFF0D6")
LINE = colors.HexColor("#C9D7E3")
WHITE = colors.white


class Diagram(Flowable):
    """Small reusable vector diagrams used in the report."""

    def __init__(self, kind: str, width: float = 16.5 * cm, height: float = 8.4 * cm):
        super().__init__()
        self.kind = kind
        self.width = width
        self.height = height

    def draw_box(self, canvas, x, y, w, h, title, subtitle, fill, title_color=INK):
        canvas.setFillColor(fill)
        canvas.setStrokeColor(LINE)
        canvas.roundRect(x, y, w, h, 7, fill=1, stroke=1)
        canvas.setFillColor(title_color)
        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawCentredString(x + w / 2, y + h - 15, title)
        if subtitle:
            canvas.setFillColor(SLATE)
            canvas.setFont("Helvetica", 6.8)
            lines = subtitle.split("\n")
            for index, line in enumerate(lines):
                canvas.drawCentredString(x + w / 2, y + h - 27 - (index * 9), line)

    def arrow(self, canvas, x1, y1, x2, y2, label=None):
        canvas.setStrokeColor(BLUE)
        canvas.setFillColor(BLUE)
        canvas.setLineWidth(1.25)
        canvas.line(x1, y1, x2, y2)
        canvas.saveState()
        canvas.translate(x2, y2)
        import math

        angle = math.atan2(y2 - y1, x2 - x1)
        canvas.rotate(angle * 180 / math.pi)
        path = canvas.beginPath()
        path.moveTo(0, 0)
        path.lineTo(-6, 3)
        path.lineTo(-6, -3)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)
        canvas.restoreState()
        if label:
            canvas.setFillColor(SLATE)
            canvas.setFont("Helvetica", 6.5)
            canvas.drawCentredString((x1 + x2) / 2, (y1 + y2) / 2 + 5, label)

    def draw(self):
        c = self.canv
        if self.kind == "architecture":
            self._architecture(c)
        elif self.kind == "flow":
            self._flow(c)
        elif self.kind == "database":
            self._database(c)
        elif self.kind == "feature":
            self._feature(c)

    def _architecture(self, c):
        w = self.width
        self.draw_box(c, 0, 138, w, 45, "React + TypeScript Frontend", "Assessment routing, forms, game interfaces, telemetry capture", PALE_BLUE)
        self.draw_box(c, 0, 69, w, 45, "FastAPI Application Layer", "Routers, Pydantic validation, services, feature extraction, status orchestration", colors.HexColor("#EAF5F3"))
        self.draw_box(c, 0, 0, w, 45, "Supabase / PostgreSQL Persistence", "Patients, sessions, screening results, game results, raw Trail Making events, Model 1 results", MIST)
        self.arrow(c, w / 2, 138, w / 2, 114, "HTTPS JSON")
        self.arrow(c, w / 2, 69, w / 2, 45, "Repository calls")
        self.draw_box(c, 8, 195, 145, 28, "User", "Participant or evaluator", PALE_ORANGE)
        self.draw_box(c, w - 153, 195, 145, 28, "Model 1", "47-feature cognitive performance regressor", PALE_GREEN)
        self.arrow(c, 80, 195, 80, 183)
        self.arrow(c, w - 80, 183, w - 80, 138, "prediction request")

    def _flow(self, c):
        boxes = [
            (0, "1. Create", "Patient + assessment_id", PALE_BLUE),
            (94, "2. Screen", "PHQ-9 and GAD-7", PALE_GREEN),
            (188, "3. Assess", "Five cognitive tasks", PALE_ORANGE),
            (282, "4. Extract", "Backend features", colors.HexColor("#EAF5F3")),
            (376, "5. Present", "Model 1 + results", MIST),
        ]
        for x, title, subtitle, fill in boxes:
            self.draw_box(c, x, 89, 84, 48, title, subtitle, fill)
        for x in [84, 178, 272, 366]:
            self.arrow(c, x, 113, x + 9, 113)
        self.draw_box(c, 42, 10, 382, 43, "Single-session consistency rule", "Every screen, task result, screening score, prediction, and final view is linked through the same assessment_id.", colors.HexColor("#F5F8FB"))
        self.arrow(c, 230, 89, 230, 53)

    def _database(self, c):
        self.draw_box(c, 184, 163, 100, 42, "patients", "patient_id\ndemographics", PALE_BLUE)
        self.draw_box(c, 184, 97, 100, 42, "assessments", "assessment_id\npatient_id + stages", colors.HexColor("#EAF5F3"))
        self.arrow(c, 234, 163, 234, 139)
        left = [(0, "phq9_results"), (0, "gad7_results"), (0, "mmse_results"), (0, "memory_results")]
        right = [(368, "nback_results"), (368, "boston_naming_results"), (368, "trail_making_results"), (368, "model1_results")]
        y = 166
        for x, label in left:
            self.draw_box(c, x, y, 100, 25, label, "assessment_id (unique)", MIST)
            self.arrow(c, 184, 118, 100, y + 12)
            y -= 38
        y = 166
        for x, label in right:
            self.draw_box(c, x, y, 100, 25, label, "assessment_id (unique)", MIST)
            self.arrow(c, 284, 118, 368, y + 12)
            y -= 38
        self.draw_box(c, 184, 16, 100, 25, "trail_making_events", "raw sampled pointer/click telemetry", PALE_ORANGE)
        self.arrow(c, 284, 99, 284, 41)

    def _feature(self, c):
        self.draw_box(c, 0, 99, 84, 48, "MMSE", "14 features", PALE_BLUE)
        self.draw_box(c, 95, 99, 84, 48, "Memory", "10 features", PALE_GREEN)
        self.draw_box(c, 190, 99, 84, 48, "N-Back", "7 features", PALE_ORANGE)
        self.draw_box(c, 285, 99, 84, 48, "Boston", "8 features", colors.HexColor("#EAF5F3"))
        self.draw_box(c, 380, 99, 84, 48, "Trail", "8 features", MIST)
        for x in [42, 137, 232, 327, 422]:
            self.arrow(c, x, 99, 232, 65)
        self.draw_box(c, 134, 17, 196, 48, "Ordered 47-feature vector", "validated for presence, numeric type, finiteness, and fixed schema order", colors.HexColor("#DCEBFA"))
        self.arrow(c, 232, 17, 232, 4, "")


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=27, leading=32, textColor=NAVY, alignment=TA_CENTER, spaceAfter=12),
        "subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontName="Helvetica", fontSize=12, leading=17, textColor=SLATE, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=17, leading=22, textColor=NAVY, spaceBefore=12, spaceAfter=8),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=BLUE, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13.2, textColor=INK, spaceAfter=6),
        "small": ParagraphStyle("Small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.7, leading=10.2, textColor=INK),
        "callout": ParagraphStyle("Callout", parent=base["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13, textColor=NAVY, leftIndent=8, rightIndent=8, spaceAfter=4),
        "formula": ParagraphStyle("Formula", parent=base["Code"], fontName="Courier", fontSize=7.4, leading=10.2, textColor=INK),
        "caption": ParagraphStyle("Caption", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=7.7, leading=10, textColor=SLATE, alignment=TA_CENTER, spaceAfter=8),
    }


S = styles()


def p(text: str, style="body"):
    return Paragraph(text, S[style])


def heading(text: str, level=1):
    return p(text, "h1" if level == 1 else "h2")


def bullet(text: str):
    return p(f"<bullet>&bull;</bullet> {text}", "body")


def callout(text: str, fill=colors.HexColor("#F2F7FB")):
    table = Table([[p(text, "callout")]], colWidths=[16.5 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fill),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def table(headers, rows, widths, *, font_size=7.4):
    data = [[p(h, "small") for h in headers]]
    data.extend([[p(str(cell), "small") for cell in row] for row in rows])
    result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#F8FBFD")]),
    ]))
    return result


def note_table(rows):
    result = Table([[p(a, "small"), p(b, "small")] for a, b in rows], colWidths=[3.3 * cm, 13.2 * cm])
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), PALE_BLUE),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return result


class ReportDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=A4, leftMargin=2.0 * cm, rightMargin=2.0 * cm, topMargin=1.7 * cm, bottomMargin=1.55 * cm)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="content")
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=self._header_footer))

    @staticmethod
    def _header_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(2 * cm, A4[1] - 1.18 * cm, A4[0] - 2 * cm, A4[1] - 1.18 * cm)
        canvas.setFont("Helvetica-Bold", 7.6)
        canvas.setFillColor(SLATE)
        canvas.drawString(2 * cm, A4[1] - 0.87 * cm, "NEURODETECT | DETAILED IMPLEMENTATION REPORT")
        canvas.setFont("Helvetica", 7.4)
        canvas.drawRightString(A4[0] - 2 * cm, 0.78 * cm, f"Page {doc.page}")
        canvas.setFillColor(SLATE)
        canvas.drawString(2 * cm, 0.78 * cm, "Research/demo prototype - not a medical diagnostic system")
        canvas.restoreState()


def section_title(story, title, text=None):
    story.append(heading(title))
    story.append(HRFlowable(width="100%", thickness=0.7, color=LINE, spaceAfter=7))
    if text:
        story.append(p(text))


def add_cover(story):
    story.extend([Spacer(1, 4.2 * cm), p("NeuroDetect", "title"), p("Detailed Implementation Report", "title"), Spacer(1, 0.3 * cm)])
    story.append(p("A complete technical record of the implemented cognitive assessment prototype", "subtitle"))
    story.append(Spacer(1, 1.3 * cm))
    story.append(callout("<b>Coverage:</b> implemented frontend flow, FastAPI backend, Supabase schema and persistence, mental-health scoring, five cognitive tasks, 47-feature Model 1 integration, result aggregation, validation, and test verification.", colors.HexColor("#EAF3FA")))
    story.append(Spacer(1, 0.7 * cm))
    story.append(note_table([
        ("Document status", "Detailed implementation record based on the current project codebase."),
        ("System type", "Browser-based research/demo cognitive assessment prototype."),
        ("Core identifier", "One assessment_id links the patient, screening, tasks, prediction, and result page."),
        ("Report date", "September 2026"),
        ("Clinical note", "Outputs are not presented as a diagnosis and must not be used as a substitute for clinical judgement."),
    ]))
    story.append(PageBreak())


def add_contents(story):
    section_title(story, "Contents")
    entries = [
        "1. Project Scope and Implementation Summary",
        "2. System Architecture",
        "3. End-to-End Assessment Process",
        "4. Frontend Implementation",
        "5. Backend, APIs, and Validation",
        "6. Supabase Data Model and Persistence",
        "7. Mental Health Screening",
        "8. Cognitive Task Implementation",
        "9. Feature Engineering and Formula Reference",
        "10. Model 1 Integration and 47-Feature Contract",
        "11. Final Results Aggregation",
        "12. Reliability, Testing, and Current Limitations",
        "Appendix A. Feature Bifurcation",
        "Appendix B. API and Database Inventory",
    ]
    for item in entries:
        story.append(bullet(item))
    story.append(Spacer(1, 0.3 * cm))
    story.append(callout("This report intentionally separates <b>implemented functionality</b> from <b>future scope</b>. MRI processing, speech analysis, multimodal fusion, diagnostic classification, Grad-CAM, SHAP, and progression prediction are not implemented in the current codebase.", colors.HexColor("#FFF5E6")))
    story.append(PageBreak())


def add_scope(story):
    section_title(story, "1. Project Scope and Implementation Summary", "NeuroDetect is a web-based cognitive assessment prototype designed to capture structured cognitive and behavioural information in one assessment session. The delivered implementation focuses on reliable collection, backend-owned feature extraction, persistence, a cognitive-performance Model 1 integration, and an aggregated final result view.")
    story.append(heading("Implemented capabilities", 2))
    for text in [
        "Patient registration and assessment-session creation with a generated UUID assessment_id.",
        "PHQ-9 and GAD-7 questionnaires with total-score calculation, severity bands, and an evaluation cutoff flag.",
        "Five integrated cognitive tasks: MMSE, Memory Recall, N-Back, Boston Naming, and Trail Making.",
        "Raw task telemetry submitted by the frontend and transformed into authoritative feature values by FastAPI services.",
        "Supabase/PostgreSQL storage for patient, assessment, screening, game, event, and Model 1 result data.",
        "A fixed-order 47-feature vector for Model 1 cognitive-performance regression.",
        "A final results endpoint and frontend page that remains usable after refresh or direct navigation because results are reloaded from persisted backend data.",
    ]:
        story.append(bullet(text))
    story.append(heading("Design principles applied", 2))
    story.append(table(["Principle", "Implementation decision", "Why it matters"], [
        ("Single source of truth", "Backend calculates authoritative features and stores results.", "Avoids browser-only state being treated as clinical/research data."),
        ("Session linkage", "All modules carry the same assessment_id.", "Preserves a coherent, auditable assessment record."),
        ("Layered architecture", "UI -> API router -> service -> repository -> Supabase.", "Keeps validation, business logic, and persistence separated."),
        ("Safe presentation", "Results use non-diagnostic language and show unavailable future components as pending.", "Prevents overclaiming system capability."),
    ], [3.2 * cm, 6.1 * cm, 7.2 * cm]))
    story.append(PageBreak())


def add_architecture(story):
    section_title(story, "2. System Architecture", "The implementation follows a client-server architecture. The React application handles interaction and telemetry capture. FastAPI validates payloads, calculates features, and persists records through repository classes. Supabase provides the PostgreSQL data store.")
    story.append(Diagram("architecture"))
    story.append(p("Figure 1. Layered system architecture and the Model 1 integration point.", "caption"))
    story.append(heading("Layer responsibilities", 2))
    story.append(table(["Layer", "Implemented responsibility"], [
        ("React + TypeScript", "Multi-step assessment route flow; patient and screening forms; five game interfaces; timing and interaction telemetry; retry/error states; final results display."),
        ("FastAPI routers", "REST endpoints for assessment creation, screening completion, game completion, Model 1 prediction, and result retrieval."),
        ("Service layer", "Assessment state control, score calculation, feature extraction, fixed-schema aggregation, error translation, and response shaping."),
        ("Repository layer", "Isolated Supabase queries and inserts/upserts; keeps persistence details out of API and calculation code."),
        ("Supabase/PostgreSQL", "Relational tables, UUID keys, referential relationships, uniqueness rules, database-level constraints, and JSON payload fields for rich telemetry."),
    ], [4.0 * cm, 12.5 * cm]))
    story.append(callout("The frontend does not directly connect to Supabase and does not compute the final authoritative feature values. This keeps the persisted research record consistent with the backend's validation and feature logic."))
    story.append(PageBreak())


def add_process(story):
    section_title(story, "3. End-to-End Assessment Process", "The system uses a session-first workflow. A patient record is created, then an assessment record is created. The resulting assessment_id is passed through every subsequent route and is the foreign key used by all result tables.")
    story.append(Diagram("flow", height=5.6 * cm))
    story.append(p("Figure 2. Assessment process and the role of the shared assessment_id.", "caption"))
    story.append(heading("Implemented sequence", 2))
    rows = [
        ("1", "Create session", "Patient details are submitted. The backend creates patients and assessments records and returns assessment_id."),
        ("2", "Mental health", "PHQ-9 and GAD-7 answers are scored and persisted once per assessment."),
        ("3", "Cognitive tasks", "MMSE, Memory Recall, N-Back, Boston Naming, and Trail Making are completed in sequence."),
        ("4", "Feature extraction", "Each game completion payload is validated and transformed into task-specific numerical features."),
        ("5", "Model 1", "After all five task records exist, the aggregator builds and validates the 47-feature vector before prediction and storage."),
        ("6", "Results", "The result service loads all persisted components, checks completion, and returns a stable response for the final page."),
    ]
    story.append(table(["Step", "Module", "Implementation"], rows, [1.0 * cm, 4.0 * cm, 11.5 * cm]))
    story.append(heading("Assessment-state handling", 2))
    story.append(p("The assessment session stores completed stages and a current stage. The Results service derives a completion checklist for PHQ-9, GAD-7, each game, and Model 1. This means the page can identify an incomplete session, an assessment waiting for a Model 1 result, or a completed assessment without relying only on browser navigation state."))
    story.append(PageBreak())


def add_frontend(story):
    section_title(story, "4. Frontend Implementation", "The frontend is implemented in React and TypeScript. The main application route flow guides a participant from the start screen through patient registration, screening, the five cognitive tasks, and the result page.")
    story.append(heading("Route and user-experience implementation", 2))
    story.append(table(["Area", "Implemented work"], [
        ("Assessment routing", "Home -> Patient -> Mental Health -> Cognitive Assessment -> MMSE -> Memory Recall -> N-Back -> Boston Naming -> Trail Making -> Results."),
        ("Shared context", "The returned assessment_id is carried into task routes and API requests to maintain one linked assessment session."),
        ("Reusable UI", "Application shell, assessment progress display, game shell, buttons, loading states, and failure states reduce repeated layout logic."),
        ("Task telemetry", "Games capture task-specific events, responses, timestamps, retries, clicks, pointer movement samples, and completion payloads."),
        ("Results resilience", "The Results screen requests persisted data from the backend. Refreshes and direct result URLs do not depend on in-memory frontend state."),
        ("User feedback", "Loading, incomplete, retry, and server-error states are exposed rather than silently showing incorrect or stale data."),
    ], [4.0 * cm, 12.5 * cm]))
    story.append(heading("Frontend API boundary", 2))
    story.append(p("The API client in frontend/src/services/api.ts owns communication with the backend. It sends typed payloads to the assessment, screening, game, Model 1, and results endpoints. The browser collects interactions; the backend owns validation and derived values."))
    story.append(callout("A key implementation improvement was changing the result page from navigation-dependent presentation to persisted-data presentation. This directly addresses the common failure mode where a refresh loses a client-only result."))
    story.append(PageBreak())


def add_backend(story):
    section_title(story, "5. Backend, APIs, and Validation", "FastAPI exposes the application API. The backend is divided into feature-oriented modules and uses Pydantic request schemas, service classes, and repositories. This separation keeps game logic testable and prevents persistence calls from being mixed with presentation code.")
    story.append(heading("API module design", 2))
    story.append(table(["Module", "Role"], [
        ("assessments", "Creates the patient and assessment session; controls stage-aware session state."),
        ("mental_health", "Receives PHQ-9/GAD-7 answers, calculates score/severity, checks valid UUIDs, and avoids duplicate records."),
        ("games/mmse", "Validates MMSE event payloads and derives orientation, attention, recall, language, timing, omission, and consistency measures."),
        ("games/memory", "Processes learning, immediate recall, delayed recall, recognition, confidence, retry, and latency data."),
        ("games/nback", "Computes accuracy, hit/false-alarm metrics, d-prime, response consistency, fatigue trend, and time measures."),
        ("games/boston_naming", "Processes naming responses, cue use, error categories, typing response durations, and difficulty-aware accuracy."),
        ("games/trail_making", "Calculates path, sequence, switching, backtracking, entropy, trajectory, and jitter features; also persists sampled raw telemetry."),
        ("ml/model1", "Fetches all required game records, builds the exact 47-feature vector, validates it, runs Model 1, and stores the result."),
        ("results", "Aggregates persisted status, screening, Model 1 metadata/result, and component completion into a frontend-safe result response."),
    ], [4.1 * cm, 12.4 * cm]))
    story.append(heading("Validation and failure behaviour", 2))
    for text in [
        "Assessment IDs are validated as UUIDs before dependent work is performed.",
        "Feature aggregation requires all five game results. Missing components produce an explicit incomplete-assessment error rather than a partial Model 1 vector.",
        "The 47-feature vector is checked for exact ordered schema, numeric values, finite values, and non-zero denominators before model inference.",
        "Screening results are idempotent: a completed PHQ-9/GAD-7 pair can be returned as already completed instead of inserted again.",
        "The results response exposes incomplete and awaiting-model statuses, enabling the frontend to show actionable retry guidance.",
    ]:
        story.append(bullet(text))
    story.append(PageBreak())


def add_database(story):
    section_title(story, "6. Supabase Data Model and Persistence", "Supabase PostgreSQL stores the assessment as a linked relational record. UUID primary keys and foreign keys connect patient, session, screening, game result, telemetry, and Model 1 rows.")
    story.append(Diagram("database", height=8.0 * cm))
    story.append(p("Figure 3. Core persisted entities. Result tables are linked to assessments through assessment_id.", "caption"))
    story.append(heading("Persistence controls", 2))
    story.append(table(["Control", "Implementation"], [
        ("Primary identifiers", "UUID primary keys are created with pgcrypto/gen_random_uuid()."),
        ("Referential integrity", "Every result record references assessments(assessment_id) with on delete cascade."),
        ("One result per task", "Each task result table enforces a unique assessment_id constraint."),
        ("Input ranges", "SQL CHECK constraints enforce valid score, ratio, count, time, and non-negative value ranges."),
        ("Query performance", "Indexes are defined for assessment_id and for Trail Making telemetry queries."),
        ("Flexible telemetry", "Raw nested payloads/layout are retained in JSONB where a fixed relational shape would lose useful interaction detail."),
    ], [4.0 * cm, 12.5 * cm]))
    story.append(heading("Stored entities", 2))
    story.append(p("The current schema includes patients, assessments, phq9_results, gad7_results, mmse_results, memory_results, nback_results, boston_naming_results, trail_making_results, trail_making_events, and model1_results. The final Results endpoint is deliberately computed from these persisted records rather than from a separate duplicate results table."))
    story.append(PageBreak())


def add_mental_health(story):
    section_title(story, "7. Mental Health Screening", "The mental-health module implements PHQ-9 and GAD-7 as structured questionnaires. Each response is an integer in the range 0 to 3. The backend calculates total score, severity category, and a boolean indicating whether the score meets the configured evaluation cutoff.")
    story.append(heading("Scoring equations", 2))
    story.append(table(["Instrument", "Equation", "Used in the system"], [
        ("PHQ-9", "PHQ9_total = sum(q1, q2, ..., q9), where qi in {0,1,2,3}", "Stored in phq9_results.total_score; maximum = 27."),
        ("GAD-7", "GAD7_total = sum(q1, q2, ..., q7), where qi in {0,1,2,3}", "Stored in gad7_results.total_score; maximum = 21."),
        ("Evaluation flag", "evaluation_cutoff_met = (total_score >= 10)", "Returned for both instruments to signal the configured review threshold."),
    ], [3.0 * cm, 7.3 * cm, 6.2 * cm]))
    story.append(heading("Severity-band implementation", 2))
    story.append(table(["Scale", "Score range", "Severity returned"], [
        ("PHQ-9", "0-4 / 5-9 / 10-14 / 15-19 / 20-27", "Minimal / Mild / Moderate / Moderately severe / Severe"),
        ("GAD-7", "0-4 / 5-9 / 10-14 / 15-21", "Minimal / Mild / Moderate / Severe"),
    ], [3.0 * cm, 6.0 * cm, 7.5 * cm]))
    story.append(callout("The current implementation reports screening scores and severity as assessment context. It does not classify pseudo-dementia, diagnose psychiatric conditions, or determine whether cognitive performance is neurodegenerative or psychiatric-related."))
    story.append(PageBreak())


def add_games(story):
    section_title(story, "8. Cognitive Task Implementation", "The five tasks are implemented as browser-based interactions. Each task produces a completion payload that is validated and transformed into a structured feature record by the backend. The following table describes the implemented scope.")
    story.append(table(["Task", "Primary cognitive area", "Captured implementation data", "Persisted outcome"], [
        ("MMSE", "Orientation, registration, attention, recall, language, command following.", "Phase answers, correctness, response timestamps, corrections, omissions, completion timing.", "Domain accuracies plus timing, error, correction, and consistency features."),
        ("Memory Recall", "Encoding, immediate recall, delayed recall, recognition, sequence retention.", "Target words, recalled words, response gaps, recognition choices, confidence ratings, retries.", "Accuracy, decay, latency, errors, hesitation, confidence variability, and consistency trend."),
        ("N-Back", "Working memory and sustained attention.", "Trial targets, responses, hits, false alarms, response latency, first/second-half performance.", "Accuracy, signal-detection measures, timing variation, consistency, omission/commission errors, fatigue."),
        ("Boston Naming", "Lexical retrieval and naming performance.", "Image responses, cues, semantic/phonemic errors, response timing/duration, self-corrections.", "Naming/cue/error rates, latency features, difficulty-adjusted accuracy, response consistency."),
        ("Trail Making", "Visual attention, sequencing, set shifting, psychomotor control.", "Ordered target clicks, timestamps, sampled pointer coordinates, error clicks, layout and paths.", "Path, sequence, switching, backtracking, entropy, deviation, jitter, and raw telemetry."),
    ], [2.2 * cm, 3.3 * cm, 5.4 * cm, 5.6 * cm]))
    story.append(heading("Backend-owned feature extraction", 2))
    story.append(p("The frontend is responsible for recording what happened during the task. It does not declare the final feature values. Backend feature functions compute the saved measures from the raw payload so the same logic is used consistently regardless of browser state or UI retries."))
    story.append(PageBreak())


def add_formula_sections(story):
    section_title(story, "9. Feature Engineering and Formula Reference", "The formulas below are the implemented feature calculations or the direct transformations used to create Model 1 inputs. For a mean, standard deviation, and ratio, only valid observed values are used and denominator checks are performed where required.")
    story.append(heading("9.1 Common notation", 2))
    story.append(table(["Symbol", "Meaning"], [
        ("N", "Number of valid trials, responses, opportunities, or time segments for the relevant task."),
        ("C", "Number of correct responses."),
        ("RTi", "Latency/reaction time for valid response i."),
        ("mean(x)", "Arithmetic mean of observed values."),
        ("stdev(x)", "Population standard deviation used for variability-related features."),
        ("max(0, x)", "Lower-bound safeguard so duration-like outputs cannot be negative."),
    ], [3.2 * cm, 13.3 * cm]))
    story.append(heading("9.2 MMSE features", 2))
    story.append(table(["Feature", "Formula", "Purpose / use"], [
        ("Domain accuracy", "domain_accuracy = correct_in_domain / domain_opportunities", "Orientation, registration, attention, serial-7, recall, language, and command-following measures."),
        ("Response latency", "response_latency = mean(submitted_at - started_at)", "Average MMSE response speed."),
        ("Latency variability", "latency_variability = stdev(RT1, ..., RTN)", "Stability of response timing."),
        ("Correction frequency", "correction_frequency = corrected_responses / response_opportunities", "Model 1 input and error recovery proxy."),
        ("Performance consistency", "performance_consistency = 1 - stdev(domain_accuracies)", "Cross-domain stability proxy."),
        ("Overall MMSE score", "10*orientation + 3*registration + 5*attention + 3*recall + 6*language + 3*command", "30-point reconstructed score used by Model 1."),
        ("MMSE hesitation", "response_latency * max(0, 1 - performance_consistency)", "Derived Model 1 feature."),
        ("MMSE skip frequency", "omission_errors / 30", "Derived Model 1 feature over response opportunities."),
        ("Error recovery time", "response_latency * correction_frequency", "Derived Model 1 proxy."),
    ], [3.1 * cm, 7.0 * cm, 6.4 * cm]))
    story.append(heading("9.3 Memory Recall features", 2))
    story.append(table(["Feature", "Formula", "Purpose / use"], [
        ("Immediate recall accuracy", "correct_immediate_targets / total_targets", "Encoding and immediate retrieval."),
        ("Delayed recall accuracy", "correct_delayed_targets / total_targets", "Delayed retrieval."),
        ("Recognition accuracy", "correct_recognition_choices / total_recognition_items", "Recognition discrimination."),
        ("Recall decay rate", "(immediate_recall_accuracy - delayed_recall_accuracy) / immediate_recall_accuracy", "Memory loss between immediate and delayed recall."),
        ("Recall latency", "first_delayed_response_time - delayed_phase_start", "Time to initiate delayed recall."),
        ("Sequence recall accuracy", "order_preserved_adjacent_pairs / recalled_adjacent_pairs", "Order retention."),
        ("Hesitation duration", "sum(gap_i - threshold for every gap_i > threshold)", "Pauses beyond the task hesitation threshold."),
        ("Confidence variability", "stdev(confidence_immediate, confidence_delayed, confidence_recognition)", "Stability of reported confidence."),
        ("Memory consistency trend", "targets_correct_in_both / targets_correct_immediately", "Retention consistency across recall phases."),
    ], [3.1 * cm, 7.0 * cm, 6.4 * cm]))
    story.append(PageBreak())
    story.append(heading("9.4 N-Back features", 2))
    story.append(table(["Feature", "Formula", "Purpose / use"], [
        ("N-Back accuracy", "correct_scored_trials / total_scored_trials", "Overall working-memory task accuracy."),
        ("Hit rate", "hits / target_trials", "Correct response to target trials."),
        ("False-alarm rate", "false_alarms / non_target_trials", "Incorrect responses to non-target trials."),
        ("Sensitivity", "hit_rate - false_alarm_rate", "Simple target/non-target separation measure."),
        ("Adjusted d-prime", "z((H + 0.5)/(T + 1)) - z((FA + 0.5)/(NT + 1))", "Signal detection discrimination; correction prevents infinite z values."),
        ("Response consistency", "1 / (1 + stdev(valid_RTs) / mean(valid_RTs))", "Inverse coefficient-of-variation consistency measure."),
        ("Fatigue trend", "second_half_accuracy - first_half_accuracy", "Change in accuracy during the task."),
        ("N-Back idle time", "max(0, completion_time - response_latency * (hit_rate*T_est + false_alarm_rate*NT_est))", "Model 1 inactive-time proxy."),
        ("Missed target rate", "min(1, omission_errors / T_est)", "Model 1 omission measure using estimated target trials."),
    ], [3.1 * cm, 7.0 * cm, 6.4 * cm]))
    story.append(heading("9.5 Boston Naming features", 2))
    story.append(table(["Feature", "Formula", "Purpose / use"], [
        ("Naming accuracy", "correct_final_responses / total_trials", "Overall lexical naming performance."),
        ("Cue rates", "cue_type_count / total_trials", "Semantic, phonemic, and total cue dependency."),
        ("Mean response latency", "mean(response_latency_ms) / 1000", "Model 1 response-latency input in seconds."),
        ("Difficulty-adjusted accuracy", "sum(weight_i * correct_i) / sum(weight_i), weights: easy=1, medium=1.25, hard=1.5", "Difficulty-sensitive task accuracy."),
        ("Latency consistency", "1 / (1 + stdev(latencies) / mean(latencies))", "Response timing stability."),
        ("Response signature consistency", "unique_response_signatures / total_response_signatures", "Diversity/repetition proxy across responses."),
        ("Naming consistency", "mean(latency_consistency, response_signature_consistency)", "Combined consistency measure."),
        ("Typing/speaking speed", "mean(number_of_words / response_duration_seconds)", "Model 1 linguistic response-speed feature."),
        ("Time per image", "(completion_time_ms / total_trials) / 1000", "Model 1 per-item time feature."),
    ], [3.1 * cm, 7.0 * cm, 6.4 * cm]))
    story.append(heading("9.6 Trail Making features", 2))
    story.append(table(["Feature", "Formula", "Purpose / use"], [
        ("Path efficiency", "ideal_path_length / actual_path_length", "How directly the participant traversed the expected path."),
        ("Sequence accuracy", "correct_target_count / total_targets", "Correctness of alternating sequence selections."),
        ("Switching delay", "mean(correct_target_RTs after first target)", "Set-shifting speed after task initiation."),
        ("Backtracking frequency", "backtracking_count / total_targets", "Reversal/correction behaviour."),
        ("Cursor movement entropy", "-sum(p(direction) * log2(p(direction)))", "Directional movement dispersion."),
        ("Trajectory deviation", "mean((actual_segment - ideal_segment) / ideal_segment)", "Deviation from the ideal sequence path."),
        ("Tremor/jitter frequency", "(direction_reversals + micro_movements) / total_time_seconds", "Fine movement instability proxy."),
        ("Time degradation ratio", "second_half_mean_RT / first_half_mean_RT", "Timing change over task progression."),
    ], [3.1 * cm, 7.0 * cm, 6.4 * cm]))
    story.append(callout("These feature equations support research/demo scoring. They are not clinical diagnostic thresholds, and the prototype does not infer disease labels from any single formula."))
    story.append(PageBreak())


def add_model(story):
    section_title(story, "10. Model 1 Integration and 47-Feature Contract", "Model 1 is integrated as a cognitive-performance regressor. It is only invoked after all five cognitive task result records are available. The feature aggregator reads the saved records, derives any required transformations, and enforces a fixed 47-feature schema before inference.")
    story.append(Diagram("feature", height=5.2 * cm))
    story.append(p("Figure 4. Task features are assembled into one ordered Model 1 vector.", "caption"))
    story.append(heading("Inference representation", 2))
    story.append(callout("<b>Model 1 prediction:</b> cognitive_performance_score = f_XGBoost(x1, x2, ..., x47). The exact prediction is produced by the trained serialized model, so it does not reduce to a single manually calculated linear equation. The implemented code validates the ordered input vector before calling the model and stores the score with model metadata and the feature vector."))
    story.append(heading("Model safeguards", 2))
    for text in [
        "The vector must have exactly 47 fields in the expected order.",
        "Every value must be numeric and finite.",
        "Required task records must exist before aggregation; otherwise the API returns the missing game names.",
        "Derived ratios use safe division and reject zero denominators rather than silently emitting invalid values.",
        "The stored model1_results row keeps assessment_id, cognitive_performance_score, model name/version, and the feature_vector JSON payload.",
    ]:
        story.append(bullet(text))
    story.append(PageBreak())


def add_results(story):
    section_title(story, "11. Final Results Aggregation", "The final page is backed by a dedicated Results service. Instead of trusting a locally-held frontend result, it loads the persisted assessment, screening results, Model 1 result, and stage completion state using assessment_id.")
    story.append(heading("Returned result components", 2))
    story.append(table(["Component", "Displayed when available", "Current status"], [
        ("Assessment summary", "Participant name, short assessment ID, completed/missing component checklist.", "Implemented"),
        ("PHQ-9", "Total score out of 27 and severity label.", "Implemented"),
        ("GAD-7", "Total score out of 21 and severity label.", "Implemented"),
        ("Model 1", "Cognitive performance score, model name/version, feature count, model type, and scale metadata.", "Implemented"),
        ("Model 3", "Speech assessment placeholder and description.", "Explicitly pending"),
        ("Fusion", "Overall multimodal result placeholder and description.", "Explicitly pending"),
    ], [3.2 * cm, 8.1 * cm, 5.2 * cm]))
    story.append(heading("Completion logic", 2))
    story.append(table(["Results status", "Condition", "Frontend meaning"], [
        ("completed", "All screening, game, and Model 1 components exist.", "Show available results and completed assessment summary."),
        ("awaiting_model1", "All non-Model 1 components exist but no stored Model 1 result exists.", "Assessment data is complete; prompt retry for Model 1."),
        ("incomplete", "One or more required components are absent.", "Show missing component information instead of an invalid score."),
    ], [3.2 * cm, 7.0 * cm, 6.3 * cm]))
    story.append(callout("The language used in the result experience is intentionally non-diagnostic. The system presents assessment scores and a research/demo cognitive performance output, not a diagnosis of Alzheimer’s disease, MCI, pseudo-dementia, or any mental health condition."))
    story.append(PageBreak())


def add_quality(story):
    section_title(story, "12. Reliability, Testing, and Current Limitations", "The project includes verification at the frontend build and backend API/service levels. Database constraints and explicit status responses add protection against missing data and invalid model inputs.")
    story.append(heading("Completed verification", 2))
    story.append(table(["Area", "Verification performed", "Outcome"], [
        ("Frontend", "Production build: npm run build.", "Passed."),
        ("Backend results", "Router and service tests for result aggregation and status behaviour.", "Passed."),
        ("Assessment/Model 1", "Assessment router and Model 1 endpoint tests in the targeted test run.", "Passed."),
        ("Targeted test run", "python -m pytest tests/results tests/assessments/test_router.py tests/model1/test_router.py -q.", "14 passed, 1 warning at the time of verification."),
    ], [3.1 * cm, 9.4 * cm, 4.0 * cm]))
    story.append(heading("Current limitations and accurately-scoped future work", 2))
    for text in [
        "This is a research/demo prototype and not a validated clinical diagnostic instrument.",
        "No authentication or role-based access control is currently implemented; CORS is permissive for development and must be tightened for deployment.",
        "Live Supabase validation depends on applying the current SQL schema in the target Supabase project.",
        "End-to-end browser automation is not yet included.",
        "Trail Making pointer data is sampled to balance telemetry detail and browser overhead; it is not a capture of every movement event.",
        "Speech assessment (Model 3), multimodal fusion, MRI analysis, disease-stage classification, explainability heatmaps/SHAP, and longitudinal progression prediction are future work, not current features.",
    ]:
        story.append(bullet(text))
    story.append(heading("Recommended next implementation steps", 2))
    story.append(p("Before wider use, add authenticated access, restrict CORS, apply migrations through a controlled environment, add end-to-end tests, introduce audit logging, establish consent/data-retention processes, validate the model on appropriate held-out data, and obtain clinical/research governance review for any real participant deployment."))
    story.append(PageBreak())


def add_appendix_features(story):
    section_title(story, "Appendix A. Model 1 Feature Bifurcation", "The 47 input columns are grouped below by task. This appendix mirrors the aggregator contract and is useful for implementation review and PPT preparation.")
    groups = [
        ("MMSE - 14", ["overall_mmse_score", "orientation_score", "attention_score", "recall_score", "language_score", "question_accuracy", "mean_reaction_time", "reaction_time_variance", "hesitation_duration", "correction_frequency", "skip_frequency", "confidence_variability", "completion_time", "error_recovery_time"]),
        ("Memory Recall - 10", ["immediate_recall_accuracy", "delayed_recall_accuracy", "recognition_accuracy", "recall_decay_rate", "recall_latency", "omission_errors", "intrusion_errors", "sequence_recall_accuracy", "retry_frequency", "memory_consistency_trend"]),
        ("N-Back - 7", ["nback_accuracy", "false_positive_rate", "missed_target_rate", "sustained_attention_score", "attention_drift", "idle_time", "fatigue_progression"]),
        ("Boston Naming - 8", ["naming_accuracy", "response_latency", "semantic_error_frequency", "phonemic_error_frequency", "cue_dependency_rate", "no_response_frequency", "typing_speaking_speed", "time_per_image"]),
        ("Trail Making - 8", ["path_efficiency", "sequence_accuracy", "switching_delay", "backtracking_frequency", "rule_violation_count", "cursor_movement_entropy", "trajectory_deviation", "tremor_jitter_frequency"]),
    ]
    rows = []
    index = 1
    for group, features in groups:
        for feature in features:
            rows.append((str(index), group, feature))
            index += 1
    story.append(table(["Order", "Task group", "Feature name"], rows, [1.5 * cm, 5.3 * cm, 10.0 * cm]))
    story.append(PageBreak())


def add_appendix_inventory(story):
    section_title(story, "Appendix B. API and Database Inventory")
    story.append(heading("Key API endpoints", 2))
    story.append(table(["Method", "Endpoint", "Purpose"], [
        ("POST", "/api/assessments", "Create patient and assessment session."),
        ("POST", "/api/assessments/{assessment_id}/mental-health/complete", "Persist PHQ-9 and GAD-7 results."),
        ("POST", "/api/assessments/{assessment_id}/games/mmse/<br/>complete", "Persist MMSE-derived result features."),
        ("POST", "/api/assessments/{assessment_id}/games/memory/<br/>complete", "Persist Memory Recall-derived result features."),
        ("POST", "/api/assessments/{assessment_id}/games/nback/<br/>complete", "Persist N-Back-derived result features."),
        ("POST", "/api/assessments/{assessment_id}/games/boston-naming/<br/>complete", "Persist Boston Naming-derived result features."),
        ("POST", "/api/assessments/{assessment_id}/games/trail-making/<br/>complete", "Persist Trail Making result features and telemetry."),
        ("POST", "/api/assessments/{assessment_id}/model1/predict", "Build the 47-feature vector, run Model 1, and store the output."),
        ("GET", "/api/assessments/{assessment_id}/results", "Return the persisted assessment summary and component statuses."),
    ], [2.0 * cm, 8.0 * cm, 6.8 * cm]))
    story.append(heading("Environment and run configuration", 2))
    story.append(note_table([
        ("Backend variables", "SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ENVIRONMENT"),
        ("Frontend variable", "VITE_API_BASE_URL"),
        ("Frontend development", "frontend: npm install; npm run dev (default localhost:5173)"),
        ("Backend development", "backend: create/activate venv; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8000"),
        ("Database setup", "Apply database/schema.sql, then any required per-game schema files in the Supabase SQL editor."),
    ]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(callout("End of report. The source of truth for the described implementation is the current NeuroDetect repository. This document is designed to support project demonstration, implementation review, and technical presentation preparation."))


def build_pdf() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    story = []
    add_cover(story)
    add_contents(story)
    add_scope(story)
    add_architecture(story)
    add_process(story)
    add_frontend(story)
    add_backend(story)
    add_database(story)
    add_mental_health(story)
    add_games(story)
    add_formula_sections(story)
    add_model(story)
    add_results(story)
    add_quality(story)
    add_appendix_features(story)
    add_appendix_inventory(story)
    ReportDoc(str(OUTPUT)).build(story)
    return OUTPUT


if __name__ == "__main__":
    print(build_pdf())
