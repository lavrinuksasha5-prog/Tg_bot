import asyncio
import os
import re
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

# Railway берет токен из настроек (Variables)
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создаем папку для временных файлов
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

def count_lines(file_path: Path) -> int:
    count = 0
    with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as f:
        for line in f:
            if line.strip():
                count += 1
    return count

def clean_name(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^\w\s\-]", "_", stem, flags=re.UNICODE)
    return stem.strip()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    # Короткий ответ на старт, чтобы бот не казался мертвым
    await message.answer("Бот работает. Скидывай .txt файлы.")

@dp.message(F.document)
async def handle_document(message: Message):
    doc = message.document

    if not doc.file_name.lower().endswith(".txt"):
        return # Если не txt - просто игнорируем (ничего не пишем)

    # Скачиваем файл
    src_path = TEMP_DIR / f"{message.from_user.id}_{doc.file_id}.txt"
    await bot.download(doc, destination=src_path)

    try:
        count = count_lines(src_path)
        base = clean_name(doc.file_name)
        new_name = f"{count}_{base}.txt"
        new_path = TEMP_DIR / new_name

        # Переименовываем
        src_path.rename(new_path)

        # Пауза, чтобы Telegram не забанил за флуд
        await asyncio.sleep(2)

        # Отправляем обратно БЕЗ подписи (caption)
        await message.reply_document(
            FSInputFile(new_path, filename=new_name)
        )
    except Exception as e:
        # Если произошла ошибка, пишем только в консоль Railway, в телегу не шлем
        print(f"Ошибка при обработке: {e}")
    finally:
        if src_path.exists():
            src_path.unlink(missing_ok=True)

async def main():
    # Удаляем старые вебхуки (на случай если бот завис)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
