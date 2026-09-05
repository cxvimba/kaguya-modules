import time
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from kaguya.types import BaseModule, ModuleInfo, on_command, on_event


def format_duration(seconds: float, lang: str = 'ru') -> str:
    """Форматирует длительность отсутствия."""
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if lang == 'ru':
        if days: parts.append(f'{days} дн.')
        if hours: parts.append(f'{hours} ч.')
        if minutes: parts.append(f'{minutes} мин.')
        if not parts or seconds: parts.append(f'{seconds} сек.')
    else:
        if days: parts.append(f'{days}d')
        if hours: parts.append(f'{hours}h')
        if minutes: parts.append(f'{minutes}m')
        if not parts or seconds: parts.append(f'{seconds}s')

    return ' '.join(parts)


async def afk_mention_check(_, client: Client, message: Message) -> bool:
    if not message.from_user or message.from_user.is_self or message.outgoing:
        return False
    if message.from_user.is_bot:
        return False

    db = client.db.get_category('afk')
    if not await db.get('is_afk'):
        return False

    if message.chat.type == enums.ChatType.PRIVATE:
        return True
    if message.mentioned:
        return True
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == client.me.id:
            return True

    return False


async def afk_outgoing_check(_, client: Client, message: Message) -> bool:
    is_me = bool(message.from_user and message.from_user.is_self or message.outgoing)
    if not is_me:
        return False

    text = (message.text or message.caption or '').strip()
    parts = text.split()
    if parts:
        prefixes = getattr(client, 'prefixes', ['.', '/'])
        for p in prefixes:
            for cmd in ['afk', 'афк']:
                if parts[0].lower() == f'{p}{cmd}':
                    return False

    db = client.db.get_category('afk')
    return bool(await db.get('is_afk'))


class AfkModule(BaseModule):
    meta = ModuleInfo(
        name='AFK Режим',
        description='Автоответчик во время отсутствия',
        version='1.0.0',
        author='cxvimba',
        commands={
            'afk | афк': 'Включить режим AFK (формат: afk [причина])'
        }
    )

    LANGUAGES = {
        'en': {
            'default_reason': 'Busy',
            'afk_enabled': (
                '💤 <b>Kaguya | AFK Mode Enabled</b>\n\n'
                ' ├ 📝 <b>Reason:</b> <i>{reason}</i>\n'
                ' └ 🕒 <b>Time:</b> <code>{time}</code>\n\n'
                '<blockquote>💡 AFK will automatically turn off once you send any message.</blockquote>'
            ),
            'afk_reply': (
                '💤 <b>Kaguya | The owner is currently AFK</b>\n\n'
                ' ├ 📝 <b>Reason:</b> <i>{reason}</i>\n'
                ' └ ⏳ <b>Away for:</b> <code>{duration}</code>\n\n'
                '<blockquote>Your message has been logged.</blockquote>'
            ),
            'pm_chat': 'Private Messages',
            'report_header': (
                '🌸 <b>Kaguya | AFK Report</b>\n\n'
                'Welcome back! AFK mode has been turned off.\n'
                ' ├ ⏳ <b>Away for:</b> <code>{duration}</code>\n'
                ' ├ 📝 <b>Reason:</b> <i>{reason}</i>\n'
                ' └ 📬 <b>Mentions while away:</b> <code>{count}</code>\n'
            ),
            'no_pings': '<blockquote>No one looked for you while you were away ✨</blockquote>',
            'more_pings': '\n<i>... and {more} more mentions.</i>'
        },
        'ru': {
            'default_reason': 'Занят(а)',
            'afk_enabled': (
                '💤 <b>Kaguya | Режим AFK активирован</b>\n\n'
                ' ├ 📝 <b>Причина:</b> <i>{reason}</i>\n'
                ' └ 🕒 <b>Время:</b> <code>{time}</code>\n\n'
                '<blockquote>💡 AFK автоматически отключится, как только вы отправите любое сообщение.</blockquote>'
            ),
            'afk_reply': (
                '💤 <b>Kaguya | Владелец сейчас AFK</b>\n\n'
                ' ├ 📝 <b>Причина:</b> <i>{reason}</i>\n'
                ' └ ⏳ <b>Отсутствует:</b> <code>{duration}</code>\n\n'
                '<blockquote>Я сохранила твоё сообщение и передам владельцу.</blockquote>'
            ),
            'pm_chat': 'Личные сообщения',
            'report_header': (
                '🌸 <b>Kaguya | Отчёт AFK</b>\n\n'
                'С возвращением! Режим AFK успешно снят.\n'
                ' ├ ⏳ <b>Время отсутствия:</b> <code>{duration}</code>\n'
                ' ├ 📝 <b>Причина:</b> <i>{reason}</i>\n'
                ' └ 📬 <b>Вас искали:</b> <code>{count}</code> раз(а)\n'
            ),
            'no_pings': '<blockquote>Никто не беспокоил вас во время отсутствия ✨</blockquote>',
            'more_pings': '\n<i>... и ещё {more} пингов.</i>'
        }
    }

    @on_command(['afk', 'афк'])
    async def toggle_afk_cmd(self, client: Client, message: Message):
        """Включает режим AFK."""
        reason = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else self.get_text('default_reason')
        current_time_str = time.strftime('%H:%M:%S')

        db = client.db.get_category('afk')
        await db.set('is_afk', True)
        await db.set('reason', reason)
        await db.set('start_time', time.time())
        await db.set('pings', [])

        await client.db.delete_category('afk_cooldown')
        await message.edit_text(
            self.get_text('afk_enabled').format(
                reason=reason,
                time=current_time_str
            )
        )

    @on_event(filters.create(afk_mention_check))
    async def on_afk_mention(self, client: Client, message: Message):
        """Обрабатывает входящие упоминания во время AFK."""
        db = client.db.get_category('afk')
        reason = await db.get('reason', self.get_text('default_reason'))
        start_time = await db.get('start_time', time.time())
        cooldown_db = client.db.get_category('afk_cooldown')
        user_key = f'cd_{message.from_user.id}'
        if not await cooldown_db.get(user_key):
            await cooldown_db.set(user_key, True, expire=180)

            lang = client.get_lang()
            duration_str = format_duration(time.time() - start_time, lang=lang)

            await message.reply_text(
                self.get_text('afk_reply').format(
                    reason=reason,
                    duration=duration_str
                )
            )

        pings = await db.get('pings', [])
        pings.append({
            'user_name': message.from_user.first_name,
            'user_id': message.from_user.id,
            'username': message.from_user.username,
            'chat_title': message.chat.title or self.get_text('pm_chat'),
            'chat_id': message.chat.id,
            'text': (message.text or message.caption or '')[:120]
        })
        await db.set('pings', pings)

    @on_event(filters.create(afk_outgoing_check))
    async def on_afk_outgoing(self, client: Client, message: Message):
        """Автоматически снимает AFK при первом исходящем сообщении и шлёт отчёт в Избранное."""
        db = client.db.get_category('afk')
        reason = await db.get('reason', self.get_text('default_reason'))
        start_time = await db.get('start_time', time.time())
        pings = await db.get('pings', [])

        await db.set('is_afk', False)
        await client.db.delete_category('afk_cooldown')

        lang = client.get_lang()
        duration_str = format_duration(time.time() - start_time, lang=lang)

        report = self.get_text('report_header').format(
            duration=duration_str,
            reason=reason,
            count=len(pings)
        )

        if not pings:
            report += f'\n{self.get_text("no_pings")}'
        else:
            report += '\n'
            for idx, p in enumerate(pings[:15], 1):
                user_repr = f'@{p["username"]}' if p['username'] else f'<a href="tg://user?id={p["user_id"]}">{p["user_name"]}</a>'
                chat_info = f'в «{p["chat_title"]}»'
                msg_preview = f'<i>«{p["text"]}»</i>' if p['text'] else '<i>[Медиа]</i>'
                report += f'{idx}. {user_repr} {chat_info}\n   └ {msg_preview}\n'

            if len(pings) > 15:
                report += self.get_text('more_pings').format(more=len(pings) - 15)
        await client.send_message('me', report)
