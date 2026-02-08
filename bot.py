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

# Logging Configuration
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client): 
    def __init__(self):
        super().__init__(
            name="main_bot_session", 
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            plugins={"root": "plugins"},
            workers=50,
            bot_token=Config.BOT_TOKEN,
            in_memory=True 
        )
        self.log = logging
        self.user = Client(
            name="main_user_session", 
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=os.environ.get("USER_SESSION"), 
            in_memory=True 
        )

    async def start(self):
        # ১. মেইন বট স্টার্ট করা
        if not self.is_connected:
            await super().start()
        
        # ২. ইউজারবট স্টার্ট করা
        if self.user and not self.user.is_connected:
            try:
                await self.user.start()
                logging.info("Userbot started successfully!")
            except Exception as e:
                logging.error(f"Userbot Error: {e}")

        me = await self.get_me()
        self.id = me.id
        self.username = me.username
        
        text = "**๏[-ิ_•ิ]๏ Bot is now Online!**"
        
        # ৩. ডাটাবেস থেকে আইডি বের করার জন্য চূড়ান্ত নিরাপদ পদ্ধতি
        try:
            users = await db.get_all_frwd()
            async for user in users:
                try:
                    # এখানে ডিকশনারি এবং সিম্পল নেমস্পেস দুটোর জন্যই চেক আছে
                    chat_id = None
                    if isinstance(user, dict):
                        chat_id = user.get('user_id') or user.get('id')
                    else:
                        # অবজেক্ট হলেgetattr ব্যবহার করে ডাটা চেক করা
                        chat_id = getattr(user, 'user_id', None) or getattr(user, 'id', None)

                    if chat_id:
                        await self.send_message(int(chat_id), text)
                except Exception as e:
                    logging.debug(f"Broadcast skip for a user: {e}")
                    continue
        except Exception as e:
            logging.error(f"Broadcasting error on start: {e}")

        logging.info(f"@{me.username} is now 24/7 Online.")

    async def stop(self, *args):
        # বন্ধ হওয়ার সময় ক্যানসেল মেসেজ পাঠানো
        stop_text = "**🔴 অপারেশন ক্যানসেল করা হয়েছে এবং বট অফলাইন যাচ্ছে।**"
        try:
            # টার্গেট চ্যানেলে (যদি থাকে)
            if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
                await self.send_message(Config.LOG_CHANNEL, stop_text)
            
            # ডাটাবেসে থাকা ইউজারদের জানানো
            users = await db.get_all_frwd()
            async for user in users:
                try:
                    # আইডি বের করার সেফ মেথড
                    if isinstance(user, dict):
                        c_id = user.get('user_id') or user.get('id')
                    else:
                        c_id = getattr(user, 'user_id', None) or getattr(user, 'id', None)
                        
                    if c_id:
                        await self.send_message(int(c_id), stop_text)
                except: continue
        except: pass

        if self.user and self.user.is_connected:
            await self.user.stop() 
        if self.is_connected:
            await super().stop()
        logging.info("Bot Stopped.")
