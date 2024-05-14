from django.contrib import admin
from .models import Category, Tag, UserQueryLog, Answer

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(UserQueryLog)
admin.site.register(Answer)
