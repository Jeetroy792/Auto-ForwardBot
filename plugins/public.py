import re
import asyncio 
from .utils import STS
from database import db
from config import temp 
from translation import Translation
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait 
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate as PrivateChat
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified, ChannelPrivate
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
# আগের ইম্পোর্টগুলো ঠিক থাকবে...

@Client.on_callback_query(filters.regex(r'^start_public_'))
async def start_public(bot, query):
    _, _, forward_id = query.data.split("_")
    data = await STS(forward_id).get()
    if not data:
        return await query.message.edit("<b>❌ Error: Data not found.</b>")
    
    chat_id, toid, target_count, last_msg_id = data
    await query.message.edit("<b>🚀 Forwarding started...</b>")
    
    success, failed = 0, 0
    processed_ids = set() # ডুপ্লিকেট রোধ করার জন্য ট্র্যাকার

    try:
        if not bot.user.is_connected:
            await bot.user.start()

        # limit ব্যবহার করা হয়েছে যাতে অতিরিক্ত মেসেজ না আসে
        async for message in bot.user.get_chat_history(chat_id, limit=int(target_count), reverse=True):
            
            # ডুপ্লিকেট চেক: একই আইডি দ্বিতীয়বার আসবে না
            if message.id in processed_ids:
                continue
            
            # ক্যানসেল চেক
            if hasattr(bot, 'is_cancelled') and bot.is_cancelled:
                bot.is_cancelled = False
                await query.message.edit("<b>❌ Process Cancelled!</b>")
                return

            if not message or message.service or message.empty:
                continue
            
            try:
                await message.copy(chat_id=toid)
                processed_ids.add(message.id) # আইডি সেভ করে রাখা হলো
                success += 1
                await asyncio.sleep(2) 
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
                await message.copy(chat_id=toid)
                success += 1
            except Exception:
                failed += 1
                
            if (success + failed) % 10 == 0:
                try:
                    await query.message.edit(f"<b>📊 Progress:</b>\n✅ Success: {success}\n❌ Failed: {failed}")
                except:
                    pass
                
        await query.message.edit(f"<b>✅ Forwarding Completed!</b>\n\nTotal Unique Messages: {success}")
        
    except Exception as e:
        await query.message.edit(f"<b>❌ Error: {e}</b>")
      
#===================Run Function===================#

@Client.on_message(filters.private & filters.command(["fwd", "forward"]))
async def run(bot, message):
    user_id = message.from_user.id
    _bot = await db.get_bot(user_id)
    if not _bot:
        return await message.reply("<code>You haven't added any bot. Please add a bot using /settings !</code>")
    
    channels = await db.get_user_channels(user_id)
    if not channels:
        return await message.reply_text("Please set a 'To' channel in /settings before forwarding.")
    
    toid = channels[0]['chat_id']
    to_title = channels[0]['title']
    
    if len(channels) > 1:
        buttons = [[KeyboardButton(f"{c['title']}")] for c in channels]
        buttons.append([KeyboardButton("cancel")])
        _toid = await bot.ask(message.chat.id, Translation.TO_MSG.format(_bot['name'], _bot['username']), reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
        if _toid.text.lower() == 'cancel' or _toid.text.startswith('/'):
            return await message.reply_text(Translation.CANCEL, reply_markup=ReplyKeyboardRemove())
        
        toid = next((c['chat_id'] for c in channels if c['title'] == _toid.text), None)
        if not toid:
            return await message.reply_text("Wrong channel chosen!", reply_markup=ReplyKeyboardRemove())
        to_title = _toid.text

    fromid = await bot.ask(message.chat.id, Translation.FROM_MSG, reply_markup=ReplyKeyboardRemove())
    if fromid.text and fromid.text.startswith('/'):
        return await message.reply(Translation.CANCEL)
    
    chat_id, last_msg_id = None, None
    if fromid.text:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(fromid.text.replace("?single", ""))
        if match:
            chat_id = match.group(4)
            last_msg_id = int(match.group(5))
            if chat_id.isnumeric():
                chat_id = int(("-100" + chat_id))
    
    if not chat_id:
        return await message.reply_text("**Invalid Link! Please send a valid message link.**")

    skip_msg = await bot.ask(message.chat.id, Translation.SKIP_MSG)
    if skip_msg.text.startswith('/'):
        return await message.reply(Translation.CANCEL)

    forward_id = f"{user_id}-{skip_msg.id}"
    buttons = [[
        InlineKeyboardButton('Yes', callback_data=f"start_public_{forward_id}"),
        InlineKeyboardButton('No', callback_data="close_btn")
    ]]
    
    await message.reply_text(
        text=f"<b>Ready to Forward?</b>\n\nFrom Chat: {chat_id}\nTo Chat: {to_title}\nTotal Messages: {skip_msg.text}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await STS(forward_id).store(chat_id, toid, int(skip_msg.text), int(last_msg_id))

#==================Callback Handler (Final Fix)==================#

@Client.on_callback_query(filters.regex(r'^start_public_'))
async def start_public(bot, query):
    _, _, forward_id = query.data.split("_")
    data = await STS(forward_id).get()
    if not data:
        return await query.message.edit("<b>❌ Error: Data not found.</b>")
    
    chat_id, toid, target_count, last_msg_id = data
    await query.message.edit("<b>🚀 Forwarding started...</b>")
    
    success, failed = 0, 0
    
    try:
        # Client Not Started Error Fix
        if not bot.user.is_connected:
            await bot.user.start()

        # Sequence Fix (reverse=True) and Limit Fix
        async for message in bot.user.get_chat_history(chat_id, limit=int(target_count), reverse=True):
            
            # Cancel Check
            if hasattr(bot, 'is_cancelled') and bot.is_cancelled:
                bot.is_cancelled = False
                await query.message.edit("<b>❌ Process Cancelled!</b>")
                return

            if not message or message.service or message.empty:
                continue
            
            try:
                await message.copy(chat_id=toid)
                success += 1
                await asyncio.sleep(2) 
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
                await message.copy(chat_id=toid)
                success += 1
            except Exception:
                failed += 1
                
            if (success + failed) % 10 == 0:
                try:
                    await query.message.edit(f"<b>📊 Progress:</b>\n✅ Success: {success}\n❌ Failed: {failed}")
                except:
                    pass
                
        await query.message.edit(f"<b>✅ Forwarding Completed!</b>\n\nTotal Success: {success}")
        
    except Exception as e:
        await query.message.edit(f"<b>❌ Final Error: {e}</b>")
