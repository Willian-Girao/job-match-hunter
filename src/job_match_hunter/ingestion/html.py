import re
from urllib.request import Request, urlopen
import json
from bs4 import BeautifulSoup, Comment

def html_to_string(url: str, timeout: int = 30, min_len: int=500) -> str:
    """Extract HTML text, separating headings and paragraphs with blank lines.

    Args:
        url: Web address.
        timeout: Timeout in seconds for blocking network operations.
        min_len: Minimun number of characters used to flag valid text extraction.

    Returns:
        Extracted text.

    Raises:
        ValueError: No text could be extracted from the web page.
    """
    # Identify the application to websites that require a descriptive User-Agent.
    request = Request(
        url,
        headers={
            "User-Agent": "JobMatchHunter/0.1 (mailto:wsoaresgirao@gmail.com)"
        },
    )

    # Download the HTML and close the response automatically afterward.
    # This does not execute JavaScript.
    with urlopen(request, timeout=timeout) as response:
        html = response.read()

    soup = BeautifulSoup(html, features="html.parser")

    # Look for a job description embedded in JSON-LD structured data.
    # Do this before removing scripts, because JSON-LD is stored in script tags.
    for script in soup.find_all("script", type="application/ld+json"):
        data = json.loads(script.get_text())

        # JSON-LD may contain a single object or a list of objects.
        items = data if isinstance(data, list) else [data]

        for item in items:
            if item.get("@type") == "JobPosting" and item.get("description"):
                # Restrict further processing to the job description's HTML.
                soup = BeautifulSoup(item["description"], "html.parser")
                break
        else:
            # No description in this script: check the next JSON-LD script.
            continue

        # A description was found: stop searching.
        break

    # If no structured description was found, soup still contains the full page.

    # Remove HTML comments before converting text nodes to ordinary strings.
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove common interface elements and non-content sections.
    # Removing a tag also removes its contents; some sites may place useful
    # job information inside elements such as forms or sidebars.
    for element in soup([
        "script", "style", "nav", "footer", "aside",
        "noscript", "iframe", "form", "button",
        "input", "select", "textarea", "svg", "canvas",
    ]):
        element.decompose()

    # Collapse source whitespace so HTML indentation does not determine layout.
    # Materialize the text nodes before modifying the parse tree.
    for text_node in list(soup.find_all(string=True)):
        text_node.replace_with(re.sub(r"\s+", " ", str(text_node)))

    # Add blank lines around selected elements to separate text sections.
    # span is normally inline; including it may split sentences across lines.
    block_tags = [
        "div", "p", "h1", "h2", "h3", "h4", "h5", "h6",
        "section", "article", "header", "footer", "blockquote", "span",
    ]

    for element in soup.find_all(block_tags):
        element.insert_before("\n\n")
        element.insert_after("\n\n")

    # Convert explicit HTML line breaks into blank lines.
    for element in soup.find_all("br"):
        element.replace_with("\n\n")

    # Put each list item in its own text block.
    for element in soup.find_all("li"):
        element.insert_before("\n\n")
        element.insert_after("\n\n")

    # Extract text while preserving the line breaks inserted above.
    text = soup.get_text()

    # Trim lines and remove Unicode replacement characters (�).
    # Removing these characters does not recover the original missing text.
    text = "\n".join(
        line.strip().replace("\uFFFD", "")
        for line in text.splitlines()
    )

    # Collapse repeated blank lines, including those from nested elements.
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    # Reject empty results instead of returning an unusable description.
    if not text or len(text) < min_len:
        raise ValueError("No text could be extracted from the URL.")

    return text