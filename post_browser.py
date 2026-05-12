"""
Playwright を使ったThreads自動投稿スクリプト
"""
import os
import json
import time
from playwright.sync_api import sync_playwright

COOKIES_FILE = "threads_cookies.json"
BASE_URL = "https://www.threads.com"

def save_cookies(context):
    cookies = context.cookies()
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f)
    print("セッションを保存しました")

def load_cookies(context):
    cookies_json = os.environ.get("THREADS_COOKIES")
    if cookies_json:
        try:
            cookies = json.loads(cookies_json)
            context.add_cookies(cookies)
            print("環境変数からCookieを読み込みました")
            return True
        except Exception as e:
            print(f"環境変数のCookie読み込み失敗: {e}")

    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print("ファイルからCookieを読み込みました")
        return True
    return False

def post_to_threads(text: str) -> bool:
    username = os.environ.get("THREADS_USERNAME")
    password = os.environ.get("THREADS_PASSWORD")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        cookie_loaded = load_cookies(context)

        page.goto(f"{BASE_URL}/intent/post", wait_until="domcontentloaded")
        time.sleep(3)
        page.screenshot(path="step1_top.png")
        print(f"ログイン確認URL: {page.url}")

        if "login" in page.url:
            print("ログイン中...")
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
            time.sleep(3)

            try:
                page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
                page.fill('input[autocomplete="username"]', username)
                print("ユーザー名入力完了")
            except:
                try:
                    page.wait_for_selector('input[type="text"]', timeout=5000)
                    page.fill('input[type="text"]', username)
                    print("ユーザー名入力完了（type=text）")
                except Exception as e:
                    print(f"ユーザー名入力失敗: {e}")
            time.sleep(1)

            try:
                page.fill('input[type="password"]', password)
                print("パスワード入力完了")
            except Exception as e:
                print(f"パスワード入力失敗: {e}")
            time.sleep(1)

            page.locator('input[type="password"]').press("Enter")
            print("パスワードフィールドでEnter送信")

            for i in range(15):
                time.sleep(1)
                if "login" not in page.url:
                    print(f"ログイン成功！URL: {page.url}")
                    break
            else:
                print(f"ログインタイムアウト: {page.url}")

            time.sleep(2)
            save_cookies(context)

        if "login" in page.url:
            print("ログイン失敗")
            browser.close()
            return False

        if "intent/post" not in page.url:
            page.goto(f"{BASE_URL}/intent/post", wait_until="domcontentloaded")
            time.sleep(3)

        if "login" in page.url:
            print("投稿フォームでログイン要求 → ログイン失敗")
            browser.close()
            return False

        try:
            time.sleep(2)

            text_input_done = False
            text_selectors = [
                '[contenteditable="true"]',
                'textarea[placeholder]',
                '[data-testid="post-input"]',
            ]
            for selector in text_selectors:
                try:
                    page.click(selector, timeout=3000)
                    page.keyboard.type(text)
                    print(f"テキスト入力完了: {selector}")
                    text_input_done = True
                    break
                except:
                    continue

            if not text_input_done:
                print("テキスト入力失敗")
                browser.close()
                return False

            time.sleep(2)
            page.keyboard.press("Escape")
            time.sleep(2)

            posted = False
            try:
                result = page.evaluate("""
                    () => {
                        const dialog = document.querySelector('div[role="dialog"]');
                        if (dialog) {
                            const btns = Array.from(dialog.querySelectorAll('div[role="button"], button'));
                            const postBtn = btns.filter(b => b.textContent.trim() === 'Post' || b.textContent.trim() === '投稿する').pop();
                            if (postBtn) {
                                postBtn.click();
                                return 'clicked: ' + postBtn.tagName;
                            }
                            return 'dialog found but no Post button. buttons: ' + btns.map(b => b.textContent.trim()).join(', ');
                        }
                        return 'no dialog found';
                    }
                """)
                print(f"JS クリック結果: {result}")
                if result and result.startswith("clicked"):
                    posted = True
            except Exception as e:
                print(f"JS クリック失敗: {e}")

            time.sleep(3)
            page.screenshot(path="step6_final.png")
            save_cookies(context)
            browser.close()
            return posted

        except Exception as e:
            print(f"投稿エラー: {e}")
            page.screenshot(path="error_screenshot.png")
            browser.close()
            return False


if __name__ == "__main__":
    test_text = "ADHD Strategy テスト投稿 #ADHD"
    result = post_to_threads(test_text)
    print(f"結果: {'成功' if result else '失敗'}")
