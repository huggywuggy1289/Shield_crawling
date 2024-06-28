# urlcrawl/management/commands/start_crawl_task.py

from django.core.management.base import BaseCommand
from urlcrawl.views import start_crawl
from django.test import RequestFactory

class Command(BaseCommand):
    help = 'Run start_crawl task'

    def handle(self, *args, **kwargs):
        request = RequestFactory().post('/dummy-url/')
        response = start_crawl(request)
        self.stdout.write(self.style.SUCCESS('Successfully ran start_crawl task'))
