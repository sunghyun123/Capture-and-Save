# tests/test_naver_news.py
import pytest
from src.naver_news import NaverNewsScraper
import csv, json, os
import time

@pytest.fixture(scope="function")
def scraper():
    s = NaverNewsScraper(headless=True, timeout=15)
    yield s
    s.quit()

def save_as_csv(path, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "query", "title", "url", "screenshot"])
        writer.writerow(row)

def save_as_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def test_search_automobile_first_news_title(scraper):
    result = scraper.search_and_get_first_news_title(query="자동차", save_screenshot_name="automobile_result.png")
    assert "title" in result
    assert result["title"] is not None
    assert result["title"] != ""  # 제목이 비어 있지 않아야 함
    assert os.path.exists(result["screenshot"])
    print("title:", result.get("title"))
    print("screenshot:", result.get("screenshot"))
    # 디버그 아티팩트가 있으면 출력
    print("debug files:", result.get("debug_screenshot"), result.get("debug_html"))
    save_as_csv("data/titles.csv", [time.time(), "자동차", result["title"], result.get("url", ""), result["screenshot"]])
    save_as_json("data/latest.json", result)
