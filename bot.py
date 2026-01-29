import os
import logging
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp
import requests

# ==================== НАСТРОЙКА ====================

TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TOKEN:
    print("❌ TELEGRAM_TOKEN не найден!")
    exit(1)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

logger.info("=" * 50)
logger.info("🚀 ENERGY BOT - RENDER.COM")
logger.info(f"✅ Токен: {TOKEN[:10]}...")
logger.info("=" * 50)

# ==================== ПРОСТОЙ HTTP СЕРВЕР ДЛЯ RENDER ====================

class HealthHandler(BaseHTTPRequestHandler):
    """Обработчик health check запросов для Render"""
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Отключаем стандартное логирование запросов
        pass

def run_http_server():
    """Запуск простого HTTP сервера на порту 8080"""
    port = int(os.getenv('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"🌐 HTTP сервер запущен на порту {port}")
    logger.info(f"🏥 Health check: http://0.0.0.0:{port}/health")
    server.serve_forever()

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
        if "disk.yandex.ru" in url or "yadi.sk" in url:
            url = get_yandex_direct_link(url)
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        
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
        f"• Порт: 8080 (health check)\n"
        f"• Версия: Render Edition\n"
        f"• Файлы: Доступны"
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /id"""
    user_id = update.effective_user.id
    await update.message.reply_text(f"Ваш ID: `{user_id}`", parse_mode='Markdown')

# ==================== ЗАПУСК БОТА ====================

def run_telegram_bot():
    """Запуск Telegram бота"""
    try:
        app = Application.builder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(CommandHandler("price", price))
        app.add_handler(CommandHandler("stock", stock))
        app.add_handler(CommandHandler("price_MP", price_mp))
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("id", get_id))
        
        logger.info("✅ Telegram бот запущен")
        logger.info("⏳ Ожидаем команды...")
        
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Ошибка бота: {e}")
        import time
        time.sleep(10)
        run_telegram_bot()

def main():
    """Основная функция"""
    # Запускаем HTTP сервер в отдельном потоке
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Ждем запуска HTTP сервера
    import time
    time.sleep(2)
    
    # Запускаем Telegram бота
    run_telegram_bot()

if __name__ == "__main__":
    main()