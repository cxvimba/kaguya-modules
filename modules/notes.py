import random
from pyrogram import Client
from pyrogram.types import Message
from kaguya.types import BaseModule, ModuleInfo, on_command, on_fsm
from kaguya.utils.prefix import get_prefix


class NotesModule(BaseModule):
    meta = ModuleInfo(
        name='Заметки',
        description='Пользовательские заметки',
        version='1.0.0',
        author='cxvimba',
        commands={
            'n | н' : 'Отправить заметку',
            'n_save | н_сохранить': 'Сохранить заметку',
            'n_del | н_удалить': 'Удалить заметку'
        }
    )

    LANGUAGES = {
        'en': {
            'none': '<code>No notes saved</code>',
            'not_found': '❌ <b>Kaguya:</b> Note «{note}» not found.',
            'list_header': '📔 <b>Kaguya</b> | ✍️ Notes: <code>{notes}</code>\n\n',
            'save_usage': ' └ 💡 Type <code>{p}n_save &lt;Name&gt;</code> to create a new note.',
            'save_header': '📔 <b>Kaguya | Note Creation</b>\n',
            'note_already_taken': (
                '❌ <b>Kaguya:</b> Note «{note}» already exists.\n\n'
                'If you want to overwrite it, delete the old one first: <code>{p}n_del {note}</code>'
            ),
            'waiting_text': (
                '✅ <b>Kaguya:</b> Title «{header}» saved. '
                'Now send the text content to save the note.\n'
                '<i>Type <code>cancel</code> to abort.</i>'
            ),
            'cancel_save': '❌ <b>Kaguya:</b> Note creation cancelled.',
            'note_save': '✅ <b>Kaguya:</b> Note successfully saved as «{note}»!',
            'delete_usage': 'ℹ️ <b>Kaguya:</b> Missing note name! Type <code>{p}n_del &lt;Name&gt;</code>',
            'note_removed': '🗑 <b>Kaguya:</b> Note «{note}» has been deleted.',
            'not_text': '❌ <b>Kaguya:</b> Text content expected! Saving media is not supported.'
        },
        'ru': {
            'none': '<code>Заметки отсутствуют</code>',
            'not_found': '❌ <b>Kaguya:</b> Заметка «{note}» не найдена.',
            'list_header': '📔 <b>Kaguya</b> | ✍️ Заметки: <code>{notes}</code>\n\n',
            'save_usage': ' └ 💡 Напиши <code>{p}n_save &lt;Название&gt;</code> для создания заметки.',
            'save_header': '📔 <b>Kaguya | Сохранение заметок</b>\n',
            'note_already_taken': (
                '❌ <b>Kaguya:</b> Заметка «{note}» уже существует.\n\n'
                'Если хочешь перезаписать её, сначала удали старую: <code>{p}n_del {note}</code>'
            ),
            'waiting_text': (
                '✅ <b>Kaguya:</b> Заголовок «{header}» записан. '
                'Теперь напиши текст для сохранения.\n'
                '<i>Напиши <code>отмена</code> или <code>cancel</code>, чтобы отменить создание заметки.</i>'
            ),
            'cancel_save': '❌ <b>Kaguya:</b> Создание заметки отклонено.',
            'note_save': '✅ <b>Kaguya:</b> Заметка сохранена под именем «{note}»!',
            'delete_usage': 'ℹ️ <b>Kaguya:</b> Пропущено название заметки! Напиши <code>{p}n_del &lt;Название&gt;</code>',
            'note_removed': '🗑 <b>Kaguya:</b> Заметка «{note}» удалена.',
            'not_text': '❌ <b>Kaguya:</b> Ожидался текст для сохранения заметки! Сохранение медиафайлов не поддерживается.'
        }
    }


    @on_command(['n', 'н'])
    async def send_notes(self, client: Client, message: Message):
        """Отправляет пользовательскую отметку в чат."""
        notes = client.db.get_category('notes')
        notes_list = list(notes._cache)

        if len(message.command) < 2:
            text = self.get_text('list_header').format(notes=len(notes_list))

            if len(notes_list) > 0:
                for i, note in enumerate(notes_list, start=1):
                    text += f'{i}. {note}\n'
            else:
                p = get_prefix(client)
                text += f' ├ {self.get_text("none")}'
                text += f'\n{self.get_text("save_usage").format(p=p)}'
            await message.edit_text(text)

        else:
            note_name = message.command[1].strip()
            if note_name in notes_list:
                text = await notes.get(note_name)
            else:
                text = self.get_text('not_found').format(note=note_name)
            await message.edit_text(text)

    @on_command(['n_save', 'н_сохранить'])
    async def start_save_note(self, client: Client, message: Message):
        """Запускает fsm сохранения заметки."""
        p = get_prefix(client)
        if len(message.command) < 2:
            await message.edit_text(
                self.get_text('save_header') + self.get_text('save_usage').format(p=p)
            )
            return

        notes = client.db.get_category('notes')
        note_name = message.command[1].strip()

        if note_name in list(notes._cache):
            await message.edit_text(
                self.get_text('note_already_taken').format(note=note_name, p=p)
            )
        else:
            await client.set_fsm('waiting_note_text', {'note_name': note_name})
            await message.edit_text(
                self.get_text('waiting_text').format(header=note_name, p=p)
            )

    @on_command(['n_del', 'н_удалить'])
    async def delete_note(self, client: Client, message: Message):
        """Удаляет заметку."""
        if len(message.command) < 2:
            p = get_prefix(client)
            await message.edit_text(
                self.get_text('delete_usage').format(p=p)
            )
            return

        name_note = message.command[1].strip()
        notes = client.db.get_category('notes')
        if not await notes.get(name_note):
            await message.reply_text(
                self.get_text('not_found').format(note=name_note)
            )
            return

        await notes.delete(name_note)
        await message.edit_text(
            self.get_text('note_removed').format(note=name_note)
        )


    @on_fsm('waiting_note_text')
    async def save_note(self, client: Client, message: Message):
        """Сохраняет пользовательскую заметку."""
        if not (message.from_user and message.from_user.is_self or message.outgoing):
            return

        note_text = message.text or message.caption
        if not note_text:
            await message.edit_text(
                self.get_text('not_text')
            )
            return

        if note_text.strip().lower() in ('отмена', 'cancel'):
            await client.clear_fsm()
            await message.edit_text(
                self.get_text('cancel_save')
            )
            return

        fsm_data = await client.get_fsm_data()
        note_name = fsm_data.get('note_name', f'Заметка#{random.randint(1, 9999999)}')

        notes = client.db.get_category('notes')
        await notes.set(note_name, note_text)

        await client.clear_fsm()
        await message.reply_text(
            self.get_text('note_save').format(note=note_name)
        )
