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
 
#===================Run Function===================#

@Client.on_message(filters.private & filters.command(["fwd", "forward"]))
async def run(bot, message):
    buttons = []
    btn_data = {}
    user_id = message.from_user.id
    _bot = await db.get_bot(user_id)
    if not _bot:
      return await message.reply("<code>You didn't added any bot. Please add a bot using /settings !</code>")
    channels = await db.get_user_channels(user_id)
    if not channels:
       return await message.reply_text("please set a to channel in /settings before forwarding")
    if len(channels) > 1:
       for channel in channels:
          buttons.append([KeyboardButton(f"{channel['title']}")])
          btn_data[channel['title']] = channel['chat_id']
       buttons.append([KeyboardButton("cancel")]) 
       _toid = await bot.ask(message.chat.id, Translation.TO_MSG.format(_bot['name'], _bot['username']), reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
       if _toid.text.startswith(('/', 'cancel')):
          return await message.reply_text(Translation.CANCEL, reply_markup=ReplyKeyboardRemove())
       to_title = _toid.text
       toid = btn_data.get(to_title)
       if not toid:
          return await message.reply_text("wrong channel choosen !", reply_markup=ReplyKeyboardRemove())
    else:
       toid = channels[0]['chat_id']
       to_title = channels[0]['title']
    fromid = await bot.ask(message.chat.id, Translation.FROM_MSG, reply_markup=ReplyKeyboardRemove())
    if fromid.text and fromid.text.startswith('/'):
        await message.reply(Translation.CANCEL)
        return 
    if fromid.text and not fromid.forward_date:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(fromid.text.replace("?single", ""))
        if not match:
            return await message.reply('Invalid link')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    elif fromid.forward_from_chat.type in [enums.ChatType.CHANNEL]:
        last_msg_id = fromid.forward_from_message_id
        chat_id = fromid.forward_from_chat.username or fromid.forward_from_chat.id
        if last_msg_id == None:
           return await message.reply_text("**Invalid forward message! Use last message link.**")
    else:
        await message.reply_text("**invalid !**")
        return 
    try:
        title = (await bot.get_chat(chat_id)).title
    except (PrivateChat, ChannelPrivate, ChannelInvalid):
        title = "private" if fromid.text else fromid.forward_from_chat.title
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        return await message.reply(f'Errors - {e}')
    skipno = await bot.ask(message.chat.id, Translation.SKIP_MSG)
    if skipno.text.startswith('/'):
        await message.reply(Translation.CANCEL)
        return
    forward_id = f"{user_id}-{skipno.id}"
    buttons = [[
        InlineKeyboardButton('Yes', callback_data=f"start_public_{forward_id}"),
        InlineKeyboardButton('No', callback_data="close_btn")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text(
        text=Translation.DOUBLE_CHECK.format(botname=_bot['name'], botuname=_bot['username'], from_chat=title, to_chat=to_title, skip=skipno.text),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )
    await STS(forward_id).store(chat_id, toid, int(skipno.text), int(last_msg_id))

#==================Callback Handler (Fixed)==================#

@Client.on_callback_query(filters.regex(r'^start_public_'))
async def start_public(bot, query):
    _, _, forward_id = query.data.split("_")
    data = await STS(forward_id).get()
    if not data:
        return await query.message.edit("<b>❌ Data not found! Please try again.</b>")
    
    chat_id, toid, target_count, last_msg_id = data
    await query.message.edit("<b>🚀 Forwarding started...</b>")
    
    success = 0
    failed = 0
    
    try:
        # এখানে limit=int(target_count) দেওয়া হয়েছে যাতে আপনি যা চেয়েছেন তার বেশি ফরওয়ার্ড না হয়
        async for message in bot.user.get_chat_history(chat_id, limit=int(target_count), reverse=True):
            
            # শক্তিশালী ক্যানসেল চেক
            if hasattr(bot, 'is_cancelled') and bot.is_cancelled:
                bot.is_cancelled = False
                await query.message.edit("<b>❌ Forwarding Process Cancelled!</b>")
                return

            if not message or message.service or message.empty:
                continue
            
            try:
                await message.copy(chat_id=toid)
                success += 1
                await asyncio.sleep(1.5) 
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await message.copy(chat_id=toid)
                success += 1
            except Exception:
                failed += 1
                
            if (success + failed) % 10 == 0:
                try:
                    await query.message.edit(f"<b>📊 Status:</b>\n✅ Success: {success}\n❌ Failed: {failed}")
                except:
                    pass
                
        await query.message.edit(f"<b>✅ Forwarding Completed!</b>\n\nTotal Success: {success}\nTotal Failed: {failed}")
        
    except Exception as e:
        await query.message.edit(f"<b>❌ Error: {e}</b>")
