import asyncio
import json

from fastapi import Request
from starlette.responses import StreamingResponse

from gigbid_core.db import Event, db


def parse_event(payload):
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {
            "status": "legacy_record",
            "detail": "Earlier redaction format retained. Exact usage is available in the saved run state.",
        }


def event_stream(request: Request, user, run_id, after=0):
    async def generate():
        cursor = after
        while not await request.is_disconnected():
            with db() as session:
                events = [
                    (e.id, e.node, e.payload, e.created)
                    for e in session.query(Event)
                    .filter(Event.tenant == user, Event.run_id == run_id, Event.id > cursor)
                    .order_by(Event.id)
                    .limit(100)
                    .all()
                ]
            for event_id, node, payload, created in events:
                cursor = event_id
                yield f"id: {cursor}\ndata: {json.dumps({'id': event_id, 'node': node, 'payload': parse_event(payload), 'created': created})}\n\n"
            if not events:
                yield ": heartbeat\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
