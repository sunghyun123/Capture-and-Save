from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time
import os
from urllib.parse import quote_plus


class NaverNewsScraper:
    """
    목적:
    - 동적 DOM 구조를 가진 웹 페이지에서 안정적으로 요소를 탐색하는
      UI 자동화 테스트 스크립트를 구현하기 위함
    - 테스트 실패 시 디버깅에 활용할 수 있도록 스크린샷 및 HTML을 남기는 구조 학습
    """

    def __init__(self, headless=False, screenshot_dir="screenshots", timeout=10):
        self.timeout = timeout
        self.screenshot_dir = screenshot_dir
        os.makedirs(self.screenshot_dir, exist_ok=True)

        # Chrome 옵션 설정
        options = webdriver.ChromeOptions()

        # CI 환경이나 백그라운드 실행을 고려한 headless 모드 지원
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

        options.add_argument("--window-size=1280,800")

        # WebDriverManager를 사용하여 드라이버 버전 관리 문제 최소화
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )

        # Explicit Wait을 통한 안정적인 요소 탐색
        self.wait = WebDriverWait(self.driver, self.timeout)

    def search_and_get_first_news_title(self, query="자동차", save_screenshot_name="result.png"):
        """
        네이버 뉴스 검색 페이지에서
        첫 번째 뉴스 제목을 수집하고 정상 동작 여부를 검증한다.
        """

        try:
            # 뉴스 검색 전용 URL로 직접 접근
            q = quote_plus(query)
            url = f"https://search.naver.com/search.naver?query={q}&where=news"
            self.driver.get(url)

            # DOM 구조 변경 가능성을 고려해 여러 locator 후보를 준비
            title_locators = [
                (By.CSS_SELECTOR, "a[data-heatmap-target='.tit'] span.sds-comps-text"),
                (By.CSS_SELECTOR, "span.sds-comps-text.sds-comps-text-ellipsis"),
                (By.XPATH, "//a[@data-heatmap-target='.tit']//span[contains(@class,'sds-comps-text')]"),
                (By.CSS_SELECTOR, "a.news_tit"),
            ]

            title_text = ""

            # 네트워크 지연이나 렌더링 타이밍을 고려한 재시도 로직
            for _ in range(3):
                for locator in title_locators:
                    try:
                        element = self.wait.until(
                            EC.presence_of_element_located(locator)
                        )
                        self.wait.until(EC.visibility_of(element))
                        title_text = element.text.strip()
                        if title_text:
                            break
                    except Exception:
                        continue
                if title_text:
                    break
                time.sleep(1)

            # 테스트 결과 스크린샷 저장
            screenshot_path = os.path.join(self.screenshot_dir, save_screenshot_name)
            self.driver.save_screenshot(screenshot_path)

            # ===== 결과 검증 =====
            # 뉴스 제목이 비어있다면 테스트 실패로 판단
            assert title_text != "", "뉴스 제목을 정상적으로 수집하지 못함"

            return {
                "title": title_text,
                "screenshot": screenshot_path
            }

        except Exception as e:
            # 예외 발생 시 디버깅을 위해 화면 캡처
            error_shot = os.path.join(self.screenshot_dir, "error.png")
            try:
                self.driver.save_screenshot(error_shot)
            except Exception:
                pass

            raise RuntimeError(
                f"뉴스 검색 자동화 실패: {e} (screenshot: {error_shot})"
            ) from e

    def quit(self):
        """브라우저 리소스 정리"""
        try:
            self.driver.quit()
        except Exception:
            pass


# ===== 실행 진입점 =====
if __name__ == "__main__":
    """
    의도:
    - 자동화 스크립트를 단독 실행 가능하도록 구성
    - 실제 테스트 실행 흐름을 명확히 보여주기 위함
    """

    scraper = NaverNewsScraper(headless=True)

    try:
        result = scraper.search_and_get_first_news_title("자동차")
        print(f"[PASS] 수집된 뉴스 제목: {result['title']}")
        print(f"[INFO] 스크린샷 저장 위치: {result['screenshot']}")
    finally:
        scraper.quit()
