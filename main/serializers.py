from rest_framework import serializers
from .models import Category, FAQ, UsefulLinks

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'

class UsefulLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsefulLinks
        fields = '__all__'
