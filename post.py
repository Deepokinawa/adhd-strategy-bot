import os
import json
import datetime
import anthropic
import feedparser
import random
import requests
from urllib.parse import quote

RSS_FEEDS = [
    ("nhk_health",   "https://www3.nhk.or.jp/rss/news/cat1.xml"),
    ("yomiuri",      "https://www.yomiuri.co.jp/feed/"),
    ("asahi",        "https://www.asahi.com/rss/asahi/newsheadlines.rdf"),
    ("mainichi",     "https://mainichi.jp/rss/etc/mainichi-flash.rss"),
]

ADHD_KEYWORDS = [
    "ADHD", "注意欠如", "注意欠陥", "発達障害", "ASD", "自閉症",
    "学習障害", "LD", "不注意", "多動", "衝動", "グレーゾーン",
    "インチュニブ", "コンサータ", "ストラテラ", "精神科", "心療内科",
    "働き方", "仕事術", "生産性", "先延ばし", "タスク管理", "集中力",
    "睡眠", "運動", "食事", "メンタル", "ストレス", "自己肯定感"
]

EXCLUDE_KEYWORDS = ["訃報", "おくやみ", "人事", "広告", "プレゼント", "求人", "株価", "為替"]

POSTS_LOG = "posts_log.json"

ORIGINAL_TOPICS = [
    "先延ばしが止まらない理由と、今日から使える対策",
    "インチュニブを飲み始めて変わったこと・変わらなかったこと",
    "ADHDの人が朝の準備を時間通りに終わらせるコツ",
    "会議中に頭が別のことを考え始める問題の対処法",
    "締め切り直前に神集中力が出る仕組みを使い倒す方法",
    "ADHDと診断されてよかったと思える瞬間",
    "「普通にできないのになんで？」と言われ続けた話",
    "衝動買いを防ぐために決めたルール",
    "ADHDの過集中を仕事に活かす方法",
    "診断前と診断後で変わった自分への見方",
    "ADHDと睡眠の切っても切れない関係",
    "マルチタスクが苦手なADHDの仕事術",
]


def get_news():
    articles = []
    week_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    for source_id, feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))[:300]
                url = entry.get("link", "")
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    pub_dt = datetime.datetime(*published[:6], tzinfo=datetime.timezone.utc)
                    if pub_dt < week_ago:
                        continue
                if any(kw in title for kw in EXCLUDE_KEYWORDS):
                    continue
                if any(kw in title + summary for kw in ADHD_KEYWORDS):
                    articles.append({"title": title, "summary": summary, "url": url, "source": source_id})
        except Exception:
            continue
    return articles


def load_posts_log():
    if os.path.exists(POSTS_LOG):
        with open(POSTS_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_post_log(article, post_text):
    logs = load_posts_log()
    logs.append({
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "article_title": article.get("title", "オリジナル投稿"),
        "article_url": article.get("url", ""),
        "post_text": post_text,
    })
    logs = logs[-100:]
    with open(POSTS_LOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def get_recent_posts_summary():
    logs = load_posts_log()
    if not logs:
        return ""
    recent = logs[-5:]
    titles = [l["article_title"] for l in recent]
    return "【直近の投稿テーマ（重複を避けてください）】\n" + "\n".join(f"- {t}" for t in titles)


def generate_post_from_news(article):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    recent_summary = get_recent_posts_summary()
    prompt = f"""あなたは「ADHD Strategy」というアカウントの運営者です。
ADHDの当事者として、同じ悩みを持つ人に寄り添い、共感・実用的な情報・希望を届けることをミッションにしています。
2026年1月に28歳でADHD診断を受け、インチュニブを服用しながら事業開発の仕事をしています。

以下のニュースを元に、Threadsに投稿する文章を1つ作ってください。

【投稿ルール】
- 本文は150文字以内（URLは別で追加するので含めない）
- ADHD当事者の目線で、リアルな共感が得られる内容
- 「自分ごと」として読めるような切り口
- 医療情報は断定せず「〜らしい」「〜と感じた」などの表現を使う
- ハッシュタグは末尾に1〜2個（#ADHD #発達障害 のどちらか）
- 媒体名・署名・URLは不要
- 文章だけ出力する

{recent_summary}

【ニュース】
タイトル：{article['title']}
内容：{article['summary']}
"""
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()


def generate_original_post(topic):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    recent_summary = get_recent_posts_summary()
    prompt = f"""あなたは「ADHD Strategy」というアカウントの運営者です。
ADHDの当事者として、同じ悩みを持つ人に寄り添い、共感・実用的な情報・希望を届けることをミッションにしています。
2026年1月に28歳でADHD診断を受け、インチュニブを服用しながら事業開発の仕事をしています。

以下のテーマでThreadsに投稿する文章を1つ作ってください。

【投稿ルール】
- 本文は150文字以内
- ADHD当事者として、リアルで共感できる体験・気づき・工夫を書く
- 「わかる！」「自分だけじゃなかった」と感じてもらえる内容
- 前向きだが、きれいごとにならないリアルさを大切に
- ハッシュタグは末尾に1〜2個（#ADHD #発達障害 のどちらか）
- 文章だけ出力する

{recent_summary}

【テーマ】
{topic}
"""
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()


def send_telegram(post_text: str, article_url: str = "") -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN または TELEGRAM_CHAT_ID 未設定")
        return False

    threads_text = f"{post_text}\n\n{article_url}" if article_url else post_text
    threads_url = f"https://www.threads.net/intent/post?text={quote(threads_text)}"
    x_url = f"https://x.com/intent/post?text={quote(post_text)}"
    url_line = f"\n\n🔗 元記事: {article_url}" if article_url else ""

    message = f"""🧠 ADHD Strategy

{post_text}

🧵 Threadsに投稿
{threads_url}

🐦 Xに投稿（テキストのみ）
{x_url}{url_line}"""

    try:
        for i in range(0, len(message), 4000):
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message[i:i+4000], "disable_web_page_preview": True},
                timeout=10
            )
        return True
    except Exception as e:
        print(f"Telegram送信エラー: {e}")
        return False


def main():
    articles = get_news()
    use_news = articles and random.random() < 0.3  # 30%ニュース / 70%オリジナル

    if use_news:
        article = random.choice(articles)
        print(f"モード: ニュース投稿（{article['title']}）")
        post_text = generate_post_from_news(article)
        article_url = article["url"] if random.random() < 0.5 else ""
    else:
        topic = random.choice(ORIGINAL_TOPICS)
        print(f"モード: オリジナル投稿（{topic}）")
        article = {"title": topic, "url": ""}
        post_text = generate_original_post(topic)
        article_url = ""

    print(f"生成テキスト:\n{post_text}")

    result = send_telegram(post_text, article_url)
    print(f"Telegram通知: {'成功' if result else '失敗'}")

    if result:
        save_post_log(article, post_text)
        print("投稿ログを保存しました")


if __name__ == "__main__":
    main()
