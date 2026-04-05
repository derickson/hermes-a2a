import mimetypes
import os
import re

from a2a.types import FilePart, FileWithUri, Part

# Extensions considered "media files" worth surfacing as FileParts
_EXTS = "jpg|jpeg|png|gif|webp|mp3|wav|ogg|mp4|pdf"
FILE_PATH_RE = re.compile(
    r"(/(?:[^\s\"'<>\\])+\.(?:" + _EXTS + r"))",
    re.IGNORECASE,
)


def detect_file_paths(text: str) -> list[str]:
    """Return deduplicated list of file paths found in *text* that exist on disk."""
    seen: set[str] = set()
    result: list[str] = []
    for match in FILE_PATH_RE.finditer(text):
        path = match.group(1)
        if path not in seen and os.path.isfile(path):
            seen.add(path)
            result.append(path)
    return result


def get_mime_type(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def build_file_part(path: str, public_url: str) -> Part:
    uri = f"{public_url.rstrip('/')}/files{path}"
    return Part(
        root=FilePart(
            kind="file",
            file=FileWithUri(
                uri=uri,
                mimeType=get_mime_type(path),
                name=os.path.basename(path),
            ),
        )
    )


def replace_file_paths(text: str, paths: list[str]) -> str:
    """Replace each file path in *text* with an inline attachment reference."""
    for path in paths:
        name = os.path.basename(path)
        text = text.replace(path, f"*see attachment for {name}*")
    return text
