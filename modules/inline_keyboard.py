import os
import re
import uuid
import logging
from pyrogram import Client
from pyrogram.enums import ButtonStyle, ParseMode
from pyrogram.types import Message, InlineQuery, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, \
    InputTextMessageContent, InlineQueryResultCachedPhoto, InlineQueryResultCachedVideo, \
    InlineQueryResultCachedDocument, InlineQueryResultCachedAnimation, InlineQueryResultCachedAudio
from kaguya.types import BaseModule, ModuleInfo, on_command, on_assistant_inline
from kaguya.utils.prefix import get_prefix


logger = logging.getLogger('Kaguya.InlineKeyboard')


class InlineKeyboardModule(BaseModule):
    meta = ModuleInfo(
        name='Клавиатура для сообщений',
        description='Отправляет клавиатуру вместе с любыми сообщениями и медиа',
        version='1.0.0',
        author='cxvimba',
        commands={
            'kb | keyboard | клавиатура': 'Отправить клавиатуру с сообщением (формат: кнопки в [], текст ниже)'
        }
    )

    LANGUAGES = {
        'en': {
            'usage': (
                '🎛 <b>Kaguya | Button Constructor</b>\n\n'
                '<b>Usage:</b>\n'
                '<code>{p}kb</code>\n'
                '<code>[ Button 1 | link_or_data | STYLE ], [ Button 2 | ... ]</code>\n\n'
                '<code>Your message text here</code>\n\n'
                '💡 <i>Button styles: DEFAULT, PRIMARY (🟠), SUCCESS (🟢), DANGER (🔴)</i>'
            ),
            'assistant_required': '❌ <b>Kaguya:</b> To use keyboards, bind a helper bot using <code>.token</code>',
            'failed_to_generate': '❌ <b>Kaguya |</b> Assistant was unable to form a response.',
            'media_video': 'Video',
            'media_file': 'File',
            'inline_kb_title': 'Message with Keyboard',
            'assistant_error_title': '⚠️ Error: Start the Assistant!',
            'assistant_error_desc': 'Press Start in the chat with @{bot_username}',
            'assistant_error_text': (
                '⚠️ <b>Kaguya | Assistant Error</b>\n\n'
                'Helper bot <b>@{bot_username}</b> was unable to forward the media file because you haven\'t started it in private messages!\n\n'
                '<b>Solution:</b>\n'
                '1️⃣ Go to the bot: @{bot_username}\n'
                '2️⃣ Press the <b>Start</b> button or send <code>/start</code>\n\n'
                'After doing this, media keyboard delivery will start working.'
            )
        },
        'ru': {
            'usage': (
                '🎛 <b>Kaguya | Конструктор кнопок</b>\n\n'
                '<b>Использование:</b>\n'
                '<code>{p}kb</code>\n'
                '<code>[ Кнопка 1 | ссылка_или_data | СТИЛЬ ], [ Кнопка 2 | ... ]</code>\n\n'
                '<code>Твой текст сообщения</code>\n\n'
                '💡 <i>Стили кнопок: DEFAULT (стандартная, по умолчанию), PRIMARY (🟠), SUCCESS (🟢), DANGER (🔴)</i>'
            ),
            'assistant_required': '❌ <b>Kaguya:</b> Для работы клавиатур привяжи бота-помощника через <code>.token</code>',
            'failed_to_generate': '❌ <b>Kaguya |</b> Ассистент не смог сформировать ответ.',
            'media_video': 'Видео',
            'media_file': 'Файл',
            'inline_kb_title': 'Сообщение с клавиатурой',
            'assistant_error_title': '⚠️ Ошибка: Запусти ассистента!',
            'assistant_error_desc': 'Нажми кнопку Старт в диалоге с @{bot_username}',
            'assistant_error_text': (
                '⚠️ <b>Kaguya | Ошибка ассистента</b>\n\n'
                'Бот-ассистент <b>@{bot_username}</b> не смог переслать медиа-файл, '
                'так как ты не запустил его в личных сообщениях!\n\n'
                '<b>Решение:</b>\n'
                '1️⃣ Перейди в чат к боту: @{bot_username}\n'
                '2️⃣ Нажми кнопку <b>Запустить</b> или команду <code>/start</code>\n\n'
                'После этого отправка медиа-клавиатур заработает.'
            )
        }
    }

    @on_command(['kb', 'keyboard', 'клавиатура'])
    async def send_inline_kb_cmd(self, client: Client, message: Message):
        """Парсит и добавляет клавиатуру к сообщению."""
        raw_text = message.text.html if message.text else (message.caption.html if message.caption else None)
        lines = raw_text.splitlines()

        if len(lines) < 2:
            p = get_prefix(client)
            await message.edit_text(
                self.get_text('usage').format(p=p)
            )
            return

        button_lines = []
        text_lines = []
        parsing_buttons = True

        for line in lines[1:]:
            stripped = line.strip()
            if not stripped:
                continue

            if parsing_buttons and stripped.startswith('[') and stripped.endswith(']'):
                button_lines.append(stripped)
            else:
                parsing_buttons = False
                text_lines.append(line)

        original_text = '\n'.join(text_lines)

        if not client.assistant:
            await message.edit_text(self.get_text('assistant_required'))
            return

        keyboard_structure = []
        for line in button_lines:
            row = []
            matches = re.findall(r'\[(.*?)\]', line)
            for match in matches:
                parts = [p.strip() for p in match.split('|')]
                btn_text = parts[0]
                val = parts[1] if len(parts) > 1 else ''
                style_str = parts[2].upper() if len(parts) > 2 else 'DEFAULT'

                row.append(
                    {
                        'text': btn_text,
                        'value': val,
                        'style': style_str
                    }
                )
            keyboard_structure.append(row)

        target_media_msg = message if (
            message.photo or message.video or message.document or message.animation or message.audio
        ) else None

        media_type = None
        media_path = None

        if target_media_msg:
            if target_media_msg.photo:
                media_type = 'photo'
                media_path = await client.download_media(target_media_msg.photo.file_id)
            elif target_media_msg.video:
                media_type = 'video'
                media_path = await client.download_media(target_media_msg.video.file_id)
            elif target_media_msg.document:
                media_type = 'document'
                media_path = await client.download_media(target_media_msg.document.file_id)
            elif target_media_msg.animation:
                media_type = 'animation'
                media_path = await client.download_media(target_media_msg.animation.file_id)
            elif target_media_msg.audio:
                media_type = 'audio'
                media_path = await client.download_media(target_media_msg.audio.file_id)

        kb_key = str(uuid.uuid4())[:8]
        payload = {
            'text': original_text,
            'media_type': media_type,
            'media_path': media_path,
            'keyboard': keyboard_structure
        }

        cache = client.db.get_category('kb_cache')
        await cache.set(kb_key, payload, expire=3600)

        settings = client.db.get_category('settings')
        bot_username = await settings.get('bot_username')

        results = await client.get_inline_bot_results(bot_username, f'kb_{kb_key}')

        if not results.results:
            await message.edit_text(self.get_text('failed_to_generate'))
            return

        await client.send_inline_bot_result(
            chat_id=message.chat.id,
            query_id=results.query_id,
            result_id=results.results[0].id
        )

        await message.delete()

    @on_assistant_inline('kb_')
    async def keyboard_inline(self, client: Client, inline_query: InlineQuery):
        """Собирает инлайн-результат на основе отправленных данных."""
        query_text = inline_query.query
        kb_key = query_text[3:]
        cache = client.db.get_category('kb_cache')
        payload = await cache.get(kb_key)

        if not payload:
            return

        keyboard_rows = []
        for row in payload['keyboard']:
            row_buttons = []
            for btn in row:
                btn_text = btn['text']
                val = btn['value']
                style_name = btn['style']

                style_obj = getattr(ButtonStyle, style_name, ButtonStyle.DEFAULT)

                if val.startswith(('http://', 'https://', 't.me/')):
                    row_buttons.append(
                        InlineKeyboardButton(text=btn_text, url=val, style=style_obj)
                    )
                else:
                    row_buttons.append(
                        InlineKeyboardButton(text=btn_text, callback_data=val, style=style_obj)
                    )
            keyboard_rows.append(row_buttons)

        markup = InlineKeyboardMarkup(keyboard_rows)
        text = payload['text']
        media_type = payload['media_type']

        results = []
        media_path = payload.get('media_path')

        if media_type and media_path and os.path.exists(media_path):
            bot_msg = None
            try:
                settings = client.db.get_category('settings')
                owner_id = await settings.get('owner_id')

                if media_type == 'photo':
                    bot_msg = await client.send_photo(chat_id=owner_id, photo=media_path)
                    bot_file_id = bot_msg.photo.file_id
                    results.append(
                        InlineQueryResultCachedPhoto(
                            id=kb_key,
                            photo_file_id=bot_file_id,
                            caption=text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=markup
                        )
                    )
                elif media_type == 'video':
                    bot_msg = await client.send_video(chat_id=owner_id, video=media_path)
                    bot_file_id = bot_msg.video.file_id
                    results.append(
                        InlineQueryResultCachedVideo(
                            id=kb_key,
                            video_file_id=bot_file_id,
                            title=self.get_text('media_video'),
                            caption=text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=markup
                        )
                    )
                elif media_type == 'document':
                    bot_msg = await client.send_document(chat_id=owner_id, document=media_path)
                    bot_file_id = bot_msg.document.file_id
                    results.append(
                        InlineQueryResultCachedDocument(
                            id=kb_key,
                            document_file_id=bot_file_id,
                            title=self.get_text('media_file'),
                            caption=text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=markup
                        )
                    )
                elif media_type == 'animation':
                    bot_msg = await client.send_animation(chat_id=owner_id, animation=media_path)
                    bot_file_id = bot_msg.animation.file_id
                    results.append(
                        InlineQueryResultCachedAnimation(
                            id=kb_key,
                            animation_file_id=bot_file_id,
                            caption=text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=markup
                        )
                    )
                elif media_type == 'audio':
                    bot_msg = await client.send_audio(chat_id=owner_id, audio=media_path)
                    bot_file_id = bot_msg.audio.file_id
                    results.append(
                        InlineQueryResultCachedAudio(
                            id=kb_key,
                            audio_file_id=bot_file_id,
                            caption=text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=markup
                        )
                    )
            except Exception as send_err:
                logger.warning(f'Ассистент не смог отправить медиа владельцу: {send_err}')
                bot_username = await settings.get('bot_username')

                results.append(
                    InlineQueryResultArticle(
                        id='setup_error',
                        title=self.get_text('assistant_error_title'),
                        description=self.get_text('assistant_error_desc').format(bot_username=bot_username),
                        input_message_content=InputTextMessageContent(
                            self.get_text('assistant_error_text').format(bot_username=bot_username)
                        )
                    )
                )
            finally:
                if bot_msg:
                    await bot_msg.delete()
                if os.path.exists(media_path):
                    os.remove(media_path)

        else:
            results.append(
                InlineQueryResultArticle(
                    id=kb_key,
                    title=self.get_text('inline_kb_title'),
                    description=text[:50] if text else '',
                    input_message_content=InputTextMessageContent(
                        text,
                        parse_mode=ParseMode.HTML
                    ),
                    reply_markup=markup
                )
            )

        await inline_query.answer(results, cache_time=1)
