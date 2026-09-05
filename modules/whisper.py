import uuid
import time
from pyrogram import Client
from pyrogram.types import (
    Message, InlineQuery, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent,
    CallbackQuery
)
from kaguya.types import BaseModule, ModuleInfo, on_command, on_assistant_inline, on_assistant_callback
from kaguya.utils.prefix import get_prefix


class WhisperModule(BaseModule):
    meta = ModuleInfo(
        name='Секретные сообщения',
        description='Секретные сообщения через инлайн-ассистента',
        version='1.0.0',
        author='cxvimba',
        commands={
            'w | whisper | шепот | шёпот': 'Отправить секрет (.w @user секрет или через инлайн @bot w @user текст)'
        }
    )

    LANGUAGES = {
        'en': {
            'usage': (
                '🤫 <b>Kaguya | Secret Messages</b>\n\n'
                '🛡 <b>100% protection from AyuGram and notifications:</b>'
                'Type in any chat:\n'
                '<code>@{bot_username} w @username Secret text</code>\n\n'
                '⚡️ <b>Via Userbot Command:</b>\n'
                '• <code>{p}w @username Secret text</code>\n'
                '• Reply to user: <code>{p}w Secret text</code>\n\n'
                '💡 <i>Limit: up to 170 characters.</i>'
            ),
            'assistant_required': (
                '⚙️ <b>Kaguya | Helper Bot</b>\n\n'
                'A secret message requires a linked assistant bot.\n'
                'Bind your bot using <code>{p}token YOUR_TOKEN</code>'
            ),
            'error_target_not_found': '❌ <b>Kaguya:</b> Failed to find target user: <code>{error}</code>',
            'error_no_text': '❌ <b>Kaguya:</b> Secret message text cannot be empty!',
            'error_too_long': '❌ <b>Kaguya:</b> Message is too long ({length}/170 chars). Telegram pop-up cannot fit it!',
            'error_self': '❌ <b>Kaguya:</b> You cannot send a secret message to yourself!',
            'error_bot': '❌ <b>Kaguya:</b> Bots cannot read secret messages!',
            'error_channel': '❌ <b>Kaguya:</b> Secret messages can only be sent to users, not channels.',
            'inline_failed': '❌ <b>Kaguya:</b> Assistant failed to generate the secret message.',
            'inline_title': '🤫 Send secret to {target}',
            'inline_desc': 'Secret text: {preview}',
            'inline_prompt_title': '🤫 Type a secret message',
            'inline_prompt_desc': 'Format: @{bot_username} w @username Secret text',
            'btn_open': '🔒 Open Secret',
            'btn_read': '🔓 Read',
            'status_unread': '<b>Awaiting read 🔒</b>',
            'status_read': '<b>Read at {time} ✅</b>',
            'msg_template': (
                '🤫 <b>Kaguya | Secret Message</b>\n'
                '<blockquote>To: <b>{target}</b>\n'
                'From: <b>{sender}</b>\n'
                'Status: {status}</blockquote>\n'
                '<i>Tap the button below to read the message.</i>'
            ),
            'alert_not_for_you': '💢 Kaguya: Hey, this secret message is not for you!',
            'alert_expired': '❌ Kaguya: This secret message has expired or was removed.',
            'alert_target_view': '🤫 Secret from {sender}:\n\n{text}',
            'alert_sender_view': '📨 Secret message to {target}:\n\n{text}\n\nStatus: {status}',
            'alert_status_unread': '🔒 Not read yet',
            'alert_status_read': '🔓 Read by recipient ({time})'
        },
        'ru': {
            'usage': (
                '🤫 <b>Kaguya | Секретные сообщения</b>\n\n'
                '🛡 <b>100% защита от AyuGram и уведомлений:</b>\n'
                'Пиши прямо в поле ввода любого чата:\n'
                '<code>@{bot_username} w @юзернейм Текст секрета</code>\n\n'
                '⚡️ <b>Через команду:</b>\n'
                '• <code>{p}w @юзернейм Текст секрета</code>\n'
                '• Ответом на сообщение: <code>{p}w Текст секрета</code>\n\n'
                '💡 <i>Лимит: до 170 символов (ограничение всплывающих окон Telegram).</i>'
            ),
            'assistant_required': (
                '⚙️ <b>Kaguya | Бот-ассистент</b>\n\n'
                'Для секретных сообщений нужен привязанный бот-помощник.\n'
                'Привяжи его через <code>{p}token ТВОЙ_ТОКЕН</code>'
            ),
            'error_target_not_found': '❌ <b>Kaguya:</b> Не удалось найти пользователя: <code>{error}</code>',
            'error_no_text': '❌ <b>Kaguya:</b> Текст секрета не может быть пустым!',
            'error_too_long': '❌ <b>Kaguya:</b> Текст слишком длинный ({length}/170 симв.). Всплывающее окно Telegram его не вместит!',
            'error_self': '❌ <b>Kaguya:</b> Нельзя отправить секрет самому себе!',
            'error_bot': '❌ <b>Kaguya:</b> Боты не умеют открывать секретные сообщения!',
            'error_channel': '❌ <b>Kaguya:</b> Секретное сообщение можно отправить только человеку, а не каналу.',
            'inline_failed': '❌ <b>Kaguya:</b> Ассистент не смог сформировать секрет.',
            'inline_title': '🤫 Отправить секрет для {target}',
            'inline_desc': 'Текст: {preview}',
            'inline_prompt_title': '🤫 Напишите секретное сообщение',
            'inline_prompt_desc': 'Формат: @{bot_username} w @юзернейм Текст секрета',
            'btn_open': '🔒 Открыть секрет',
            'btn_read': '🔓 Прочитано',
            'status_unread': '<b>Ожидает прочтения 🔒</b>',
            'status_read': '<b>Прочитано в {time} ✅</b>',
            'msg_template': (
                '🤫 <b>Kaguya | Секретное сообщение</b>\n'
                '<blockquote>Для: <b>{target}</b>\n'
                'От: <b>{sender}</b>\n'
                'Статус: {status}</blockquote>\n'
                '<i>Нажмите кнопку ниже, чтобы прочитать.</i>'
            ),
            'alert_not_for_you': '💢 Kaguya: Эй, это секретное сообщение не для тебя!',
            'alert_expired': '❌ Kaguya: Сообщение устарело или было удалено.',
            'alert_target_view': '🤫 Секрет от {sender}:\n\n{text}',
            'alert_sender_view': '📨 Секретное сообщение для {target}:\n\n{text}\n\nСтатус: {status}',
            'alert_status_unread': '🔒 Ещё не прочитано',
            'alert_status_read': '🔓 Прочитано получателем ({time})'
        }
    }

    @on_command(['w', 'whisper', 'шепот', 'шёпот'])
    async def create_whisper_cmd(self, client: Client, message: Message):
        """Создает и отправляет инлайн сообщение через команду юзербота."""
        p = get_prefix(client)
        if not client.assistant:
            await message.edit_text(self.get_text('assistant_required').format(p=p))
            return

        settings = client.db.get_category('settings')
        bot_username = await settings.get('bot_username')

        reply = message.reply_to_message
        target_user = None
        secret_text = ''
        if reply:
            if reply.sender_chat:
                await message.edit_text(self.get_text('error_channel'))
                return

            if reply.from_user:
                if len(message.command) >= 3 and (message.command[1].startswith('@') or message.command[1].isdigit()):
                    target_raw = message.command[1].strip()
                    secret_text = message.text.split(maxsplit=2)[2].strip()
                    try:
                        clean_id = int(target_raw.lstrip('@')) if target_raw.lstrip('@').isdigit() else target_raw
                        target_user = await client.get_users(clean_id)
                    except Exception as e:
                        await message.edit_text(self.get_text('error_target_not_found').format(error=e))
                        return
                else:
                    target_user = reply.from_user
                    if len(message.command) > 1:
                        secret_text = message.text.split(maxsplit=1)[1].strip()
        else:
            if len(message.command) < 3:
                await message.edit_text(self.get_text('usage').format(p=p, bot_username=bot_username))
                return

            target_raw = message.command[1].strip()
            secret_text = message.text.split(maxsplit=2)[2].strip()

            try:
                clean_id = int(target_raw.lstrip('@')) if target_raw.lstrip('@').isdigit() else target_raw
                target_user = await client.get_users(clean_id)
            except Exception as e:
                await message.edit_text(self.get_text('error_target_not_found').format(error=e))
                return

        if not target_user:
            await message.edit_text(self.get_text('usage').format(p=p, bot_username=bot_username))
            return
        if not secret_text:
            await message.edit_text(self.get_text('error_no_text'))
            return
        if target_user.id == client.me.id:
            await message.edit_text(self.get_text('error_self'))
            return
        if target_user.is_bot:
            await message.edit_text(self.get_text('error_bot'))
            return
        if len(secret_text) > 170:
            await message.edit_text(self.get_text('error_too_long').format(length=len(secret_text)))
            return

        w_key = str(uuid.uuid4())[:8]
        cache = client.db.get_category('whisper_cache')
        target_mention = f'@{target_user.username}' if target_user.username else target_user.first_name
        target_username = target_user.username.lower() if target_user.username else None
        sender_name = client.me.username or client.me.first_name or f'ID {client.me.id}'

        payload = {
            'sender_id': client.me.id,
            'sender_name': sender_name,
            'target_id': target_user.id,
            'target_username': target_username,
            'target_mention': target_mention,
            'text': secret_text,
            'is_read': False,
            'read_at': None
        }

        await cache.set(w_key, payload, expire=86400 * 7)

        results = await client.get_inline_bot_results(bot_username, f'w_{w_key}')
        if not results.results:
            await message.edit_text(self.get_text('inline_failed'))
            return

        await client.send_inline_bot_result(
            chat_id=message.chat.id,
            query_id=results.query_id,
            result_id=results.results[0].id,
            reply_to_message_id=reply.id if reply else None
        )
        await message.delete()

    @on_assistant_inline('w')
    async def whisper_inline(self, client: Client, inline_query: InlineQuery):
        """Обрабатывает инлайн-запросы"""
        query = inline_query.query.strip()
        cache = client.db.get_category('whisper_cache')
        if query.startswith('w_'):
            w_key = query[2:]
            payload = await cache.get(w_key)
            if not payload:
                return
        elif query.startswith(('w ', 'w@')):
            raw = query[2:].strip() if query.startswith('w ') else query[1:].strip()
            parts = raw.split(maxsplit=1)
            settings = client.db.get_category('settings')
            bot_username = await settings.get('bot_username')

            if len(parts) < 2:
                results = [
                    InlineQueryResultArticle(
                        id='w_prompt',
                        title=self.get_text('inline_prompt_title'),
                        description=self.get_text('inline_prompt_desc').format(bot_username=bot_username),
                        input_message_content=InputTextMessageContent(
                            self.get_text('usage').format(p='.', bot_username=bot_username)
                        )
                    )
                ]
                await inline_query.answer(results, cache_time=1)
                return

            target_raw = parts[0].strip()
            secret_text = parts[1].strip()

            target_id = None
            target_username = target_raw.lstrip('@').lower()
            if target_raw.lstrip('@').isdigit():
                target_id = int(target_raw.lstrip('@'))
            else:
                try:
                    user_obj = await client.get_users(target_raw)
                    target_id = user_obj.id
                    if user_obj.username:
                        target_username = user_obj.username.lower()
                except Exception:
                    pass

            sender = inline_query.from_user
            sender_name = sender.first_name or sender.username or 'Владелец'

            w_key = str(uuid.uuid4())[:8]
            payload = {
                'sender_id': sender.id,
                'sender_name': sender_name,
                'target_id': target_id,
                'target_username': target_username,
                'target_mention': target_raw,
                'text': secret_text[:170],
                'is_read': False,
                'read_at': None
            }
            await cache.set(w_key, payload, expire=86400 * 7)

        else:
            return

        markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    text=self.get_text('btn_open'),
                    callback_data=f'w_open_{w_key}')
                ]
            ]
        )

        text = self.get_text('msg_template').format(
            target=payload.get('target_mention', 'Собеседник'),
            sender=payload.get('sender_name', 'Владелец'),
            status=self.get_text('status_unread')
        )

        preview = payload['text'][:45] + '...' if len(payload['text']) > 45 else payload['text']
        results = [
            InlineQueryResultArticle(
                id=w_key,
                title=self.get_text('inline_title').format(target=payload.get('target_mention', 'User')),
                description=self.get_text('inline_desc').format(preview=preview),
                input_message_content=InputTextMessageContent(text),
                reply_markup=markup
            )
        ]
        await inline_query.answer(results, cache_time=1)

    @on_assistant_callback('w_open_')
    async def whisper_callback(self, client: Client, callback_query: CallbackQuery):
        """Обрабатывает клик по кнопке секрета."""
        parts = callback_query.data.split('_', 2)
        if len(parts) < 3:
            return

        w_key = parts[2]
        cache = client.db.get_category('whisper_cache')
        payload = await cache.get(w_key)

        if not payload:
            await callback_query.answer(
                text=self.get_text('alert_expired'),
                show_alert=True
            )
            return

        user_id = callback_query.from_user.id
        user_username = (callback_query.from_user.username or '').lower()
        is_target = (
            (payload.get('target_id') and user_id == payload['target_id']) or
            (payload.get('target_username') and user_username == payload['target_username'])
        )
        is_sender = (user_id == payload['sender_id'])

        if not is_target and not is_sender:
            await callback_query.answer(
                text=self.get_text('alert_not_for_you'),
                show_alert=True
            )
            return

        if is_sender and not is_target:
            read_status = (
                self.get_text('alert_status_read').format(time=payload.get('read_at', ''))
                if payload['is_read']
                else self.get_text('alert_status_unread')
            )
            await callback_query.answer(
                text=self.get_text('alert_sender_view').format(
                    target=payload.get('target_mention', 'User'),
                    text=payload['text'],
                    status=read_status
                )[:200],
                show_alert=True
            )
            return

        await callback_query.answer(
            text=self.get_text('alert_target_view').format(
                sender=payload.get('sender_name', 'Владелец'),
                text=payload['text'])[:200],
            show_alert=True
        )

        if not payload['is_read']:
            current_time_str = time.strftime('%H:%M:%S')
            payload['is_read'] = True
            payload['read_at'] = current_time_str
            await cache.set(w_key, payload, expire=86400 * 7)

            new_markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        text=self.get_text('btn_read'),
                        callback_data=f'w_open_{w_key}')
                    ]
                ]
            )

            new_text = self.get_text('msg_template').format(
                target=payload.get('target_mention', 'Собеседник'),
                sender=payload.get('sender_name', 'Владелец'),
                status=self.get_text('status_read').format(time=current_time_str)
            )

            try:
                await client.edit_inline_text(
                    inline_message_id=callback_query.inline_message_id,
                    text=new_text,
                    reply_markup=new_markup
                )
            except Exception:
                try:
                    await client.edit_inline_reply_markup(
                        inline_message_id=callback_query.inline_message_id,
                        reply_markup=new_markup
                    )
                except Exception:
                    pass
