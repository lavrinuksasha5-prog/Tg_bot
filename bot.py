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
    # 1. Берем имя без расширения
    stem = Path(name).stem
    
    # 2. Удаляем ВСЕ цифры из названия
    stem = re.sub(r'\d+', '', stem)
    
    # 3. Заменяем недопустимые символы на подчеркивание (оставляем буквы, пробелы, дефисы)
    stem = re.sub(r"[^\w\s\-]", "_", stem, flags=re.UNICODE)
    
    # 4. Убираем множественные подчеркивания и пробелы по краям
    stem = re.sub(r'[_\s]+', '_', stem).strip('_')
    
    return stem

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Бот работает. Скидывай .txt файлы.")

@dp.message(F.document)
async def handle_document(message: Message):
    doc = message.document

    if not doc.file_name.lower().endswith(".txt"):
        return

    src_path = TEMP_DIR / f"{message.from_user.id}_{doc.file_id}.txt"
    await bot.download(doc, destination=src_path)

    try:
        count = count_lines(src_path)
        base = clean_name(doc.file_name)
        # Формируем новое имя: ЦИФРЫ_БУКВЫ.txt
        new_name = f"{count}_{base}.txt"
        new_path = TEMP_DIR / new_name

        src_path.rename(new_path)

        # Пауза от бана
        await asyncio.sleep(2)

        # Отправляем обратно БЕЗ подписи
        await message.reply_document(
            FSInputFile(new_path, filename=new_name)
        )
    except Exception as e:
        print(f"Ошибка при обработке: {e}")
    finally:
        if src_path.exists():
            src_path.unlink(missing_ok=True)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
