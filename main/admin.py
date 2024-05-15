from django.contrib import admin
from .models import Category, Tag, UserQueryLog, Answer, FAQ


class TagAdmin(admin.ModelAdmin):
    search_fields = ["name"]

admin.site.register(Category)
admin.site.register(Tag, TagAdmin)
admin.site.register(UserQueryLog)
admin.site.register(Answer)
admin.site.register(FAQ)
