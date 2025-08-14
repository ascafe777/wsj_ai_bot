import os
import requests
from bs4 import BeautifulSoup
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RSS_URL = "https://feeds.content.dowjones.io/public/rss/RSSWSJD"

SENT_FILE = "sent_links.json"

if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r") as f:
        sent_links = set(json.load(f))
else:
    sent_links = set()

def send_telegram(msg):
    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "disable_web_page_preview": False  # чтобы была превьюшка статьи
        }
    )
    if not response.ok:
        print("Ошибка Telegram:", response.status_code, response.text)
    return response.ok

def check_news():
    resp = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml-xml")
    
    new_items = []

    for item in soup.find_all("item"):
        title = item.title.text if item.title else None
        link = item.link.text if item.link else None
        description = item.description.text if item.description else ""  # краткое описание

        if link and "https://www.wsj.com/tech/ai/" in link and link not in sent_links:
            new_items.append((title, link, description))
            sent_links.add(link)

    for i, (title, link, description) in enumerate(new_items, start=1):
        # делаем компактное описание без HTML и лишних пробелов
        short_desc = BeautifulSoup(description, "html.parser").get_text().strip()
        message = f"{i}. {title}\n{short_desc}\n{link}"
        send_telegram(message)
        print(message, "\n")

    with open(SENT_FILE, "w") as f:
        json.dump(list(sent_links), f)

if __name__ == "__main__":
    check_news()

