import os
import telebot
import google.generativeai as genai
import re
import yt_dlp
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== ВАШИ ДАННЫЕ ==========
TOKEN = '8719783774:AAHp4nEoQxqM23xpU8ppmEq9OeiVbpfCljU'
GEMINI_KEY = 'AQ.Ab8RN6JEtEtiIyJpZbxrH2ePFbCMfcqFTnssccwC5V8NRBcDJg'  # ВСТАВЬТЕ ВАШ КЛЮЧ
ADMIN_ID = 8577385618

# ========== ИНИЦИАЛИЗАЦИЯ ==========
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
bot = telebot.TeleBot(TOKEN)

# Хранилище для истории (простое)
user_history = {}

# ========== ФУНКЦИИ ==========
def extract_video_url(text):
    """Ищет ссылки на видео"""
    patterns = [
        r'(https?://(?:www\.)?tiktok\.com/\S+)',
        r'(https?://(?:www\.)?youtube\.com/watch\?v=\S+)',
        r'(https?://youtu\.be/\S+)',
        r'(https?://(?:www\.)?instagram\.com/(?:reel|p)/\S+)'  # Инстаграм
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def download_video(url):
    """Скачивает видео"""
    ydl_opts = {
        'outtmpl': 'video.mp4',
        'format': 'best[ext=mp4]',
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return 'video.mp4'
    except Exception as e:
        print(f"Ошибка скачивания: {e}")
        return None

def analyze_video(file_path):
    """Анализирует видео через Gemini"""
    try:
        # Загружаем видео
        video_file = genai.upload_file(file_path)
        
        # Ждём обработки
        timeout = 60
        start = time.time()
        while video_file.state.name == "PROCESSING":
            if time.time() - start > timeout:
                return "⏰ Превышено время ожидания обработки видео"
            time.sleep(2)
        
        if video_file.state.name == "FAILED":
            return "❌ Не удалось обработать видео"
        
        # Промпт для Смайла
        prompt = """Ты — Смайл 😊, дружелюбный и весёлый ИИ-помощник!
        Проанализируй это видео максимально подробно:

        🎯 ОПИШИ:
        1. Что происходит на видео? (сюжет, действия)
        2. Кто участвует? (люди, персонажи, объекты)
        3. Какое настроение и атмосфера?
        4. Есть ли текст, субтитры или диалоги? Распиши их.
        5. Какой звуковой фон? (музыка, шумы, голоса)

        💡 ВЫВОД:
        - Чему учит это видео?
        - Какой главный посыл?
        - Что можно взять из этого в жизнь?

        ОТВЕЧАЙ ЯРКО, С ЭМОДЗИ, КАК ЛУЧШИЙ ДРУГ! 🌟"""
        
        response = model.generate_content([prompt, video_file])
        return response.text
        
    except Exception as e:
        return f"😅 Ошибка при анализе: {str(e)[:200]}"

def get_smile_response(text, user_id):
    """Генерация ответа с контекстом"""
    # Сохраняем историю (последние 5 сообщений)
    if user_id not in user_history:
        user_history[user_id] = []
    
    history = user_history[user_id]
    history.append(f"Пользователь: {text}")
    if len(history) > 10:
        history.pop(0)
    
    context = "\n".join(history[-5:])
    
    prompt = f"""Ты — Смайл 😊, весёлый, умный и очень дружелюбный ИИ-помощник.

    КОНТЕКСТ ОБЩЕНИЯ:
    {context}

    ПРАВИЛА ОТВЕТА:
    - Отвечай живо, с юмором и эмодзи
    - Будь полезным и информативным
    - Если не знаешь — честно скажи
    - Используй форматирование Markdown (жирный, курсив)
    - Длина ответа: 2-5 предложений для простых вопросов, подробнее для сложных

    ВОПРОС ПОЛЬЗОВАТЕЛЯ: {text}
    
    ОТВЕТ СМАЙЛА:"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"😅 Не могу ответить: {str(e)[:100]}"

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📹 О видео", callback_data="help_video"),
        InlineKeyboardButton("💬 О боте", callback_data="help_bot")
    )
    markup.row(
        InlineKeyboardButton("👨‍💻 Создатель", url="https://t.me/FallenMercenary")
    )
    
    bot.reply_to(
        message,
        "👋 Привет! Я **Смайл** — твой персональный ИИ-помощник!\n\n"
        "🎯 **Что я умею:**\n"
        "• Отвечать на любые вопросы как друг\n"
        "• Анализировать видео из TikTok, YouTube, Instagram\n"
        "• Давать полезные советы и идеи\n\n"
        "📹 **Как пользоваться:**\n"
        "Просто отправь мне ссылку на видео или задай вопрос!",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(
        message,
        "📖 **Помощь по боту Смайл:**\n\n"
        "🎬 **Видео:** отправь ссылку на TikTok/YouTube/Instagram\n"
        "💬 **Текст:** просто напиши сообщение\n"
        "🔄 **Контекст:** я помню последние 5 сообщений\n"
        "🧹 **Очистить историю:** /clear\n"
        "ℹ️ **Инфо:** /stats",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_id = message.from_user.id
    if user_id in user_history:
        user_history[user_id] = []
        bot.reply_to(message, "🧹 История очищена! Можем начать заново 😊")
    else:
        bot.reply_to(message, "📭 У нас и так нет истории")

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    count = len(user_history.get(user_id, []))
    bot.reply_to(
        message,
        f"📊 **Статистика Смайла:**\n\n"
        f"• Сообщений в диалоге: {count}\n"
        f"• Всего пользователей: {len(user_history)}\n"
        f"• Статус: 🟢 Активен\n\n"
        f"❤️ Спасибо, что пользуешься!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda msg: msg.text and not msg.text.startswith('/'))
def handle_message(message):
    user_id = message.from_user.id
    text = message.text
    
    # Проверка на видео
    video_url = extract_video_url(text)
    
    if video_url:
        # === АНАЛИЗ ВИДЕО ===
        status = bot.reply_to(message, "🔄 Скачиваю видео... Подожди немного")
        
        try:
            bot.edit_message_text("📥 Скачиваю...", message.chat.id, status.id)
            video_path = download_video(video_url)
            
            if not video_path:
                bot.edit_message_text(
                    "❌ Не удалось скачать видео. Проверь ссылку!\n\n"
                    "Поддерживаются:\n"
                    "• TikTok (https://tiktok.com/...)\n"
                    "• YouTube (https://youtube.com/watch?v=...)\n"
                    "• Instagram (https://instagram.com/reel/...)",
                    message.chat.id, status.id
                )
                return
            
            bot.edit_message_text("🧠 Анализирую видео через ИИ...", message.chat.id, status.id)
            analysis = analyze_video(video_path)
            
            # Отправляем результат
            result_text = f"🎬 **Анализ видео от Смайла:**\n\n{analysis}"
            
            # Если слишком длинное — разбиваем
            if len(result_text) > 4000:
                parts = [result_text[i:i+4000] for i in range(0, len(result_text), 4000)]
                for part in parts:
                    bot.send_message(message.chat.id, part, parse_mode='Markdown')
                bot.delete_message(message.chat.id, status.id)
            else:
                bot.edit_message_text(
                    result_text,
                    message.chat.id, status.id,
                    parse_mode='Markdown'
                )
            
            # Удаляем файл
            if os.path.exists(video_path):
                os.remove(video_path)
                
        except Exception as e:
            bot.edit_message_text(
                f"😭 Ошибка: {str(e)[:200]}\n\n"
                "Попробуй другую ссылку или отправь текст",
                message.chat.id, status.id
            )
    else:
        # === ОБЫЧНЫЙ ДИАЛОГ ===
        try:
            response = get_smile_response(text, user_id)
            
            # Разбиваем длинный ответ
            if len(response) > 4000:
                for i in range(0, len(response), 4000):
                    bot.send_message(message.chat.id, response[i:i+4000], parse_mode='Markdown')
            else:
                bot.reply_to(message, response, parse_mode='Markdown')
                
        except Exception as e:
            bot.reply_to(message, f"😅 Упс... Ошибка: {str(e)[:100]}")

# ========== ОБРАБОТЧИК КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "help_video":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "📹 **Как анализировать видео:**\n\n"
            "1️⃣ Найди видео в TikTok/YouTube/Instagram\n"
            "2️⃣ Скопируй ссылку из браузера\n"
            "3️⃣ Отправь её в чат с ботом\n\n"
            "⏳ Обработка занимает 30-60 секунд\n"
            "📊 Я опишу сюжет, участников, музыку и дам вывод!",
            parse_mode='Markdown'
        )
    elif call.data == "help_bot":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "🤖 **О боте Смайл:**\n\n"
            "Я создан на основе **Google Gemini AI**\n"
            "Умею анализировать видео и общаться на любые темы\n\n"
            "💡 **Совет:** Чем подробнее вопрос — тем полезнее ответ!\n"
            "📈 Контекст сохраняется на 5 сообщений\n\n"
            "Создано с ❤️ для Telegram",
            parse_mode='Markdown'
        )

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🤖 Бот Смайл запущен!")
    print(f"👤 Admin ID: {ADMIN_ID}")
    print(f"🔑 Bot token: {TOKEN[:10]}...")
    try:
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        print(f"Ошибка: {e}")