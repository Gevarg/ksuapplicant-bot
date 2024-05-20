from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class FAQ(models.Model):
    question = models.CharField(max_length=500)
    answer = models.TextField()
    def __str__(self):
        return self.question

class UsefulLinks(models.Model):
    name = models.CharField(max_length=500)
    link = models.TextField()
    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class UserQueryLog(models.Model):
    query = models.TextField()
    response = models.TextField()
    is_helpful = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)


class Answer(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='answers')
    tags = models.ManyToManyField(Tag, related_name='answers')
    answer = models.TextField()

    def __str__(self):
        return f"{self.answer}"
