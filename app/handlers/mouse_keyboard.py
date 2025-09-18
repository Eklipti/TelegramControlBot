# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

import cv2
import numpy as np
import pyautogui
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from ..router import router
from ..state import mouse_positions


@router.message(Command("mouse_move_rel"))
async def handle_mouse_move_rel(message: Message) -> None:
    try:
        _, dx, dy = message.text.split()
        pyautogui.moveRel(int(dx), int(dy))
        await message.answer(f"🖱 Мышь перемещена на ({dx}, {dy})")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}\nИспользуйте: /mouse_move_rel dx dy")


@router.message(Command("screen_mark"))
async def handle_screen_mark(message: Message) -> None:
    try:
        screenshot = pyautogui.screenshot()
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        width, height = screenshot.size
        for x in range(0, width, 100):
            cv2.line(img, (x, 0), (x, height), (0, 0, 255), 1)
            cv2.putText(img, str(x), (x+5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,255), 1)
        for y in range(0, height, 100):
            cv2.line(img, (0, y), (width, y), (0, 0, 255), 1)
            cv2.putText(img, str(y), (5, y+15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,255), 1)
        mx, my = pyautogui.position()
        cv2.circle(img, (mx, my), 10, (0, 255, 0), 2)
        cv2.putText(img, f"Mouse: ({mx},{my})", (mx+15, my-15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        _, buffer = cv2.imencode('.png', img)
        await message.answer_photo(BufferedInputFile(buffer.tobytes(), filename='screen_marked.png'),
                                   caption=f"📐 Экран с разметкой\nТекущая позиция: ({mx}, {my})")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")


@router.message(Command("mouse_save"))
async def handle_mouse_save(message: Message) -> None:
    try:
        name = message.text.split()[1]
        x, y = pyautogui.position()
        mouse_positions[name] = (x, y)
        await message.answer(f"📍 Позиция сохранена как '{name}' ({x}, {y})")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}\nИспользуйте: /mouse_save имя_позиции")


@router.message(Command("mouse_goto"))
async def handle_mouse_goto(message: Message) -> None:
    try:
        name = message.text.split()[1]
        x, y = mouse_positions[name]
        pyautogui.moveTo(x, y)
        await message.answer(f"🖱 Мышь перемещена в позицию '{name}' ({x}, {y})")
    except Exception as e:
        available = "\n".join([f"- {k}" for k in mouse_positions.keys()])
        await message.answer(f"⚠️ Ошибка: {e}\nДоступные позиции:\n{available}")


@router.message(Command("mouse_speed"))
async def handle_mouse_speed(message: Message) -> None:
    try:
        speed = float(message.text.split()[1])
        pyautogui.MINIMUM_DURATION = speed
        pyautogui.MINIMUM_SLEEP = speed
        await message.answer(f"⚡ Скорость мыши установлена: {speed} сек")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}\nИспользуйте: /mouse_speed 0.1 (быстро) или 1.0 (медленно)")


@router.message(Command("mouse_move"))
async def handle_mouse_move(message: Message) -> None:
    try:
        _, x, y = message.text.split()
        pyautogui.moveTo(int(x), int(y))
        await message.answer(f"🖱 Мышь перемещена в ({x}, {y})")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}\nИспользуйте: /mouse_move x y")


@router.message(Command("mouse_click"))
async def handle_mouse_click(message: Message) -> None:
    try:
        button = 'left'
        if len(message.text.split()) > 1:
            button = message.text.split()[1]
        pyautogui.click(button=button)
        await message.answer(f"🖱 Клик {button} кнопкой")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}\nДоступные кнопки: left, right, middle")


@router.message(Command("mouse_scroll"))
async def handle_mouse_scroll(message: Message) -> None:
    try:
        _, steps = message.text.split()
        pyautogui.scroll(int(steps))
        await message.answer(f"🖱 Скролл на {steps} шагов")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}\nИспользуйте: /mouse_scroll steps")


@router.message(Command("key"))
async def handle_key_press(message: Message) -> None:
    try:
        args = message.text.split()[1:]
        if not args:
            await message.answer("⚠️ Укажите клавиши для нажатия")
            return
        keys_str = ' '.join(args)
        keys = [k.strip() for k in keys_str.split('+') if k.strip()]
        if not keys:
            await message.answer("⚠️ Не указаны клавиши")
            return
        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)
        await message.answer(f"⌨ Нажаты клавиши: {'+'.join(keys)}")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}\nПример: /key enter или /key ctrl+alt+delete")


@router.message(Command("type"))
async def handle_type_text(message: Message) -> None:
    try:
        text = message.text.split(' ', 1)[1]
        pyautogui.typewrite(text)
        await message.answer(f"⌨ Введен текст: {text}")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}\nИспользуйте: /type ваш_текст")



