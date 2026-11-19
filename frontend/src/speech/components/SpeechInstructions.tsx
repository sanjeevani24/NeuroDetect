export function SpeechInstructions() {
  return (
    <section className="speech-instructions">
      <div className="section-copy">
        <p className="hero-card__eyebrow">SPEECH ACTIVITY · PICTURE DESCRIPTION</p>
        <h2>Cookie Theft Picture Description</h2>
        <p className="hero-card__body">
          Please describe everything you see happening in the picture. Speak clearly, at your normal pace,
          and in full sentences. When you are ready, grant microphone access and select <strong>Start Recording</strong>.
        </p>
      </div>

      <div className="speech-stimulus-card" role="region" aria-label="Task stimulus">
        <div className="speech-stimulus-container">
          <div className="speech-stimulus-image-wrapper">
            <img
              src="/images/cookie-theft.png"
              alt="Cookie Theft Picture Description Stimulus showing a kitchen scene with children and overflowing sink"
              className="speech-stimulus-image"
              loading="eager"
            />
          </div>
          <div className="speech-stimulus-prompt-box">
            <p className="speech-stimulus-prompt">
              Tell us everything you see happening in this picture. Describe what the people are doing,
              what is happening around them, and all the details you can observe.
            </p>
          </div>
        </div>
      </div>

      <div className="speech-task-tips" role="note" aria-label="Helpful tips">
        <h4>Before you begin:</h4>
        <ul>
          <li>Find a quiet room with minimal background noise.</li>
          <li>Speak naturally for at least 15 to 60 seconds describing all details.</li>
          <li>You will have a chance to listen to your recording before submitting.</li>
        </ul>
      </div>
    </section>
  );
}
