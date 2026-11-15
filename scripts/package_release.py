import hashlib
import json
import zipfile

from gigbid_core.config import ROOT
from scripts.repository_checks import main as check, source_files


def main():
    check()
    folder = ROOT / "dist"
    folder.mkdir(exist_ok=True)
    output = folder / "GigBid_Source.zip"
    manifest = []
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source_files()):
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith("evaluation/raw/orchestration-progress"):
                continue
            archive.write(path, "gigbid/" + relative)
            manifest.append(
                {
                    "path": relative,
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        assert all(
            not any(
                part in name.split("/")
                for part in [".env", ".private", ".venv", "node_modules", ".cache", "runtime", "raw"]
            )
            or name.startswith("gigbid/evaluation/raw/")
            for name in names
        )
        assert not any(name.endswith(".env") for name in names)
    (folder / "release_manifest.json").write_text(
        json.dumps(
            {
                "archive": output.name,
                "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "files": manifest,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Clean release written: {output.name} ({output.stat().st_size:,} bytes; {len(manifest)} files).")


if __name__ == "__main__":
    main()
