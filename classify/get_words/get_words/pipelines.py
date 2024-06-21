import os
import django
from asgiref.sync import sync_to_async
from classify.models import Host, FullSentence

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

class NewGetWordsPipeline:
    async def process_item(self, item, spider):
        host, created = await sync_to_async(Host.objects.get_or_create)(host=item['host'])
        await sync_to_async(FullSentence.objects.create)(
            host=host,
            redirect=item['redirect_url'],
            full_sentence=item['full_sentence']
        )
        return item
