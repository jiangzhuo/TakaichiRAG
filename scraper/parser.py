"""HTML parser for extracting content from web pages."""

import re
from typing import List, Dict, Tuple, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class HTMLParser:
    """Parser for extracting content and links from HTML."""

    def __init__(self, base_url: str):
        """
        Initialize the HTML parser.

        Args:
            base_url: The base URL for resolving relative links
        """
        self.base_url = base_url

    def extract_content(self, html: str, url: str) -> Dict:
        """
        Extract text content and metadata from HTML.

        Args:
            html: The HTML content
            url: The URL of the page

        Returns:
            Dictionary containing extracted content and metadata
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove script and style elements
        for element in soup(['script', 'style', 'noscript', 'iframe']):
            element.decompose()

        # Extract metadata
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        publish_date = self._extract_publish_date(soup)

        # Extract main content
        main_content = self._extract_main_content(soup)

        # Extract all text if main content not found
        if not main_content:
            main_content = self._extract_all_text(soup)

        # Clean the extracted text
        main_content = self._clean_text(main_content)

        # Calculate character count (suitable for Japanese/CJK languages)
        # Remove whitespace and newlines to get actual content length
        char_count = len(''.join(main_content.split())) if main_content else 0

        return {
            'url': url,
            'title': title,
            'description': description,
            'content': main_content,
            'word_count': char_count,  # Actually character count for Japanese
            'publish_date': publish_date
        }

    def extract_links(self, html: str, current_url: str) -> List[str]:
        """
        Extract all internal links from HTML.

        Args:
            html: The HTML content
            current_url: The current page URL

        Returns:
            List of absolute URLs for internal links
        """
        soup = BeautifulSoup(html, 'lxml')
        links = []

        for tag in soup.find_all('a', href=True):
            href = tag['href']

            # Skip empty links, anchors, and external links
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue

            # Convert to absolute URL
            absolute_url = urljoin(current_url, href)

            # Only include links within the same domain
            if self._is_same_domain(absolute_url, self.base_url):
                links.append(absolute_url)

        return list(set(links))  # Remove duplicates

    def extract_subpage_links(self, html: str, current_url: str, pattern: Optional[str] = None) -> List[str]:
        """
        Extract specific subpage links (e.g., for column details).

        Args:
            html: The HTML content
            current_url: The current page URL
            pattern: Optional regex pattern to filter links

        Returns:
            List of matching subpage URLs
        """
        all_links = self.extract_links(html, current_url)

        if pattern:
            # Filter links by pattern
            pattern_regex = re.compile(pattern)
            return [link for link in all_links if pattern_regex.search(link)]

        return all_links

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try multiple methods to get title
        title_tag = soup.find('title')
        if title_tag:
            return self._clean_text(title_tag.get_text())

        h1_tag = soup.find('h1')
        if h1_tag:
            return self._clean_text(h1_tag.get_text())

        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description from meta tags."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return self._clean_text(meta_desc['content'])

        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return self._clean_text(og_desc['content'])

        return ""

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract article publish date from time tag.

        Args:
            soup: BeautifulSoup object

        Returns:
            Publish date in YYYY-MM-DD format or None
        """
        # Try to find time tag in article title area
        # CSS selector: #contents > div.container > div > article > div.articleTit > p > time
        time_tag = soup.select_one('#contents div.container div article div.articleTit p time')

        if time_tag:
            # Try to get datetime attribute first
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                return datetime_attr

            # Fallback to text content
            time_text = time_tag.get_text(strip=True)
            if time_text:
                # Try to parse Japanese date format: 2014年06月05日
                match = re.search(r'(\d{4})年(\d{2})月(\d{2})日', time_text)
                if match:
                    year, month, day = match.groups()
                    return f"{year}-{month}-{day}"

        # Try alternative selectors
        alternative_selectors = [
            'article time',
            '.articleTit time',
            'time[datetime]',
            '.date time',
            '.publish-date time'
        ]

        for selector in alternative_selectors:
            time_tag = soup.select_one(selector)
            if time_tag:
                datetime_attr = time_tag.get('datetime')
                if datetime_attr:
                    return datetime_attr

        return None

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page."""
        # Try to find main content areas
        content_selectors = [
            {'name': 'main'},
            {'name': 'article'},
            {'name': 'div', 'class': re.compile(r'content|main|body|article', re.I)},
            {'name': 'div', 'id': re.compile(r'content|main|body|article', re.I)},
        ]

        for selector in content_selectors:
            content_area = soup.find(**selector)
            if content_area:
                return content_area.get_text(separator='\n', strip=True)

        return ""

    def _extract_all_text(self, soup: BeautifulSoup) -> str:
        """Extract all text from the page."""
        # Get text from body or entire soup
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)
        return soup.get_text(separator='\n', strip=True)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)

        return text

    def _is_same_domain(self, url: str, base_url: str) -> bool:
        """Check if URL is from the same domain as base URL."""
        url_parsed = urlparse(url)
        base_parsed = urlparse(base_url)
        return url_parsed.netloc == base_parsed.netloc or url_parsed.netloc == ""