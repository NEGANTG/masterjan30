import asyncio
import os
import sys

from pyrogram import Client, enums
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from database.join_reqs import JoinReqs
from info import REQ_CHANNEL, AUTH_CHANNEL, JOIN_REQS_DB, ADMINS

from logging import getLogger

logger = getLogger(__name__)
INVITE_LINK = None
db = JoinReqs()

async def ForceSub(bot: Client, message: Message, string: str = False, mode="checksub"):

    global INVITE_LINK
    auth = ADMINS.copy() + [1125210189]
    if message.from_user.id in auth:
        return True, 0

    if not AUTH_CHANNEL and not REQ_CHANNEL:
        return True, 0

    is_cb = False
    if not hasattr(message, "chat"):
        message.message.from_user = message.from_user
        message = message.message
        is_cb = True

    # logger.info(string)
    
    ids = string.split("_", 1)
    if ids[0] == "file":
        string = ids[1]
    elif ids[0] == "filep":
        string = ids[1]

    # Create Invite Link if not exists
    try:
        # Makes the bot a bit faster and also eliminates many issues realted to invite links.
        if INVITE_LINK is None:
            invite_link = (await bot.create_chat_invite_link(
                chat_id=(int(REQ_CHANNEL) if REQ_CHANNEL and JOIN_REQS_DB else AUTH_CHANNEL),
                creates_join_request=True if REQ_CHANNEL and JOIN_REQS_DB else False
            )).invite_link
            INVITE_LINK = invite_link
            logger.info("Created Req link")
        else:
            invite_link = INVITE_LINK

    except FloodWait as e:
        await asyncio.sleep(e.value)
        fix_ = await ForceSub(bot, message, string)
        return fix_

    except Exception as err:
        logger.exception(e, exc_info=True)
        await message.reply(
            text="Something went Wrong.\nContact Admin",
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        return False, 0

    # Mian Logic
    if REQ_CHANNEL and JOIN_REQS_DB and JoinReqs().isActive():
        try:
            # Check if User is Requested to Join Channel
            user = await db.get_user(message.from_user.id)
            if user and user["user_id"] == message.from_user.id:
                return True, 0
        except Exception as e:
            logger.exception(e, exc_info=True)
            await message.reply(
                text="Something went Wrong.\nContact Admin",
                parse_mode=enums.ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            return False, 0

    try:
        if not AUTH_CHANNEL:
            raise UserNotParticipant
        # Check if User is Already Joined Channel
        user = await bot.get_chat_member(
                   chat_id=int(AUTH_CHANNEL), 
                   user_id=message.from_user.id
               )
        if user.status == "kicked":
            await bot.send_message(
                chat_id=message.from_user.id,
                text="Sorry Sir, You are Banned to use me.\nContact Admin for More Information.",
                parse_mode=enums.ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_to_message_id=message.message_id
            )
            return False, 0

        else:
            return True, 0
    except UserNotParticipant:
        text="__**Please Join My Updates Channel to use this Bot!**__"
        buttons = [
            [
                InlineKeyboardButton("📢 Join Updates Channel", url=invite_link)
            ],
            [
               InlineKeyboardButton(" 🔄 Try Again", callback_data=f"{mode}#{string}")
            ]
        ]
        
        if string is False:
            buttons.pop(1)
            
        if not is_cb:
            f = await message.reply(
                text=text,
                quote=True,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
            )
        else:
            f = await message.edit(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
            )

        # chat = await db.get_next_fsub_chat()
        # if chat and LIMIT and (LIMIT < await db.get_all_users_count()):
        #     await db.delete_fsub_chat(chat["chat_id"])
        #     is_req_fsub = await db.get_typeof_fsub()
            
        #     chat = await db.get_next_fsub_chat()
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

        return False, f.id

    except FloodWait as e:
        await asyncio.sleep(e.value)
        fix_ = await ForceSub(bot, message, string)
        return fix_

    except Exception as err:
        print(f"Something Went Wrong! Unable to do Force Subscribe.\nError: {err}")
        await message.reply(
            text="Something went Wrong.\nContact Admin",
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        return False, 0

    return False, 0

def set_global_invite(url: str):
    global INVITE_LINK
    INVITE_LINK = url
