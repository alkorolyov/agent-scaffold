"""Tests for fetch_paper.py.

Two tiers:
- **Unit tests** (default): no network. Mock Sci-Hub responses to verify URL
  resolution logic. Run with `pytest test_fetch_paper.py`.
- **Integration tests** (opt-in): hit live Sci-Hub mirrors. Marked
  `@pytest.mark.network`. Run with `pytest test_fetch_paper.py -m network`.
  These are flaky by nature (mirror availability varies).

The failing-DOI fixtures encode regressions caught while building a
clinical KB on 2026-05-09 — see the docstrings on each fixture.
"""
import sys
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fetch_paper import fetch_from_scihub, normalize_doi


# ---------------------------------------------------------------------------
# Failing-DOI regression fixtures
#
# Each entry is a DOI that *should* be fetchable through the Sci-Hub cascade
# but failed in some prior version of the script. New DOIs added here on
# every fetch failure root-caused to a tool bug — not on transient network
# failure.
# ---------------------------------------------------------------------------
FAILING_DOI_REGRESSIONS = [
    pytest.param(
        "10.1016/j.jaad.2021.02.054",
        id="vano-galvan-2021-jaad",
        marks=pytest.mark.network,
    ),
    # ^ Vano-Galvan et al. JAAD 2021. Closed-access. sci-hub.pl returns 302
    #   redirect to sci-net.xyz, which serves a SPA-style page with the PDF
    #   in an <iframe src="/storage/<hash>/...pdf">. Pre-fix, the script
    #   prepended the original `base_url` (sci-hub.pl) instead of the final
    #   redirected host (sci-net.xyz), 404'ing the PDF download.
    pytest.param(
        "10.1016/j.jaad.2024.10.057",
        id="chen-2025-jaad-letter",
        marks=pytest.mark.network,
    ),
    # ^ Chen et al. JAAD 2025. JAAD letter, same redirect chain as above.
    pytest.param(
        "10.1111/ijd.17524",
        id="sobral-2025-ijd-meta",
        marks=pytest.mark.network,
    ),
    # ^ Sobral et al. Int J Dermatol 2025. Wiley journal, same redirect.
    pytest.param(
        "10.1002/j.1552-4604.1989.tb03307.x",
        id="fleishaker-1989-jclinpharmacol",
        marks=pytest.mark.network,
    ),
    # ^ Fleishaker et al. J Clin Pharmacol 1989. Older paper but same path.
]


# ---------------------------------------------------------------------------
# Unit tests (no network, deterministic)
# ---------------------------------------------------------------------------

# Minimal HTML fixture mimicking sci-net.xyz response (the real shape after
# sci-hub.pl redirects). The PDF iframe src is a *relative* path that must
# resolve against sci-net.xyz, NOT against the original sci-hub.pl base.
SCINET_REDIRECT_HTML = """\
<!DOCTYPE html><html><body>
<div class="article">
  <div class="title">Test Article</div>
  <div class="doi"><a href="//doi.org/10.1234/example">10.1234/example</a></div>
</div>
<div class="pdf">
  <iframe src="/storage/12345/abcdef/Test-Article.pdf#view=FitH"></iframe>
</div>
</body></html>
"""

PDF_BYTES = b"%PDF-1.7\n<minimal valid PDF stub bytes>"


def _mock_session_factory(html_response_url, html_text, pdf_url, pdf_bytes):
    """Build a MagicMock session whose .get() returns:
    - For sci-hub.pl/<doi>: an HTML response with .url == html_response_url
      (simulating the sci-hub -> sci-net redirect).
    - For the resolved PDF URL: bytes starting with %PDF.
    """
    def _get(url, **kwargs):
        resp = MagicMock()
        if url.endswith(html_response_url.split("/")[-1]) or "sci-hub" in url:
            # The HTML page (after redirect)
            resp.url = html_response_url
            resp.headers = {"content-type": "text/html; charset=utf-8"}
            resp.text = html_text
            resp.content = html_text.encode()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            return resp
        if url == pdf_url:
            resp.url = pdf_url
            resp.headers = {"content-type": "application/pdf"}
            resp.content = pdf_bytes
            resp.text = ""
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            return resp
        # Unknown URL → 404-equivalent
        resp.url = url
        resp.headers = {"content-type": "text/html"}
        resp.content = b"<html>not found</html>"
        resp.text = "<html>not found</html>"
        resp.status_code = 404
        resp.raise_for_status = MagicMock(side_effect=Exception(f"404 for {url}"))
        return resp
    s = MagicMock()
    s.get.side_effect = _get
    return s


def test_relative_pdf_path_resolves_against_final_redirect_host():
    """REGRESSION — the load-bearing bug fixed on 2026-05-09.

    sci-hub.pl returned 302 -> sci-net.xyz/<doi>. The HTML had
    <iframe src="/storage/.../file.pdf">. Pre-fix, the script prepended
    base_url (sci-hub.pl). Post-fix, it must resolve against resp.url
    (sci-net.xyz) so the PDF download succeeds.
    """
    redirect_html_url = "https://sci-net.xyz/10.1234/example"
    expected_pdf_url = "https://sci-net.xyz/storage/12345/abcdef/Test-Article.pdf"
    fake_session = _mock_session_factory(
        html_response_url=redirect_html_url,
        html_text=SCINET_REDIRECT_HTML,
        pdf_url=expected_pdf_url,
        pdf_bytes=PDF_BYTES,
    )
    with patch("fetch_paper.create_session", return_value=fake_session):
        result = fetch_from_scihub("10.1234/example")
    assert result is not None, "fetch_from_scihub returned None — relative PDF path resolution likely broken"
    assert result.startswith(b"%PDF"), f"got non-PDF bytes: {result[:40]!r}"
    # Verify the script actually requested the *final-host* PDF URL,
    # not a sci-hub-prefixed one.
    requested_urls = [c.args[0] for c in fake_session.get.call_args_list]
    assert expected_pdf_url in requested_urls, (
        f"PDF was not requested at the final-host URL.\n"
        f"Expected: {expected_pdf_url}\n"
        f"Actually requested: {requested_urls}"
    )


def test_protocol_relative_url_resolved_with_https():
    """An iframe src starting with `//` should be treated as protocol-relative."""
    proto_relative_html = SCINET_REDIRECT_HTML.replace(
        'src="/storage/', 'src="//cdn.example.com/storage/'
    )
    expected_pdf_url = "https://cdn.example.com/storage/12345/abcdef/Test-Article.pdf"
    fake_session = _mock_session_factory(
        html_response_url="https://sci-net.xyz/10.1234/example",
        html_text=proto_relative_html,
        pdf_url=expected_pdf_url,
        pdf_bytes=PDF_BYTES,
    )
    with patch("fetch_paper.create_session", return_value=fake_session):
        result = fetch_from_scihub("10.1234/example")
    assert result == PDF_BYTES


def test_absolute_pdf_url_passes_through_unchanged():
    """If the iframe src is already an absolute http(s) URL, fetch it directly."""
    absolute_html = SCINET_REDIRECT_HTML.replace(
        'src="/storage/', 'src="https://other.cdn.example.com/storage/'
    )
    expected_pdf_url = "https://other.cdn.example.com/storage/12345/abcdef/Test-Article.pdf"
    fake_session = _mock_session_factory(
        html_response_url="https://sci-net.xyz/10.1234/example",
        html_text=absolute_html,
        pdf_url=expected_pdf_url,
        pdf_bytes=PDF_BYTES,
    )
    with patch("fetch_paper.create_session", return_value=fake_session):
        result = fetch_from_scihub("10.1234/example")
    assert result == PDF_BYTES


def test_pdf_detected_by_magic_bytes_when_content_type_is_wrong():
    """Some CDNs return text/html or octet-stream for PDFs. We should still
    accept the response if the bytes start with %PDF."""
    expected_pdf_url = "https://sci-net.xyz/storage/12345/abcdef/Test-Article.pdf"

    def _get(url, **kwargs):
        resp = MagicMock()
        if "sci-hub" in url:
            resp.url = "https://sci-net.xyz/10.1234/example"
            resp.headers = {"content-type": "text/html"}
            resp.text = SCINET_REDIRECT_HTML
            resp.content = SCINET_REDIRECT_HTML.encode()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            return resp
        if url == expected_pdf_url:
            resp.url = url
            resp.headers = {"content-type": "application/octet-stream"}  # wrong CT
            resp.content = PDF_BYTES  # but valid PDF magic bytes
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            return resp
        return MagicMock(status_code=404, content=b"", headers={})

    s = MagicMock()
    s.get.side_effect = _get
    with patch("fetch_paper.create_session", return_value=s):
        result = fetch_from_scihub("10.1234/example")
    assert result == PDF_BYTES, "should accept bytes starting with %PDF regardless of content-type header"


# ---------------------------------------------------------------------------
# DOI normalization
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("input_doi,expected", [
    ("10.1016/j.jaad.2021.02.054", "10.1016/j.jaad.2021.02.054"),
    ("https://doi.org/10.1016/j.jaad.2021.02.054", "10.1016/j.jaad.2021.02.054"),
    ("http://doi.org/10.1111/ced.15338", "10.1111/ced.15338"),
    ("doi:10.1023/a:1016212804288", "10.1023/a:1016212804288"),
    ("  10.1234/test  ", "10.1234/test"),
])
def test_normalize_doi(input_doi, expected):
    assert normalize_doi(input_doi) == expected


# ---------------------------------------------------------------------------
# Integration tests (network, opt-in via `pytest -m network`)
# ---------------------------------------------------------------------------

@pytest.mark.network
@pytest.mark.parametrize("doi", FAILING_DOI_REGRESSIONS)
def test_failing_doi_regressions_now_fetch(doi):
    """Each DOI here previously failed under the pre-2026-05-09 fetch_paper.py.

    With the redirect-aware fix, all should return non-None PDF bytes via
    the Sci-Hub cascade. If any of these starts failing again, look first at
    Sci-Hub mirror availability before assuming a code regression.
    """
    result = fetch_from_scihub(doi)
    assert result is not None, (
        f"DOI {doi} no longer fetches via Sci-Hub. Either: (a) all mirrors are "
        f"down (transient — re-run later), or (b) the redirect/extraction logic "
        f"has regressed (check fetch_from_scihub for a recent change)."
    )
    assert result.startswith(b"%PDF"), f"got non-PDF: {result[:40]!r}"
