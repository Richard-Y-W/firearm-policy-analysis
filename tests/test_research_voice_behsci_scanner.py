import importlib.util
from pathlib import Path


def test_top_cited_voice_scanner_includes_behavioral_science_domain():
    scanner_path = Path("/Users/byungkim/docs/research_voice_corpus/scan_top_cited_voice_corpus.py")
    spec = importlib.util.spec_from_file_location("scan_top_cited_voice_corpus", scanner_path)
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)

    domains = dict(scanner.DOMAINS)

    assert "behavioral_science_policy" in domains
    assert any("behavioral" in query.lower() for query in domains["behavioral_science_policy"])


def test_top_cited_voice_scanner_can_filter_to_behavioral_science(monkeypatch):
    scanner_path = Path("/Users/byungkim/docs/research_voice_corpus/scan_top_cited_voice_corpus.py")
    spec = importlib.util.spec_from_file_location("scan_top_cited_voice_corpus", scanner_path)
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)

    seen_domains = []

    def fake_search(query, limit, min_citations, token=None):
        seen_domains.append(query)
        return {"data": []}

    monkeypatch.setattr(scanner, "s2_search", fake_search)
    scanner.collect_candidates(
        per_query=1,
        min_citations=0,
        domain_filter={"behavioral_science_policy"},
    )

    assert seen_domains
    assert all("behavioral" in query.lower() or "behavioural" in query.lower() or "public health" in query.lower() or "natural experiment" in query.lower() or "field experiment" in query.lower() or "randomized trial" in query.lower() or "quasi-experimental" in query.lower() for query in seen_domains)


def test_top_cited_voice_scanner_keeps_arxiv_default_but_allows_open_access_pdf_urls():
    scanner_path = Path("/Users/byungkim/docs/research_voice_corpus/scan_top_cited_voice_corpus.py")
    spec = importlib.util.spec_from_file_location("scan_top_cited_voice_corpus", scanner_path)
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)

    pdf_url = "https://example.org/open-paper.pdf"

    assert scanner.normalize_pdf_url(pdf_url, {}, "arxiv") == ""
    assert scanner.normalize_pdf_url(pdf_url, {}, "open-access") == pdf_url
    assert scanner.is_allowed_pdf_url(pdf_url, "open-access")
