from django.db.models import Q
from functools import reduce
from operator import or_

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .serializers import FAQSerializer
from .models import Category, Tag, UserQueryLog, FAQ, Answer

from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, Doc
import nltk
import numpy as np
import re
import fasttext
import joblib
from nltk.corpus import stopwords


import logging
# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка моделей
model = joblib.load('model.pkl')
ft_model = fasttext.load_model("./fast.bin")

# Скачивание стоп-слов для русского языка (если не скачаны)
nltk.download('stopwords')
nltk.download('punkt')\

# Инициализация natasha
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)

def preprocess_text(text):
    text = re.sub(r'[^\w\s]', '', text.lower())
    doc = Doc(text.lower())
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    tokens = [token.lemma if token.lemma is not None else token.text for token in doc.tokens if token.pos not in ['PUNCT', 'ADP', 'CONJ', 'PRON']]
    return list(tokens)

def get_sentence_vector(text):
    vectors = [ft_model.get_word_vector(word) for word in text]
    return np.mean(vectors, axis=0)

@api_view(['POST'])
def classify_question(request):
    try:
        data = request.data
        question = data.get('question', '')

        if not question:
            logger.warning("Пустой вопрос")
            return Response({'error': 'No question provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Предобработка текста
        processed_question = preprocess_text(question)
        logger.info(f"Предобработанный вопрос: {processed_question}")

        # Векторизация вопроса
        vectorized_question = get_sentence_vector(processed_question)
        logger.info(f"Векторизованный вопрос: {vectorized_question}")

        # Предсказание категории вопроса
        predicted_category = model.predict([vectorized_question])[0]  # Передаем вектор как список
        print(predicted_category)


        logger.info(f"Предсказанная категория: {predicted_category}")

        return Response({'category': predicted_category}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}", exc_info=True)
        return Response({'error': 'Internal Server Error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def get_answer(request):
    question = request.data.get('question')
    processed_question = preprocess_text(question)

    category_name = request.data.get('category')  # Получаем имя категории
    if processed_question and category_name:
        try:
            answer = find_answer(processed_question, category_name)
            print(answer)
            return Response({'answer': answer})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    else:
        return Response({'error': 'No question or category provided'}, status=400)

def find_answer(question, category_name):
    q_object = reduce(or_, (Q(name__icontains=word) for word in question))
    tags = Tag.objects.filter(q_object)
    # tags = Tag.objects.filter(name__in=question) # Совпадение по точному слову(одному)
    print(f"t: {tags.values_list('name', flat=True)}")
    category = Category.objects.get(name=category_name)  # Ищем категорию
    print(f"c: {category}")
    if tags.exists():
        answer = Answer.objects.filter(tags__in=tags, category=category).first()  # Фильтруем по категории и тегам
        print(f"a: {answer}")
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

class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
