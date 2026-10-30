"""
STEP 2 — CAPTION: turn images and videos into searchable text with the model.
  * image -> a description, with any visible text transcribed
  * video -> the spoken words with [mm:ss] timestamps, then the on-screen text and scenes
Files that produced text in step 1 pass through unchanged.

Extend: also caption images inside PDFs / DOCX, scanned PDF pages, or audio files.
"""
from pathlib import Path

from app.ingestion_service.steps.step1_extract import IMAGE_TYPES, VIDEO_TYPES
from app.providers import get_chat_model

CAPTION_INSTRUCTION = (
    "Describe this image for a search index. Transcribe any visible text exactly, "
    "then explain what the image shows (diagram steps, labels, chart values, people, objects). "
    "Plain text only."
)
VIDEO_INSTRUCTION = (
    "Make this video searchable. First transcribe everything that is said, word for word, in the language "
    "it is spoken in, starting each paragraph with a [mm:ss] timestamp. Then add a section 'On screen:' that "
    "lists the important on-screen text, slides and scenes, each with a [mm:ss] timestamp. Plain text only."
)


def caption(filename: str, data: bytes, sections: list[dict]) -> tuple[list[dict], str | None]:
    """Returns (sections, what was described: "image", "video" or None)."""
    ext = Path(filename).suffix.lower()
    if ext in IMAGE_TYPES:
        description = get_chat_model().describe_image(data, IMAGE_TYPES[ext], CAPTION_INSTRUCTION)
        return [{"text": description, "page": None}], "image"
    if ext in VIDEO_TYPES:
        transcript = get_chat_model().describe_video(data, VIDEO_TYPES[ext], VIDEO_INSTRUCTION)
        return [{"text": transcript, "page": None}], "video"
    return sections, None
