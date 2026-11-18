const REFERENCES = [
  {
    name: "Mood questions (PHQ-9)",
    why: "We use these nine questions to ask about low mood and related difficulties over the past two weeks.",
    source: "Kroenke, Spitzer & Williams (2001). The PHQ-9: validity of a brief depression severity measure.",
    url: "https://pubmed.ncbi.nlm.nih.gov/11556941/",
    use: "The app uses the PHQ-9 questions and response scale.",
  },
  {
    name: "Worry questions (GAD-7)",
    why: "We use these seven questions to ask about worry, tension, and difficulty relaxing over the past two weeks.",
    source: "Spitzer, Kroenke, Williams & Löwe (2006). A brief measure for assessing generalized anxiety disorder: the GAD-7.",
    url: "https://pubmed.ncbi.nlm.nih.gov/16717171/",
    use: "The app uses the GAD-7 questions and response scale.",
  },
  {
    name: "Everyday questions (MMSE-inspired)",
    why: "We include questions about the day and place, remembering words, attention, and following instructions to explore different thinking skills.",
    source: "Folstein, Folstein & McHugh (1975). Mini-mental state: a practical method for grading the cognitive state of patients for the clinician.",
    url: "https://pubmed.ncbi.nlm.nih.gov/1202204/",
    use: "Reference for the activity design. Our browser questions and scoring are adapted; this is not the standard clinical MMSE.",
  },
  {
    name: "Letter matching (N-Back)",
    why: "We ask you to compare letters with earlier ones to explore how you hold and update information in mind.",
    source: "Kirchner (1958). Age differences in short-term retention of rapidly changing information.",
    url: "https://pubmed.ncbi.nlm.nih.gov/13539317/",
    use: "Research background for the N-Back approach. The app uses its own letter sequence, practice round, and timing.",
  },
  {
    name: "Name the pictures (Boston Naming-style)",
    why: "We ask you to name objects to explore finding words, including whether a hint helps.",
    source: "Boston Naming Test, Second Edition — PRO-ED publisher information.",
    url: "https://proedinc.com/products-11870.html?bCategory=TBI",
    use: "Reference for the picture-naming approach. The app uses its own emoji pictures and hints, rather than the published test materials.",
  },
  {
    name: "Connect the circles (Trail Making-style)",
    why: "We ask you to alternate numbers and letters to explore attention and switching between two sequences.",
    source: "Reitan (1958). Validity of the Trail Making Test as an indicator of organic brain damage.",
    url: "https://doi.org/10.2466/pms.1958.8.3.271",
    use: "Research background for the alternating sequence. The app uses a generated browser layout and pointer movements, rather than the standard paper test.",
  },
];

export function AssessmentSources() {
  return (
    <details className="assessment-sources">
      <summary>Sources and why we use them</summary>
      <div className="assessment-sources__body">
        <p>
          These references explain the questionnaires and approaches behind the activities.
          The memory and thinking activities are adapted for this prototype. Research on the
          original tests does not establish that this app has the same accuracy.
        </p>
        <ul className="assessment-sources__list">
          {REFERENCES.map((reference) => (
            <li key={reference.url}>
              <h3>{reference.name}</h3>
              <p><strong>Why we use it:</strong> {reference.why}</p>
              <p><strong>Source:</strong> <a href={reference.url}>{reference.source}</a></p>
              <p className="assessment-sources__note">{reference.use}</p>
            </li>
          ))}
          <li>
            <h3>Remember the items</h3>
            <p><strong>Why we use it:</strong> To explore remembering items straight away, after a delay, and when choosing from a list.</p>
            <p><strong>Source:</strong> NeuroDetect’s own word list and activity configuration. The project does not document a specific published test as its source.</p>
          </li>
          <li>
            <h3>Where the computer score comes from</h3>
            <p><strong>Source:</strong> The model’s saved training information identifies its training data as synthetic: computer-generated examples, rather than patient records.</p>
            <p><strong>Why it is used:</strong> The model combines results from the five thinking activities into an experimental performance score.</p>
            <p className="assessment-sources__note">The saved information does not explain why synthetic data was chosen. The model has not been clinically validated, and its score does not provide a diagnosis.</p>
          </li>
        </ul>
      </div>
    </details>
  );
}
