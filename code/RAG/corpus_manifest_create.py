from pathlib import Path
import hashlib
import json

BASE_DIR = Path(__file__).resolve().parent
CORPUS_DIR = BASE_DIR / "corpus"
OUTPUT_PATH = BASE_DIR / "CORPUS_MANIFEST.json"

files = []

for path in sorted(CORPUS_DIR.rglob("*")):
    if path.is_file():
        data = path.read_bytes()
        file_hash = hashlib.sha256(data).hexdigest()

        # Create CORPUS_MANIFEST.json with each local filename, byte size, and SHA-256 hash
        files.append({
            "filename": str(path.relative_to(CORPUS_DIR)),
            "byte_size": len(data),
            "sha256": file_hash
        })

manifest = {
    "files": files
}

OUTPUT_PATH.write_text(
    json.dumps(manifest, indent=2),
    encoding="utf-8"
)

print(f"Manifest created for {len(files)} files.")
print(f"Saved to: {OUTPUT_PATH}")