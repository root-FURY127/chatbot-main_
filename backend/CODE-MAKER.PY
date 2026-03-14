#!/usr/bin/env python3

import os
from pathlib import Path

# --------------------------------------
# HARDCODED FOLDER PATH
# --------------------------------------
HARDCODED_FOLDER = r"C:\\BYTECAMP\\backend"

# Output file name
OUTPUT_FILE = "privacyGuardian-BACKEND.txt"

# Max file size (0 = no limit)
MAX_SIZE = 0

# Folders to exclude
EXCLUDE_FOLDERS = {'venv', '__pycache__', '.git', '.idea', '.vscode'}

# File extensions to exclude
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe'}

# --------------------------------------


def is_binary_file(path, blocksize=1024):
    """Detect binary files safely."""
    try:
        with open(path, "rb") as f:
            block = f.read(blocksize)
            if not block:
                return False
            if b"\x00" in block:
                return True
            text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
            nontext = sum(1 for b in block if b not in text_chars)
            return (nontext / max(1, len(block))) > 0.30
    except Exception:
        return True


def build_tree(root: Path):
    """Build a clean folder tree view."""
    lines = []
    root = root.resolve()

    def _walk(dir_path: Path, prefix=""):
        entries = []
        for entry in dir_path.iterdir():
            if entry.is_dir() and entry.name in EXCLUDE_FOLDERS:
                continue
            entries.append(entry)

        entries.sort(key=lambda p: (p.is_file(), p.name.lower()))

        for i, entry in enumerate(entries):
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")

            if entry.is_dir():
                extension = "    " if i == len(entries) - 1 else "│   "
                _walk(entry, prefix + extension)

    lines.append(root.name)
    _walk(root)
    return lines


def escape_triple_backticks(text: str):
    """Prevent markdown code block breaks."""
    return text.replace("```", "`\u200b``")


def dump_folder(root_path: str, out_file: str, max_size: int):
    root = Path(root_path)

    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Error: '{root_path}' is not a valid directory.")

    out_path = Path(out_file)

    with out_path.open("w", encoding="utf-8") as out:

        # Header
        out.write(f"# Folder dump for: {root.resolve()}\n\n")

        # Folder structure
        out.write("## Folder structure\n\n")
        for line in build_tree(root):
            out.write(line + "\n")

        out.write("\n---\n\n")
        out.write("## Files and contents\n\n")

        # Walk files
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_FOLDERS]

            rel_dir = os.path.relpath(dirpath, root)

            for fname in sorted(filenames):
                if any(fname.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    continue

                file_path = Path(dirpath) / fname
                rel_path = fname if rel_dir == "." else os.path.join(rel_dir, fname)

                out.write(f"### {rel_path}\n\n")

                try:
                    size = file_path.stat().st_size
                except Exception as e:
                    out.write(f"_Could not read file info: {e}_\n\n")
                    continue

                if max_size and size > max_size:
                    out.write(f"_Skipped (size {size} bytes exceeds limit)_\n\n")
                    continue

                if is_binary_file(file_path):
                    out.write(f"_Skipped binary file (size {size} bytes)_\n\n")
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    out.write(f"_Could not read file: {e}_\n\n")
                    continue

                content = escape_triple_backticks(content)

                lang = file_path.suffix.lstrip(".").lower()

                out.write(f"```{lang}\n")
                out.write(content)
                if not content.endswith("\n"):
                    out.write("\n")
                out.write("```\n\n")

    print(f"✅ Done. Output written to: {out_path.resolve()}")


if __name__ == "__main__":
    dump_folder(HARDCODED_FOLDER, OUTPUT_FILE, MAX_SIZE)