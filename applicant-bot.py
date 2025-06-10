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
    await update.message.reply_text("Привет! Напиши мне свой вопрос, и я постараюсь на него ответить. ", reply_markup=reply_markup)


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

    max_message_length = 4096  # Максимальная длина сообщения в Telegram
    current_message = "__*Часто задаваемые вопросы:*__\n\n"  # Текст текущего сообщения, которое собирается

    for i, item in enumerate(faq_data):
        # Форматируем вопрос и ответ для отправки
        formatted_question = f" __*{i + 1}. {item['question']}*__ \n\n"
        formatted_answer = f"{item['answer']}\n\n\n"

        # Проверяем, не превысит ли добавление вопроса и ответа лимит длины сообщения
        if len(current_message) + len(formatted_question) + len(formatted_answer) > max_message_length:
            # Отправляем текущее сообщение
            await update.message.reply_text(current_message, parse_mode=ParseMode.MARKDOWN)
            # Начинаем новое сообщение с вопроса и ответа
            current_message = formatted_question + formatted_answer
        else:
            # Добавляем вопрос и ответ к текущему сообщению
            current_message += formatted_question + formatted_answer

    # Отправляем оставшийся текст в текущем сообщении, если он есть
    if current_message:
        await update.message.reply_text(current_message, parse_mode=ParseMode.MARKDOWN)

async def useful_links(update: Update, context: CallbackContext) -> None:
    response = requests.get('http://127.0.0.1:8000/api/useful_list/')
    links_data = response.json()
    links_texts = "\n".join([f" {i + 1}. {item['name']} \n{item['link']}\n" for i, item in enumerate(links_data)])
    print(f'{links_texts}')
    await update.message.reply_text(f"__*Полезные ссылки:*__\n\n\n{links_texts}", parse_mode=ParseMode.MARKDOWN)



def main():
    application = Application.builder().token("///").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex('^(🔗 Полезные ссылки)$'), useful_links))
    application.add_handler(MessageHandler(filters.Regex('^(❓ Часто задаваемые вопросы)$'), faq))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Regex('^(👍 Помогло)$'), handle_helpful_button))
    application.add_handler(MessageHandler(filters.Regex('^(👎 Не помогло)$'), handle_not_helpful_button))

    application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
