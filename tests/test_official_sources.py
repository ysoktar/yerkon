"""Official/primary source list: every entry states its verification status."""
from locbench3d.references.official_sources import OFFICIAL_SOURCES


def test_every_source_has_a_url_and_nonempty_scope():
    for src in OFFICIAL_SOURCES:
        assert src.evidence.source_url.startswith("https://")
        assert src.evidence.source_scope.strip()


def test_verification_status_is_explicit_per_source():
    unverified = [s for s in OFFICIAL_SOURCES if not s.verified_this_session]
    verified = [s for s in OFFICIAL_SOURCES if s.verified_this_session]
    assert unverified  # most sources were not fetched live this session
    assert verified  # a couple were confirmed via search snippet
    for src in unverified:
        assert "not freshly fetched" in src.evidence.source_scope.lower()


def test_topics_are_unique():
    topics = [s.topic for s in OFFICIAL_SOURCES]
    assert len(topics) == len(set(topics))
