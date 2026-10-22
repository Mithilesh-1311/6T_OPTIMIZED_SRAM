"""Package accepted exports privately; provision only manifest-verified numerical files."""
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 256 * 1024 * 1024


def provision(payload, digest, destination, records):
    if hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError("Evidence archive SHA256 mismatch")
    expected = {r["file"]: r["sha256"] for r in records}
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("Archive must contain exactly the accepted manifest filenames")
        if any(Path(n).name != n or "/" in n or "\\" in n for n in names):
            raise ValueError("Unsafe evidence path")
        if sum(i.file_size for i in archive.infolist()) > 1024*1024*1024:
            raise ValueError("Expanded evidence exceeds 1 GiB")
        # Verify everything before creating any file; never overwrite an existing export.
        for name in names:
            if hashlib.sha256(archive.read(name)).hexdigest() != expected[name]:
                raise ValueError(f"Export hash mismatch: {name}")
            path = destination/name
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != expected[name]:
                raise ValueError(f"Existing export differs; preserved unchanged: {name}")
        destination.mkdir(parents=True, exist_ok=True)
        for name in names:
            path = destination/name
            if not path.exists():
                with path.open("xb") as out:
                    out.write(archive.read(name))


def main():
    records = json.loads((ROOT/"data/derived/experiments.json").read_text(encoding="utf-8"))
    if sys.argv[1:] == ["pack"]:
        path = ROOT/"deployment/sams-evidence.zip"
        path.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for record in records:
                source = ROOT/"CSVs"/record["file"]
                if hashlib.sha256(source.read_bytes()).hexdigest() != record["sha256"]:
                    raise ValueError(f"Original changed: {record['file']}")
                archive.write(source, record["file"])
        print(f"Private archive: {path.name}; SHA256 {hashlib.sha256(path.read_bytes()).hexdigest()}")
    elif sys.argv[1:] == ["provision"]:
        url = os.environ.get("SAMS_EVIDENCE_URL", "")
        digest = os.environ.get("SAMS_EVIDENCE_SHA256", "")
        if not url.startswith("https://") or len(digest) != 64:
            raise ValueError("Set private HTTPS SAMS_EVIDENCE_URL and SAMS_EVIDENCE_SHA256")
        with urllib.request.urlopen(url, timeout=120) as response:
            if not response.url.startswith("https://"):
                raise ValueError("Evidence download redirected away from HTTPS")
            payload = response.read(LIMIT + 1)
        if len(payload) > LIMIT:
            raise ValueError("Evidence archive exceeds 256 MiB")
        provision(payload, digest, ROOT/"CSVs", records)
        print(f"Verified {len(records)} private waveform exports")
    else:
        raise ValueError("Usage: python scripts/evidence_bundle.py pack|provision")


if __name__ == "__main__":
    main()
