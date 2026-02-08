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
    # SimpleNamespace বা dict হ্যান্ডলিং
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
    
    source_chat = await sts.get("FROW") # FROW used in your STS class
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
        
        # সংশোধিত ফেচিং লজিক (iter_messages এর বদলে get_chat_history)
        async for msg in auth_client.get_chat_history(
            chat_id=source_chat, 
            limit=int(await sts.get('last_msg_id')),
            offset_id=int(await sts.get('skip')) if await sts.get('skip') else 0
        ):
            if await is_cancelled(client, user, m, sts):
               return
            if pling % 20 == 0: 
               await edit(m, 'Progressing', 10, sts)
            pling += 1
            await sts.add('fetched')
            
            if not msg or msg.service or msg.empty:
               await sts.add('deleted')
               continue

            if forward_tag:
               MSG.append(msg.id)
               if len(MSG) >= 50: # Batch forwarding
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
               
        # Remaining messages
        if MSG:
            await forward(client, MSG, m, sts, protect)
            await sts.add('total_files', len(MSG))

    except Exception as e:
        await msg_edit(m, f'<b>ERROR:</b>\n<code>{e}</code>', wait=True)
    finally:
        if target_chat in temp.IS_FRWD_CHAT:
            temp.IS_FRWD_CHAT.remove(target_chat)
        await send(client, user, "<b>🎉 𝙵𝙾𝚁𝚆𝙰𝚁𝙳𝙸𝙽𝙶 𝙲𝙾𝙼𝙿𝙻𝙴𝚃𝙴𝙳</b>")
        await edit(m, 'Completed', "completed", sts) 
        await stop(client, user)

# ... (বাকি ফাংশনগুলো copy, forward, edit ইত্যাদি আপনার আগের কোডেই ঠিক আছে)
