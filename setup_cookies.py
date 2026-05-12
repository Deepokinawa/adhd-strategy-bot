"""
初回セットアップ用：ブラウザを開いてログイン → Cookieを保存
このスクリプトは最初の1回だけ実行する
"""
import json
import time
from playwright.sync_api import sync_playwright

COOKIES_FILE = "threads_cookies.json"
REPO = "Deepokinawa/adhd-strategy-bot"

def setup():
    print("ブラウザを開いています...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        page.goto("https://www.threads.com/login")
        print()
        print("=" * 50)
        print("ブラウザが開きました。")
        print("Threadsに手動でログインしてください。")
        print("ログイン完了後、このターミナルでEnterを押してください。")
        print("=" * 50)
        input()

        cookies = context.cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f)

        print(f"✅ Cookieを保存しました（{len(cookies)}件）")
        browser.close()

    with open(COOKIES_FILE, "r") as f:
        cookie_content = f.read()

    print()
    print("GitHub Secretsに登録します...")
    import subprocess
    result = subprocess.run(
        ["gh", "secret", "set", "THREADS_COOKIES", "--body", cookie_content, "-R", REPO],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ GitHub Secrets に THREADS_COOKIES を保存しました！")
    else:
        print(f"GitHub Secrets への保存に失敗: {result.stderr}")
        print("手動でコピーして登録してください")

if __name__ == "__main__":
    setup()
