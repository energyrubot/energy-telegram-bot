import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp
import requests

# ==================== НАСТРОЙКА ====================

# Получаем токен из переменных окружения
TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TOKEN:
    print("❌ ОШИБКА: TELEGRAM_TOKEN не найден!")
    print("Добавьте в Environment Variables Render:")
    print("Key: TELEGRAM_TOKEN")
    print("Value: ваш_токен_бота")
    exit(1)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

logger.info("=" * 50)
logger.info("🚀 ENERGY BOT - RENDER.COM")
logger.info(f"✅ Токен получен: {TOKEN[:10]}...")
logger.info("=" * 50)

# ==================== URL ФАЙЛОВ ====================

YANDEX_PRICE_URL = "https://disk.yandex.ru/i/SmIWUAht3f_ceQ"
FTP_STOCK_URL = "ftp://energy:H7wY}vM9WcnScPTLs8]-AaF#@ftp.compel.ru/Ostatki_Specavtomatika.xls"
GOOGLE_PRICE_MP_URL = "https://docs.google.com/spreadsheets/d/1UyVdqe6s-C8l8DJGYyvgyBVjXNW7re0QMAZ0f9Cbpo0/export?format=xlsx"

# ==================== ФУНКЦИИ ДЛЯ ФАЙЛОВ ====================

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
        
        # Используем aiohttp для асинхронного скачивания
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=60) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f"HTTP ошибка: {response.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None

# ==================== TELEGRAM КОМАНДЫ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🤖 Добро пожаловать!\n"
        "Я бот для загрузки файлов с сайта Энергия.рф\n\n"
        "📁 Доступные файлы:\n"
        "/price - Прайс-лист\n"
        "/stock - Остатки\n"
        "/price_MP - Прайс для МП\n\n"
        "🔧 Другие команды:\n"
        "/help - Справка\n"
        "/status - Статус\n"
        "/id - Ваш ID\n\n"
        "⚡ Хостинг: Render.com\n"
        "✅ Активен 24/7"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📋 Справка:\n\n"
        "📥 Загрузка файлов:\n"
        "/price - Прайс с Яндекс.Диска\n"
        "/stock - Остатки с FTP\n"
        "/price_MP - Прайс для МП\n\n"
        "⚙️ Сервисные:\n"
        "/start - Приветствие\n"
        "/status - Статус бота\n"
        "/id - Узнать ID\n"
        "/help - Эта справка"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /price"""
    await send_file(update, YANDEX_PRICE_URL, "Прайс_Энергия.xlsx", "прайс-лист")

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stock"""
    await send_file(update, FTP_STOCK_URL, "Остатки_Энергия.xls", "остатки")

async def price_mp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /price_MP"""
    await send_file(update, GOOGLE_PRICE_MP_URL, "Прайс_МП.xlsx", "прайс для МП")

async def send_file(update: Update, url: str, filename: str, description: str):
    """Отправка файла"""
    msg = await update.message.reply_text(f"⏳ Скачиваю {description}...")
    
    try:
        file_data = await download_file(url)
        
        if file_data:
            await update.message.reply_document(
                document=file_data,
                filename=filename,
                caption=f"📁 {filename}"
            )
            await msg.edit_text(f"✅ {description} отправлен!")
        else:
            await msg.edit_text(f"❌ Не удалось скачать {description}")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await msg.edit_text(f"❌ Ошибка при отправке")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status"""
    import datetime
    await update.message.reply_text(
        f"📊 Статус бота:\n"
        f"• Хостинг: Render.com\n"
        f"• Состояние: ✅ Активен\n"
        f"• Время: {datetime.datetime.now().strftime('%H:%M:%S')}\n"
        f"• Версия: Render Edition\n"
        f"• Файлы: Доступны"
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /id"""
    user_id = update.effective_user.id
    await update.message.reply_text(f"Ваш ID: `{user_id}`", parse_mode='Markdown')

# ==================== ЗАПУСК БОТА ====================

def main():
    """Запуск бота"""
    try:
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # Регистрируем команды
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(CommandHandler("price", price))
        app.add_handler(CommandHandler("stock", stock))
        app.add_handler(CommandHandler("price_MP", price_mp))
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("id", get_id))
        
        logger.info("✅ Бот запущен на Render")
        logger.info("⏳ Ожидаем команды...")
        
        # Запускаем polling
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")
        logger.info("Перезапуск через 10 секунд...")
        import time
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()