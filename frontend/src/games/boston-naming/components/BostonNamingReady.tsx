import { PrimaryButton, SecondaryButton } from "../../../components/ui/buttons";

interface BostonNamingReadyProps {
  permissionState: "idle" | "requesting" | "granted" | "denied" | "unsupported";
  permissionError: string | null;
  onRequestPermission: () => void;
  onStart: () => void;
}

export function BostonNamingReady({
  permissionState,
  permissionError,
  onRequestPermission,
  onStart,
}: BostonNamingReadyProps) {
  const canStart = permissionState === "granted";

  return (
    <section className="boston-naming__panel">
      <p className="boston-naming__eyebrow">Ready</p>
      <h2>You&apos;re ready to begin.</h2>
      <p className="boston-naming__copy">
        We&apos;ll show one visual prompt at a time, record your spoken answer, and keep everything in the same assessment session.
      </p>
      <div className="boston-naming__actions">
        <SecondaryButton type="button" onClick={onRequestPermission} disabled={permissionState === "requesting"}>
          {permissionState === "requesting" ? "Requesting Microphone..." : "Enable Microphone"}
        </SecondaryButton>
        <PrimaryButton type="button" onClick={onStart} disabled={!canStart}>
          Start Boston Naming
        </PrimaryButton>
      </div>
      <p className="boston-naming__hint">
        {permissionState === "granted" ? "Microphone connected." : permissionError ?? "Microphone access is required to begin this stage."}
      </p>
    </section>
  );
}
