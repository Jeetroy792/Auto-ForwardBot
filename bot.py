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
            except Exception as e:
                logging.error(f"Userbot Error: {e}")

        # ৩. সামান্য অপেক্ষা করা যাতে কানেকশন স্ট্যাবল হয়
        await asyncio.sleep(2)

        me = await self.get_me()
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        
        text = "**๏[-ิ_•ิ]๏ Bot is now Online!**"
        
        # ৪. সুরক্ষিতভাবে ব্রডকাস্ট করা
        if self.is_connected:
            try:
                users = await db.get_all_frwd()
                async for user in users:
                    try:
                        if isinstance(user, dict):
                            chat_id = user.get('user_id')
                        else:
                            chat_id = getattr(user, 'user_id', None) or getattr(user, 'id', None)

                        if chat_id:
                            await self.send_message(chat_id, text)
                    except Exception:
                        continue
            except Exception as e:
                logging.error(f"Broadcast Error: {e}")

        logging.info(f"{me.first_name} started on @{me.username}.")

    async def stop(self, *args):
        # বন্ধ হওয়ার আগে চেক করে মেসেজ পাঠানো
        if self.is_connected:
            try:
                stop_text = "**🔴 বটটি বর্তমানে অফলাইন করা হয়েছে।**"
                if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
                    await self.send_message(Config.LOG_CHANNEL, stop_text)
            except:
                pass

        if self.user and self.user.is_connected:
            await self.user.stop() 
        if self.is_connected:
            await super().stop()
        logging.info("Bot Stopped.")
