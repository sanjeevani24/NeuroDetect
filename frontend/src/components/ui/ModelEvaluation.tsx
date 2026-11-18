import type { ModelEvaluationSummary } from "../../services/api";

function formatMetric(value: number | null | undefined, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "Unavailable";
}

export function ModelEvaluation({ evaluation }: { evaluation?: ModelEvaluationSummary | null }) {
  const metrics = evaluation?.test_metrics;

  return (
    <details className="hero-card model-evaluation">
      <summary>Model confidence, accuracy and test results</summary>
      <div className="model-evaluation__body">
        <p>
          These details describe the computer model, separate from your personal performance score.
          It predicts a number rather than a diagnosis or a category.
        </p>
        <div className="results-grid">
          <article className="results-card">
            <h3>Confidence score</h3>
            <p><strong>Unavailable</strong></p>
            <p>The current model does not provide a confidence percentage or a prediction interval for your score.</p>
          </article>
          <article className="results-card">
            <h3>Accuracy rate</h3>
            <p><strong>Not applicable to this model</strong></p>
            <p>Classification accuracy counts correct categories. This model predicts a numeric score, so its saved tests report prediction errors and R² instead.</p>
          </article>
        </div>
        <section className="results-card" aria-labelledby="confusion-matrix-heading">
          <h3 id="confusion-matrix-heading">Confusion matrix</h3>
          <p><strong>Not applicable to this model</strong></p>
          <p>A confusion matrix compares actual and predicted categories. The current model has no category predictions or saved category-labelled test results, so no matrix can be calculated from its saved metrics.</p>
        </section>
        <section aria-labelledby="regression-metrics-heading">
          <h3 id="regression-metrics-heading">Saved model test results</h3>
          {evaluation ? (
            <>
              <p>
                Data: {evaluation.data_type === "synthetic" ? "computer-generated examples (synthetic)" : evaluation.data_type ?? "not recorded"}.
                {evaluation.test_samples !== null ? ` Test examples: ${evaluation.test_samples.toLocaleString()}.` : " Test sample count not recorded."}
                {evaluation.clinical_validation === false ? " The model has not been clinically validated." : evaluation.clinical_validation === null ? " Clinical validation status is not recorded." : ""}
              </p>
              <div className="model-evaluation__table-scroll">
                <table className="model-evaluation__table">
                  <caption>Evaluation of the packaged model on its test examples</caption>
                  <thead><tr><th scope="col">Measure</th><th scope="col">Value</th><th scope="col">What it means</th></tr></thead>
                  <tbody>
                    <tr><th scope="row">Mean absolute error (MAE)</th><td>{formatMetric(metrics?.mae)}</td><td>Average absolute difference between predicted and target scores. Lower is better.</td></tr>
                    <tr><th scope="row">Root mean squared error (RMSE)</th><td>{formatMetric(metrics?.rmse)}</td><td>A prediction error measure that gives larger mistakes more weight. Lower is better.</td></tr>
                    <tr><th scope="row">R²</th><td>{formatMetric(metrics?.r2, 4)}</td><td>How well predictions explain variation in target scores. This is not an accuracy or confidence percentage.</td></tr>
                    <tr><th scope="row">Median absolute error</th><td>{formatMetric(metrics?.median_absolute_error)}</td><td>The middle absolute prediction error. Lower is better.</td></tr>
                  </tbody>
                </table>
              </div>
              <p className="results-disclaimer">Source: the packaged model’s {evaluation.source}. These saved test results do not measure how accurate your individual score is.</p>
            </>
          ) : <p>Evaluation data for this model version is unavailable. No test values are estimated or substituted.</p>}
        </section>
        <p><a href="https://scikit-learn.org/stable/modules/model_evaluation.html">Read about model evaluation measures</a></p>
      </div>
    </details>
  );
}
