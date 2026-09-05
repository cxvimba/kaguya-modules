import io
import aiohttp
from pyrogram import Client
from pyrogram.types import Message, LinkPreviewOptions
from kaguya.types import BaseModule, ModuleInfo, on_command
from kaguya.utils.prefix import get_prefix


def format_timestamp(seconds: float) -> str:
    """Переводит секунды в формат."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f'{h:02d}:{m:02d}:{s:02d}'
    return f'{m:02d}:{s:02d}'


class AnimeSauceModule(BaseModule):
    meta = ModuleInfo(
        name='Аниме по кадру',
        description='Поиск аниме по скриншоту, гифке или видео через Trace.moe',
        version='1.0.0',
        author='cxvimba',
        commands={
            'sauce | anifind | соус': 'Найти аниме по кадру (ответом на фото, гиф, стикер или видео)'
        }
    )

    LANGUAGES = {
        'en': {
            'usage': (
                '🌸 <b>Kaguya | Anime Finder</b>\n\n'
                'Reply to a photo, gif, sticker, or video with <code>{p}sauce</code> to find the original anime!'
            ),
            'searching': '🔍 <b>Kaguya:</b> Analyzing anime scene via Trace.moe...',
            'downloading_preview': '📥 <b>Kaguya:</b> Match found! Uploading scene preview...',
            'not_found': '❌ <b>Kaguya:</b> No matching anime scenes found.',
            'low_similarity': '⚠️ <i>Low similarity ({similarity}). Might be fanart, edit, or incorrect scene.</i>\n\n',
            'api_error': '❌ <b>Kaguya:</b> Trace.moe API error: <code>{error}</code>',
            'unsupported_media': '❌ <b>Kaguya:</b> Please reply to an image, sticker, animation, or video.',
            'yes': 'Yes 🔞',
            'no': 'No',
            'unknown': 'Unknown',
            'card_text': (
                '🌸 <b>Kaguya | Anime Scene Found</b>\n\n'
                ' ├ 🎬 <b>Title:</b> <code>{title}</code>\n'
                ' ├ 🇯🇵 <b>Native:</b> <code>{title_native}</code>\n'
                ' ├ 🎞 <b>Episode:</b> <code>{episode}</code>\n'
                ' ├ ⏱ <b>Timestamp:</b> <code>{timestamp}</code>\n'
                ' ├ 🎯 <b>Similarity:</b> <code>{similarity}</code>\n'
                ' ├ 🔞 <b>Adult (18+):</b> <code>{is_adult}</code>\n'
                ' └ 🔗 <b>AniList:</b> <a href="https://anilist.co/anime/{anilist_id}">Open Link</a>'
            )
        },
        'ru': {
            'usage': (
                '🌸 <b>Kaguya | Поиск по кадру</b>\n\n'
                'Ответьте на фото, гифку, стикер или видео командой <code>{p}sauce</code> для поиска аниме!'
            ),
            'searching': '🔍 <b>Kaguya:</b> Анализирую кадр через Trace.moe...',
            'downloading_preview': '📥 <b>Kaguya:</b> Найдено! Загружаю превью сцены...',
            'not_found': '❌ <b>Kaguya:</b> Совпадений среди аниме не найдено.',
            'low_similarity': '⚠️ <i>Низкая точность ({similarity}). Возможно, это фанарт, коллаж или эдит.</i>\n\n',
            'api_error': '❌ <b>Kaguya:</b> Ошибка API Trace.moe: <code>{error}</code>',
            'unsupported_media': '❌ <b>Kaguya:</b> Пожалуйста, ответьте на фото, стикер, анимацию или видео.',
            'yes': 'Да 🔞',
            'no': 'Нет',
            'unknown': 'Неизвестно',
            'card_text': (
                '🌸 <b>Kaguya | Аниме найдено</b>\n\n'
                ' ├ 🎬 <b>Тайтл:</b> <code>{title}</code>\n'
                ' ├ 🇯🇵 <b>Оригинал:</b> <code>{title_native}</code>\n'
                ' ├ 🎞 <b>Эпизод:</b> <code>{episode}</code>\n'
                ' ├ ⏱ <b>Таймкод:</b> <code>{timestamp}</code>\n'
                ' ├ 🎯 <b>Точность:</b> <code>{similarity}</code>\n'
                ' ├ 🔞 <b>18+ (NSFW):</b> <code>{is_adult}</code>\n'
                ' └ 🔗 <b>AniList:</b> <a href="https://anilist.co/anime/{anilist_id}">Открыть тайтл</a>'
            )
        }
    }

    @on_command(['sauce', 'соус', 'anifind'])
    async def find_sauce_cmd(self, client: Client, message: Message):
        """Ищет аниме по скриншоту/кадру."""
        p = get_prefix(client)
        reply = message.reply_to_message
        target = reply if reply else message

        file_id = None
        if target.photo:
            file_id = target.photo.file_id
        elif target.sticker:
            file_id = target.sticker.file_id
        elif target.animation:
            file_id = target.animation.thumbs[0].file_id if target.animation.thumbs else target.animation.file_id
        elif target.video:
            file_id = target.video.thumbs[0].file_id if target.video.thumbs else target.video.file_id
        elif target.document and target.document.mime_type and target.document.mime_type.startswith('image/'):
            file_id = target.document.file_id

        if not file_id:
            await message.edit_text(self.get_text('usage').format(p=p))
            return

        await message.edit_text(self.get_text('searching'))

        try:
            media_io = await client.download_media(file_id, in_memory=True)
            img_bytes = media_io.getvalue()

            form = aiohttp.FormData()
            form.add_field('image', img_bytes, filename='frame.jpg', content_type='image/jpeg')

            endpoint = 'https://api.trace.moe/search?cutBorders&anilistInfo'
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, data=form, timeout=25) as resp:
                    if resp.status == 429:
                        await message.edit_text(
                            self.get_text('api_error').format(error='Rate Limit Exceeded'))
                        return
                    if resp.status != 200:
                        await message.edit_text(self.get_text('api_error').format(error=f'HTTP {resp.status}'))
                        return

                    data = await resp.json()

            results = data.get('result', [])
            if not results:
                await message.edit_text(self.get_text('not_found'))
                return

            best = results[0]
            similarity = best.get('similarity', 0.0)
            similarity_str = f'{similarity * 100:.1f}%'

            episode = best.get('episode') or self.get_text('unknown')
            from_time = best.get('from', 0)
            timestamp_str = format_timestamp(from_time)
            video_url = best.get('video')

            anilist = best.get('anilist', {})
            if isinstance(anilist, dict):
                titles = anilist.get('title', {})
                title = titles.get('romaji') or titles.get('english') or self.get_text('unknown')
                title_native = titles.get('native') or self.get_text('unknown')
                is_adult = self.get_text('yes') if anilist.get('isAdult') else self.get_text('no')
                anilist_id = anilist.get('id', '')
            else:
                title = best.get('filename', self.get_text('unknown'))
                title_native = self.get_text('unknown')
                is_adult = self.get_text('unknown')
                anilist_id = anilist

            card_text = self.get_text('card_text').format(
                title=title,
                title_native=title_native,
                episode=episode,
                timestamp=timestamp_str,
                similarity=similarity_str,
                is_adult=is_adult,
                anilist_id=anilist_id
            )

            if similarity < 0.82:
                card_text = self.get_text('low_similarity').format(similarity=similarity_str) + card_text

            if video_url:
                try:
                    await message.edit_text(self.get_text('downloading_preview'))
                    async with aiohttp.ClientSession() as v_session:
                        async with v_session.get(video_url, timeout=12) as v_resp:
                            if v_resp.status == 200:
                                v_bytes = await v_resp.read()
                                v_io = io.BytesIO(v_bytes)
                                v_io.name = 'preview.mp4'

                                await client.send_video(
                                    chat_id=message.chat.id,
                                    video=v_io,
                                    caption=card_text,
                                    reply_to_message_id=reply.id if reply else None
                                )
                                await message.delete()
                                return
                except Exception:
                    pass

            await message.edit_text(
                card_text,
                link_preview_options=LinkPreviewOptions(is_disabled=False)
            )
        except Exception as e:
            await message.edit_text(self.get_text('api_error').format(error=e))
