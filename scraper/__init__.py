"""Web scraper module for collecting data from Sanae's website."""

from .crawler import WebCrawler
from .parser import HTMLParser

__all__ = ['WebCrawler', 'HTMLParser']