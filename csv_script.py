import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ksuapplicant.settings')
django.setup()

import csv
from main.models import Category, Tag, Answer

def load_answers_from_csv(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            category, created = Category.objects.get_or_create(name=row['category'])
            keywords = [keyword.strip() for keyword in row['keywords'].split(',')]
            for keyword in keywords:
                tag, created = Tag.objects.get_or_create(name=keyword)
                answer, created = Answer.objects.get_or_create(category=category, answer=row['answer'])
                answer.tags.add(tag)

if __name__ == '__main__':
    load_answers_from_csv('./answers.csv')