from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from urllib.parse import quote_plus
from selenium.webdriver.common.by import By

class NaverNewsScraper:
    def __init__(self, headless=False, screenshot_dir="screenshots", timeout=10):
        self.timeout = timeout
        self.screenshot_dir = screenshot_dir
        os.makedirs(self.screenshot_dir, exist_ok=True)

        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")


        options.add_argument("--window-size=1280,800")

        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                       options=options)
        self.wait = WebDriverWait(self.driver, self.timeout)

    def search_and_get_first_news_title(self, query="자동차", save_screenshot_name="result.png"):
        try:
            # 직접 뉴스 검색 URL로 이동 (where=news)
            q = quote_plus(query)
            news_search_url = f"https://search.naver.com/search.naver?query={q}&where=news"
            self.driver.get(news_search_url)

            # 페이지가 완전히 로드될 때까지 잠깐 대기

            title_locators = [
                (By.CSS_SELECTOR, "a[data-heatmap-target='.tit'] span.sds-comps-text"),
                (By.CSS_SELECTOR, "span.sds-comps-text.sds-comps-text-ellipsis"),
                (By.XPATH, "//a[@data-heatmap-target='.tit']//span[contains(@class,'sds-comps-text')]"),
                (By.CSS_SELECTOR, "a.news_tit"),  # 기존 후보(남겨두면 호환성↑)
            ]

            title_text = ""
            for attempt in range(3):
                for tloc in title_locators:
                    try:
                        elem = WebDriverWait(self.driver, self.timeout).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "a[data-heatmap-target='.tit'] span.sds-comps-text"))
                        )
                        # 요소가 보일 때까지 기다리기
                        WebDriverWait(self.driver, self.timeout).until(EC.visibility_of(elem))
                        title_text = elem.text.strip()
                        if title_text:
                            break
                    except Exception:
                        continue
                if title_text:
                    break
                time.sleep(1)

            screenshot_path = os.path.join(self.screenshot_dir, save_screenshot_name)
            try:
                self.driver.save_screenshot(screenshot_path)
            except Exception:
                pass

            # 디버그 아티팩트(제목 없을 때)
            if not title_text:
                dbg_shot, dbg_html = self._save_debug_artifacts("no_title_direct")
                return {"title": title_text, "screenshot": screenshot_path, "debug_screenshot": dbg_shot,
                        "debug_html": dbg_html}

            return {"title": title_text, "screenshot": screenshot_path}

        except Exception as e:
            dbg_shot, dbg_html = self._save_debug_artifacts("exception_direct")
            raise RuntimeError(f"search failed: {e}. debug_screenshot={dbg_shot}, debug_html={dbg_html}") from e

    def quit(self):
        try:
            self.driver.quit()
        except Exception:
            pass
