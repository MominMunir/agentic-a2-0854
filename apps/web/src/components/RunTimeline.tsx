export default function RunTimeline({ events }: { events: any[] }) {
  return (
    <ol className="timeline">
      {events.map((event, i) => (
        <li key={event.id || i}>
          <span className="timeline-dot" />
          <div>
            <strong>{event.node.replaceAll("_", " ")}</strong>
            <small>
              {event.payload?.status || "completed"}{" "}
              {event.payload?.usage
                ?.map(
                  (u: any) =>
                    ` · ${u.model} · ${u.input_tokens + u.output_tokens} tokens`,
                )
                .join("")}
            </small>
          </div>
        </li>
      ))}
    </ol>
  );
}
