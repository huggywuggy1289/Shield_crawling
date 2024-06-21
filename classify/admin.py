from django.contrib import admin
from .models import Host, WordCount, FullSentence

class WordCountInline(admin.TabularInline):
    model = WordCount
    extra = 1

class FullSentenceInline(admin.TabularInline):
    model = FullSentence
    extra = 1

class HostAdmin(admin.ModelAdmin):
    inlines = [WordCountInline, FullSentenceInline]
    list_display = ('host', 'classification', 'create_time', 'last_check_time')

admin.site.register(Host, HostAdmin)
admin.site.register(WordCount)
admin.site.register(FullSentence)
