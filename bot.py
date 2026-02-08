import os
import asyncio
import logging 
import logging.config
from database import db 
from config import Config  
from pyrogram import Client, __version__
from pyrogram.raw.all import layer 
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait 

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
        await super().start()
        await self.user.start() 
        me = await self.get_me()
        logging.info(f"{me.first_name} started on @{me.username}.")
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)
        
        text = "**๏[-ิ_•ิ]๏ bot restarted !**"
        
        # টার্গেট চ্যানেলে রিস্টার্ট মেসেজ পাঠানো
        if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
            await self.send_message(Config.LOG_CHANNEL, text)
            
        success = failed = 0
        users = await db.get_all_frwd()
        async for user in users:
           chat_id = user['user_id']
           try:
              await self.send_message(chat_id, text)
              success += 1
           except FloodWait as e:
              await asyncio.sleep(e.value + 1)
              await self.send_message(chat_id, text)
              success += 1
           except Exception:
              failed += 1 
              
        if (success + failed) != 0:
           await db.rmve_frwd(all=True)
           logging.info(f"Restart message status success: {success} failed: {failed}")

    async def stop(self, *args):
        # বন্ধ হওয়ার সময় মেসেজ পাঠানো
        shutdown_msg = "**🔴 Bot is going Offline!**"
        try:
            if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
                await self.send_message(Config.LOG_CHANNEL, shutdown_msg)
        except:
            pass
            
        if self.user.is_connected:
            await self.user.stop() 
        await super().stop()
        logging.info("Bot Stopped.")
