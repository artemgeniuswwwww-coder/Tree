import os
import telebot
import google.generativeai as genai
import re
import yt_dlp
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== КОНФИГ ==========
TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_KEY')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

bot = telebot.TeleBot(TOKEN)
ADMIN_ID = os.getenv('ADMIN_ID')  # Ваш Telegram ID для логов

# ========== ФУНКЦИИ ==========
def extract_video_url(text):
    """Ищет ссылку на TikTok или YouTube"""
    patterns = [
        r'(https?://(?:www\.)?tiktok\.com/\S+)',
        r'(https?://(?:www\.)?youtube\.com/watch\?v=\S+)',
        r'(https?://youtu\.be/\S+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def download_video(url):
    """Скачивает видео в MP4"""
    ydl_opts = {
        'outtmpl': 'video.mp4',
        'format': 'best[ext=mp4]',
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return 'video.mp4'
    except:
        return None

def analyze_video(file_path):
    """Отправляет видео в Gemini для анализа"""
    try:
        video_file = genai.upload_file(file_path)
        # Ждём обработки
        while video_file.state.name == "PROCESSING":
            continue
        
        prompt = """Ты — Смайл, дружелюбный ИИ-помощник. 
        Проанализируй это видео подробно:
        1. Что происходит на видео?
        2. Основная тема или идея.
        3. Настроение и атмосфера.
        4. Если есть текст или диалоги — расшифруй.
        5. Дай полезный совет или вывод.
        Ответ должен быть живым, с эмодзи, как у друга."""
        
        response = model.generate_content([prompt, video_file])
        return response.text
    except Exception as e:
        return f"😅 Ошибка анализа: {str(e)}"

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "👋 Привет! Я **Смайл** — твой ИИ-друг!\n\n"
        "📹 Просто отправь мне ссылку на видео из:\n"
        "• TikTok (https://tiktok.com/...)\n"
        "• YouTube (https://youtube.com/watch?v=...)\n\n"
        "💬 Или просто напиши текст — я отвечу как Gemini!"
    )

@bot.message_handler(func=lambda msg: msg.text and not msg.text.startswith('/'))
def handle_message(message):
    text = message.text
    
    # Проверяем, есть ли ссылка на видео
    video_url = extract_video_url(text)
    
    if video_url:
        # === ОБРАБОТКА ВИДЕО ===
        status_msg = bot.reply_to(message, "🔄 Скачиваю видео... Это может занять минуту")
        
        try:
            # Скачиваем
            bot.edit_message_text("📥 Скачиваю...", message.chat.id, status_msg.id)
            video_path = download_video(video_url)
            
            if not video_path:
                bot.edit_message_text(
                    "❌ Не удалось скачать видео. Проверьте ссылку.",
                    message.chat.id, status_msg.id
                )
                return
            
            # Анализируем
            bot.edit_message_text("🧠 Анализирую видео через ИИ...", message.chat.id, status_msg.id)
            analysis = analyze_video(video_path)
            
            # Отправляем результат
            bot.edit_message_text(
                f"🎬 **Анализ видео:**\n\n{analysis}",
                message.chat.id, status_msg.id,
                parse_mode='Markdown'
            )
            
            # Удаляем файл
            os.remove(video_path)
            
        except Exception as e:
            bot.edit_message_text(
                f"😭 Произошла ошибка: {str(e)[:200]}",
                message.chat.id, status_msg.id
            )
    else:
        # === ОБЫЧНЫЙ ЧАТ ===
        try:
            response = model.generate_content(
                f"Ты — Смайл, весёлый и умный ИИ-друг. Отвечай живо, с эмодзи. Вопрос: {text}"
            )
            # Разбиваем длинные ответы
            if len(response.text) > 4000:
                for i in range(0, len(response.text), 4000):
                    bot.reply_to(message, response.text[i:i+4000])
            else:
                bot.reply_to(message, response.text)
        except Exception as e:
            bot.reply_to(message, f"😅 Не могу ответить: {str(e)[:100]}")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🤖 Бот Смайл запущен!")
    bot.polling(none_stop=True)
