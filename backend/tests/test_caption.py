from app.ingestion_service.api import _max_mb
from app.ingestion_service.steps.step2_caption import caption

TEXT = [{"text": "Leave is 24 days.", "page": None}]


def test_video_is_transcribed_with_timestamps(fake_chat):
    sections, described = caption("vhsnd.mp4", b"video-bytes", [])
    assert described == "video"
    assert sections[0]["text"].startswith("[00:05] Seema")
    mime_type, instruction = fake_chat.calls[-1]
    assert mime_type == "video/mp4" and "[mm:ss]" in instruction


def test_mov_uses_its_own_mime_type(fake_chat):
    caption("clip.MOV", b"video-bytes", [])
    assert fake_chat.calls[-1][0] == "video/mov"


def test_image_is_described():
    sections, described = caption("steps.png", b"\x89PNG", [])
    assert described == "image" and "hand washing" in sections[0]["text"]


def test_text_files_pass_through():
    assert caption("handbook.txt", b"x", TEXT) == (TEXT, None)


def test_videos_get_a_bigger_upload_limit(monkeypatch):
    from app.ingestion_service import api
    monkeypatch.setattr(api.settings, "max_upload_mb", 20)
    monkeypatch.setattr(api.settings, "max_video_mb", 200)
    assert _max_mb("talk.mp4") == 200 and _max_mb("guide.pdf") == 20
