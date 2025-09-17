import os
import shutil
import tempfile
import time
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from ..router import router


@router.message(Command("upload"))
async def handle_upload_command(message: Message) -> None:
    from ..state import upload_requests

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите путь для сохранения после /upload")
        return
    target_path = args[1]
    upload_requests[message.chat.id] = target_path
    await message.answer(
        f"📤 Отправьте файл для сохранения по пути:\n{target_path}\n\nИспользуйте /cancel для отмены."
    )


@router.message(Command("download"))
async def handle_download_command(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите путь к файлу/папке после /download")
        return
    path = args[1]

    try:
        if not os.path.exists(path):
            await message.answer(f"⚠️ Путь не существует: {path}")
            return

        if os.path.isfile(path):
            with open(path, "rb") as f:
                await message.answer_document(BufferedInputFile(f.read(), filename=os.path.basename(path)),
                                              caption=f"📥 Файл: {path}")
        else:
            msg = await message.answer("📦 Архивация папки...")
            zip_path = shutil.make_archive(
                base_name=os.path.join(tempfile.gettempdir(), f"folder_{time.time()}"),
                format='zip',
                root_dir=path
            )
            with open(zip_path, 'rb') as zip_file:
                await message.answer_document(BufferedInputFile(zip_file.read(), filename=os.path.basename(zip_path)),
                                              caption=f"📁 Папка: {path}")
            os.remove(zip_path)
            await msg.delete()
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")


@router.message(Command("cut"))
async def handle_cut_command(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите путь к файлу после /cut")
        return

    file_path = args[1]
    try:
        if not os.path.exists(file_path):
            await message.answer(f"⚠️ Файл не существует: {file_path}")
            return
        if not os.path.isfile(file_path):
            await message.answer(f"⚠️ Указанный путь не является файлом: {file_path}")
            return
        with open(file_path, 'rb') as f:
            await message.answer_document(BufferedInputFile(f.read(), filename=os.path.basename(file_path)),
                                          caption=f"✂️ Файл отправлен и УДАЛЁН: {file_path}")
        os.remove(file_path)
        await message.answer(f"✅ Файл успешно удалён: {file_path}")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при отправке или удалении файла: {e}")



