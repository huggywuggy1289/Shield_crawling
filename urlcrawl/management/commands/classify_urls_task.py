# urlcrawl/management/commands/classify_urls_task.py

from django.core.management.base import BaseCommand
import asyncio
from urlcrawl.views import classify_urls
from django.test import RequestFactory

class Command(BaseCommand):
    help = 'Run classify_urls task'

    def handle(self, *args, **kwargs):
        request = RequestFactory().post('/dummy-url/')
        asyncio.run(classify_urls(request))
        self.stdout.write(self.style.SUCCESS('Successfully ran classify_urls task'))
