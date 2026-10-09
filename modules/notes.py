import os
import logging
from typing import Optional, Tuple
from pyrogram import Client
from pyrogram.types import Message
from kaguya.types import BaseModule, ModuleInfo, on_command, on_fsm
from kaguya.utils.prefix import get_prefix

logger = logging.getLogger('Kaguya.Notes')


class NotesModule(BaseModule):
    meta = ModuleInfo(
        name='Заметки',
        description='Пользовательские заметки с поддержкой текста и медиа',
        version='2.0.0',
        author='cxvimba',
        commands={
            'n | н': 'Отправить заметку или показать список заметок',
            'nsave | нсейв': 'Сохранить заметку',
            'ndel | ндел': 'Удалить заметку'
        }
    )

    MAX_FILE_SIZE = 50 * 1024 * 1024
    MEDIA_DIR = os.path.join('downloads', 'notes')

    MEDIA_TYPES = {
        'ru': {
            'text': ('📝', 'текст'),
            'photo': ('📷', 'фото'),
            'video': ('📹', 'видео'),
            'document': ('📁', 'файл'),
            'audio': ('🎵', 'аудио'),
            'voice': ('🎙', 'голосовое'),
            'video_note': ('⭕', 'кружочек'),
            'animation': ('🎬', 'GIF'),
            'sticker': ('🎭', 'стикер'),
            'unknown': ('📎', 'медиа'),
        },
        'en': {
            'text': ('📝', 'text'),
            'photo': ('📷', 'photo'),
            'video': ('📹', 'video'),
            'document': ('📁', 'file'),
            'audio': ('🎵', 'audio'),
            'voice': ('🎙', 'voice'),
            'video_note': ('⭕', 'video note'),
            'animation': ('🎬', 'GIF'),
            'sticker': ('🎭', 'sticker'),
            'unknown': ('📎', 'media'),
        }
    }

    LANGUAGES = {
        'en': {
            'none': '<code>No notes saved</code>',
            'not_found': '❌ <b>Kaguya:</b> Note «{note}» not found.',
            'list_header': '📔 <b>Kaguya</b> | ✍️ Notes: <code>{notes}</code>\n\n',
            'save_tip': ' └ 💡 Type <code>{p}nsave &lt;name&gt;</code> to create a new note.',
            'list_footer': '💡 <i>Type <code>{p}n &lt;name&gt;</code> to send note.</i>',
            'save_usage': (
                '📔 <b>Kaguya | Save Note</b>\n\n'
                ' ├ 💡 Reply to message: <code>{p}nsave &lt;title&gt;</code>\n'
                ' ├ 💡 One-line: <code>{p}nsave "title" text</code> or <code>{p}nsave title | text</code>\n'
                ' └ 💡 Interactive: <code>{p}nsave "title"</code>'
            ),
            'waiting_content': (
                '✅ <b>Kaguya:</b> Title «<b>{name}</b>» set.\n\n'
                'Now send text or any media to save.\n'
                '<i>Type <code>cancel</code> to abort.</i>'
            ),
            'cancel_save': '❌ <b>Kaguya:</b> Note creation cancelled.',
            'note_saved': '✅ <b>Kaguya:</b> Note «<b>{note}</b>» ({type_icon} {type_name}) successfully saved!',
            'note_updated': '🔄 <b>Kaguya:</b> Note «<b>{note}</b>» ({type_icon} {type_name}) updated!',
            'delete_usage': 'ℹ️ <b>Kaguya:</b> Missing note name! Type <code>{p}ndel &lt;name&gt;</code>',
            'note_removed': '🗑 <b>Kaguya:</b> Note «<b>{note}</b>» has been deleted.',
            'note_empty': '❌ <b>Kaguya:</b> Empty content! Nothing to save.',
            'file_too_large': '❌ <b>Kaguya:</b> File is too large ({size} MB)! Maximum limit for notes is 50 MB.',
            'send_error': '❌ <b>Kaguya:</b> Failed to send note: {error}',
        },
        'ru': {
            'none': '<code>Заметки отсутствуют</code>',
            'not_found': '❌ <b>Kaguya:</b> Заметка «{note}» не найдена.',
            'list_header': '📔 <b>Kaguya</b> | ✍️ Заметки: <code>{notes}</code>\n\n',
            'save_tip': ' └ 💡 Напиши <code>{p}нсейв &lt;название&gt;</code> для создания заметки.',
            'list_footer': '💡 <i>Напиши <code>{p}н &lt;название&gt;</code> для отправки заметки.</i>',
            'save_usage': (
                '📔 <b>Kaguya | Сохранение заметки</b>\n\n'
                ' ├ 💡 В ответ на сообщение: <code>{p}нсейв &lt;заголовок&gt;</code>\n'
                ' ├ 💡 В одну строку: <code>{p}нсейв "заголовок" текст</code> или <code>{p}нсейв заголовок | текст</code>\n'
                ' └ 💡 Интерактивно: <code>{p}нсейв "заголовок"</code>'
            ),
            'waiting_content': (
                '✅ <b>Kaguya:</b> Заголовок «<b>{name}</b>» сохранен.\n\n'
                'Теперь отправь текст или любое медиа для сохранения.\n'
                '<i>Напиши <code>отмена</code> или <code>cancel</code>, чтобы отменить.</i>'
            ),
            'cancel_save': '❌ <b>Kaguya:</b> Создание заметки отменено.',
            'note_saved': '✅ <b>Kaguya:</b> Заметка «<b>{note}</b>» ({type_icon} {type_name}) успешно сохранена!',
            'note_updated': '🔄 <b>Kaguya:</b> Заметка «<b>{note}</b>» ({type_icon} {type_name}) обновлена!',
            'delete_usage': 'ℹ️ <b>Kaguya:</b> Укажи название заметки! Пример: <code>{p}ндел &lt;название&gt;</code>',
            'note_removed': '🗑 <b>Kaguya:</b> Заметка «<b>{note}</b>» удалена.',
            'note_empty': '❌ <b>Kaguya:</b> Пустое сообщение! Нечего сохранять.',
            'file_too_large': '❌ <b>Kaguya:</b> Файл слишком большой ({size} МБ)! Лимит для сохранения заметок — 50 МБ.',
            'send_error': '❌ <b>Kaguya:</b> Ошибка при отправке заметки: {error}',
        }
    }

    def get_type_info(self, type_key: str) -> Tuple[str, str]:
        """Возвращает иконку и локализованное название типа контента."""
        lang = self.client.get_lang()
        types_dict = self.MEDIA_TYPES.get(lang, self.MEDIA_TYPES['ru'])
        return types_dict.get(type_key, types_dict['unknown'])

    @staticmethod
    def _remove_file_safe(path: Optional[str]):
        """Безопасно удаляет локальный файл заметки."""
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    @staticmethod
    def _extract_file_id(msg: Message, note_type: str) -> Optional[str]:
        """Извлекает file_id из отправленного сообщения."""
        media_obj = getattr(msg, note_type, None)
        if media_obj and hasattr(media_obj, 'file_id'):
            return media_obj.file_id

        for attr in ('photo', 'video', 'document', 'audio', 'voice', 'animation', 'sticker', 'video_note'):
            obj = getattr(msg, attr, None)
            if obj and hasattr(obj, 'file_id'):
                return obj.file_id
        return None

    @staticmethod
    def get_media_size(message: Message) -> Optional[int]:
        """Возвращает размер медиафайла в байтах."""
        media_types = (
            'photo', 'video', 'document', 'audio',
            'voice', 'video_note', 'animation', 'sticker'
        )
        for m_type in media_types:
            obj = getattr(message, m_type, None)
            if obj:
                return getattr(obj, 'file_size', None)
        return None

    @staticmethod
    def find_note_key(cache_keys: list, target_name: str) -> Optional[str]:
        """Ищет ключ заметки в кэше с учетом регистра и подстроки."""
        if not target_name:
            return None

        clean_target = target_name.strip().strip(' "\'«»“”').lstrip('#')
        if not clean_target:
            return None

        if clean_target in cache_keys:
            return clean_target

        target_lower = clean_target.lower()
        for key in cache_keys:
            if str(key).lower() == target_lower:
                return str(key)

        for key in cache_keys:
            if target_lower in str(key).lower():
                return str(key)

        return None

    @staticmethod
    def parse_save_input(message: Message) -> Tuple[str, str]:
        """Разбирает аргументы команды сохранения на название и текст."""
        raw = ''
        if message.text:
            raw = message.text.html if hasattr(message.text, 'html') and message.text.html else message.text
        elif message.caption:
            raw = message.caption.html if hasattr(message.caption, 'html') and message.caption.html else message.caption

        raw = raw.strip() if raw else ''
        parts = raw.split(None, 1)
        if len(parts) < 2:
            return ('', '')

        args_str = parts[1].strip()
        first_char = args_str[0] if args_str else ''
        quotes_map = {'"': '"', "'": "'", '«': '»', '“': '”'}

        if first_char in quotes_map:
            closing_quote = quotes_map[first_char]
            closing_idx = args_str.find(closing_quote, 1)
            if closing_idx != -1:
                title = args_str[1:closing_idx].strip()
                rest = args_str[closing_idx + 1:].strip()
                if rest.startswith('|'):
                    rest = rest[1:].strip()
                return (title, rest)
            return (args_str[1:].strip(), '')

        if '|' in args_str:
            left, right = args_str.split('|', 1)
            return (left.strip().strip(' "\'«»“”'), right.strip())

        if message.reply_to_message:
            return (args_str.strip().strip(' "\'«»“”'), '')

        words = args_str.split(None, 1)
        if len(words) == 2:
            return (words[0].strip().strip(' "\'«»“”'), words[1].strip())
        return (args_str.strip().strip(' "\'«»“”'), '')

    async def extract_and_download_content(self, client: Client, message: Message, custom_caption: str = '') -> Optional[dict]:
        """Извлекает контент из сообщения и сохраняет медиафайлы локально."""
        media_attrs = (
            ('photo', 'photo'),
            ('video', 'video'),
            ('animation', 'animation'),
            ('document', 'document'),
            ('audio', 'audio'),
            ('voice', 'voice'),
            ('video_note', 'video_note'),
            ('sticker', 'sticker')
        )

        for attr, n_type in media_attrs:
            obj = getattr(message, attr, None)
            if obj:
                caption = ''
                if n_type not in ('video_note', 'sticker'):
                    caption = custom_caption or (
                        message.caption.html if hasattr(message.caption, 'html') and message.caption.html else message.caption
                    ) or ''

                file_id = getattr(obj, 'file_id', None)
                local_path = None
                try:
                    os.makedirs(self.MEDIA_DIR, exist_ok=True)
                    local_path = await client.download_media(message, file_name=f"{self.MEDIA_DIR}/")
                except Exception as e:
                    logger.warning(f"Не удалось скачать медиа заметки: {e}")

                return {
                    'type': n_type,
                    'file_id': file_id,
                    'local_path': local_path,
                    'caption': caption
                }

        if message.text or custom_caption:
            text = custom_caption or (
                message.text.html if hasattr(message.text, 'html') and message.text.html else message.text
            ) or ''
            if text:
                return {'type': 'text', 'file_id': None, 'local_path': None, 'text': text}

        if message.caption:
            text = custom_caption or (
                message.caption.html if hasattr(message.caption, 'html') and message.caption.html else message.caption
            ) or ''
            if text:
                return {'type': 'text', 'file_id': None, 'local_path': None, 'text': text}

        return None

    async def _send_raw_media(self, client: Client, chat_id: int | str, note_type: str, source: str, caption: str, kwargs: dict) -> Message:
        """Отправляет медиафайл по источнику (file_id или локальный путь)."""
        if note_type == 'photo':
            return await client.send_photo(chat_id, photo=source, caption=caption or None, **kwargs)
        elif note_type == 'video':
            return await client.send_video(chat_id, video=source, caption=caption or None, **kwargs)
        elif note_type == 'document':
            return await client.send_document(chat_id, document=source, caption=caption or None, **kwargs)
        elif note_type == 'audio':
            return await client.send_audio(chat_id, audio=source, caption=caption or None, **kwargs)
        elif note_type == 'voice':
            return await client.send_voice(chat_id, voice=source, caption=caption or None, **kwargs)
        elif note_type == 'animation':
            return await client.send_animation(chat_id, animation=source, caption=caption or None, **kwargs)
        elif note_type == 'sticker':
            return await client.send_sticker(chat_id, sticker=source, **kwargs)
        elif note_type == 'video_note':
            return await client.send_video_note(chat_id, video_note=source, **kwargs)
        else:
            return await client.send_cached_media(chat_id, file_id=source, caption=caption or None, **kwargs)

    async def send_media_note(
        self, client: Client, chat_id: int | str, note_name: str, note: dict, reply_to_id: Optional[int] = None
    ) -> Message:
        """Отправляет медиафайл с приоритетом кэшированного file_id и откатом на локальный файл."""
        note_type = note.get('type', 'text')
        cached_file_id = note.get('file_id')
        local_path = note.get('local_path')
        caption = note.get('caption') or ''

        has_local = bool(local_path and os.path.exists(local_path))
        kwargs = {}
        if reply_to_id:
            kwargs['reply_to_message_id'] = reply_to_id

        if cached_file_id:
            try:
                return await self._send_raw_media(client, chat_id, note_type, cached_file_id, caption, kwargs)
            except Exception as e:
                if has_local:
                    logger.warning(f"File ID для заметки «{note_name}» устарел ({e}). Повторная отправка с диска...")
                else:
                    raise e

        if not has_local:
            raise FileNotFoundError(f"Файл заметки «{note_name}» не найден на диске и отсутствует рабочий file_id")

        res = await self._send_raw_media(client, chat_id, note_type, local_path, caption, kwargs)

        new_file_id = self._extract_file_id(res, note_type)
        if new_file_id and new_file_id != cached_file_id:
            notes = client.db.get_category('notes')
            note['file_id'] = new_file_id
            await notes.set(note_name, note)
            logger.info(f"Обновлен кэшированный file_id для заметки «{note_name}»: {new_file_id}")

        return res

    @on_command([
        'n', 'н', 'notes', 'заметки'
    ])
    async def send_notes(self, client: Client, message: Message):
        """Отправляет сохраненную заметку или выводит список всех заметок."""
        p = get_prefix(client)
        notes = client.db.get_category('notes')
        notes_list = list(notes._cache)

        raw = message.text or message.caption or ''
        parts = raw.strip().split(None, 1)

        if len(parts) < 2:
            if not notes_list:
                text = (
                    self.get_text('list_header').format(notes=0)
                    + f' ├ {self.get_text("none")}\n'
                    + f'{self.get_text("save_tip").format(p=p)}'
                )
                await message.edit_text(text)
                return

            lines = [self.get_text('list_header').format(notes=len(notes_list))]
            for i, key in enumerate(notes_list, start=1):
                data = await notes.get(key)
                n_type = 'text'
                if isinstance(data, dict):
                    n_type = data.get('type', 'text')
                icon, _ = self.get_type_info(n_type)
                lines.append(f' {i}. {icon} <b>{key}</b>')

            lines.append(f'\n{self.get_text("list_footer").format(p=p)}')
            await message.edit_text('\n'.join(lines))
            return

        query = parts[1].strip()
        target_key = self.find_note_key(notes_list, query)

        if not target_key:
            await message.edit_text(self.get_text('not_found').format(note=query))
            return

        note_data = await notes.get(target_key)

        if isinstance(note_data, str):
            await message.edit_text(note_data)
            return

        if not isinstance(note_data, dict):
            await message.edit_text(self.get_text('not_found').format(note=query))
            return

        n_type = note_data.get('type', 'text')

        if n_type == 'text':
            text = note_data.get('text', '')
            await message.edit_text(text)
            return

        reply_to = message.reply_to_message.id if message.reply_to_message else None
        try:
            await self.send_media_note(client, message.chat.id, target_key, note_data, reply_to_id=reply_to)
            try:
                await message.delete()
            except Exception:
                pass
        except Exception as e:
            logger.error(f'Ошибка отправки медиа-заметки «{target_key}»: {e}', exc_info=True)
            await message.edit_text(self.get_text('send_error').format(error=str(e)))

    @on_command(['nsave', 'нсейв', 'n_save', 'н_сохранить'])
    async def start_save_note(self, client: Client, message: Message):
        """Сохраняет новую заметку или обновляет существующую."""
        p = get_prefix(client)
        note_name, body_text = self.parse_save_input(message)

        if not note_name:
            await message.edit_text(self.get_text('save_usage').format(p=p))
            return

        notes = client.db.get_category('notes')
        cached_keys = list(notes._cache)
        existing_key = self.find_note_key(cached_keys, note_name)
        save_key = existing_key or note_name
        is_update = existing_key is not None

        if message.reply_to_message:
            target = message.reply_to_message
            size = self.get_media_size(target)
            if size and size > self.MAX_FILE_SIZE:
                size_mb = round(size / (1024 * 1024), 1)
                await message.edit_text(self.get_text('file_too_large').format(size=size_mb))
                return

            content = await self.extract_and_download_content(client, target, custom_caption=body_text)
            if not content:
                await message.edit_text(self.get_text('note_empty'))
                return

            if existing_key:
                old_data = await notes.get(existing_key)
                if isinstance(old_data, dict) and old_data.get('local_path'):
                    self._remove_file_safe(old_data['local_path'])

            await notes.set(save_key, content)
            icon, type_name = self.get_type_info(content.get('type', 'text'))
            text_key = 'note_updated' if is_update else 'note_saved'
            await message.edit_text(
                self.get_text(text_key).format(note=save_key, type_icon=icon, type_name=type_name)
            )
            return

        if body_text:
            content = {'type': 'text', 'file_id': None, 'local_path': None, 'text': body_text}
            if existing_key:
                old_data = await notes.get(existing_key)
                if isinstance(old_data, dict) and old_data.get('local_path'):
                    self._remove_file_safe(old_data['local_path'])

            await notes.set(save_key, content)
            icon, type_name = self.get_type_info('text')
            text_key = 'note_updated' if is_update else 'note_saved'
            await message.edit_text(
                self.get_text(text_key).format(note=save_key, type_icon=icon, type_name=type_name)
            )
            return

        await client.set_fsm('waiting_note_content', {'note_name': save_key})
        await message.edit_text(
            self.get_text('waiting_content').format(name=save_key, p=p)
        )

    @on_command(['ndel', 'ндел', 'n_del', 'н_удалить'])
    async def delete_note(self, client: Client, message: Message):
        """Удаляет заметку."""
        p = get_prefix(client)
        raw = message.text or message.caption or ''
        parts = raw.strip().split(None, 1)

        if len(parts) < 2:
            await message.edit_text(self.get_text('delete_usage').format(p=p))
            return

        query = parts[1].strip()
        notes = client.db.get_category('notes')
        notes_list = list(notes._cache)
        target_key = self.find_note_key(notes_list, query)

        if not target_key:
            await message.edit_text(self.get_text('not_found').format(note=query))
            return

        old_data = await notes.get(target_key)
        if isinstance(old_data, dict) and old_data.get('local_path'):
            self._remove_file_safe(old_data['local_path'])

        await notes.delete(target_key)
        await message.edit_text(self.get_text('note_removed').format(note=target_key))

    async def _process_fsm_save(self, client: Client, message: Message):
        """Обрабатывает сохранение заметки из состояния FSM."""
        if not (message.from_user and message.from_user.is_self or message.outgoing):
            return

        text = message.text or message.caption or ''
        if text.strip().lower() in ('отмена', 'cancel'):
            await client.clear_fsm()
            await message.reply_text(self.get_text('cancel_save'))
            return

        fsm_data = await client.get_fsm_data()
        note_name = fsm_data.get('note_name')
        if not note_name:
            await client.clear_fsm()
            return

        size = self.get_media_size(message)
        if size and size > self.MAX_FILE_SIZE:
            size_mb = round(size / (1024 * 1024), 1)
            await message.reply_text(self.get_text('file_too_large').format(size=size_mb))
            return

        content = await self.extract_and_download_content(client, message)
        if not content:
            await message.reply_text(self.get_text('note_empty'))
            return

        notes = client.db.get_category('notes')
        old_data = await notes.get(note_name)
        if isinstance(old_data, dict) and old_data.get('local_path'):
            self._remove_file_safe(old_data['local_path'])

        is_update = old_data is not None
        await notes.set(note_name, content)
        await client.clear_fsm()

        icon, type_name = self.get_type_info(content.get('type', 'text'))
        text_key = 'note_updated' if is_update else 'note_saved'
        await message.reply_text(
            self.get_text(text_key).format(
                note=note_name,
                type_icon=icon,
                type_name=type_name
            )
        )

    @on_fsm('waiting_note_content')
    async def fsm_save_content(self, client: Client, message: Message):
        """Обработчик FSM для сохранения контента заметки."""
        await self._process_fsm_save(client, message)

    @on_fsm('waiting_note_text')
    async def fsm_save_text_compat(self, client: Client, message: Message):
        """Совместимый обработчик старого состояния FSM."""
        await self._process_fsm_save(client, message)
