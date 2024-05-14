from rest_framework import serializers, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Category, Tag, UserQueryLog, FAQ, Answer
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import joblib
import nltk
from nltk.corpus import stopwords
from .serializers import FAQSerializer
from django.db.models import Q  #  Для  использования  OR  в  запросах

from rest_framework import status #  Для  использования  HTTP  статус  кодов
import logging
# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка моделей
model = joblib.load('model.pkl')
vectorizer = joblib.load('tfidf_vectorizer.pkl')

# Скачивание стоп-слов для русского языка (если не скачаны)
nltk.download('stopwords')
russian_stopwords = stopwords.words('russian')

# Создание обратного словаря категорий
categories = Category.objects.all()
index_to_category = {i: category.name for i, category in enumerate(categories)}

print(f"к: {categories}\n i: {index_to_category}")

#  Функция предобработки текста
def preprocess_text(text):
    text = text.lower()
    tokens = nltk.word_tokenize(text)
    tokens = [token for token in tokens if token not in russian_stopwords and token.isalnum()]
    return " ".join(tokens)


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer

@api_view(['POST'])
def classify_question(request):
    try:
        data = request.data
        question = data.get('question', '')

        if not question:
            logger.warning("Пустой вопрос")
            return Response({'error': 'No question provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Предобработка текста
        preprocessed_question = preprocess_text(question)
        logger.info(f"Предобработанный вопрос: {preprocessed_question}")

        # Векторизация вопроса
        vectorized_question = vectorizer.transform([preprocessed_question])
        logger.info(f"Векторизованный вопрос: {vectorized_question}")

        # Предсказание категории вопроса
        predicted_category_index = model.predict(vectorized_question)[0]  # Исправлено!
        print(model.predict(vectorized_question)[0])
        predicted_category = index_to_category.get(predicted_category_index, 'Unknown')
        logger.info(f"Предсказанная категория: {predicted_category}")

        # Поиск ответа по предсказанной категории
        answer = find_answer(question, predicted_category)
        logger.info(f"Найденный ответ: {answer}")

        return Response({'answer': answer, 'category': predicted_category}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}", exc_info=True)
        return Response({'error': 'Internal Server Error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def get_answer(request):
    question = request.data.get('question')
    category_name = request.data.get('category')  # Получаем имя категории
    if question and category_name:
        try:
            answer = find_answer(question, category_name)
            return Response({'answer': answer})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    else:
        return Response({'error': 'No question or category provided'}, status=400)

def find_answer(question, category_name):
    tags = Tag.objects.filter(name__icontains=question)
    category = Category.objects.get(name=category_name)  # Ищем категорию
    if tags.exists():
        answer = Answer.objects.filter(tags__in=tags, category=category).first()  # Фильтруем по категории и тегам
        return answer.answer if answer else "Ответ не найден."
    else:
        return "Ответ не найден."


@require_http_methods(["POST"])
def log_user_query(request):
    try:
        data = request.POST
        query = data.get('query')
        response = data.get('response')
        is_helpful = data.get('is_helpful', False) # Добавлено получение is_helpful

        log_entry = UserQueryLog(query=query, response=response, is_helpful=is_helpful)
        log_entry.save()

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})