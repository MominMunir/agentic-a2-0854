import { useState } from "react";
import { post } from "../lib/api/client";
export default function ApprovalPanel({
  run,
  text,
  onDone,
  onError,
}: {
  run: any;
  text: string;
  onDone: () => void;
  onError: (message: string) => void;
}) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  async function decide(decision: string) {
    setBusy(true);
    try {
      await post(`/runs/${run.id}/approve`, { decision, text, reason });
      onDone();
    } catch (e: any) {
      onError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="approval">
      <div>
        <span className="eyebrow">YOUR DECISION</span>
        <h3>Review the proof. Make the call.</h3>
        <p>Approval authorizes this exact text and the displayed cost.</p>
      </div>
      <div className="preview">
        <strong>{run.state.preview?.connects_cost ?? 0} Connects</strong>
        <span>
          {run.kind === "conversation"
            ? "Message"
            : `USD ${run.state.price?.amount ?? 0} bid`}{" "}
          · {run.state.preview?.marketplace || "marketplace"} · preview
        </span>
      </div>
      <label>
        Rejection reason
        <input
          aria-label="Rejection reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="What should change?"
        />
      </label>
      <div className="actions">
        <button
          className="primary"
          disabled={busy}
          onClick={() =>
            decide(text !== run.state.draft?.cover_letter ? "edit" : "approve")
          }
        >
          Approve {run.kind === "conversation" ? "message" : "proposal"}
        </button>
        <button
          className="danger"
          disabled={busy || !reason.trim()}
          onClick={() => decide("reject")}
        >
          Reject draft
        </button>
      </div>
    </section>
  );
}
