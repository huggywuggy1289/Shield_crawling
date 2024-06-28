import os
import django
from asgiref.sync import sync_to_async
from classify.models import Hosts, FullSentence

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


class NewGetWordsPipeline:
    async def process_item(self, item, spider):
        # host_instance로 변수 이름 변경
        host_instance, created = await sync_to_async(Hosts.objects.get_or_create)(host=item['host'])

        # 리다이렉트 URL이 있을 경우 hosts 테이블의 redirect 컬럼을 업데이트
        redirect_url = item.get('redirect_url')
        if redirect_url:
            host_instance.redirect = redirect_url
            await sync_to_async(host_instance.save)()

        # FullSentence 테이블에 full_sentence 저장
        await sync_to_async(FullSentence.objects.create)(
            host=host_instance,
            full_sentence=item['full_sentence']
        )
        return item
