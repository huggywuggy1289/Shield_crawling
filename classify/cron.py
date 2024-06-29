from django.core.management import call_command
def save_keywords_task():
    call_command('save_keywords')
