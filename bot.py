import telebot
import google.generativeai as genai
import os

# ========== ДАННЫЕ ==========
TOKEN = '8719783774:AAHp4nEoQxqM23xpU8ppmEq9OeiVbpfCljU'
GEMINI_KEY = 'AQ.Ab8RN6JJzEAFFt8IvzQ2ou_z1ADHRXte2hF3cJPzObXHYjhYwg'  # ЗАМЕНИТЕ!

# ========== ИНИЦИАЛИЗАЦИЯ ==========
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
bot = telebot.TeleBot(TOKEN)

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Привет! Я **Смайл** — твой ИИ-друг!\n\n"
        "💬 Просто напиши мне что угодно!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    try:
        # Отправляем запрос в Gemini
        response = model.generate_content(
            f"Ты — Смайл 😊, дружелюбный помощник. Ответь: {message.text}"
        )
        bot.reply_to(message, response.text[:1000])  # Ограничиваем 1000 символов
    except Exception as e:
        bot.reply_to(message, f"😅 Ошибка: {str(e)[:100]}")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🤖 Бот Смайл запущен!")
    bot.polling(none_stop=True)