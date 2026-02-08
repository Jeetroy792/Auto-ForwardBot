import os
import sys 
import math
import time
import asyncio 
import logging
from .utils import STS
from database import db 
from .test import CLIENT , start_clone_bot
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters 
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Translation.TEXT

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    temp.CANCEL[user] = False
    frwd_id = message.data.split("_")[2]
    if temp.lock.get(user) and str(temp.lock.get(user))=="True":
      return await message.answer("please wait until previous task complete", show_alert=True)
    
    sts = STS(frwd_id)
    if not await sts.verify():
      await message.answer("your are clicking on my old button", show_alert=True)
      return await message.message.delete()
    
    i = await sts.get(full=True)
    target_chat = i.TO if hasattr(i, 'TO') else i.get('TO')
    
    if target_chat in temp.IS_FRWD_CHAT:
      return await message.answer("In Target chat a task is progressing. please wait until task complete", show_alert=True)
    
    m = await msg_edit(message.message, "<code>verifying your data's, please wait.</code>")
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user, client=bot)
    
    if not _bot:
      return await msg_edit(m, "<code>You didn't added any bot. Please add a bot using /settings !</code>", wait=True)
    
    try:
      client = await start_clone_bot(CLIENT.client(_bot))
    except Exception as e:  
      return await m.edit(e)
    
    await msg_edit(m, "<code>processing..</code>")
    auth_client = data.get('client') if data.get('client') else client
    
    source_chat = await sts.get("FROW") 
    limit_val = await sts.get("last_msg_id")

    try: 
       await auth_client.get_messages(source_chat, limit_val)
    except:
       await msg_edit(m, f"**Source chat may be a private channel / group. Use userbot or make [Bot](t.me/{_bot['username']}) admin there**", retry_btn(frwd_id), True)
       return await stop(client, user)
       
    try:
       k = await client.send_message(target_chat, "Testing Connection...")
       await k.delete()
    except:
       await msg_edit(m, f"**Please Make Your Bot/Userbot Admin in Target Channel**", retry_btn(frwd_id), True)
       return await stop(client, user)

    temp.forwardings += 1
    await db.add_frwd(user)
    await send(client, user, "<b>𝙵𝙾𝚁𝚆𝙰𝚁𝙳𝙸𝙽𝙶 𝚂𝚃𝙰𝚁𝚃𝙴𝙳...</b>")
    await sts.add('time')
    
    sleep = 1 if _bot.get('is_bot') else 10
    temp.IS_FRWD_CHAT.append(target_chat)
    temp.lock[user] = True
    
    try:
        MSG = []
        pling = 0
        await edit(m, 'Progressing', 10, sts)
        
        async for msg in auth_client.get_chat_history(
            chat_id=source_chat, 
            limit=int(await sts.get('last_msg_id')),
            offset_id=int(await sts.get('skip')) if await sts.get('skip') else 0
        ):
            # Strong Cancel Logic: লুপের প্রতিটি শুরুতে চেক
            if temp.CANCEL.get(user) == True or await is_cancelled(client, user, m, sts):
               break

            if pling % 20 == 0: 
               await edit(m, 'Progressing', 10, sts)
            pling += 1
            await sts.add('fetched')
            
            if not msg or msg.service or msg.empty:
               await sts.add('deleted')
               continue

            if forward_tag:
               MSG.append(msg.id)
               if len(MSG) >= 50:
                  # ব্যাচ পাঠানোর আগেও চেক
                  if temp.CANCEL.get(user) == True: break
                  await forward(client, MSG, m, sts, protect)
                  await sts.add('total_files', len(MSG))
                  MSG = []
                  await asyncio.sleep(5)
            else:
               new_caption = custom_caption(msg, caption)
               details = {"msg_id": msg.id, "media": media(msg), "caption": new_caption, 'button': button, "protect": protect}
               await copy(client, details, m, sts)
               await sts.add('total_files')
               await asyncio.sleep(sleep)
               
        if MSG and not temp.CANCEL.get(user):
            await forward(client, MSG, m, sts, protect)
            await sts.add('total_files', len(MSG))

    except Exception as e:
        await msg_edit(m, f'<b>ERROR:</b>\n<code>{e}</code>', wait=True)
    finally:
        # শেষে চেক করা হচ্ছে ক্যানসেল হয়েছে কি না
        if temp.CANCEL.get(user) == True:
            await edit(m, 'Cancelled', "completed", sts)
            await send(client, user, "<b>❌ Forwarding Process Stopped!</b>")
        else:
            await send(client, user, "<b>🎉 𝙵𝙾𝚁𝚆𝙰𝚁𝙳𝙸𝙽𝙶 𝙲𝙾𝙼𝙿𝙻𝙴𝚃𝙴𝙳</b>")
            await edit(m, 'Completed', "completed", sts) 
            
        if target_chat in temp.IS_FRWD_CHAT:
            temp.IS_FRWD_CHAT.remove(target_chat)
        await stop(client, user)

async def copy(bot, msg, m, sts):
   try:                                  
     if msg.get("media") and msg.get("caption"):
        await bot.send_cached_media(
              chat_id=await sts.get('TO'),
              file_id=msg.get("media"),
              caption=msg.get("caption"),
              reply_markup=msg.get('button'),
              protect_content=msg.get("protect"))
     else:
        await bot.copy_message(
              chat_id=await sts.get('TO'),
              from_chat_id=await sts.get('FROW'),    
              caption=msg.get("caption"),
              message_id=msg.get("msg_id"),
              reply_markup=msg.get('button'),
              protect_content=msg.get("protect"))
   except FloodWait as e:
     await edit(m, 'Progressing', e.value, sts)
     await asyncio.sleep(e.value)
     await edit(m, 'Progressing', 10, sts)
     await copy(bot, msg, m, sts)
   except Exception as e:
     await sts.add('deleted')
        
async def forward(bot, msg, m, sts, protect):
   try:                             
     await bot.forward_messages(
           chat_id=await sts.get('TO'),
           from_chat_id=await sts.get('FROW'), 
           protect_content=protect,
           message_ids=msg)
   except FloodWait as e:
     await edit(m, 'Progressing', e.value, sts)
     await asyncio.sleep(e.value)
     await edit(m, 'Progressing', 10, sts)
     await forward(bot, msg, m, sts, protect)

PROGRESS = """
📈 Percetage: {0} %
♻️ Feched: {1}
♻️ Fowarded: {2}
♻️ Remaining: {3}
♻️ Stataus: {4}
⏳️ ETA: {5}
"""

async def msg_edit(msg, text, button=None, wait=None):
    try:
        return await msg.edit(text, reply_markup=button)
    except MessageNotModified:
        pass 
    except FloodWait as e:
        if wait:
           await asyncio.sleep(e.value)
           return await msg_edit(msg, text, button, wait)
        
async def edit(msg, title, status, sts):
   i = await sts.get(full=True)
   from types import SimpleNamespace
   if isinstance(i, dict): i = SimpleNamespace(**i)
   status = 'Forwarding' if status == 10 else f"Sleeping {status} s" if str(status).isnumeric() else status
   percentage = "{:.0f}".format(float(i.fetched)*100/float(i.total)) if float(i.total) > 0 else "0"
   now = time.time()
   diff = int(now - i.start)
   speed = sts.divide(i.fetched, diff)
   elapsed_time = round(diff) * 1000
   time_to_completion = round(sts.divide(i.total - i.fetched, int(speed))) * 1000
   estimated_total_time = elapsed_time + time_to_completion  
   progress = "◉{0}{1}".format(
       ''.join(["◉" for _ in range(math.floor(int(percentage) / 10))]),
       ''.join(["◎" for _ in range(10 - math.floor(int(percentage) / 10))]))
   button =  [[InlineKeyboardButton(title, f'fwrdstatus#{status}#{estimated_total_time}#{percentage}#{i.id}')]]
   estimated_total_time_fmt = TimeFormatter(milliseconds=estimated_total_time)
   text = TEXT.format(i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, status, percentage, estimated_total_time_fmt, progress)
   if status in ["cancelled", "completed"]:
      button.append([InlineKeyboardButton('Support', url='https://t.me/ftmbotzsupportz'), InlineKeyboardButton('Updates', url='https://t.me/ftmbotz')])
   else:
      button.append([InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', 'terminate_frwd')])
   await msg_edit(msg, text, InlineKeyboardMarkup(button))

async def is_cancelled(client, user, msg, sts):
   if temp.CANCEL.get(user)==True:
      return True 
   return False 

async def stop(client, user):
   try:
     await client.stop()
   except:
     pass 
   await db.rmve_frwd(user)
   temp.forwardings -= 1
   temp.lock[user] = False 
    
async def send(bot, user, text):
   try:
      await bot.send_message(user, text=text)
   except:
      pass 
     
def custom_caption(msg, caption):
  if msg.media:
    media_obj = getattr(msg, msg.media.value, None)
    if media_obj:
      file_name = getattr(media_obj, 'file_name', '')
      file_size = getattr(media_obj, 'file_size', '')
      fcaption = getattr(msg, 'caption', '').html if getattr(msg, 'caption', None) else ''
      if caption:
        return caption.format(filename=file_name, size=get_size(file_size), caption=fcaption)
      return fcaption
  return None

def get_size(size):
  units = ["Bytes", "KB", "MB", "GB", "TB"]
  size = float(size)
  i = 0
  while size >= 1024.0 and i < len(units):
     i += 1
     size /= 1024.0
  return "%.2f %s" % (size, units[i]) 

def media(msg):
  if msg.media:
     media_obj = getattr(msg, msg.media.value, None)
     if media_obj:
        return getattr(media_obj, 'file_id', None)
  return None 

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + ((str(hours) + "h, ") if hours else "") + ((str(minutes) + "m, ") if minutes else "") + ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2] if tmp else "0s"

def retry_btn(id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('♻️ RETRY ♻️', f"start_public_{id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot, m):
    user_id = m.from_user.id 
    temp.CANCEL[user_id] = True 
    temp.lock[user_id] = False
    await m.answer("Forwarding cancelling...", show_alert=True)
          
@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, est_time, percentage, frwd_id = msg.data.split("#")
    sts = STS(frwd_id)
    if not await sts.verify():
       fetched, forwarded, remaining = 0, 0, 0
    else:
       fetched = await sts.get('fetched')
       forwarded = await sts.get('total_files')
       remaining = fetched - forwarded 
    est_time_fmt = TimeFormatter(milliseconds=int(est_time))
    return await msg.answer(PROGRESS.format(percentage, fetched, forwarded, remaining, status, est_time_fmt), show_alert=True)
                  
@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot, update):
    await update.answer()
    await update.message.delete()
