import requests


class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.chat_id = "-1002577073651"
        self.base_url = f'https://api.telegram.org/bot{self.token}/sendMessage'

    def send_message(self, message):
        payload = {
            'chat_id': self.chat_id,
            'text': message
        }
        response = requests.post(self.base_url, data=payload)

        if not response.status_code == 200:
            print(f'❌ Error sending message to telegram {response.status_code}: {response.text}')