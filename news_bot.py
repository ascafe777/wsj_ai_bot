import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RSS_URL = "https://feeds.content.dowjones.io/public/rss/RSSWSJD"

# Сколько часов назад брать статьи
HOURS_LIMIT = 24

def send_telegram(msg):
    """Отправка сообщения в Telegram"""
    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "disable_web_page_preview": True
        }
    )
    if not response.ok:
        print("Ошибка Telegram:", response.status_code, response.text)
    return response.ok

def check_news():
    resp = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml-xml")

    now_utc = datetime.now(timezone.utc)
    new_items = []

    for item in soup.find_all("item"):
        title = item.title.text if item.title else None
        link = item.link.text if item.link else None
        description = item.description.text if item.description else ""
        pub_date_text = item.pubDate.text if item.pubDate else None

        if not (title and link and pub_date_text):
            continue

        # Парсим дату публикации
        pub_date = parsedate_to_datetime(pub_date_text)

        # Фильтруем: за последние HOURS_LIMIT часов
        if now_utc - pub_date <= timedelta(hours=HOURS_LIMIT) and "https://www.wsj.com/tech/ai/" in link:
            short_desc = BeautifulSoup(description, "html.parser").get_text().strip()
            new_items.append((title, short_desc, link))

    # Отправляем статьи в Telegram
    for i, (title, desc, link) in enumerate(new_items, start=1):
        message = f"{i}. {title}\n{desc}\n{link}"
        send_telegram(message)
        print(message, "\n")

if __name__ == "__main__":
    check_news()
