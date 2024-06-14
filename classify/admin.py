from django.contrib import admin
from .models import Host, WordCount

class WordCountInline(admin.TabularInline):
    model = WordCount
    extra = 1

class HostAdmin(admin.ModelAdmin):
    inlines = [WordCountInline]
    list_display = ('host', 'classification')

admin.site.register(Host, HostAdmin)
admin.site.register(WordCount)
