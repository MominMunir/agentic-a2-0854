import hashlib
import json
from datetime import date
from io import BytesIO

from pypdf import PdfReader


def load_upload(filename, content, persona, industry="unspecified"):
    extension = filename.rsplit(".", 1)[-1].lower()
    if extension == "pdf":
        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
        kind = "cv"
    elif extension in {"md", "txt", "py", "ts", "tsx", "js", "sql", "json"}:
        text = content.decode("utf-8")
        kind = "code" if extension in {"py", "ts", "tsx", "js", "sql"} else "case_study"
        if extension == "json":
            parsed = json.loads(text)
            if isinstance(parsed, list) and all(
                isinstance(item, dict) and any(k in item for k in ["text", "summary", "cover_letter"])
                for item in parsed
            ):
                output = []
                digest = hashlib.sha256(content).hexdigest()[:20]
                for index, item in enumerate(parsed):
                    value = item.get("text") or item.get("summary") or item.get("cover_letter")
                    for part, start in enumerate(range(0, len(value.split()), 160)):
                        output.append(
                            {
                                "id": f"upload-{digest}-{index}-{part}",
                                "persona": persona,
                                "type": item.get(
                                    "type",
                                    "proposal"
                                    if "outcome" in item
                                    else "review"
                                    if "rating" in item
                                    else "case_study",
                                ),
                                "project": item.get("project", item.get("id", digest)),
                                "title": item.get("title", filename),
                                "text": " ".join(value.split()[start : start + 200]),
                                "skills": item.get("skills", []),
                                "date": item.get("date", date.today().isoformat()),
                                "industry": item.get("industry", industry),
                                "outcome": item.get("outcome", "unverified"),
                                "source": "upload://" + filename,
                                "provenance": "synthetic" if item.get("synthetic") else "user_upload",
                                "synthetic": bool(item.get("synthetic", False)),
                            }
                        )
                return output
            text = json.dumps(parsed, ensure_ascii=False)
    else:
        raise ValueError(
            "Supported formats: PDF, Markdown, UTF-8 text, JSON, Python, TypeScript, JavaScript, SQL"
        )
    if not text.strip():
        raise ValueError("Document contains no extractable text; scanned PDFs require OCR before upload.")
    digest = hashlib.sha256(content).hexdigest()[:20]
    chunks = []
    words = text.split()
    for index, start in enumerate(range(0, len(words), 160)):
        chunks.append(
            {
                "id": f"upload-{digest}-{index}",
                "persona": persona,
                "type": kind,
                "project": digest,
                "title": filename,
                "text": " ".join(words[start : start + 200]),
                "skills": [],
                "date": date.today().isoformat(),
                "industry": industry,
                "outcome": "unverified",
                "source": "upload://" + filename,
                "provenance": "user_upload",
                "synthetic": False,
            }
        )
    return chunks
