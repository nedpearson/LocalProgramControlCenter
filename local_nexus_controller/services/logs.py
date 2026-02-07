from __future__ import annotations

from pathlib import Path


def tail_text_file(path: Path, max_lines: int = 200) -> str:
    """
    Efficient-ish tail for small/medium local log files.
    For very large files, we still keep memory bounded by reading from the end.
    """

    if not path.exists():
        return ""

    # Read from end in chunks until we have enough newlines.
    chunk_size = 8192
    data = b""
    with path.open("rb") as f:
        f.seek(0, 2)
        file_size = f.tell()
        pos = file_size
        newlines = 0
        while pos > 0 and newlines <= max_lines:
            step = min(chunk_size, pos)
            pos -= step
            f.seek(pos)
            chunk = f.read(step)
            data = chunk + data
            newlines = data.count(b"\n")

    text = data.decode(errors="replace")
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])
