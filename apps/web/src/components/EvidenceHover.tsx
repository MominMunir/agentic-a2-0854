export default function EvidenceHover({
  claim,
  evidence,
}: {
  claim: any;
  evidence: any[];
}) {
  const sources = evidence.filter((e) => claim.evidence_ids.includes(e.id));
  return (
    <div
      className={"claim " + (sources.length ? "grounded" : "")}
      title={sources
        .map((e) => `${e.title}\n${e.text}\n${e.source}`)
        .join("\n\n")}
    >
      <p>{claim.text}</p>
      {sources.length > 0 && (
        <details>
          <summary>
            ✓ Inspect {sources.length} evidence source
            {sources.length > 1 ? "s" : ""}
          </summary>
          {sources.map((e) => (
            <div key={e.id}>
              <strong>{e.title}</strong>
              <p>{e.text}</p>
              <small>
                {e.provenance} · {e.date} · {e.source}
              </small>
            </div>
          ))}
        </details>
      )}
    </div>
  );
}
