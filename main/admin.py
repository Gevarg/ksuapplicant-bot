from django.contrib import admin
from .models import Category, Tag, UserQueryLog, Answer, FAQ, UsefulLinks


class TagAdmin(admin.ModelAdmin):
    search_fields = ["name"]

class AnswerAdmin(admin.ModelAdmin):
    search_fields = ["answer"]

admin.site.register(Category)
admin.site.register(Tag, TagAdmin)
admin.site.register(UserQueryLog)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(FAQ)
admin.site.register(UsefulLinks)
