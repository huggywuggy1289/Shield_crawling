from django.contrib import admin
from .models import Hosts, WordCount, FullSentence, Normal, Casino, Adult, Copyright, Whitelist

class WordCountInline(admin.TabularInline):
    model = WordCount
    extra = 1

class FullSentenceInline(admin.TabularInline):
    model = FullSentence
    extra = 1

class HostAdmin(admin.ModelAdmin):
    inlines = [WordCountInline, FullSentenceInline]
    list_display = ('host', 'redirect', 'classification', 'create_time', 'last_check_time')

class NormalAdmin(admin.ModelAdmin):
    list_display = ('id', 'word')

class CasinoAdmin(admin.ModelAdmin):
    list_display = ('id', 'word')

class AdultAdmin(admin.ModelAdmin):
    list_display = ('id', 'word')

class CopyrightAdmin(admin.ModelAdmin):
    list_display = ('id', 'word')

class WhitelistAdmin(admin.ModelAdmin):
    list_display = ('id', 'url')

admin.site.register(Hosts, HostAdmin)
admin.site.register(WordCount)
admin.site.register(FullSentence)
admin.site.register(Normal, NormalAdmin)
admin.site.register(Casino, CasinoAdmin)
admin.site.register(Adult, AdultAdmin)
admin.site.register(Copyright, CopyrightAdmin)
admin.site.register(Whitelist, WhitelistAdmin)
