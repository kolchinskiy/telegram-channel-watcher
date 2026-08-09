import os
import json
import requests
from bs4 import BeautifulSoup

CHANNELS = [
    "whatwwme",
    "test42_5",
]

STATE_FILE = "state.json"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def get_last_post(channel):
    url = f"https://t.me/s/{channel}"

    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    posts = soup.select(".tgme_widget_message")

    if not posts:
        raise RuntimeError(f"Не удалось найти посты канала @{channel}")

    post = posts[-1]

    data_post = post.get("data-post")
    if not data_post:
        raise RuntimeError(f"Не удалось определить ID поста @{channel}")

    post_id = data_post.split("/")[-1]

    text_element = post.select_one(".tgme_widget_message_text")
    text = text_element.get_text("\n", strip=True) if text_element else ""

    link = f"https://t.me/{channel}/{post_id}"

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


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def main():
    state = load_state()
    changed = False

    for channel in CHANNELS:
        try:
            post_id, text, link = get_last_post(channel)

            old_id = state.get(channel)

            if old_id == post_id:
                print(f"@{channel}: новых постов нет.")
                continue

            state[channel] = post_id
            changed = True

            # Первый запуск для конкретного канала:
            # только запоминаем текущий пост.
            if old_id is None:
                print(f"@{channel}: первый запуск, пост {post_id} сохранён.")
                continue

            message = f"🔔 Новый пост в @{channel}\n\n"

            if text:
                message += text[:3500] + "\n\n"

            message += f"👉 {link}"

            send_message(message)

            print(f"@{channel}: уведомление отправлено, пост {post_id}")

        except Exception as e:
            print(f"@{channel}: ошибка: {e}")

    if changed:
        save_state(state)


if __name__ == "__main__":
    main()
