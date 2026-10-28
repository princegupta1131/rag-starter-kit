from app.ingestion_service.steps.step3_chunk import chunk_sections


def words(n, word="alpha"):
    return " ".join(f"{word}{i}." for i in range(n))


def test_short_text_is_one_chunk():
    chunks = chunk_sections([{"text": "One sentence. Two sentences.", "page": 3}])
    assert len(chunks) == 1
    assert chunks[0] == {"index": 0, "page": 3, "text": "One sentence. Two sentences."}


def test_long_text_splits_near_size_with_overlap():
    chunks = chunk_sections([{"text": words(500), "page": None}], size=100, overlap=20)
    assert len(chunks) > 4
    assert all(len(c["text"].split()) <= 100 for c in chunks)
    first, second = chunks[0]["text"].split(), chunks[1]["text"].split()
    assert first[-1] in second[:25]  # the next chunk starts with the tail of the previous one


def test_sentence_longer_than_chunk_is_cut_by_words():
    long_sentence = " ".join(f"w{i}" for i in range(250))
    chunks = chunk_sections([{"text": long_sentence, "page": None}], size=100, overlap=0)
    assert [len(c["text"].split()) for c in chunks] == [100, 100, 50]


def test_duplicate_chunks_are_skipped():
    sections = [{"text": "Company confidential.", "page": 1}, {"text": "company   CONFIDENTIAL.", "page": 2}]
    assert len(chunk_sections(sections)) == 1


def test_indexes_are_sequential_across_sections():
    sections = [{"text": words(150), "page": 1}, {"text": words(150, "beta"), "page": 2}]
    chunks = chunk_sections(sections, size=100, overlap=0)
    assert [c["index"] for c in chunks] == list(range(len(chunks)))
    assert {c["page"] for c in chunks} == {1, 2}
