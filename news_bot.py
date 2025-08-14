import os
import requests
from bs4 import BeautifulSoup
import json

TELEGRAM_TOKEN = os.environ["8410867421:AAFP6ZJW4Ice_9P2yvT7cxwxV3lAfHGA42Q"]
TELEGRAM_CHAT_ID = os.environ["198971151"]
URL = "https://www.wsj.com/tech/ai?mod=nav_top_subsection"

# Файл для хранения уже отправленных ссылок
SENT_FILE = "sent_links.json"

# Загружаем уже отправленные ссылки
if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r") as f:
        sent_links = set(json.load(f))
else:
    sent_links = set()

def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "disable_web_page_preview": True}
    )

def check_news():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")
    new_links = []

    # Пробегаем по всем ссылкам на статьи
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)
        if "/articles/" in href and title and href not in sent_links:
            new_links.append((title, href))
            sent_links.add(href)

    # Отправляем новые статьи в Telegram
    for title, href in new_links:
        send_telegram(f"{title}\n{href}")

    # Сохраняем отправленные ссылки
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent_links), f)

if __name__ == "__main__":
    check_news()
