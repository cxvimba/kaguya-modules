import os
from pyrogram import Client, enums
from pyrogram.types import Message, LinkPreviewOptions, InputMediaPhoto
from kaguya.types import BaseModule, ModuleInfo, on_command
from kaguya.utils.prefix import get_prefix


class UserInfoModule(BaseModule):
    meta = ModuleInfo(
        name='Информация о пользователе',
        description='Чекер аккаунтов по ответам и поисковик по ID или @username',
        version='1.0.0',
        author='cxvimba',
        commands={
            'user | юзер | пользователь': 'Показать информацию о пользователе (себе или по ответу)',
            'tg-find | тг-найти': 'Найти пользователя по его ID или @username (пример: .tg-find @username)'
        }
    )

    LANGUAGES = {
        'en': {
            'error_detect': '❌ <b>Kaguya:</b> Failed to determine user.',
            'fetching': '⏳ <b>Kaguya:</b> Gathering profile info...',
            'find_usage': (
                'ℹ️ <b>Kaguya | User Search</b>\n\n'
                'Usage: <code>{p}tg-find &lt;@username or ID&gt;</code>\n'
                'Example: <code>{p}tg-find @durov</code>'
            ),
            'searching': '🔍 <b>Kaguya:</b> Searching for user «{target}»...',
            'not_found': '❌ <b>Kaguya |</b> User not found.\n<i>Error: {error}</i>',
            'card_error': '❌ <b>Kaguya:</b> Error generating user card:\n<code>{error}</code>',
            'yes': 'Yes',
            'no': 'No',
            'unknown': 'Unknown',
            'none': 'None',
            'status_offline': 'Offline 💤',
            'status_online': 'Online 🟢',
            'status_recently': 'Recently online 🕒',
            'card_text': (
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
            )
        },
        'ru': {
            'error_detect': '❌ <b>Kaguya:</b> Не удалось определить пользователя.',
            'fetching': '⏳ <b>Kaguya:</b> Собираю информацию о профиле...',
            'find_usage': (
                'ℹ️ <b>Kaguya | Поиск пользователей</b>\n\n'
                'Использование: <code>{p}tg-find &lt;@username или ID&gt;</code>\n'
                'Пример: <code>{p}tg-find @durov</code>'
            ),
            'searching': '🔍 <b>Kaguya:</b> Ищу пользователя «{target}»...',
            'not_found': '❌ <b>Kaguya |</b> Пользователь не найден.\n<i>Ошибка: {error}</i>',
            'card_error': '❌ <b>Kaguya:</b> Ошибка при формировании карточки пользователя:\n<code>{error}</code>',
            'yes': 'Да',
            'no': 'Нет',
            'unknown': 'Неизвестно',
            'none': 'Нет',
            'status_offline': 'Вне сети 💤',
            'status_online': 'В сети 🟢',
            'status_recently': 'Недавно был(а) в сети 🕒',
            'card_text': (
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
            )
        }
    }

    @on_command(['user', 'юзер', 'пользователь'])
    async def user_info_cmd(self, client: Client, message: Message):
        """Выводит информацию о себе/пользователе по ответу."""
        reply = message.reply_to_message

        if reply:
            target_user = reply.from_user
        else:
            target_user = client.me

        if not target_user:
            await message.edit_text(self.get_text('error_detect'))
            return

        await message.edit_text(self.get_text('fetching'))
        await self._send_user_card(client, message, target_user.id)

    @on_command(['tg-find', 'тг-поиск'])
    async def find_user_cmd(self, client: Client, message: Message):
        """Ищет пользователя в Telegram по ID или @username."""
        if len(message.command) < 2:
            p = get_prefix(client)
            await message.edit_text(
                self.get_text('find_usage').format(p=p)
            )
            return

        target = message.command[1].strip()
        await message.edit_text(
            self.get_text('searching').format(target=target)
        )

        try:
            if target.isdigit():
                target = int(target)
        except ValueError:
            pass

        try:
            user = await client.get_users(target)
            await self._send_user_card(client, message, user.id)
        except Exception as e:
            await message.edit_text(
                self.get_text('not_found').format(error=e)
            )

    async def _send_user_card(self, client: Client, message: Message, user_id: int):
        """Метод для генерации и отправки карточки пользователя."""
        try:
            user = await client.get_users(user_id)
            chat_info = await client.get_chat(user_id)

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

            text = self.get_text('card_text').format(
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

        except Exception as e:
            await message.edit_text(
                self.get_text('card_error').format(error=e)
            )