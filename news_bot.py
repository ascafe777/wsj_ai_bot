import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import json

# Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RSS_URL = "https://feeds.content.dowjones.io/public/rss/RSSWSJD"
HOURS_LIMIT = 24  # за сколько часов брать новости

# Настройки Gist
GIST_ID = os.getenv("GIST_ID")
GIST_FILE = "sent_links.json"
GIST_TOKEN = os.getenv("WSJ")
HEADERS = {"Authorization": f"token {GIST_TOKEN}"}

def fetch_sent_links():
    """Загружаем sent_links.json из Gist"""
    resp = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=HEADERS)
    resp.raise_for_status()
    gist_data = resp.json()
    content = gist_data['files'][GIST_FILE]['content']
    try:
        return set(json.loads(content))
    except:
        return set()

def update_sent_links(sent_links):
    """Обновляем Gist с новыми ссылками"""
    update_data = {
        "files": {
            GIST_FILE: {
                "content": json.dumps(list(sent_links), indent=2)
            }
        }
    }
    resp = requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=HEADERS, json=update_data)
    if not resp.ok:
        print("Ошибка обновления Gist:", resp.text)

def send_telegram(msg):
    """Отправка сообщения в Telegram"""
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "disable_web_page_preview": False
        }
    )
    if not resp.ok:
        print("Ошибка Telegram:", resp.status_code, resp.text)

def check_news():
    sent_links = fetch_sent_links()
    resp = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml-xml")

    now_utc = datetime.now(timezone.utc)
    fresh_items = []

    for item in soup.find_all("item"):
        title = item.title.text.strip() if item.title else None
        link = item.link.text.strip() if item.link else None
        description_html = item.description.text if item.description else ""
        pub_date_text = item.pubDate.text if item.pubDate else None

        if not (title and link and pub_date_text):
            continue

        pub_date = parsedate_to_datetime(pub_date_text)

        if now_utc - pub_date <= timedelta(hours=HOURS_LIMIT) and "https://www.wsj.com/tech/ai/" in link:
            if link in sent_links:
                continue  # пропускаем уже отправленные
            short_desc = BeautifulSoup(description_html, "html.parser").get_text().strip()
            fresh_items.append((title, short_desc, link))
            sent_links.add(link)

    for i, (title, desc, link) in enumerate(fresh_items, start=1):
        message = f"{i}. {title}\n{desc}\n{link}"
        send_telegram(message)
        print(message, "\n")

    if fresh_items:
        update_sent_links(sent_links)

if __name__ == "__main__":
    check_news()
