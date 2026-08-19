import requests

from bs4 import BeautifulSoup
from urllib.parse import urlparse


# =====================================================
# Configuration
# =====================================================

DEFAULT_TIMEOUT = 20

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/142.0 Safari/537.36"
)


# =====================================================
# URL Validation
# =====================================================

def is_valid_url(url: str) -> bool:

    if not url:
        return False

    try:

        parsed = urlparse(
            url.strip()
        )

        return (
            parsed.scheme in {
                "http",
                "https"
            }
            and bool(parsed.netloc)
        )

    except Exception:

        return False


# =====================================================
# HTML Text Extraction
# =====================================================

def extract_html_text(html: str) -> str:

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # -------------------------------------------------
    # Remove non-content elements
    # -------------------------------------------------

    for tag in soup.find_all(
        [
            "script",
            "style",
            "noscript",
            "nav",
            "header",
            "footer",
            "aside",
            "form",
            "iframe",
            "svg",
        ]
    ):

        tag.decompose()

    # -------------------------------------------------
    # Extract text
    # -------------------------------------------------

    text = soup.get_text(
        separator="\n"
    )

    # -------------------------------------------------
    # Clean lines
    # -------------------------------------------------

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        lines.append(
            line
        )

    # -------------------------------------------------
    # Remove excessive duplicate lines
    # -------------------------------------------------

    cleaned_lines = []

    previous = None

    for line in lines:

        if line == previous:
            continue

        cleaned_lines.append(
            line
        )

        previous = line

    return "\n".join(
        cleaned_lines
    )


# =====================================================
# Crawl URL
# =====================================================

def crawl_url(
    url: str,
    timeout: int = DEFAULT_TIMEOUT
):

    print(
        f"\n[Crawler] Fetching: {url}"
    )

    # -------------------------------------------------
    # Validate URL
    # -------------------------------------------------

    if not is_valid_url(url):

        raise ValueError(
            f"Invalid URL: {url}"
        )

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "image/avif,"
            "image/webp,"
            "*/*;q=0.8"
        ),
        "Accept-Language": (
            "en-US,en;q=0.9"
        ),
    }

    try:

        # -------------------------------------------------
        # Request page
        # -------------------------------------------------

        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True
        )

    except requests.exceptions.Timeout:

        raise RuntimeError(
            f"Request timed out: {url}"
        )

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            f"Connection failed: {url}"
        )

    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"Request failed: {e}"
        )

    # -------------------------------------------------
    # HTTP status
    # -------------------------------------------------

    if response.status_code >= 400:

        raise RuntimeError(
            f"HTTP {response.status_code}: {url}"
        )

    # -------------------------------------------------
    # Content type
    # -------------------------------------------------

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    print(
        f"[Crawler] Status: "
        f"{response.status_code}"
    )

    print(
        f"[Crawler] Content-Type: "
        f"{content_type}"
    )

    # -------------------------------------------------
    # Handle HTML
    # -------------------------------------------------

    if (
        "text/html" in content_type
        or "application/xhtml+xml" in content_type
    ):

        text = extract_html_text(
            response.text
        )

    # -------------------------------------------------
    # Handle plain text
    # -------------------------------------------------

    elif "text/plain" in content_type:

        text = response.text.strip()

    # -------------------------------------------------
    # Unsupported formats
    # -------------------------------------------------

    else:

        print(
            "[Crawler] Unsupported content type."
        )

        return ""

    # =================================================
    # Content validation
    # =================================================

    if not text:

        print(
            "[Crawler] No text extracted."
        )

        return ""

    print(
        f"[Crawler] Extracted "
        f"{len(text)} characters."
    )

    return text