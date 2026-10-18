import asyncio
import os
import re
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.exceptions import TelegramRetryAfter

# Railway берет токен из настроек (Variables)
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

# Блокировка для строгой очереди (чтобы бот не брался за 10 файлов сразу)
processing_lock = asyncio.Lock()

def count_lines(file_path: Path) -> int:
    count = 0
    with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as f:
        for line in f:
            if line.strip():
                count += 1
    return count

def clean_name(name: str) -> str:
    stem = Path(name).stem
    # Удаляем ВСЕ цифры из названия
    stem = re.sub(r'\d+', '', stem)
    # Оставляем только буквы, пробелы и дефисы
    stem = re.sub(r"[^\w\s\-]", "_", stem, flags=re.UNICODE)
    # Убираем лишние подчеркивания и пробелы
    stem = re.sub(r'[_\s]+', '_', stem).strip('_')
    return stem

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Бот работает. Скидывай .txt файлы. Обработка идет строго по очереди.")

@dp.message(F.document)
async def handle_document(message: Message):
    doc = message.document

    if not doc.file_name.lower().endswith(".txt"):
        return

    # Ставим файл в очередь
    async with processing_lock:
        src_path = TEMP_DIR / f"{message.from_user.id}_{doc.file_id}.txt"
        await bot.download(doc, destination=src_path)

        try:
            count = count_lines(src_path)
            base = clean_name(doc.file_name)
            new_name = f"{count}_{base}.txt"
            new_path = TEMP_DIR / new_name

            src_path.rename(new_path)

            # Жесткая пауза в 3 секунды ПЕРЕД отправкой
            await asyncio.sleep(3)

            # Пытаемся отправить файл (с защитой от антифлуда)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await message.reply_document(
                        FSInputFile(new_path, filename=new_name)
                    )
                    break # Если отправилось — выходим из цикла попыток
                except TelegramRetryAfter as e:
                    # Если Телеграм сказал "подожди", ждем столько, сколько он просит + 5 секунд для запаса
                    wait_time = e.retry_after + 5
                    print(f"Антифлуд! Ждем {wait_time} секунд...")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    print(f"Ошибка отправки (попытка {attempt+1}): {e}")
                    await asyncio.sleep(5) # Если другая ошибка, просто ждем 5 сек

        except Exception as e:
            print(f"Ошибка при обработке файла: {e}")
        finally:
            if src_path.exists():
                src_path.unlink(missing_ok=True)
            if new_path.exists():
                new_path.unlink(missing_ok=True)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
