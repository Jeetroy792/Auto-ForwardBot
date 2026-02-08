from pyrogram import Client, filters
from config import Config

@Client.on_message(filters.command("cancel") & filters.user(Config.BOT_OWNER_ID))
async def cancel_task_handler(client, message):
    # বটের গ্লোবাল ক্যানসেল সুইচটি অন করে দিবে
    client.is_cancelled = True 
    
    await message.reply_text(
        "**❌ ক্যানসেল করার অনুরোধ গ্রহণ করা হয়েছে!**\n"
        "বর্তমান ফরওয়ার্ডিং টাস্কটি থামানো হচ্ছে। অনুগ্রহ করে কয়েক সেকেন্ড অপেক্ষা করুন..."
    )
  
