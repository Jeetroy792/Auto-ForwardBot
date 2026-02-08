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
        self.user = None

    async def start(self):
        # ১. মেইন বট কানেক্ট করা (যদি অলরেডি কানেক্টেড না থাকে)
        if not self.is_connected:
            await super().start()
        
        me = await self.get_me()
        self.id = me.id
        self.username = me.username
        logging.info(f"@{me.username} is starting...")

        # ২. ইউজার সেশন চেক ও স্টার্ট
        session_string = os.environ.get("USER_SESSION")
        if session_string:
            try:
                self.user = Client(
                    name="dynamic_user",
                    api_id=Config.API_ID,
                    api_hash=Config.API_HASH,
                    session_string=session_string,
                    in_memory=True
                )
                await self.user.start()
                logging.info("Userbot started successfully!")
            except Exception as e:
                # সেশন ভুল থাকলে শুধু এরর দেখাবে, বট ক্র্যাশ করবে না
                logging.error(f"Userbot Session Error: {e}")
                self.user = None 
        
        logging.info(f"@{me.username} is now 24/7 Online.")

    async def stop(self, *args):
        # ক্যানসেল বা স্টপ মেসেজ পাঠানো
        stop_text = "**🔴 বটটি বর্তমানে অফলাইন করা হয়েছে।**"
        try:
            # টার্গেট চ্যানেলে (যদি কনফিগার করা থাকে)
            if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
                await self.send_message(Config.LOG_CHANNEL, stop_text)
            
            # ডাটাবেসে থাকা ইউজারদের জানানো
            users = await db.get_all_frwd()
            async for user in users:
                try: await self.send_message(user['user_id'], stop_text)
                except: continue
        except:
            pass

        if self.user and self.user.is_connected:
            await self.user.stop() 
        
        if self.is_connected:
            await super().stop()
        logging.info("Bot Stopped.")
