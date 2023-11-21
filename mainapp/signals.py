from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import Order
import os
import shutil

@receiver(post_delete, sender=Order)
def OrderDeleteSignal(sender, instance, **kwargs):
    try:
        csv_file = os.path.join(settings.MEDIA_ROOT, 'csv_file_step2', instance.unique_code + '.csv')
        figure_folder = os.path.join(settings.MEDIA_ROOT, f'Figures_step2_{instance.id}')

        if (os.path.isfile(csv_file)):
            os.remove(csv_file)
        
        if (os.path.isdir(figure_folder)):
            shutil.rmtree(figure_folder)
    except:
        pass

