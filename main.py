from flask import Flask
from threading import Thread
from bot import Bot

# Create Flask App
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is Alive"

def run():
    web_app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Main section to start the bot
if __name__ == "__main__":
    keep_alive()  # This will keep port 8000 active
    app = Bot()
    app.run()
