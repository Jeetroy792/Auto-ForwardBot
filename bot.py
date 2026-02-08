import os
import asyncio
import logging 
import logging.config
from database import db 
from config import Config  
from pyrogram import Client, __version__
from pyrogram.raw.all import layer 
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, RPCError

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client): 
    def __init__(self):
        super().__init__(
            name="main_bot", 
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            plugins={"root": "plugins"},
            workers=50,
            bot_token=Config.BOT_TOKEN,
            in_memory=True 
        )
        self.user = None # শুরুতে None থাকবে, পরে ডাটাবেস থেকে লোড হবে

    async def start(self):
        await super().start()
        me = await self.get_me()
        
        # ১. ডাটাবেস থেকে সেশন স্ট্রিং খুঁজে বের করা
        saved_session = await db.get_config("USER_SESSION")
        session_to_use = saved_session if saved_session else os.environ.get("USER_SESSION")

        # ২. ইউজারবট ক্লায়েন্ট সেটআপ
        self.user = Client(
            name="dynamic_userbot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=session_to_use,
            in_memory=True
        )

        try:
            await self.user.start()
            # নতুন সেশন হলে ডাটাবেসে আপডেট করে রাখা
            new_session = await self.user.export_session_string()
            await db.set_config("USER_SESSION", new_session)
            logging.info("Userbot Session synced with Database.")
        except Exception as e:
            logging.error(f"Userbot error: {e}. Please login again if session expired.")

        logging.info(f"@{me.username} is Online.")

    async def stop(self, *args):
        # ক্যানসেলেশন বা অফলাইন মেসেজ
        msg = "**⚠️ টাস্ক ক্যানসেল করা হয়েছে এবং বট অফলাইনে যাচ্ছে!**"
        
        # টার্গেট চ্যানেলে মেসেজ (যদি Config-এ থাকে)
        if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
            try: await self.send_message(Config.LOG_CHANNEL, msg)
            except: pass
            
        # ডাটাবেসে থাকা ইউজারদের জানানো
        users = await db.get_all_frwd()
        async for user in users:
            try: await self.send_message(user['user_id'], msg)
            except: continue

        if self.user and self.user.is_connected:
            await self.user.stop() 
        await super().stop()

    # ক্যানসেল করার জন্য স্পেশাল ফাংশন যা আপনি প্লাগিন থেকে কল করতে পারবেন
    async def send_cancel_notif(self, chat_id=None):
        cancel_text = "**❌ অপারেশন ক্যানসেল করা হয়েছে!**"
        # ১. বটের নিজের চ্যাটে বা ইউজারের চ্যাটে
        if chat_id:
            await self.send_message(chat_id, cancel_text)
        # ২. টার্গেট চ্যানেলে
        if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
            await self.send_message(Config.LOG_CHANNEL, cancel_text)
