#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) @AlbertEinsteinTG
import os
import sys

from logging import getLogger
from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest, Message, ChatMemberUpdated
from pyrogram.handlers import ChatJoinRequestHandler
from database.join_reqs import JoinReqs
from info import ADMINS, REQ_CHANNEL, AUTH_CHANNEL
from plugins.fsub import set_global_invite

db = JoinReqs
logger = getLogger(__name__)

@Client.on_chat_join_request(filters.chat(REQ_CHANNEL if REQ_CHANNEL else "self"))
async def join_reqs(bot: Client, join_req: ChatJoinRequest):

    if db().isActive():
        user_id = join_req.from_user.id
        first_name = join_req.from_user.first_name
        username = join_req.from_user.username
        date = join_req.date

        await db().add_user(
            user_id=user_id,
            first_name=first_name,
            username=username,
            date=date
        )
    
    # from plugins.commands import FILE_CACHE, send_file
    # if FILE_CACHE.get(join_req.from_user.id, False):
    #     file_id, pre, mid = FILE_CACHE[join_req.from_user.id]
    #     await send_file(bot, join_req, file_id, pre)
    #     FILE_CACHE.pop(join_req.from_user.id)
    #     await bot.delete_messages(
    #         join_req.from_user.id,
    #         mid
    #     )

    # dbi = db()

    # chat = await dbi.get_next_fsub_chat()
    # if chat and LIMIT and (LIMIT <= await dbi.get_all_users_count()):
    #     await dbi.delete_fsub_chat(chat["chat_id"])
    #     is_req_fsub = await dbi.get_typeof_fsub()
        
    #     chat = await dbi.get_next_fsub_chat()
    #     if chat:
    #         auth_channel = chat["chat_id"]
    #         limit = chat["limit"]
    #         req_channel = False
    #         if is_req_fsub:
    #             req_channel = chat["chat_id"]
    #     else:
    #         auth_channel = False
    #         req_channel = False
    #         limit = None

    #     with open("./dynamic.env", "wt+") as f:
    #         f.write(f"AUTH_CHANNEL={auth_channel}\nREQ_CHANNEL={req_channel}\nLIMIT={limit}\n")
            
    #     logger.info("Limit threshold passed, Restarting...!")
    #     try:
    #         os.remove("TelegramBot.txt")
    #     except:
    #         pass
    #     os.execl(sys.executable, sys.executable, "bot.py")


@Client.on_chat_member_updated(filters.chat(AUTH_CHANNEL if AUTH_CHANNEL else "self"))
async def joined_chat(bot: Client, update: ChatMemberUpdated):
    
    from plugins.commands import FILE_CACHE, send_file
    if FILE_CACHE.get(update.from_user.id, False):
        file_id, pre, mid = FILE_CACHE[update.from_user.id]
        await send_file(bot, update, file_id, pre)
        FILE_CACHE.pop(update.from_user.id)
        await bot.delete_messages(
            update.from_user.id,
            mid
        )


@Client.on_message(filters.command("addchats") & filters.user(ADMINS))
async def add_fsub_chats(bot: Client, update: Message):
    
    # chats = update.text.split(None)[1:]
    # if len(chats) > 1:
    #     chats = [int(chat) for chat in chats]
    # elif len(chats) == 1 and chats[0][1:].isalpha():
    #     if chats[0].lower() == "false":
    #         pass
    #     else:
    #         await update.reply_text("Invalid chat id.", quote=True)
    #         return
    # else:
    #     chats = [int(chats[0])]
    
    if len(update.command) > 2:
        chat_id, limit = update.command[1:]
    elif len(update.command) == 2:
        chat_id = update.command[1]
        limit = None
    else:
        await update.reply_text("Invalid chat id.", quote=True)
        return

    db = JoinReqs()
    await db.add_fsub_chat(chat_id, limit=limit)
    
    text = f"Added chat <code>{chat_id}</code> with limit <code>{limit}</code> to the database."
    await update.reply_text(text=text, quote=True, parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.command("viewchats") & filters.user(ADMINS))
async def view_fsub_chats(bot: Client, update: Message):
    
    db = JoinReqs()
    chats = await db.get_all_fsub_chats()
    text = f"**Total {len(chats)} chats in the database.**\n\n"
    for chat in chats:
        text += f"**Chat:** `{chat['chat_id']}`\tLimit: `{chat['limit']}`\n"
    
    await update.reply_text(text=text, quote=True)


@Client.on_message(filters.command("clearchats") & filters.user(ADMINS))
async def clear_fsub_chats(bot: Client, update: Message):
    
    db = JoinReqs()
    chats = await db.delete_all_fsub_chats()
    await update.reply_text(text="Cleared all fsub chats from the database.", quote=True)
    

@Client.on_message(filters.command("changechat") & filters.user(ADMINS))
async def change_chat(bot: Client, update: Message):
    
    db = JoinReqs()
    chat = await db.get_next_fsub_chat()
    if chat:
        if REQ_CHANNEL == chat["chat_id"] or AUTH_CHANNEL == chat["chat_id"]:
            await update.reply_text("Deleteing existing chat from db", quote=True)
            await db.delete_fsub_chat(chat["chat_id"])
            chat = await db.get_next_fsub_chat()

        if chat:
            # set_global_invite(None)
            is_req_fsub = await db.get_typeof_fsub()
            auth_channel = chat["chat_id"]
            limit = chat["limit"]
            req_channel = False
            if is_req_fsub:
                req_channel = chat["chat_id"]

            with open("./dynamic.env", "wt+") as f:
                f.write(f"AUTH_CHANNEL={auth_channel}\nREQ_CHANNEL={req_channel}\nLIMIT={limit}\n")
            
            await update.reply_text("Changed chat successfully.\nRestarting bot to make the changes...!", quote=True)
            try:
                os.remove("TelegramBot.txt")
            except:
                pass
            os.execl(sys.executable, sys.executable, "bot.py")
        return
        
    await update.reply_text("No chats in the database to change to.", quote=True)


@Client.on_message(filters.command("togglereq") & filters.user(ADMINS))
async def toggle_fsub_type(bot: Client, update: Message):
    
    key = update.text.split(None, 1)[1].lower()
    key = is_enabled(key, True)
    await db().toggle_req_normal_fsub(key)

    await update.reply_text(f"Changed fsub type to {'Req Type' if key else 'Normal Join'}.", quote=True)
    await update.reply("Restarting bot to make the changes...!")
    
    chat = await db().get_next_fsub_chat()
    if not chat:
        await update.reply_text("No chats in the database to change to.", quote=True)
        return
    
    with open("./dynamic.env", "wt+") as f:
        f.write(f"AUTH_CHANNEL={chat['chat_id']}\nREQ_CHANNEL={chat['chat_id'] if key else False}\nLIMIT={chat['limit']}\n")
    
    try:
        os.remove("TelegramBot.txt")
    except:
        pass
    os.execl(sys.executable, sys.executable, "bot.py")


@Client.on_message(filters.command("totalrequests") & filters.private & filters.user((ADMINS.copy() + [1125210189])))
async def total_requests(client, message):

    if db().isActive():
        total = await db().get_all_users_count()
        await message.reply_text(
            text=f"Total Requests: {total}",
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )


@Client.on_message(filters.command("purgerequests") & filters.private & filters.user(ADMINS))
async def purge_requests(client, message):
    
    if db().isActive():
        await db().delete_all_users()
        await message.reply_text(
            text="Purged All Requests.",
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )


def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y", "on", "req"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n", "off", "normal"]:
        return False
    else:
        return default

