import os
import django
from asgiref.sync import sync_to_async
from classify.models import Hosts, FullSentence

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

class NewGetWordsPipeline:
    async def process_item(self, item, spider):
        host, created = await sync_to_async(Hosts.objects.get_or_create)(host=item['host'])
        if 'redirect_url' in item:
            host.redirect = item['redirect_url']
            await sync_to_async(host.save)()

        await sync_to_async(FullSentence.objects.create)(
            host=host,
            full_sentence=item['full_sentence']
        )
        return item
