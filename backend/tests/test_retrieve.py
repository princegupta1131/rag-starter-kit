from app.retrieval_service.steps.step5_retrieve import fuse, keyword_terms, select_top


def row(chunk_id, similarity):
    return (chunk_id, f"doc{chunk_id}", f"text {chunk_id}", None, "file.md", similarity)


def test_fuse_ranks_chunks_found_by_both_searches_first():
    vector = [row(1, 0.9), row(2, 0.8), row(3, 0.7)]
    keyword = [row(3, 0.7), row(4, 0.4)]
    ranked = fuse([("vector", vector), ("keyword", keyword)])
    assert ranked[0]["chunk_id"] == 3
    assert ranked[0]["found_by"] == ["vector", "keyword"]
    assert {h["chunk_id"] for h in ranked} == {1, 2, 3, 4}


def test_fuse_with_no_keyword_hits_keeps_vector_order():
    assert [h["chunk_id"] for h in fuse([("vector", [row(1, 0.9), row(2, 0.8)]), ("keyword", [])])] == [1, 2]


def test_fuse_two_query_vectors_keeps_best_similarity_and_one_label():
    rewritten = [row(1, 0.55), row(2, 0.50)]
    original = [row(2, 0.70), row(1, 0.52)]
    ranked = {h["chunk_id"]: h for h in fuse([("vector", rewritten), ("vector", original)])}
    assert ranked[2]["similarity"] == 0.70 and ranked[1]["similarity"] == 0.55
    assert ranked[1]["found_by"] == ["vector"]


def test_keyword_terms_are_unique_safe_words():
    assert keyword_terms("Leave? leave & 'carry'-over!") == "leave | carry | over"
    assert keyword_terms("a ? !") == ""


def test_keyword_terms_keep_non_latin_words_whole():
    assert keyword_terms("छुट्टी कितने दिन की मिलती है?") == "छुट्टी | कितने | दिन | की | मिलती | है"
    assert keyword_terms("café: naïve—test (2FA)") == "café | naïve | test | 2fa"


def test_select_top_never_drops_the_closest_meaning_matches():
    scores = [("a", 0.55), ("b", 0.54), ("c", 0.53), ("best", 0.66), ("next", 0.64)]
    noisy = [{"similarity": s, "name": n} for n, s in scores]
    kept = [h["name"] for h in select_top(noisy, 3)]
    assert kept == ["a", "best", "next"]  # fusion order kept; the two best by meaning forced in
