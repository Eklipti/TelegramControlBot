import os
from aiogram.filters import Command
from aiogram.types import Message

from ..router import router
from ..paths_config import PATHS, save_paths


@router.message(Command("add_path"))
async def handle_add_path(message: Message) -> None:
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("❌ Используйте: /add_path <имя> <путь>")
        return

    name = args[1]
    path = args[2]

    if not os.path.exists(path):
        await message.answer(f"⚠️ Путь не существует: {path}")
        return

    PATHS[name] = os.path.abspath(path)
    save_paths(PATHS)
    await message.answer(f"✅ Путь сохранен:\n{name} → {PATHS[name]}")


@router.message(Command("list_paths"))
async def handle_list_paths(message: Message) -> None:
    if not PATHS:
        await message.answer("ℹ️ Нет зарегистрированных путей")
        return

    response = "📁 Зарегистрированные пути:\n\n"
    for name, path in PATHS.items():
        response += f"• <b>{name}</b>: {path}\n"
    await message.answer(response)


@router.message(Command("del_path"))
async def handle_del_path(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите имя пути для удаления")
        return

    name = args[1]
    if name in PATHS:
        del PATHS[name]
        save_paths(PATHS)
        await message.answer(f"✅ Путь удален: {name}")
    else:
        await message.answer(f"⚠️ Путь не найден: {name}")



