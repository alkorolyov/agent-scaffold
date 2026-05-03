#!/usr/bin/env python3
"""Fetch research papers by DOI using Sci-Hub or CrossRef API."""

import sys
import json
import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("Error: requests library required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from curl_cffi import requests as cffi_requests
    _CFFI_AVAILABLE = True
except ImportError:
    _CFFI_AVAILABLE = False


def create_session():
    """Create requests session with retry strategy."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    })
    return session


def normalize_doi(doi: str) -> str:
    """Extract DOI from various formats."""
    # Remove common prefixes
    for prefix in ["https://doi.org/", "http://doi.org/", "https://", "http://", "doi.org/", "doi:"]:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.strip()


def fetch_from_scihub(doi: str) -> Optional[bytes]:
    """Attempt to download PDF from Sci-Hub."""
    session = create_session()
    sci_hub_urls = [
        "https://sci-hub.pl",
        "https://sci-hub.se",
        "https://sci-hub.st",
    ]

    for base_url in sci_hub_urls:
        try:
            url = f"{base_url}/{doi}"
            resp = session.get(url, timeout=10)
            resp.raise_for_status()

            # Check if we got a PDF or error page
            if resp.headers.get("content-type", "").startswith("application/pdf"):
                return resp.content

            # Try to extract PDF URL from HTML
            if "pdf" in resp.text.lower():
                # Look for iframe, embed, or href pointing to PDF
                pdf_match = re.search(r'<iframe[^>]*src\s*=\s*["\']([^"\']*)["\']', resp.text)
                if not pdf_match:
                    pdf_match = re.search(r'src\s*=\s*["\']([^"\']*\.pdf[^"\']*)["\']', resp.text)
                if not pdf_match:
                    pdf_match = re.search(r'href\s*=\s*["\']([^"\']*\.pdf[^"\']*)["\']', resp.text)

                if pdf_match:
                    pdf_url = pdf_match.group(1)
                    if not pdf_url.startswith("http"):
                        pdf_url = base_url + pdf_url
                    pdf_resp = session.get(pdf_url, timeout=10)
                    if pdf_resp.headers.get("content-type", "").startswith("application/pdf"):
                        return pdf_resp.content
        except Exception:
            continue

    return None


def fetch_from_openalex(doi: str, session=None) -> Optional[bytes]:
    """Try to download a PDF via OpenAlex open-access URLs.

    Uses curl-cffi with Chrome TLS impersonation when available (bypasses Cloudflare/bot
    detection on publisher sites). Falls back to plain requests otherwise.
    """
    if session is None:
        session = create_session()
    try:
        url = f"https://api.openalex.org/works/doi:{doi}"
        resp = session.get(url, timeout=10, headers={"User-Agent": "fetch_paper/1.0 (mailto:fetch@example.com)"})
        if resp.status_code != 200:
            return None
        work = resp.json()

        # Collect all candidate PDF URLs (best_oa_location first, then others)
        pdf_urls = []
        best = work.get("best_oa_location") or {}
        if best.get("pdf_url"):
            pdf_urls.append(best["pdf_url"])
        oa_url = (work.get("open_access") or {}).get("oa_url")
        if oa_url and oa_url not in pdf_urls:
            pdf_urls.append(oa_url)
        for loc in work.get("locations", []):
            u = loc.get("pdf_url")
            if u and u not in pdf_urls:
                pdf_urls.append(u)

        if not pdf_urls:
            return None

        # Try with curl-cffi (Chrome TLS fingerprint) first, then plain requests
        download_fns = []
        if _CFFI_AVAILABLE:
            def _cffi_get(pdf_url):
                s = cffi_requests.Session(impersonate="chrome124")
                r = s.get(pdf_url, timeout=30, allow_redirects=True)
                return r.content if r.status_code == 200 else None
            download_fns.append(_cffi_get)

        def _plain_get(pdf_url):
            r = session.get(pdf_url, timeout=15, allow_redirects=True)
            return r.content if r.ok else None
        download_fns.append(_plain_get)

        for pdf_url in pdf_urls:
            for download_fn in download_fns:
                try:
                    content = download_fn(pdf_url)
                    if content and content[:4] == b"%PDF":
                        return content
                except Exception:
                    continue
    except Exception:
        pass
    return None


def fetch_from_europepmc(doi: str) -> dict:
    """Fetch abstract and attempt PDF download via Europe PMC search API.

    Europe PMC's ?pdf=render endpoint serves real PDFs without bot-challenge
    pages, making it the reliable fallback when PMC direct URLs return PoW HTML.
    """
    try:
        session = create_session()
        r = session.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": f'DOI:"{doi}"', "format": "json", "resultType": "core"},
            timeout=10,
        )
        results = r.json().get("resultList", {}).get("result", [])
        if not results:
            return {}
        hit = results[0]
        abstract = (hit.get("abstractText") or "").strip()

        # Collect OA PDF URLs from fullTextUrlList (Europe PMC ?pdf=render works
        # without PoW challenges that block direct PMC downloads)
        pdf_urls = []
        for entry in hit.get("fullTextUrlList", {}).get("fullTextUrl", []):
            if (entry.get("availabilityCode") == "OA"
                    and entry.get("documentStyle") == "pdf"):
                pdf_urls.append(entry["url"])

        meta = {
            "title": hit.get("title", ""),
            "authors": [a.get("fullName", "") for a in hit.get("authorList", {}).get("author", [])][:10],
            "year": hit.get("pubYear"),
            "abstract": abstract,
            "doi": doi,
            "source": "europepmc",
            "_pdf_urls": pdf_urls,  # passed through to fetch_paper() for PDF attempt
        }
        return meta if abstract or pdf_urls else {}
    except Exception:
        return {}


def fetch_from_crossref(doi: str) -> dict:
    """Fetch metadata and abstract from CrossRef API."""
    session = create_session()
    url = f"https://api.crossref.org/works/{quote(doi)}"

    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        work = data.get("message", {})
        return {
            "title": work.get("title", [""])[0] if isinstance(work.get("title"), list) else work.get("title", ""),
            "authors": [
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in work.get("author", [])
            ][:10],
            "year": work.get("published-online", {}).get("date-parts", [[None]])[0][0] or work.get("issued", {}).get("date-parts", [[None]])[0][0],
            "abstract": work.get("abstract", ""),
            "doi": doi,
        }
    except Exception as e:
        return {"error": str(e), "doi": doi}


def save_pdf(content: bytes, output_path: Path) -> dict:
    """Save PDF, rejecting non-PDF bytes (e.g. Cloudflare block pages)."""
    if not content.startswith(b"%PDF"):
        return {
            "success": False,
            "error": f"content is not a valid PDF — got {len(content)} bytes starting with {content[:20]!r}",
        }
    # Use string concatenation instead of with_suffix() — slugs like "acs.jcim.3c01661"
    # have dots that with_suffix() misreads as extensions, truncating the filename.
    if not str(output_path).endswith(".pdf"):
        output_path = Path(str(output_path) + ".pdf")
    output_path.write_bytes(content)
    return {
        "success": True,
        "file_path": str(output_path),
        "file_type": "pdf",
        "size_mb": len(content) / (1024 * 1024),
    }


def save_abstract_md(metadata: dict, output_path: Path) -> dict:
    """Save abstract as markdown and return metadata."""
    output_path = Path(str(output_path) + "_abstract.md")

    content = f"# {metadata.get('title', 'Untitled')}\n\n"

    if metadata.get("authors"):
        content += f"**Authors**: {', '.join(metadata['authors'])}\n"
    if metadata.get("year"):
        content += f"**Year**: {metadata['year']}\n"
    content += f"**DOI**: {metadata.get('doi', 'N/A')}\n\n"

    if metadata.get("abstract"):
        content += "## Abstract\n\n"
        content += metadata["abstract"].strip() + "\n\n"

    content += "---\n\n*Full PDF not available via Sci-Hub.*\n"

    output_path.write_text(content)
    return {
        "success": True,
        "file_path": str(output_path),
        "file_type": "abstract_md",
        "size_mb": len(content.encode()) / (1024 * 1024),
    }


def fetch_paper(doi: str, output_path: Optional[str] = None) -> dict:
    """
    Fetch paper by DOI (journal papers only — not arXiv).

    Strategy:
    1. Sci-Hub → full PDF saved as <output_path>.pdf
    2. PDF not available → CrossRef API → abstract saved as <output_path>_abstract.md

    If you get back file_type="abstract_md", the full PDF was not available.
    In that case, search for an arXiv preprint separately.

    Returns:
        {
            "success": bool,
            "file_path": str,
            "file_type": "pdf" | "abstract_md",
            "size_mb": float,
            "error": str  (only if success=False)
        }
    """
    doi = normalize_doi(doi)

    if not output_path:
        output_path = f"./{doi.replace('/', '_')}"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Try Sci-Hub first
    try:
        pdf_content = fetch_from_scihub(doi)
        if pdf_content:
            result = save_pdf(pdf_content, output_path)
            if result["success"]:
                return result
    except Exception:
        pass

    # Try OpenAlex open-access URLs
    try:
        pdf_content = fetch_from_openalex(doi)
        if pdf_content:
            result = save_pdf(pdf_content, output_path)
            if result["success"]:
                return result
    except Exception:
        pass

    # Try Europe PMC — also attempts PDF download via ?pdf=render (no PoW)
    try:
        metadata = fetch_from_europepmc(doi)
        if metadata:
            for pdf_url in metadata.pop("_pdf_urls", []):
                try:
                    session = create_session()
                    pdf_resp = session.get(pdf_url, timeout=30, allow_redirects=True)
                    if pdf_resp.ok and pdf_resp.content[:4] == b"%PDF":
                        result = save_pdf(pdf_resp.content, output_path)
                        if result["success"]:
                            return result
                except Exception:
                    continue
            if metadata.get("abstract"):
                return save_abstract_md(metadata, output_path)
    except Exception:
        pass

    # Fall back to CrossRef
    try:
        metadata = fetch_from_crossref(doi)
        if "error" not in metadata:
            return save_abstract_md(metadata, output_path)
        else:
            return {"success": False, "doi": doi, "error": f"CrossRef API error: {metadata['error']}"}
    except Exception as e:
        return {"success": False, "doi": doi, "error": str(e)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch research paper by DOI")
    parser.add_argument("doi", help="Paper DOI (e.g., 10.1038/...)")
    parser.add_argument("--output", help="Output path (without extension)", default=None)
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    result = fetch_paper(args.doi, args.output)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"✓ {result['file_type'].upper()}: {result['file_path']} ({result['size_mb']:.2f}MB)")
        else:
            print(f"✗ Failed: {result.get('error', 'unknown error')}")
        sys.exit(0 if result["success"] else 1)
