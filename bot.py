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
        # Userbot Client Initialization
        self.user = Client(
            name="main_user_session", 
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=os.environ.get("USER_SESSION"), 
            in_memory=True 
        )

    async def start(self):
        # ১. মেইন বট কানেক্ট করা
        if not self.is_connected:
            await super().start()
        
        # ২. ইউজারবট কানেক্ট করা (সেশন ভুল থাকলেও বট চলবে)
        if self.user and not self.user.is_connected:
            try:
                await self.user.start()
                logging.info("Userbot started successfully!")
            except Exception as e:
                logging.error(f"Userbot Error: {e}")

        me = await self.get_me()
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)
        
        text = "**๏[-ิ_•ิ]๏ Bot is now Online!**"
        
        # ৩. ডাটাবেস থেকে ইউজারদের মেসেজ পাঠানো (Attribute Error Fix)
        try:
            users = await db.get_all_frwd()
            async for user in users:
                try:
                    # ডিকশনারি বা অবজেক্ট থেকে আইডি বের করার নিরাপদ পদ্ধতি
                    if isinstance(user, dict):
                        chat_id = user.get('user_id')
                    else:
                        chat_id = getattr(user, 'user_id', None) or getattr(user, 'id', None)

                    if chat_id:
                        await self.send_message(chat_id, text)
                except Exception:
                    continue
        except Exception as e:
            logging.error(f"Database Broadcast Error: {e}")

        logging.info(f"{me.first_name} (Layer {layer}) started on @{me.username}.")

    async def stop(self, *args):
        # বন্ধ হওয়ার সময় নোটিফিকেশন
        stop_text = "**🔴 বটটি বর্তমানে অফলাইন করা হয়েছে।**"
        try:
            # টার্গেট চ্যানেলে (যদি কনফিগার করা থাকে)
            if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
                await self.send_message(Config.LOG_CHANNEL, stop_text)
            
            # ডাটাবেসে থাকা ইউজারদের জানানো
            users = await db.get_all_frwd()
            async for user in users:
                try:
                    chat_id = user.get('user_id') if isinstance(user, dict) else getattr(user, 'user_id', None)
                    if chat_id:
                        await self.send_message(chat_id, stop_text)
                except: continue
        except: pass

        # প্রপারলি ক্লায়েন্টগুলো বন্ধ করা
        if self.user and self.user.is_connected:
            await self.user.stop() 
        if self.is_connected:
            await super().stop()
        logging.info("Bot Stopped.")
