import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp
import requests

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота из переменных окружения
TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TOKEN:
    logger.error("❌ TELEGRAM_TOKEN не найден!")
    exit(1)

logger.info(f"✅ Токен получен: {TOKEN[:10]}...")

# URL файлов
YANDEX_PRICE_URL = "https://disk.yandex.ru/i/SmIWUAht3f_ceQ"
FTP_STOCK_URL = "ftp://energy:H7wY}vM9WcnScPTLs8]-AaF#@ftp.compel.ru/Ostatki_Specavtomatika.xls"
GOOGLE_PRICE_MP_URL = "https://docs.google.com/spreadsheets/d/1UyVdqe6s-C8l8DJGYyvgyBVjXNW7re0QMAZ0f9Cbpo0/export?format=xlsx"

def get_yandex_direct_link(yandex_url: str) -> str:
    """Получаем прямую ссылку для скачивания с Яндекс.Диска"""
    try:
        api_url = f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={yandex_url}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('href', yandex_url)
        return yandex_url
            
    except Exception as e:
        logger.error(f"Ошибка Яндекс.Диска: {e}")
        return yandex_url

async def download_file(url: str) -> bytes:
    """Асинхронное скачивание файла"""
    try:
        # Если Яндекс.Диск - получаем прямую ссылку
        if "disk.yandex.ru" in url or "yadi.sk" in url:
            url = get_yandex_direct_link(url)
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = bytearray()
                    async for chunk in response.content.iter_chunked(8192):
                        content.extend(chunk)
                    logger.info(f"Файл скачан: {len(content)} байт")
                    return bytes(content)
                else:
                    logger.error(f"HTTP ошибка: {response.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🤖 Добро пожаловать!\n"
        "Я бот для загрузки файлов с сайта Энергия.рф\n\n"
        "📁 Доступные файлы:\n"
        "/price - Прайс-лист\n"
        "/stock - Остатки\n"
        "/price_MP - Прайс для МП\n\n"
        "🔧 Сервисные:\n"
        "/help - Справка\n"
        "/status - Статус\n"
        "/id - Ваш ID"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📋 Справка:\n\n"
        "📥 Загрузка файлов:\n"
        "/price - Скачать прайс с Яндекс.Диска\n"
        "/stock - Скачать остатки с FTP\n"
        "/price_MP - Скачать прайс для МП\n\n"
        "⚙️ Сервисные:\n"
        "/start - Приветствие\n"
        "/status - Статус бота\n"
        "/id - Узнать ID\n"
        "/help - Эта справка"
    )

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /price"""
    await send_file(update, YANDEX_PRICE_URL, "Прайс_Энергия.xlsx", "прайс-лист")

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stock"""
    await send_file(update, FTP_STOCK_URL, "Остатки_Энергия.xls", "остатки")

async def price_mp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /price_MP"""
    await send_file(update, GOOGLE_PRICE_MP_URL, "Прайс_МП.xlsx", "прайс для МП")

async def send_file(update: Update, url: str, filename: str, description: str):
    """Отправка файла пользователю"""
    status_msg = await update.message.reply_text(f"⏳ Скачиваю {description}...")
    
    try:
        file_content = await download_file(url)
        
        if file_content is None:
            await status_msg.edit_text(f"❌ Не удалось скачать {description}")
            return
        
        # Проверка размера (Telegram limit ~50MB)
        if len(file_content) > 45 * 1024 * 1024:
            await status_msg.edit_text(f"❌ Файл слишком большой (>45MB)")
            return
        
        await update.message.reply_document(
            document=file_content,
            filename=filename,
            caption=f"📁 {filename}"
        )
        
        await status_msg.edit_text(f"✅ {description} отправлен!")
        
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        await status_msg.edit_text(f"❌ Ошибка отправки")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status"""
    import datetime
    await update.message.reply_text(
        f"📊 Статус бота:\n"
        f"• Хостинг: Render.com\n"
        f"• Состояние: ✅ Активен 24/7\n"
        f"• Время: {datetime.datetime.now().strftime('%H:%M:%S')}\n"
        f"• Версия: 3.0\n"
        f"• Файлы: Доступны"
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /id"""
    user_id = update.effective_user.id
    await update.message.reply_text(f"Ваш ID: `{user_id}`", parse_mode='Markdown')

def main():
    """Запуск бота"""
    logger.info("🚀 Energy Bot запускается на Render...")
    
    app = Application.builder().token(TOKEN).build()
    
    # Регистрация команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("stock", stock_command))
    app.add_handler(CommandHandler("price_MP", price_mp_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("id", id_command))
    
    logger.info("✅ Бот настроен. Ожидаем команды...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()