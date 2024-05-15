import asyncio
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

import logging
# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [KeyboardButton("🔗 Полезные ссылки")],
        [KeyboardButton("❓ Часто задаваемые вопросы")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text("Привет! Напиши мне свой вопрос, и я постараюсь на него ответить.", reply_markup=reply_markup)


async def handle_message(update: Update, context: CallbackContext):
    question = update.message.text

    response = requests.post('http://127.0.0.1:8000/api/classify_question/', data={'question': question})
    result = response.json()

    category = result.get('category', 'unknown')  # Получите категорию
    response = requests.post('http://127.0.0.1:8000/api/get_answer/',
                             data={'question': question, 'category': category})
    result = response.json()
    print(result)
    message = result.get('answer', 'Извините, я не нашел ответа на ваш вопрос.')

    #  Отправка ответа с кнопками
    # keyboard = [
    #     [KeyboardButton("👍 Помогло"), KeyboardButton("👎 Не помогло")]
    # ]
    # reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    log_data = {
        'query': question,
        'response': message,
        'is_helpful': None
    }
    context.user_data['log_data'] = log_data

async def handle_helpful_button(update: Update, context: CallbackContext):
    log_data = context.user_data.get('log_data')
    if log_data:
        log_data['is_helpful'] = True
        requests.post('http://127.0.0.1:8000/api/log_user_query/', data=log_data)
        await update.message.reply_text("Спасибо за ваш отзыв! 😊")

async def handle_not_helpful_button(update: Update, context: CallbackContext):
    log_data = context.user_data.get('log_data')
    if log_data:
        log_data['is_helpful'] = False
        requests.post('http://127.0.0.1:8000/api/log_user_query/', data=log_data)
        await update.message.reply_text("Спасибо за ваш отзыв! 😊 Мне это поможет стать лучше")


async def faq(update: Update, context: CallbackContext) -> None:
    response = requests.get('http://127.0.0.1:8000/api/faq_list/')
    faq_data = response.json()
    faq_texts = "\n\n".join([f" __*{i + 1}. {item['question']}*__ \n\n{item['answer']}\n" for i, item in enumerate(faq_data)])
    await update.message.reply_text(f"__*Часто задаваемые вопросы:*__\n\n\n{faq_texts}", parse_mode=ParseMode.MARKDOWN)


def main():
    application = Application.builder().token("7148428054:AAGf47FlSRTF6SvsUgJ5hl3voPzRPIvBQUA").build()

    application.add_handler(CommandHandler("start", start))
    # application.add_handler(MessageHandler(filters.Regex('^(🔗 Полезные ссылки)$'), useful_links))
    application.add_handler(MessageHandler(filters.Regex('^(❓ Часто задаваемые вопросы)$'), faq))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Regex('^(👍 Помогло)$'), handle_helpful_button))
    application.add_handler(MessageHandler(filters.Regex('^(👎 Не помогло)$'), handle_not_helpful_button))

    application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
