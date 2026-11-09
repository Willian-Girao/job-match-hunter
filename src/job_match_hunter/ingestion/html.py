import re
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


def html_to_string(url: str, timeout: int = 5) -> str:
    """Extract HTML text, separating headings and paragraphs with blank lines."""

    request = Request(
        url,
        headers={
            "User-Agent": "JobMatchHunter/0.1 (mailto:wsoaresgirao@gmail.com)"
        },
    )

    with urlopen(request, timeout=timeout) as response:
        html = response.read()

    soup = BeautifulSoup(html, features="html.parser")

    # Remove common non-content elements.
    for element in soup([
        "script", "style", "nav", "footer", "aside",
        "noscript", "iframe", "form", "button",
        "input", "select", "textarea", "svg", "canvas",
    ]):
        element.decompose()

    # Normalize whitespace from the HTML source before adding formatting.
    for text_node in list(soup.find_all(string=True)):
        text_node.replace_with(re.sub(r"\s+", " ", str(text_node)))

    # Separate block elements with blank lines.
    block_tags = [
        "div", "p", "h1", "h2", "h3", "h4", "h5", "h6",
        "section", "article", "header", "footer", "blockquote",
    ]

    for element in soup.find_all(block_tags):
        element.insert_before("\n\n")
        element.insert_after("\n\n")

    for element in soup.find_all("br"):
        element.replace_with("\n")

    for element in soup.find_all("li"):
        element.insert_before("\n")
        element.insert_after("\n")

    text = soup.get_text()

    # Trim each line and collapse excess blank lines.
    text = "\n".join(line.strip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if not text:
        raise ValueError("No text could be extracted from the URL.")

    return text