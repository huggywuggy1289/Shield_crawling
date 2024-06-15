import logging
from asgiref.sync import sync_to_async
from classify.models import Host, WordCount
from django.utils import timezone

class GetWordsPipeline:
    async def process_item(self, item, spider):
        try:
            host_instance, created = await sync_to_async(Host.objects.get_or_create)(
                host=item['host']
            )
            if created:
                host_instance.create_time = timezone.now()
                host_instance.last_check_time = timezone.now()
            host_instance.last_check_time = timezone.now()
            await sync_to_async(host_instance.save)()

            await sync_to_async(WordCount.objects.create)(
                host=host_instance,
                redirect=item['redirect'],
                words=item['words'],
                count=item['count']
            )
        except Exception as e:
            logging.error(f"Error processing item: {e}")
        return item
