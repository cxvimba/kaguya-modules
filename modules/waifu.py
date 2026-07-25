import io
import random
import uuid
import urllib.parse
import aiohttp
from pyrogram import Client
from pyrogram.types import (
    Message, InlineQuery, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent,
    CallbackQuery
)
from kaguya.types import BaseModule, ModuleInfo, on_command, on_assistant_inline, on_assistant_callback, on_fsm
from kaguya.utils.prefix import get_prefix

SFW_CATEGORIES = [
    'waifu', 'neko', 'kitsune', 'husbando',
    'hug', 'kiss', 'pat', 'smile', 'smug', 'wink', 'dance', 'happy'
]

HEADERS = {'User-Agent': 'KaguyaUserBot (https://github.com/cxvimba/KaguyaUserBot)'}


class WaifuModule(BaseModule):
    meta = ModuleInfo(
        name='Вайфу',
        description='Интерактивный аниме-вайфу менеджер',
        version='1.2.0',
        author='cxvimba',
        commands={
            'тян | вайфу | chan | waifu': 'Открыть интерактивное меню тян (пиши <b>Теги</b> для быстрой отправки)',
            'waifu_auth | тян_авторизация': 'Сохранить ключи авторизации для Rule34 API'
        }
    )

    LANGUAGES = {
        'en': {
            'searching_sfw': '🔍 <i>Searching for a cute {category} waifu...</i>',
            'searching_nsfw': '🔥 <i>Looking for a hot chick by tags: {tags}...</i>',
            'api_error': '❌ <b>Kaguya:</b> Failed to fetch image: <code>{error}</code>',
            'not_found': '❌ <b>Kaguya:</b> No images found.',
            'invalid_tag': (
                '❌ <b>Kaguya:</b> Invalid SFW category <code>{tag}</code>!\n\n'
                '💡 <b>Available SFW categories:</b>\n'
                '<code>{sfw_tags}</code>'
            ),
            'menu_header': '🌸 <b>Kaguya | Anime Waifu</b>\n\n<blockquote>Select a category from the buttons below or switch to NSFW mode:</blockquote>',
            'alert_not_owner': '💢 Kaguya: This is not your control panel!',
            'alert_loading': '⏳ Loading new art...',
            'fsm_prompt_tags': '📝 <b>Kaguya | Custom Search</b>\n\nSend me tags to search (e.g., <code>neko thighhighs</code>):\n<i>Type <code>cancel</code> to abort.</i>',
            'fsm_cancel': '❌ <b>Kaguya:</b> Search aborted.',
            'btn_waifu': '👩 Waifu',
            'btn_neko': '🐱 Neko',
            'btn_kitsune': '🦊 Kitsune',
            'btn_husbando': '🤵 Husbando',
            'btn_kiss': '💖 Kiss',
            'btn_hug': '🫂 Hug',
            'btn_pat': '🫳 Pat',
            'btn_smug': '😏 Smug',
            'btn_wink': '😉 Wink',
            'btn_happy': '😊 Happy',
            'btn_dance': '💃 Dance',
            'btn_nsfw': '🔞 NSFW (18+)',
            'btn_more_sfw': '🔄 One More!',
            'btn_sfw_menu': '⬅️ Back to Menu',
            'btn_close': '❌ Close Menu',
            'r34_auth_required': (
                '❌ <b>Kaguya:</b> Rule34 authorization is required for NSFW search!\n\n'
                '1. Register an account on https://rule34.xxx/ (no email required, just username and password 🥞)\n'
                '2. Go to <b>Account ➔ Options</b>.\n'
                '3. Find <b>API Access Credentials</b> and check the box.\n'
                '4. Click <b>Save</b> and copy the long string.\n'
                '5. Bind the key (paste that long string):\n'
                '<code>{p}waifu_auth &api_key=3cb46...574&user_id=6...50</code>'
            ),
            'auth_usage': (
                'ℹ️ <b>Kaguya:</b> Copy and send me the <i>API Access Credentials</i> string!\n'
                'Example: <code>{p}waifu_auth &api_key=3cb46...574&user_id=6...50</code>'
            ),
            'auth_success': '✅ <b>Kaguya:</b> Rule34 API keys successfully saved!',
            'menu_closed': '🚪 <b>Kaguya:</b> Menu closed.',
            'images_sent': '✅ <b>Kaguya:</b> Images sent!',
        },
        'ru': {
            'searching_sfw': '🔍 <i>Ищу милую тянку из категории «{category}»...</i>',
            'searching_nsfw': '🔥 <i>Ищу горячую тянку по тегам: {tags}...</i>',
            'api_error': '❌ <b>Kaguya:</b> Не удалось получить изображение: <code>{error}</code>',
            'not_found': '❌ <b>Kaguya:</b> По вашему запросу ничего не найдено.',
            'invalid_tag': (
                '❌ <b>Kaguya:</b> Неизвестная SFW категория <code>{tag}</code>!\n\n'
                '💡 <b>Доступные SFW категории:</b>\n'
                '<code>{sfw_tags}</code>'
            ),
            'menu_header': '🌸 <b>Kaguya | Аниме Тяночки</b>\n\n<blockquote>Выберите интересующую категорию или перейдите в 18+ поиск по любым тегам:</blockquote>',
            'alert_not_owner': '💢 Kaguya: Эй, это не твоя панель управления!',
            'alert_loading': '⏳ Ищу новый арт...',
            'fsm_prompt_tags': '📝 <b>Kaguya | Поиск по тегам</b>\n\nНапишите теги для поиска (например, <code>neko thighhighs</code>):\n<i>Напишите <code>отмена</code> или <code>cancel</code> для выхода.</i>',
            'fsm_cancel': '❌ <b>Kaguya:</b> Поиск отменен.',
            'btn_waifu': '👩 Вайфу',
            'btn_neko': '🐱 Неко',
            'btn_kitsune': '🦊 Кицунэ',
            'btn_husbando': '🤵 Хасбандо',
            'btn_kiss': '💖 Поцелуй',
            'btn_hug': '🫂 Обнимашки',
            'btn_pat': '🫳 Погладить',
            'btn_smug': '😏 Ухмылка',
            'btn_wink': '😉 Подмигнуть',
            'btn_happy': '😊 Радость',
            'btn_dance': '💃 Танец',
            'btn_nsfw': '🔞 NSFW (18+)',
            'btn_more_sfw': '🔄 Еще одну!',
            'btn_sfw_menu': '⬅️ Назад в меню',
            'btn_close': '❌ Закрыть',
            'r34_auth_required': (
                '❌ <b>Kaguya:</b> Для поиска NSFW требуется авторизация на Rule34!\n\n'
                '1. Зарегистрируйтесь на сайте https://rule34.xxx/ (почту не требуют, просто логин и пароль 🥞)\n'
                '2. Перейдите в раздел <b>Account ➔ Options</b>.\n'
                '3. Найдите пункт <b>API Access Credentials</b> и поставьте галочку.\n'
                '4. Жмите <b>Save</b> и копируйте большую строку.\n'
                '5. Привяжите ключ (вставьте ту большую строку):\n'
                '<code>{p}waifu_auth &api_key=3cb46...574&user_id=6...50</code>'
            ),
            'auth_usage': (
                'ℹ️ <b>Kaguya:</b> Скопируйте и отправьте мне строку <i>API Access Credentials</i>!\n'
                'Пример: <code>{p}waifu_auth &api_key=3cb46...574&user_id=6...50</code>'
            ),
            'auth_success': '✅ <b>Kaguya:</b> Ключи авторизации для Rule34 успешно сохранены!',
            'menu_closed': '🚪 <b>Kaguya:</b> Меню закрыто.',
            'images_sent': '✅ <b>Kaguya:</b> Изображения отправлены!',
        }
    }

    async def _get_sfw_url(self, client: Client, category: str) -> str:
        """Получает sfw-арт с фильтрацией просмотренных."""
        cache = client.db.get_category('waifu_seen')

        results = []
        for _ in range(3):
            endpoint_url = f'https://nekos.best/api/v2/{category}?amount=20'
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                async with session.get(endpoint_url, timeout=10) as response:
                    if response.status != 200:
                        continue
                    data = await response.json()
                    results = data.get('results', [])
                    if not results:
                        continue

                    unseen = []
                    for item in results:
                        url = item.get('url')
                        if url and not await cache.get(f'seen:{url}'):
                            unseen.append(url)

                    if unseen:
                        chosen = random.choice(unseen)
                        await cache.set(f'seen:{chosen}', True)
                        return chosen

        if results:
            chosen = random.choice(results).get('url')
            return chosen
        return None

    async def _get_nsfw_url(self, client: Client, tags: str) -> str:
        """Получает nsfw-арт с постраничной навигацией и фильтрацией просмотренных."""
        cache = client.db.get_category('waifu_seen')
        settings = client.db.get_category('settings')
        r34_api = await settings.get('r34_api')

        if not r34_api:
            return 'AUTH_REQUIRED'

        current_page = await cache.get(f'page:{tags}', 0)

        data = []
        for _ in range(3):
            encoded_tags = urllib.parse.quote(tags)
            endpoint_url = (
                f'https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&limit=100'
                f'&pid={current_page}&tags={encoded_tags}{r34_api}'
            )

            async with aiohttp.ClientSession(headers=HEADERS) as session:
                async with session.get(endpoint_url, timeout=10) as response:
                    if response.status != 200:
                        return None
                    data = await response.json(content_type=None)

                    if not data or not isinstance(data, list):
                        if current_page > 0:
                            current_page = 0
                            await cache.set(f'page:{tags}', 0)
                            continue
                        return None

                    unseen = []
                    for post in data:
                        url = post.get('file_url')
                        if url and not await cache.get(f'seen:{url}'):
                            unseen.append(url)

                    if unseen:
                        chosen = random.choice(unseen)
                        await cache.set(f'seen:{chosen}', True)
                        await cache.set(f'page:{tags}', current_page)
                        return chosen

                    current_page += 1
                    await cache.set(f'page:{tags}', current_page)

        await cache.set(f'page:{tags}', 0)
        if data:
            chosen = random.choice(data).get('file_url')
            return chosen
        return None

    @on_command(['тян', 'вайфу', 'chan', 'waifu'])
    async def get_waifu(self, client: Client, message: Message):
        """Обрабатывает запрос."""
        args = [arg.lower() for arg in message.command[1:]] if len(message.command) > 1 else []

        if not args and client.assistant:
            settings = client.db.get_category('settings')
            bot_username = await settings.get('bot_username')

            tr_key = str(uuid.uuid4())[:8]
            results = await client.get_inline_bot_results(bot_username, f'tyan_{tr_key}')

            await client.send_inline_bot_result(
                chat_id=message.chat.id,
                query_id=results.query_id,
                result_id=results.results[0].id
            )
            await message.delete()
            return

        is_nsfw = False
        nsfw_triggers = ['18+', 'nsfw', 'порно', 'porno']
        for trigger in nsfw_triggers:
            if trigger in args:
                is_nsfw = True
                args.remove(trigger)
                break

        try:
            if is_nsfw:
                search_tags = ' '.join(args) if args else 'waifu'
                await message.edit_text(
                    self.get_text('searching_nsfw').format(tags=search_tags)
                )

                image_url = await self._get_nsfw_url(client, search_tags)

                if image_url == 'AUTH_REQUIRED':
                    p = get_prefix(client)
                    await message.edit_text(self.get_text('r34_auth_required').format(p=p))
                    return
                if not image_url:
                    await message.edit_text(self.get_text('not_found'))
                    return
            else:
                category = args[0] if args else random.choice(SFW_CATEGORIES)
                if category not in SFW_CATEGORIES:
                    sfw_str = ', '.join(SFW_CATEGORIES)
                    await message.edit_text(
                        self.get_text('invalid_tag').format(tag=category, sfw_tags=sfw_str)
                    )
                    return

                await message.edit_text(self.get_text('searching_sfw').format(category=category))
                image_url = await self._get_sfw_url(client, category)

            if not image_url:
                await message.edit_text(
                    self.get_text('api_error').format(error='Empty image URL')
                )
                return

            file_obj = image_url
            filename = image_url.split('/')[-1].split('?')[0]

            if is_nsfw:
                try:
                    async with aiohttp.ClientSession(headers=HEADERS) as download_session:
                        async with download_session.get(image_url, timeout=15) as img_resp:
                            if img_resp.status != 200:
                                await message.edit_text(
                                    self.get_text('api_error').format(error=f'CDN HTTP {img_resp.status}')
                                )
                                return
                            file_bytes = await img_resp.read()

                    file_obj = io.BytesIO(file_bytes)
                    file_obj.name = filename
                except Exception as download_err:
                    await message.edit_text(
                        self.get_text('api_error').format(error=f'Download failed: {download_err}')
                    )
                    return

            ext = filename.lower()
            try:
                if ext.endswith(('.mp4', '.mov', '.webm')):
                    await client.send_video(chat_id=message.chat.id, video=file_obj)
                elif ext.endswith(('.gif', '.gifv')):
                    await client.send_animation(chat_id=message.chat.id, animation=file_obj)
                else:
                    await client.send_photo(chat_id=message.chat.id, photo=file_obj)
            except Exception:
                await client.send_document(chat_id=message.chat.id, document=file_obj)
            await message.delete()

        except Exception as e:
            await message.edit_text(
                self.get_text('api_error').format(error=e)
            )

    @on_assistant_inline('tyan_')
    async def waifu_inline_menu(self, client: Client, inline_query: InlineQuery):
        """Отвечает инлайн-результатом с приветственным меню."""
        markup = self._get_sfw_keyboard()
        results = [
            InlineQueryResultArticle(
                id='tyan_menu',
                title='Kaguya | Аниме Тяночки 🌸',
                description='Открыть интерактивную панель генератора артов',
                input_message_content=InputTextMessageContent(self.get_text('menu_header')),
                reply_markup=markup
            )
        ]
        await inline_query.answer(results, cache_time=1)

    @on_assistant_callback('tyan_')
    async def waifu_callback(self, client: Client, callback_query: CallbackQuery):
        """Обрабатывает вызовы."""
        settings = self.client.db.get_category('settings')
        owner_id = await settings.get('owner_id')

        if callback_query.from_user.id != owner_id:
            await callback_query.answer(
                text=self.get_text('alert_not_owner'),
                show_alert=True
            )
            return

        data = callback_query.data

        if data == 'tyan_close':
            await client.edit_inline_text(
                inline_message_id=callback_query.inline_message_id,
                text=self.get_text('menu_closed'),
                reply_markup=None
            )
            return

        if data == 'tyan_sfw_menu':
            await client.edit_inline_text(
                inline_message_id=callback_query.inline_message_id,
                text=self.get_text('menu_header'),
                reply_markup=self._get_sfw_keyboard()
            )
            return

        if data == 'tyan_nsfw_search':
            await self.client.set_fsm(
                'waiting_r34_tags',
                {'inline_msg_id': callback_query.inline_message_id}
            )

            await client.edit_inline_text(
                inline_message_id=callback_query.inline_message_id,
                text=self.get_text('fsm_prompt_tags')
            )
            return

        if data.startswith('tyan_sfw_'):
            category = data.split('_')[2]
            await callback_query.answer(text=self.get_text('alert_loading'))

            try:
                image_url = await self._get_sfw_url(self.client, category)
                if not image_url:
                    raise Exception('Не удалось получить вайфу-арт.')

                text = f'🌸 <b>Kaguya | <a href="{image_url}">{category.upper()}</a>:</b>'
                markup = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text=self.get_text('btn_more_sfw'),
                                callback_data=f'tyan_sfw_{category}'
                            ),
                            InlineKeyboardButton(
                                text=self.get_text('btn_sfw_menu'),
                                callback_data='tyan_sfw_menu')
                        ]
                    ]
                )

                await client.edit_inline_text(
                    inline_message_id=callback_query.inline_message_id,
                    text=text,
                    reply_markup=markup
                )
            except Exception as e:
                await callback_query.answer(text=f'Ошибка: {e}', show_alert=True)

    @on_fsm('waiting_r34_tags')
    async def capture_r34_tags(self, client: Client, message: Message):
        """Перехватывает теги в состоянии FSM."""
        if not (message.from_user and message.from_user.is_self or message.outgoing):
            return

        search_tags = message.text
        fsm_data = await client.get_fsm_data()
        inline_msg_id = fsm_data.get('inline_msg_id')

        if search_tags.strip().lower() in ('отмена', 'cancel'):
            await client.clear_fsm()
            await message.delete()
            if inline_msg_id:
                await client.assistant.edit_inline_text(
                    inline_message_id=inline_msg_id,
                    text=self.get_text('fsm_cancel')
                )
            return

        image_url = await self._get_nsfw_url(client, search_tags)

        if image_url == 'AUTH_REQUIRED':
            await message.delete()
            if inline_msg_id:
                p = get_prefix(client)
                await client.assistant.edit_inline_text(
                    inline_message_id=inline_msg_id,
                    text=self.get_text('r34_auth_required').format(p=p)
                )
            await client.clear_fsm()
            return

        if not image_url:
            await message.delete()
            if inline_msg_id:
                await client.assistant.edit_inline_text(
                    inline_message_id=inline_msg_id,
                    text=self.get_text('not_found')
                )
            await client.clear_fsm()
            return


        filename = image_url.split('/')[-1].split('?')[0]
        try:
            async with aiohttp.ClientSession(headers=HEADERS) as download_session:
                async with download_session.get(image_url, timeout=15) as img_resp:
                    if img_resp.status != 200:
                        await message.delete()
                        if inline_msg_id:
                            await client.assistant.edit_inline_text(
                                inline_message_id=inline_msg_id,
                                text=self.get_text('api_error').format(error=f'CDN HTTP {img_resp.status}')
                            )
                        await client.clear_fsm()
                        return
                    file_bytes = await img_resp.read()

            file_obj = io.BytesIO(file_bytes)
            file_obj.name = filename
        except Exception as download_err:
            await message.delete()
            if inline_msg_id:
                await client.assistant.edit_inline_text(
                    inline_message_id=inline_msg_id,
                    text=self.get_text('api_error').format(error=f'Download failed: {download_err}')
                )
            await client.clear_fsm()
            return

        ext = filename.lower()
        try:
            if ext.endswith(('.mp4', '.mov', '.webm')):
                await client.send_video(chat_id=message.chat.id, video=file_obj)
            elif ext.endswith(('.gif', '.gifv')):
                await client.send_animation(chat_id=message.chat.id, animation=file_obj)
            else:
                await client.send_photo(chat_id=message.chat.id, photo=file_obj)
        except Exception:
            await client.send_document(chat_id=message.chat.id, document=file_obj)

        await message.delete()
        await client.clear_fsm()

        if inline_msg_id:
            await client.assistant.delete_inline_message(inline_msg_id)

    def _get_sfw_keyboard(self) -> InlineKeyboardMarkup:
        """Собирает клавиатуру с быстрыми тегами."""
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text=self.get_text('btn_waifu'), callback_data='tyan_sfw_waifu'),
                    InlineKeyboardButton(text=self.get_text('btn_neko'), callback_data='tyan_sfw_neko'),
                    InlineKeyboardButton(text=self.get_text('btn_kitsune'), callback_data='tyan_sfw_kitsune')
                ],
                [
                    InlineKeyboardButton(text=self.get_text('btn_husbando'), callback_data='tyan_sfw_husbando'),
                    InlineKeyboardButton(text=self.get_text('btn_kiss'), callback_data='tyan_sfw_kiss'),
                    InlineKeyboardButton(text=self.get_text('btn_hug'), callback_data='tyan_sfw_hug')
                ],
                [
                    InlineKeyboardButton(text=self.get_text('btn_pat'), callback_data='tyan_sfw_pat'),
                    InlineKeyboardButton(text=self.get_text('btn_smug'), callback_data='tyan_sfw_smug'),
                    InlineKeyboardButton(text=self.get_text('btn_wink'), callback_data='tyan_sfw_wink')
                ],
                [
                    InlineKeyboardButton(text=self.get_text('btn_happy'), callback_data='tyan_sfw_happy'),
                    InlineKeyboardButton(text=self.get_text('btn_dance'), callback_data='tyan_sfw_dance')
                ],
                [
                    InlineKeyboardButton(text=self.get_text('btn_nsfw'), callback_data='tyan_nsfw_search'),
                    InlineKeyboardButton(text=self.get_text('btn_close'), callback_data='tyan_close')
                ]
            ]
        )

    @on_command(['waifu_auth', 'тян_авторизация'])
    async def auth_rule34(self, client: Client, message: Message):
        """Сохраняет ключи авторизации для Rule34 API."""
        p = get_prefix(client)
        if len(message.command) < 2:
            await message.edit_text(
                self.get_text('auth_usage').format(p=p)
            )
            return

        api_key = message.command[1].strip()

        settings = client.db.get_category('settings')
        await settings.set('r34_api', api_key)

        await message.edit_text(self.get_text('auth_success'))
