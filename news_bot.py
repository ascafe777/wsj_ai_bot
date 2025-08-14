import os
import requests
from bs4 import BeautifulSoup
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RSS_URL = "https://feeds.content.dowjones.io/public/rss/RSSWSJD"
SENT_FILE = "sent_links.json"

# Загружаем уже отправленные ссылки
if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r") as f:
        sent_links = set(json.load(f))
else:
    sent_links = set()

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
    return response.ok

def check_news():
    resp = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.content, "lxml-xml")
    
    new_items = []

    for item in soup.find_all("item"):
        title = item.title.text if item.title else None
        link = item.link.text if item.link else None

        if link and "https://www.wsj.com/tech/ai/" in link and link not in sent_links:
            new_items.append((title, link))
            sent_links.add(link)

    # Отправляем новые статьи в Telegram в нужном формате
    for i, (title, link) in enumerate(new_items, start=1):
        message = f"{i}. {title}\n   {link}"
        if send_telegram(message):
            print(f"Отправлено: {title}")
        else:
            print(f"Ошибка отправки: {title}")

    # Сохраняем отправленные ссылки
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent_links), f)

if __name__ == "__main__":
    check_news()

