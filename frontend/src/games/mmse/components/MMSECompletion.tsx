import { CompletionState, ErrorState, LoadingState } from "../../../components/ui/States";
import { PrimaryButton } from "../../../components/ui/buttons";

interface MMSECompletionProps {
  status: "idle" | "submitting" | "success" | "error";
  error: string | null;
  onRetry: () => void;
}

export function MMSECompletion({ status, error, onRetry }: MMSECompletionProps) {
  if (status === "submitting" || status === "idle") {
    return <LoadingState title="Saving MMSE results" message="Your responses are being processed." />;
  }

  if (status === "error") {
    return (
      <ErrorState
        title="We could not save the MMSE result"
        message={error ?? "Please try the submission again."}
        action={
          <PrimaryButton type="button" onClick={onRetry}>
            Retry submission
          </PrimaryButton>
        }
      />
    );
  }

  return (
    <CompletionState
      title="MMSE complete"
      message="The MMSE stage has been recorded. The assessment will continue to Memory Recall."
    />
  );
}
