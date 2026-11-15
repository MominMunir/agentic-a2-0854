"""Build the final submission archive from required source and evidence only."""

import hashlib
import json
import subprocess
import zipfile

from dotenv import dotenv_values
from pypdf import PdfReader

from gigbid_core.config import ROOT
from scripts.repository_checks import main as check, source_files

DOCUMENTS = {
    "AI_USAGE.md", "ARCHITECTURE.md", "DATA_CARD.md", "TOOLS.md", "RUNBOOK.md",
    "FREE_DEPLOYMENT.md", "DEPLOYMENT_STATUS.md", "EXTENSION.md", "RnD_Report.md",
    "Technical_Writeup.md", "Resume_Bullets.md", "Demo_Script.md", "FINAL_STATUS.md",
    "RESULTS.md", "IMPLEMENTATION_PLAN.md", "openapi.json",
}
ROOT_FILES = {"README.md", "Makefile", "pyproject.toml", "uv.lock", ".env.example",
              ".gitignore", ".gitattributes", ".dockerignore", "compose.yaml",
              "render.yaml", "LICENSE", "conftest.py"}
DIRECTORIES = {".github", "agent", "apps", "gigbid_core", "mcp_servers", "rag",
               "worker", "simulator", "gigsim", "data", "evals", "evaluation",
               "infra", "tests", "scripts"}


def required(path):
    relative = path.relative_to(ROOT)
    parts = relative.parts
    if path.name.startswith("~$") or path.suffix in {".tsbuildinfo", ".log", ".pyc"}:
        return False
    if relative.as_posix().startswith("evaluation/raw/orchestration-progress"):
        return False
    if parts[:2] == ("evaluation", "annotations") and path.suffix != ".md":
        return False
    if parts[0] == "docs":
        return len(parts) == 2 and path.name in DOCUMENTS or parts[1] in {"adr", "graphs", "images", "traces"}
    return parts[0] in DIRECTORIES or len(parts) == 1 and path.name in ROOT_FILES


def private_values():
    values = []
    configurations = [dict(dotenv_values(ROOT / ".env"))]
    for name in ["cloud-deployment.json", "registration-check.json", "demo-rehearsal.json"]:
        path = ROOT / ".private" / name
        if path.exists():
            configurations.append(json.loads(path.read_text(encoding="utf-8")))
    for cfg in configurations:
        for key, value in cfg.items():
            if any(part in key.lower() for part in ["password", "api_key", "secret", "encryption_key", "database_url", "checkpoint_url"]):
                if value and len(str(value)) >= 12 and not str(value).startswith("sqlite"):
                    values.append(str(value).encode())
    return values


def main():
    check()
    report = ROOT / "output/pdf/RnD_Report.pdf"
    reader = PdfReader(report)
    assert len(reader.pages) <= 10
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert all(value in text for value in ["Muhammad Momin Munir", "22I-0854", "Compiled bid", "Compiled conversation"])
    assert chr(8212) not in text
    publication = json.loads((ROOT / "evals/results/article_publication.json").read_text())
    assert publication["passed"], "Verify public article publication before sealing the archive"
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    files = [("gigbid/" + p.relative_to(ROOT).as_posix(), p.read_bytes()) for p in sorted(source_files()) if required(p)]
    files.append(("gigbid/output/pdf/RnD_Report.pdf", report.read_bytes()))
    links = """Muhammad Momin Munir
Roll Number: 22I-0854
Agentic AI Assignment-02

Public app: https://gigbid-wr80.onrender.com
Public source: https://github.com/MominMunir/agentic-a2-0854
Technical article: https://gigbid-wr80.onrender.com/blog/gigbid
Portfolio MCP: https://gigbid-wr80.onrender.com/portfolio/mcp
MCP installation: https://github.com/MominMunir/agentic-a2-0854/blob/main/mcp_servers/portfolio/README.md

Report in this archive: gigbid/output/pdf/RnD_Report.pdf
Demo video: not included; provide its link separately in Classroom.
Reviewer login: share privately in Classroom; credentials are excluded here.

Workflow traces:
https://github.com/MominMunir/agentic-a2-0854/blob/main/docs/traces/scam-skip.json
https://github.com/MominMunir/agentic-a2-0854/blob/main/docs/traces/approved-proposal.json
https://github.com/MominMunir/agentic-a2-0854/blob/main/docs/traces/critic-loop.json

Evaluation scope and unfinished external requirements: gigbid/docs/FINAL_STATUS.md
"""
    files.append(("SUBMISSION_LINKS.txt", links.encode()))
    secrets = private_values()
    for name, content in files:
        assert not any(value in content for value in secrets), "Private credential detected in " + name
    manifest = dict(source_git_revision=revision, report_pages=len(reader.pages), files=[
        dict(path=name, bytes=len(content), sha256=hashlib.sha256(content).hexdigest()) for name, content in files
    ])
    files.append(("SUBMISSION_MANIFEST.json", json.dumps(manifest, indent=2).encode()))
    output = ROOT / "dist/22I-0854_Agentic_AI_Assignment-02_Final.zip"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in files:
            archive.writestr(name, content)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(set(archive.namelist()))
        for row in manifest["files"]:
            assert hashlib.sha256(archive.read(row["path"])).hexdigest() == row["sha256"]
        assert "gigbid/.env.example" in archive.namelist()
        assert all("gigbid/" + name in archive.namelist() for name in ROOT_FILES)
        assert "gigbid/infra/docker-compose.yml" in archive.namelist()
        assert not any("/.private/" in name or name.endswith(".docx") or name.endswith(".tsbuildinfo") for name in archive.namelist())
        assert not any(name.startswith("gigbid/evaluation/annotations/") and name.endswith(".csv") for name in archive.namelist())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(digest + "  " + output.name + "\n")
    print(f"Final submission verified: {output.name}; {len(files)} files; {output.stat().st_size:,} bytes.")


if __name__ == "__main__":
    main()
