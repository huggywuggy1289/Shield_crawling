from django.core.management import call_command

def start_crawl_task():
    call_command('start_crawl_task')

def classify_urls_task():
    call_command('classify_urls_task')
