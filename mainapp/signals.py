from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.db.models import Max 
from .models import Order
import os
import shutil

@receiver(post_delete, sender=Order)
def OrderDeleteSignal(sender, instance, **kwargs):
    try:
        if instance.is_today_latest:
            date = instance.createdAt
            order_list = Order.objects.filter(is_today_latest=False, createdAt__year=date.year,
                createdAt__month=date.month, createdAt__day=date.day)
            if order_list.exists():
                max_id = order_list.aggregate(Max('id')).get('id__max')
                order = Order.objects.filter(id=max_id).first()
                order.is_today_latest = True
                order.save()

        csv_file = os.path.join(settings.MEDIA_ROOT, 'input_csv', instance.unique_code + '.csv')
        figure_folder = os.path.join(settings.MEDIA_ROOT, f'ai_figure/Figures_{instance.id}')

        if os.path.isfile(csv_file):
            os.remove(csv_file)
        
        if os.path.isdir(figure_folder):
            shutil.rmtree(figure_folder)
    except:
        pass

