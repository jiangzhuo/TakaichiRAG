"""Web crawler for scraping content from Sanae's website."""

import time
import json
from typing import List, Dict, Set, Optional
from pathlib import Path
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from tqdm import tqdm
from .parser import HTMLParser


class WebCrawler:
    """Crawler for collecting content from Sanae's website."""

    def __init__(self, config: Dict, data_dir: Path):
        """
        Initialize the web crawler.

        Args:
            config: Scraper configuration dictionary
            data_dir: Directory to save scraped data
        """
        self.config = config
        self.base_url = config['base_url']
        self.data_dir = data_dir
        self.parser = HTMLParser(self.base_url)

        # Set up session with retry logic
        self.session = self._create_session()

        # Track visited URLs to avoid duplicates
        self.visited_urls = set()
        self.scraped_data = []

        # Timestamp for consistent file naming across categories
        self.timestamp = None
        self.saved_files = []

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()

        # Set up retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set headers
        session.headers.update(self.config['headers'])

        return session

    def crawl_all_pages(self) -> List[Dict]:
        """
        Crawl all target pages and their subpages.
        Each category is saved immediately after crawling.

        Returns:
            List of scraped data dictionaries (empty if saved incrementally)
        """
        print("Starting web crawling...")
        print("="*50)

        # Initialize timestamp for consistent file naming
        if self.timestamp is None:
            self.timestamp = int(time.time())

        total_pages = 0

        # Crawl main target pages
        for page_name, page_path in self.config['target_pages'].items():
            url = urljoin(self.base_url, page_path)
            print(f"\n📂 Crawling {page_name}: {url}")
            print("-"*50)

            # Special handling for different page types based on their structure
            if page_name == "idea" or page_name == "posture":
                # Single pages - simple crawling
                self._crawl_single_page(url, page_name)
            elif page_name == "results":
                # List page with direct content pages
                self._crawl_results_pages(url)
            elif page_name == "kaiken":
                # Two-level structure: main → list pages → detail pages
                self._crawl_kaiken_pages(url)
            elif page_name == "column":
                # Complex structure with list and detail pages
                self._crawl_column_pages(url)
            else:
                # Default crawling
                self._crawl_page_and_subpages(url, page_name)

            # Save this category's data immediately
            saved_file = self._save_category_data(page_name)
            if saved_file:
                # Count pages before they're removed from scraped_data
                with open(saved_file, 'r', encoding='utf-8') as f:
                    category_data = json.load(f)
                    total_pages += len(category_data)

            # Be polite to the server
            time.sleep(self.config['delay_between_requests'])

        print("\n" + "="*50)
        print(f"✅ Crawling complete! Scraped {total_pages} pages total.")
        print(f"📁 Saved {len(self.saved_files)} category files")
        print("="*50)
        return self.scraped_data

    def _crawl_single_page(self, url: str, category: str):
        """
        Crawl a single page without following subpages.

        Args:
            url: The URL to crawl
            category: The category of the page
        """
        if url in self.visited_urls:
            return

        self.visited_urls.add(url)

        # Fetch and parse the page
        html = self._fetch_page(url)
        if not html:
            return

        # Parse content
        content_data = self.parser.extract_content(html, url)
        content_data['category'] = category

        # Save if content is substantial (100 characters minimum for Japanese content)
        if content_data['word_count'] > 100:
            self.scraped_data.append(content_data)
            print(f"  ✓ Scraped: {content_data['title'][:50]}... ({content_data['word_count']} chars)")
        else:
            print(f"  ⊘ Skipped: {content_data['title'][:50]}... ({content_data['word_count']} chars - too short)")

    def _crawl_page_and_subpages(self, url: str, category: str, max_depth: int = 2, current_depth: int = 0):
        """
        Crawl a page and its subpages recursively.

        Args:
            url: The URL to crawl
            category: The category of the page
            max_depth: Maximum crawling depth
            current_depth: Current crawling depth
        """
        # Skip if already visited or max depth reached
        if url in self.visited_urls or current_depth > max_depth:
            return

        self.visited_urls.add(url)

        # Fetch the page
        html = self._fetch_page(url)
        if not html:
            return

        # Parse content
        content_data = self.parser.extract_content(html, url)
        content_data['category'] = category
        content_data['depth'] = current_depth

        # Only save if content is substantial (100 characters minimum for Japanese content)
        if content_data['word_count'] > 100:
            self.scraped_data.append(content_data)
            print(f"  Scraped: {content_data['title'][:50]}... ({content_data['word_count']} chars)")

        # Extract and crawl subpage links
        if current_depth < max_depth:
            links = self.parser.extract_links(html, url)
            for link in links:
                # Only follow links that seem related to the category
                if self._should_follow_link(link, category):
                    self._crawl_page_and_subpages(link, category, max_depth, current_depth + 1)
                    time.sleep(self.config['delay_between_requests'])

    def _crawl_results_pages(self, url: str):
        """
        Crawl results pages (実績).
        Structure: main page → results_*.html content pages

        Args:
            url: The results main page URL
        """
        print("  📋 Fetching results pages...")

        # First, crawl the main results page
        self._crawl_single_page(url, "results")

        # Fetch the main page to find result links
        html = self._fetch_page(url)
        if not html:
            return

        # Look for results_*.html pages (e.g., results_japan7.html, results_nara6.html)
        results_links = self.parser.extract_subpage_links(html, url, pattern=r'results_[^/]+\.html')

        print(f"  Found {len(results_links)} results pages")

        # Crawl each results page
        for link in tqdm(results_links, desc="  Crawling results"):
            if link not in self.visited_urls:
                self._crawl_single_page(link, "results")
                time.sleep(self.config['delay_between_requests'])

        print(f"  ✅ Results section complete: {len(results_links) + 1} pages")

    def _crawl_column_pages(self, url: str):
        """
        Crawl column pages (コラム).
        Structure: main page → column_list*.html → column_detail*.html
                   main page also has direct links to recent column_detail*.html

        Args:
            url: The column main page URL
        """
        print("  📝 Fetching column pages...")

        # First, crawl the main column page
        self._crawl_single_page(url, "column")

        # Fetch the main page to find both list pages and detail pages
        html = self._fetch_page(url)
        if not html:
            return

        # Look for column_list*.html pages
        list_links = self.parser.extract_subpage_links(html, url, pattern=r'column_list\d+\.html')
        print(f"  Found {len(list_links)} column list pages")

        # Look for column_detail*.html pages on the main page (recent articles)
        all_detail_links = self.parser.extract_subpage_links(html, url, pattern=r'column_detail\d+\.html')
        print(f"  Found {len(all_detail_links)} recent column articles on main page")

        # Process each list page to find more detail pages
        for list_url in tqdm(list_links, desc="  Processing list pages"):
            if list_url not in self.visited_urls:
                # Crawl the list page itself
                self._crawl_single_page(list_url, "column")

                # Fetch list page to find detail links
                list_html = self._fetch_page(list_url)
                if list_html:
                    # Look for column_detail*.html pages
                    detail_links = self.parser.extract_subpage_links(
                        list_html, list_url, pattern=r'column_detail\d+\.html'
                    )
                    all_detail_links.extend(detail_links)
                    time.sleep(self.config['delay_between_requests'])

        # Remove duplicates
        all_detail_links = list(set(all_detail_links))
        print(f"  Found {len(all_detail_links)} column detail pages total")

        # Crawl all detail pages
        for detail_url in tqdm(all_detail_links, desc="  Crawling detail pages"):
            if detail_url not in self.visited_urls:
                self._crawl_single_page(detail_url, "column")
                time.sleep(self.config['delay_between_requests'])

        print(f"  ✅ Column section complete: {1 + len(list_links) + len(all_detail_links)} pages")

    def _crawl_kaiken_pages(self, url: str):
        """
        Crawl press conference pages (記者会見).
        Structure: main page → kaiken_list*.html → kaiken_detail*.html

        Args:
            url: The press conference main page URL
        """
        print("  🎤 Fetching press conference pages...")

        # First, crawl the main kaiken page
        self._crawl_single_page(url, "kaiken")

        # Fetch the main page to find list pages
        html = self._fetch_page(url)
        if not html:
            return

        # Look for kaiken_list*.html pages
        list_links = self.parser.extract_subpage_links(html, url, pattern=r'kaiken_list\d+\.html')
        print(f"  Found {len(list_links)} kaiken list pages")

        all_detail_links = []

        # Process each list page to find detail pages
        for list_url in tqdm(list_links, desc="  Processing list pages"):
            if list_url not in self.visited_urls:
                # Crawl the list page itself
                self._crawl_single_page(list_url, "kaiken")

                # Fetch list page to find detail links
                list_html = self._fetch_page(list_url)
                if list_html:
                    # Look for kaiken_detail*.html pages
                    detail_links = self.parser.extract_subpage_links(
                        list_html, list_url, pattern=r'kaiken_detail\d+\.html'
                    )
                    all_detail_links.extend(detail_links)
                    time.sleep(self.config['delay_between_requests'])

        # Remove duplicates
        all_detail_links = list(set(all_detail_links))
        print(f"  Found {len(all_detail_links)} kaiken detail pages total")

        # Crawl all detail pages
        for detail_url in tqdm(all_detail_links, desc="  Crawling detail pages"):
            if detail_url not in self.visited_urls:
                self._crawl_single_page(detail_url, "kaiken")
                time.sleep(self.config['delay_between_requests'])

        print(f"  ✅ Kaiken section complete: {1 + len(list_links) + len(all_detail_links)} pages")

    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a web page with error handling.

        Args:
            url: The URL to fetch

        Returns:
            The HTML content or None if failed
        """
        try:
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()

            # Ensure proper encoding for Japanese content
            response.encoding = response.apparent_encoding or 'utf-8'

            return response.text
        except Exception as e:
            print(f"  Error fetching {url}: {e}")
            return None

    def _should_follow_link(self, link: str, category: str) -> bool:
        """
        Determine if a link should be followed based on category.

        Args:
            link: The URL to check
            category: The current category

        Returns:
            True if the link should be followed
        """
        # Don't follow external links
        if not link.startswith(self.base_url):
            return False

        # Don't follow media files
        media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.mp4', '.mp3']
        if any(link.lower().endswith(ext) for ext in media_extensions):
            return False

        # Category-specific rules
        if category == "column":
            return "column" in link.lower()
        elif category == "kaiken":
            return "kaiken" in link.lower()
        elif category == "idea":
            return "idea" in link.lower() or "policy" in link.lower()
        elif category == "posture":
            return "posture" in link.lower() or "stance" in link.lower()
        elif category == "results":
            return "result" in link.lower() or "achievement" in link.lower()

        # Default: follow if it seems related
        return True

    def _save_category_data(self, category: str) -> Optional[Path]:
        """
        Save data for a specific category immediately after crawling.

        Args:
            category: The category to save

        Returns:
            Path to the saved file, or None if no data for this category
        """
        # Filter data for this category
        category_data = [item for item in self.scraped_data if item.get('category') == category]

        if not category_data:
            return None

        # Use consistent timestamp across all categories
        if self.timestamp is None:
            self.timestamp = int(time.time())

        # Save to file
        category_file = self.data_dir / f"{category}_{self.timestamp}.json"
        with open(category_file, 'w', encoding='utf-8') as f:
            json.dump(category_data, f, ensure_ascii=False, indent=2)

        print(f"  ✅ Saved {category}: {len(category_data)} pages → {category_file.name}")

        # Remove saved data from scraped_data to free memory
        self.scraped_data = [item for item in self.scraped_data if item.get('category') != category]

        # Track saved files
        self.saved_files.append(category_file)

        return category_file

    def save_data(self, output_file: Optional[Path] = None):
        """
        Save scraped data to JSON files, organized by category.

        Note: If using crawl_all_pages(), data is saved incrementally per category.
        This method is kept for backward compatibility.

        Args:
            output_file: Optional output file path (ignored, kept for compatibility)
        """
        # If data already saved incrementally, return those files
        if self.saved_files and not self.scraped_data:
            print(f"\n✅ Data already saved to {len(self.saved_files)} category files")
            return self.saved_files

        # Otherwise, save remaining data (backward compatibility)
        if not self.scraped_data:
            print("\n⚠️  No data to save")
            return []

        # Group data by category
        data_by_category = {}
        for item in self.scraped_data:
            category = item.get('category', 'unknown')
            if category not in data_by_category:
                data_by_category[category] = []
            data_by_category[category].append(item)

        # Generate timestamp for filenames if not already set
        if self.timestamp is None:
            self.timestamp = int(time.time())

        # Save each category to a separate file
        saved_files = []
        for category, items in data_by_category.items():
            category_file = self.data_dir / f"{category}_{self.timestamp}.json"
            with open(category_file, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)

            saved_files.append(category_file)
            print(f"  📄 {category}: {len(items)} pages → {category_file.name}")

        print(f"\n✅ Data saved to {len(saved_files)} category files")
        self.saved_files.extend(saved_files)
        return saved_files