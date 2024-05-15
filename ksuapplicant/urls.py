from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from main import views

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api/classify_question/', views.classify_question, name='classify_question'),
    path('api/log_user_query/', views.log_user_query, name='log_user_query'),
    path('api/get_answer/', views.get_answer, name='get_answer'),
    path('api/faq_list/', views.faq_list, name='faq_list'),

]
