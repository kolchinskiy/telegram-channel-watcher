import os
import requests
from bs4 import BeautifulSoup

CHANNEL = "whatwwme"
STATE_FILE = "state.txt"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def get_last_post():
    url = f"https://t.me/s/{CHANNEL}"

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    posts = soup.select(".tgme_widget_message")

    if not posts:
        raise RuntimeError("Не удалось найти посты канала")

    post = posts[-1]

    data_post = post.get("data-post")
    if not data_post:
        raise RuntimeError("Не удалось определить ID поста")

    post_id = data_post.split("/")[-1]

    text_element = post.select_one(".tgme_widget_message_text")
    text = text_element.get_text("\n", strip=True) if text_element else ""

    link = f"https://t.me/{CHANNEL}/{post_id}"

    return post_id, text, link


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "disable_web_page_preview": False,
        },
        timeout=30,
    )

    response.raise_for_status()


def main():
    post_id, text, link = get_last_post()

    old_id = None

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            old_id = f.read().strip()

    if old_id == post_id:
        print("Новых постов нет.")
        return

    with open(STATE_FILE, "w") as f:
        f.write(post_id)

    # Первый запуск только запоминает последний пост.
    # Старые посты уведомлением не отправляем.
    if old_id is None:
        print(f"Первый запуск. Последний пост: {post_id}")
        return

    message = f"🔔 Новый пост в @{CHANNEL}\n\n"

    if text:
        message += text[:3500] + "\n\n"

    message += f"👉 {link}"

    send_message(message)

    print(f"Отправлено уведомление о посте {post_id}")


if __name__ == "__main__":
    main()
