import os
import telebot
import google.generativeai as genai
import re
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== ВАШИ ДАННЫЕ ==========
TOKEN = '8719783774:AAHp4nEoQxqM23xpU8ppmEq9OeiVbpfCljU'
GEMINI_KEY = 'AQ.Ab8RN6JJzEAFFt8IvzQ2ou_z1ADHRXte2hF3cJPzObXHYjhYwg'  # ЗАМЕНИТЕ!
ADMIN_ID = 8577385618

# ========== ИНИЦИАЛИЗАЦИЯ ==========
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
bot = telebot.TeleBot(TOKEN)

# Хранилище
user_history = {}

# ========== ФУНКЦИИ ==========
def get_smile_response(text, user_id):
    """Ответ Смайла на текст"""
    if user_id not in user_history:
        user_history[user_id] = []
    
    history = user_history[user_id]
    history.append(f"Пользователь: {text}")
    if len(history) > 10:
        history.pop(0)
    
    context = "\n".join(history[-5:])
    
    prompt = f"""Ты — Смайл 😊, дружелюбный ИИ-помощник.

Контекст:
{context}

Вопрос пользователя: {text}

Ответь кратко (до 500 символов), с эмодзи, по делу."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"😅 Ошибка: {str(e)[:100]}"

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "👋 Привет! Я **Смайл** — твой ИИ-помощник!\n\n"
        "💬 Просто напиши мне что-нибудь!\n"
        "Команды: /help, /clear",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(
        message,
        "📖 **Помощь:**\n\n"
        "💬 Напиши текст — я отвечу\n"
        "🧹 /clear — очистить историю\n"
        "ℹ️ /start — приветствие",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_id = message.from_user.id
    user_history[user_id] = []
    bot.reply_to(message, "🧹 История очищена!")

@bot.message_handler(func=lambda msg: msg.text and not msg.text.startswith('/'))
def handle_message(message):
    user_id = message.from_user.id
    text = message.text
    
    try:
        response = get_smile_response(text, user_id)
        bot.reply_to(message, response, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"😅 Ошибка: {str(e)[:100]}")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🤖 Смайл запущен!")
    bot.polling(none_stop=True)