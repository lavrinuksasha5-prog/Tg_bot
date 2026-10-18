import asyncio
import os
import re
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile

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

@dp.message(F.document)
async def handle_document(message: Message):
    doc = message.document

    if not doc.file_name.lower().endswith(".txt"):
        await message.reply("Пришли, пожалуйста, файл .txt")
        return

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

        # Отправляем обратно
        await message.reply_document(
            FSInputFile(new_path, filename=new_name),
            caption=f"Готово: {count} строк\nИмя: <code>{new_name}</code>",
        )
    except Exception as e:
        await message.reply(f"Ошибка при обработке: {e}")
    finally:
        if src_path.exists():
            src_path.unlink(missing_ok=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
