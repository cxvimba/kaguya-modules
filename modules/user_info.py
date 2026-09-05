import asyncio
import os
import re
from pyrogram import Client, enums
from pyrogram.types import Message, LinkPreviewOptions, InputMediaPhoto, InputPhoneContact, User, Chat
from kaguya.types import BaseModule, ModuleInfo, on_command
from kaguya.utils.prefix import get_prefix


class UserInfoModule(BaseModule):
    meta = ModuleInfo(
        name='ЮзЧекер',
        description='Инспектор пользователей, чатов/каналов и быстрый просмотр ID',
        version='1.2.0',
        author='cxvimba',
        commands={
            'user | юзер | пользователь': 'Информация о пользователе (себе или по ответу)',
            'tg-find | тг-найти': 'Поиск пользователя по ID или @username',
            'chat | чат': 'Информация о чате/канале (текущий, по аргументу или реплаю)',
            'id | ид': 'Быстрый инспектор ID (чат, топик, сообщение, автор, пересылка)'
        }
    )

    LANGUAGES = {
        'en': {
            'error_detect': '❌ <b>Kaguya:</b> Failed to determine user.',
            'fetching': '⏳ <b>Kaguya:</b> Gathering profile info...',
            'fetching_chat': '⏳ <b>Kaguya:</b> Gathering chat info...',
            'find_usage': (
                'ℹ️ <b>Kaguya | User Search</b>\n\n'
                'Usage: <code>{p}tg-find &lt;@username or ID&gt;</code>\n'
                'Example: <code>{p}tg-find @durov</code>'
            ),
            'chat_usage': (
                'ℹ️ <b>Kaguya | Chat Search</b>\n\n'
                'Usage: <code>{p}chat [optional: @username, link, or ID]</code>\n'
                '<i>Tip: You can also reply to a forwarded message!</i>'
            ),
            'searching_phone': '☎️ <b>Kaguya:</b> Importing phone contact «{target}»...',
            'searching': '🔍 <b>Kaguya:</b> Searching for «{target}»...',
            'not_found': '❌ <b>Kaguya |</b> Entity not found.\n<i>Error: {error}</i>',
            'timeout_error': '⏱ <b>Kaguya:</b> Request timed out! Telegram servers did not respond in time.',
            'card_error': '❌ <b>Kaguya:</b> Error generating card:\n<code>{error}</code>',
            'yes': 'Yes',
            'no': 'No',
            'unknown': 'Unknown',
            'none': 'None',
            'status_offline': 'Offline 💤',
            'status_online': 'Online 🟢',
            'status_recently': 'Recently online 🕒',
            'type_supergroup': 'Supergroup 👥',
            'type_group': 'Group 👥',
            'type_channel': 'Channel 📢',
            'type_private': 'Private Chat 👤',
            'type_bot': 'Bot 🤖',
            'user_card_text': (
                'ℹ️ <b>Kaguya | Profile Info</b>\n\n'
                ' ├ 🏷️ <b>Name:</b> <code>{full_name}</code>\n'
                ' ├ 🆔 <b>ID:</b> <code>{user_id}</code>\n'
                ' ├ 🌐 <b>Language:</b> <code>{language}</code>\n'
                ' ├ 👤 <b>Username:</b> {usernames}\n'
                ' ├ 🔗 <b>Mention:</b> {mention}\n'
                ' ├ 🎉 <b>Birthday:</b> {birthday}\n'
                ' ├ ⭐️ <b>Premium:</b> <code>{is_premium}</code>\n'
                ' ├ 🤖 <b>Bot:</b> <code>{is_bot}</code>\n'
                ' ├ 🔘 <b>Status:</b> <code>{status}</code>\n'
                ' ├ ☎️ <b>Phone:</b> {phone_number}\n'
                ' ├ 📢 <b>Personal Channel:</b> {channel_username}\n'
                ' ├ 🏢 <b>DC ID:</b> <code>{dc_id}</code>\n'
                ' └ 💬 <b>Bio:</b> <i>{bio}</i>'
            ),
            'chat_card_text': (
                '💬 <b>Kaguya | Chat Info</b>\n\n'
                ' ├ 🏷️ <b>Title:</b> <code>{title}</code>\n'
                ' ├ 🆔 <b>ID:</b> <code>{chat_id}</code>\n'
                ' ├ 📁 <b>Type:</b> <code>{chat_type}</code>\n'
                ' ├ 👤 <b>Username:</b> {username}\n'
                ' ├ 👥 <b>Members:</b> <code>{members_count}</code>\n'
                ' ├ 🏢 <b>DC ID:</b> <code>{dc_id}</code>\n'
                ' ├ 🔗 <b>Invite Link:</b> {invite_link}\n'
                ' ├ 📢 <b>Linked Chat:</b> {linked_chat}\n'
                ' ├ 🏛️ <b>Forum:</b> <code>{is_forum}</code>\n'
                ' ├ ⏱ <b>Slow Mode:</b> <code>{slow_mode}</code>\n'
                ' ├ 🔒 <b>Protected Content:</b> <code>{protected}</code>\n'
                ' ├ ⭐️ <b>Verified:</b> <code>{is_verified}</code>\n'
                ' └ 💬 <b>Description:</b> <i>{description}</i>'
            ),
            'id_header': '🆔 <b>Kaguya | ID Inspector</b>\n\n',
            'id_chat': ' ├ 💬 <b>Chat ID:</b> <code>{chat_id}</code>\n',
            'id_thread': ' ├ 🧵 <b>Topic ID:</b> <code>{thread_id}</code>\n',
            'id_msg': ' ├ ✉️ <b>Message ID:</b> <code>{msg_id}</code>\n',
            'id_reply_user': ' ├ 👤 <b>Replied User ID:</b> <code>{user_id}</code>\n',
            'id_reply_sender_chat': ' ├ 📢 <b>Replied Channel ID:</b> <code>{chat_id}</code>\n',
            'id_reply_msg': ' ├ 📨 <b>Replied Message ID:</b> <code>{msg_id}</code>\n',
            'id_forward_user': ' ├ 🔄 <b>Forwarded User ID:</b> <code>{user_id}</code>\n',
            'id_forward_chat': ' ├ 🔄 <b>Forwarded Chat ID:</b> <code>{chat_id}</code>\n',
            'seconds': 's'
        },
        'ru': {
            'error_detect': '❌ <b>Kaguya:</b> Не удалось определить пользователя.',
            'fetching': '⏳ <b>Kaguya:</b> Собираю информацию о профиле...',
            'fetching_chat': '⏳ <b>Kaguya:</b> Собираю информацию о чате...',
            'find_usage': (
                'ℹ️ <b>Kaguya | Поиск пользователей</b>\n\n'
                'Использование: <code>{p}tg-find &lt;@username или ID&gt;</code>\n'
                'Пример: <code>{p}tg-find @durov</code>'
            ),
            'chat_usage': (
                'ℹ️ <b>Kaguya | Поиск чата</b>\n\n'
                'Использование: <code>{p}chat [опционально: @username, ссылка или ID]</code>\n'
                '<i>Подсказка: можно ответить на пересланное сообщение!</i>'
            ),
            'searching': '🔍 <b>Kaguya:</b> Ищу «{target}»...',
            'searching_phone': '☎️ <b>Kaguya:</b> Импортирую телефонный контакт «{target}»...',
            'not_found': '❌ <b>Kaguya:</b> Объект не найден.\n<i>Ошибка: {error}</i>',
            'timeout_error': '⏱ <b>Kaguya:</b> Превышено время ожидания запроса! Серверы Telegram не ответили вовремя.',
            'card_error': '❌ <b>Kaguya:</b> Ошибка при формировании карточки:\n<code>{error}</code>',
            'yes': 'Да',
            'no': 'Нет',
            'unknown': 'Неизвестно',
            'none': 'Нет',
            'status_offline': 'Вне сети 💤',
            'status_online': 'В сети 🟢',
            'status_recently': 'Недавно был(а) в сети 🕒',
            'type_supergroup': 'Супергруппа 👥',
            'type_group': 'Группа 👥',
            'type_channel': 'Канал 📢',
            'type_private': 'Личные сообщения 👤',
            'type_bot': 'Бот 🤖',
            'user_card_text': (
                'ℹ️ <b>Kaguya | Информация о профиле</b>\n\n'
                ' ├ 🏷️ <b>Имя:</b> <code>{full_name}</code>\n'
                ' ├ 🆔 <b>ID:</b> <code>{user_id}</code>\n'
                ' ├ 🌐 <b>Язык:</b> <code>{language}</code>\n'
                ' ├ 👤 <b>Username:</b> {usernames}\n'
                ' ├ 🔗 <b>Упоминание:</b> {mention}\n'
                ' ├ 🎉 <b>Birthday:</b> {birthday}\n'
                ' ├ ⭐️ <b>Премиум:</b> <code>{is_premium}</code>\n'
                ' ├ 🤖 <b>Бот:</b> <code>{is_bot}</code>\n'
                ' ├ 🔘 <b>Статус:</b> <code>{status}</code>\n'
                ' ├ ☎️ <b>№ Телефона:</b> {phone_number}\n'
                ' ├ 📢 <b>Личный канал:</b> {channel_username}\n'
                ' ├ 🏢 <b>DC ID:</b> <code>{dc_id}</code>\n'
                ' └ 💬 <b>Bio:</b> <i>{bio}</i>'
            ),
            'chat_card_text': (
                '💬 <b>Kaguya | Информация о чате</b>\n\n'
                ' ├ 🏷️ <b>Название:</b> <code>{title}</code>\n'
                ' ├ 🆔 <b>ID:</b> <code>{chat_id}</code>\n'
                ' ├ 📁 <b>Тип:</b> <code>{chat_type}</code>\n'
                ' ├ 👤 <b>Username:</b> {username}\n'
                ' ├ 👥 <b>Участников:</b> <code>{members_count}</code>\n'
                ' ├ 🏢 <b>DC ID:</b> <code>{dc_id}</code>\n'
                ' ├ 🔗 <b>Ссылка:</b> {invite_link}\n'
                ' ├ 📢 <b>Связанный чат:</b> {linked_chat}\n'
                ' ├ 🏛️ <b>Форум (топики):</b> <code>{is_forum}</code>\n'
                ' ├ ⏱ <b>Медленный режим:</b> <code>{slow_mode}</code>\n'
                ' ├ 🔒 <b>Защита контента:</b> <code>{protected}</code>\n'
                ' ├ ⭐️ <b>Верифицирован:</b> <code>{is_verified}</code>\n'
                ' └ 💬 <b>Описание:</b> <i>{description}</i>'
            ),
            'id_header': '🆔 <b>Kaguya | Инспектор ID</b>\n\n',
            'id_chat': ' ├ 💬 <b>Чат:</b> <code>{chat_id}</code>\n',
            'id_thread': ' ├ 🧵 <b>Топик (Thread):</b> <code>{thread_id}</code>\n',
            'id_msg': ' ├ ✉️ <b>Сообщение:</b> <code>{msg_id}</code>\n',
            'id_reply_user': ' ├ 👤 <b>Автор (Reply):</b> <code>{user_id}</code>\n',
            'id_reply_sender_chat': ' ├ 📢 <b>Канал-отправитель (Reply):</b> <code>{chat_id}</code>\n',
            'id_reply_msg': ' ├ 📨 <b>Сообщение (Reply):</b> <code>{msg_id}</code>\n',
            'id_forward_user': ' ├ 🔄 <b>Переслано от (User):</b> <code>{user_id}</code>\n',
            'id_forward_chat': ' ├ 🔄 <b>Переслано из (Chat):</b> <code>{chat_id}</code>\n',
            'seconds': 'сек'
        }
    }

    @on_command(['user', 'юзер', 'пользователь'])
    async def user_info_cmd(self, client: Client, message: Message):
        """Выводит информацию о себе/пользователе по ответу."""
        reply = message.reply_to_message

        if reply and reply.from_user:
            target_user_id = reply.from_user.id
        elif reply and reply.sender_chat:
            await self._send_chat_card(client, message, reply.sender_chat.id)
            return
        else:
            target_user_id = client.me.id

        await message.edit_text(self.get_text('fetching'))
        await self._send_user_card(client, message, target_user_id)

    @on_command(['tg-find', 'тг-поиск', 'тг-найти'])
    async def find_user_cmd(self, client: Client, message: Message):
        """Ищет пользователя по ID, @username или ном телефона."""
        if len(message.command) < 2:
            p = get_prefix(client)
            await message.edit_text(
                self.get_text('find_usage').format(p=p)
            )
            return

        target = message.command[1].strip()

        clean_target = target.replace('+', '').replace(' ', '').replace('-', '')
        if target.startswith('+') and clean_target.isdigit():
            await message.edit_text(
                self.get_text('searching_phone').format(target=target)
            )
            try:
                imported = await asyncio.wait_for(
                    client.import_contacts(
                        [InputPhoneContact(
                            phone=target,
                            first_name='Kaguya Search')
                        ]
                    ),
                    timeout=8
                )
                if imported and imported.users:
                    user = imported.users[0]
                    await client.delete_contacts(user.id)
                    await self._send_user_card(client, message, user.id)
                else:
                    await message.edit_text(
                        self.get_text('not_found').format(error='Phone number not registered')
                    )
            except asyncio.TimeoutError:
                await message.edit_text(self.get_text('timeout_error'))
            except Exception as e:
                await message.edit_text(
                    self.get_text('not_found').format(error=e)
                )
            return

        await message.edit_text(
            self.get_text('searching').format(target=target)
        )
        try:
            if target.isdigit():
                target = int(target)
        except ValueError:
            pass

        try:
            user = await asyncio.wait_for(client.get_users(target), timeout=8)
            await self._send_user_card(client, message, user.id)
        except asyncio.TimeoutError:
            await message.edit_text(self.get_text('timeout_error'))
        except Exception as e:
            await message.edit_text(
                self.get_text('not_found').format(error=e)
            )

    @on_command(['id', 'ид'])
    async def quick_id_cmd(self, client: Client, message: Message):
        """Быстро инспектирует ID текущего чата, сообщения, треда и реплая."""
        text = self.get_text('id_header')
        text += self.get_text('id_chat').format(chat_id=message.chat.id)

        if message.message_thread_id:
            text += self.get_text('id_thread').format(thread_id=message.message_thread_id)

        text += self.get_text('id_msg').format(msg_id=message.id)

        reply = message.reply_to_message
        if reply:
            if reply.from_user:
                text += self.get_text('id_reply_user').format(user_id=reply.from_user.id)
            elif reply.sender_chat:
                text += self.get_text('id_reply_sender_chat').format(chat_id=reply.sender_chat.id)

            text += self.get_text('id_reply_msg').format(msg_id=reply.id)

            if reply.forward_from:
                text += self.get_text('id_forward_user').format(user_id=reply.forward_from.id)
            elif reply.forward_from_chat:
                text += self.get_text('id_forward_chat').format(chat_id=reply.forward_from_chat.id)
        await message.edit_text(text)

    @on_command(['chat', 'чат'])
    async def chat_info_cmd(self, client: Client, message: Message):
        """Выводит информацию о текущем чате или чате по аргументу или реплаю."""
        reply = message.reply_to_message
        if len(message.command) > 1:
            raw_arg = message.command[1].strip()
            link_match = re.match(r'^(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/([a-zA-Z0-9_]{4,})/?$', raw_arg)
            if link_match:
                target_chat = f'@{link_match.group(1)}'
            else:
                clean_num = raw_arg.lstrip('-')
                if clean_num.isdigit():
                    target_chat = int(raw_arg)
                else:
                    target_chat = raw_arg

        elif reply:
            if reply.forward_from_chat:
                target_chat = reply.forward_from_chat.id
            elif reply.sender_chat:
                target_chat = reply.sender_chat.id
            else:
                target_chat = message.chat.id
        else:
            target_chat = message.chat.id

        await message.edit_text(self.get_text('fetching_chat'))
        await self._send_chat_card(client, message, target_chat)


    async def _send_chat_card(self, client: Client, message: Message, target):
        """Генерирует и отправляет карточку чата."""
        try:
            chat: Chat = await asyncio.wait_for(client.get_chat(target), timeout=8)

            title = chat.title or self.get_text('type_private')
            chat_id = chat.id

            type_map = {
                enums.ChatType.SUPERGROUP: self.get_text('type_supergroup'),
                enums.ChatType.GROUP: self.get_text('type_group'),
                enums.ChatType.CHANNEL: self.get_text('type_channel'),
                enums.ChatType.PRIVATE: self.get_text('type_private'),
                enums.ChatType.BOT: self.get_text('type_bot')
            }
            chat_type = type_map.get(chat.type, self.get_text('unknown'))
            username = f'@{chat.username}' if chat.username else self.get_text('none')

            members_count = chat.members_count
            if members_count is None and chat.type in (enums.ChatType.SUPERGROUP, enums.ChatType.GROUP,
                                                       enums.ChatType.CHANNEL):
                try:
                    members_count = await client.get_chat_members_count(chat.id)
                except Exception:
                    members_count = self.get_text('unknown')
            members_str = f'{members_count:,}'.replace(',', ' ') if isinstance(members_count, int) else str(
                members_count or self.get_text('unknown'))

            dc_id = chat.dc_id
            if not dc_id and chat.photo:
                dc_id = chat.photo.dc_id
            dc_id = dc_id or self.get_text('unknown')

            invite_link = chat.invite_link or (
                f'https://t.me/{chat.username}' if chat.username else self.get_text('none'))

            linked_chat = self.get_text('none')
            if chat.linked_chat:
                lc = chat.linked_chat
                linked_chat = f'@{lc.username}' if lc.username else f'<code>{lc.title}</code> (ID: <code>{lc.id}</code>)'

            is_forum = self.get_text('yes') if getattr(chat, 'is_forum', False) else self.get_text('no')
            protected = self.get_text('yes') if getattr(chat, 'has_protected_content', False) else self.get_text('no')
            is_verified = self.get_text('yes') if chat.is_verified else self.get_text('no')

            slow_mode = (
                f'{chat.slow_mode_delay} {self.get_text("seconds")}'
                if getattr(chat, 'slow_mode_delay', None)
                else self.get_text('no')
            )
            description = chat.description or self.get_text('none')

            text = self.get_text('chat_card_text').format(
                title=title,
                chat_id=chat_id,
                chat_type=chat_type,
                username=username,
                members_count=members_str,
                dc_id=dc_id,
                invite_link=invite_link,
                linked_chat=linked_chat,
                is_forum=is_forum,
                slow_mode=slow_mode,
                protected=protected,
                is_verified=is_verified,
                description=description
            )

            if chat.photo:
                photo_path = await client.download_media(chat.photo.big_file_id)
                try:
                    await message.edit_media(
                        InputMediaPhoto(
                            media=photo_path,
                            caption=text
                        )
                    )
                except Exception:
                    await message.edit_text(
                        text=text,
                        link_preview_options=LinkPreviewOptions(is_disabled=True)
                    )
                finally:
                    if photo_path and os.path.exists(photo_path):
                        os.remove(photo_path)
            else:
                await message.edit_text(
                    text=text,
                    link_preview_options=LinkPreviewOptions(is_disabled=True)
                )

        except asyncio.TimeoutError:
            await message.edit_text(self.get_text('timeout_error'))
        except Exception as e:
            await message.edit_text(
                self.get_text('card_error').format(error=e)
            )

    async def _send_user_card(self, client: Client, message: Message, user_id: int):
        """Генерация и отправка карточки пользователя."""
        try:
            try:
                user = await asyncio.wait_for(client.get_users(user_id), timeout=6)
            except Exception:
                user = User(id=user_id)
            try:
                chat_info = await asyncio.wait_for(client.get_chat(user_id), timeout=6)
            except Exception:
                chat_info = Chat(id=user_id)

            full_name = user.full_name
            usernames = f'@{user.username}' if user.username else self.get_text('none')
            is_premium = self.get_text('yes') if user.is_premium else self.get_text('no')
            is_bot = self.get_text('yes') if user.is_bot else self.get_text('no')
            dc_id = user.dc_id or self.get_text('unknown')
            bio = chat_info.raw.about or chat_info.description or self.get_text('none')
            language = user.language_code if user.language_code else self.get_text('unknown')
            phone_number = user.phone_number if user.phone_number else self.get_text('unknown')

            birthday = chat_info.raw.birthday
            if birthday:
                birthday = f'{birthday.year or "????"}.{birthday.month or "??"}.{birthday.day or "??"}'
            else:
                birthday = self.get_text('unknown')

            if chat_info.raw.personal_channel_id:
                try:
                    channel_chat = await client.get_chat(int(f'-100{chat_info.raw.personal_channel_id}'))
                    channel_username = f'@{channel_chat.username}' if channel_chat.username else channel_chat.title
                except Exception:
                    channel_username = f'ID: {chat_info.raw.personal_channel_id}'
            else:
                channel_username = self.get_text('no')

            status = self.get_text('status_offline')
            if user.status == enums.UserStatus.ONLINE:
                status = self.get_text('status_online')
            elif user.status == enums.UserStatus.RECENTLY:
                status = self.get_text('status_recently')

            text = self.get_text('user_card_text').format(
                full_name=full_name,
                user_id=user.id,
                language=language,
                usernames=usernames,
                mention=user.mention,
                birthday=birthday,
                is_premium=is_premium,
                is_bot=is_bot,
                status=status,
                phone_number=phone_number,
                channel_username=channel_username,
                dc_id=dc_id,
                bio=bio
            )

            if user.photo:
                photo_path = await client.download_media(user.photo.big_file_id)

                try:
                    await message.edit_media(
                        InputMediaPhoto(
                            media=photo_path,
                            caption=text
                        )
                    )
                except Exception:
                    await message.edit_text(
                        text=text,
                        link_preview_options=LinkPreviewOptions(is_disabled=True)
                    )
                finally:
                    if photo_path and os.path.exists(photo_path):
                        os.remove(photo_path)
            else:
                await message.edit_text(
                    text=text,
                    link_preview_options=LinkPreviewOptions(
                        is_disabled=True
                    )
                )

        except asyncio.TimeoutError:
            await message.edit_text(self.get_text('timeout_error'))
        except Exception as e:
            await message.edit_text(
                self.get_text('card_error').format(error=e)
            )
