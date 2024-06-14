import logging
from asgiref.sync import sync_to_async
from classify.models import Host, WordCount

logger = logging.getLogger(__name__)

class GetWordsPipeline:

    async def process_item(self, item, spider):
        host_url = item['host']
        redirect_url = item.get('redirect', None)
        word = item['words']
        count = item['count']

        # host_url에 해당하는 Host 객체를 가져오거나 생성합니다.
        host, created = await sync_to_async(Host.objects.get_or_create)(host=host_url)

        # WordCount 객체를 생성합니다.
        await sync_to_async(WordCount.objects.create)(
            host=host,
            redirect=redirect_url,
            words=word,
            count=count
        )

        return item
