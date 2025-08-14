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
        title = item.title.text if item.title else "Без заголовка"
        link = item.link.text if item.link else None
        guid = item.guid.text if item.guid else None
        description = item.description.text if item.description else "Описание отсутствует"

        # Получаем картинку (media:content или media:thumbnail)
        media = item.find("media:content")
        if media and media.get("url"):
            image_url = media["url"]
        else:
            thumbnail = item.find("media:thumbnail")
            image_url = thumbnail["url"] if thumbnail and thumbnail.get("url") else None

        # проверяем, что guid уникальный и статья по AI
        if guid and link and "https://www.wsj.com/tech/ai/" in link and guid not in sent_links:
            new_items.append((title, link, description, image_url))
            sent_links.add(guid)

    # Отправляем новые статьи в Telegram
    for i, (title, link, description, image_url) in enumerate(new_items, start=1):
        if image_url:
            # Отправляем с картинкой
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": f"{i}. {title}\n{description}\n{link}",
                    "disable_web_page_preview": True
                },
                files={"photo": requests.get(image_url).content}
            )
            if response.ok:
                print(f"Отправлено: {title} (с картинкой)")
            else:
                print(f"Ошибка отправки: {title}")
        else:
            # Отправляем текстом, если нет картинки
            message = f"{i}. {title}\n{description}\n{link}"
            send_telegram(message)
            print(f"Отправлено: {title} (без картинки)")

    # Сохраняем отправленные guid
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent_links), f)



if __name__ == "__main__":
    check_news()

