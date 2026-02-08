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
            name="dynamic_bot", 
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            plugins={"root": "plugins"},
            workers=100, # দ্রুত কাজের জন্য বাড়ানো হয়েছে
            bot_token=Config.BOT_TOKEN,
            in_memory=True 
        )
        self.user = Client(
            name="dynamic_user", 
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=os.environ.get("USER_SESSION"), 
            in_memory=True 
        )

    async def start(self):
        try:
            await super().start()
            if self.user:
                await self.user.start()
            
            me = await self.get_me()
            self.id = me.id
            self.username = me.username
            
            logging.info(f"@{me.username} is now 24/7 Online!")
            
            # ডাটাবেসের ইউজারদের নোটিফাই করা (ঐচ্ছিক)
            text = "**๏[-ิ_•ิ]๏ Bot is back Online & Stable!**"
            users = await db.get_all_frwd()
            async for user in users:
                try:
                    await self.send_message(user['user_id'], text)
                except:
                    continue

        except Exception as e:
            logging.error(f"Error while starting: {e}")
            await asyncio.sleep(5) # ৫ সেকেন্ড অপেক্ষা করে আবার চেষ্টা করবে
            return await self.start()

    async def stop(self, *args):
        # অফলাইন হওয়ার সময় যাতে কোনো মেসেজ না যায় (যেহেতু আপনি অফলাইন চান না)
        if self.user.is_connected:
            await self.user.stop() 
        await super().stop()
        logging.info("Bot Stopped Temporarily.")

