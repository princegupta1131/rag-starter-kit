"""
STEP 2 — CAPTION: describe images so they become searchable text.

Text can't be pulled out of a diagram or photo, so we ask a Gemini vision model
to describe it. The description is then chunked and embedded like any other text.

Files that already produced text in step 1 pass through unchanged.

Extend: also caption images embedded inside PDFs / DOCX, or scanned PDF pages.
"""
from pathlib import Path

from app.ingestion_service.steps.step1_extract import IMAGE_TYPES
from app.shared import gemini

CAPTION_INSTRUCTION = (
    "Describe this image for a search index. Transcribe any visible text exactly, "
    "then explain what the image shows (diagram steps, labels, chart values, people, objects). "
    "Plain text only."
)


def caption(filename: str, data: bytes, sections: list[dict]) -> tuple[list[dict], bool]:
    """Returns (sections, captioned?)."""
    mime_type = IMAGE_TYPES.get(Path(filename).suffix.lower())
    if not mime_type:
        return sections, False
    description = gemini.describe_image(data, mime_type, CAPTION_INSTRUCTION)
    return [{"text": description, "page": None}], True
