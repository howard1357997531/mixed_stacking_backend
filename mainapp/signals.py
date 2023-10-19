from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import Order
import os

@receiver(post_delete, sender=Order)
def OrderDeleteSignal(sender, instance, **kwargs):
    try:
        os.remove(os.path.join(settings.MEDIA_ROOT, 'csv_file_step2', instance.unique_code + '.csv'))
    except:
        pass