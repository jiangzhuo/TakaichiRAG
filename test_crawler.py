#!/usr/bin/env python3
"""
Test script for the improved Takaichi website crawler.
"""

import sys
import json
from pathlib import Path
from collections import Counter

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import SCRAPER_CONFIG, RAW_DATA_DIR
from scraper import WebCrawler


def test_crawler():
    """Test the improved web crawler."""
    print("=" * 60)
    print("高市早苗ウェブサイト クローラーテスト")
    print("=" * 60)

    # Initialize crawler
    crawler = WebCrawler(SCRAPER_CONFIG, RAW_DATA_DIR)

    # Run the crawler
    scraped_data = crawler.crawl_all_pages()

    # Analyze results
    print("\n" + "=" * 60)
    print("📊 クローリング結果分析")
    print("=" * 60)

    # Count pages by category
    category_counts = Counter(item['category'] for item in scraped_data)

    print(f"\n総ページ数: {len(scraped_data)}")
    print("\nカテゴリ別ページ数:")
    for category, count in category_counts.items():
        print(f"  - {category}: {count} ページ")

    # Analyze URLs
    print("\nURL パターン分析:")
    url_patterns = Counter()
    for item in scraped_data:
        url = item['url']
        if 'column_detail' in url:
            url_patterns['column_detail'] += 1
        elif 'column_list' in url:
            url_patterns['column_list'] += 1
        elif 'kaiken_detail' in url:
            url_patterns['kaiken_detail'] += 1
        elif 'kaiken_list' in url:
            url_patterns['kaiken_list'] += 1
        elif 'results_' in url:
            url_patterns['results_pages'] += 1
        else:
            url_patterns['main_pages'] += 1

    for pattern, count in url_patterns.items():
        print(f"  - {pattern}: {count} ページ")

    # Calculate total word count
    total_words = sum(item['word_count'] for item in scraped_data)
    avg_words = total_words // len(scraped_data) if scraped_data else 0

    print(f"\n総単語数: {total_words:,}")
    print(f"平均単語数/ページ: {avg_words:,}")

    # Save detailed report
    report_path = RAW_DATA_DIR / "crawler_test_report.json"
    report = {
        "total_pages": len(scraped_data),
        "category_counts": dict(category_counts),
        "url_patterns": dict(url_patterns),
        "total_words": total_words,
        "average_words_per_page": avg_words,
        "sample_pages": [
            {
                "url": item['url'],
                "title": item['title'][:50] + "..." if len(item['title']) > 50 else item['title'],
                "category": item['category'],
                "word_count": item['word_count']
            }
            for item in scraped_data[:10]  # First 10 pages as sample
        ]
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n詳細レポート保存先: {report_path}")

    # Save scraped data
    data_path = crawler.save_data()
    print(f"スクレイピングデータ保存先: {data_path}")

    # Success criteria
    print("\n" + "=" * 60)
    print("✅ テスト結果")
    print("=" * 60)

    success_criteria = [
        ("基本理念 (idea) ページ取得", category_counts.get('idea', 0) >= 1),
        ("政治姿勢 (posture) ページ取得", category_counts.get('posture', 0) >= 1),
        ("実績 (results) ページ取得", category_counts.get('results', 0) >= 2),
        ("記者会見 (kaiken) 詳細ページ取得", url_patterns.get('kaiken_detail', 0) >= 10),
        ("コラム (column) 詳細ページ取得", url_patterns.get('column_detail', 0) >= 10),
        ("総ページ数 > 50", len(scraped_data) > 50),
    ]

    all_passed = True
    for criteria, passed in success_criteria:
        status = "✅" if passed else "❌"
        print(f"{status} {criteria}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 すべてのテストに合格しました！")
        print("クローラーは正常に動作しています。")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")
        print("クローラーの設定を確認してください。")

    return scraped_data


if __name__ == "__main__":
    test_crawler()