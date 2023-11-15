from django.db import models
import os

class Common(models.Model):
    createdAt = models.DateTimeField(auto_now_add=True)
    modifiedAt = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class workOrder(Common):
    name = models.CharField(max_length=120, null=True, blank=True)
    file_name = models.CharField(max_length=120, null=True, blank=True)
    _16A_qty = models.PositiveIntegerField(default=1)
    _18A_qty = models.PositiveIntegerField(default=1)
    _33_qty = models.PositiveIntegerField(default=1)
    _7A_qty = models.PositiveIntegerField(default=1)
    _13_qty = models.PositiveIntegerField(default=1)
    _22_qty = models.PositiveIntegerField(default=1)
    _20_qty = models.PositiveIntegerField(default=1)
    _29_qty = models.PositiveIntegerField(default=1)
    _9_qty = models.PositiveIntegerField(default=1)
    _26_qty = models.PositiveIntegerField(default=1)
    _35_qty = models.PositiveIntegerField(default=1)
    total_count = models.PositiveIntegerField(default=1)
    hasAiTrained = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.total_count = self._16A_qty + self._18A_qty + self._33_qty + self._7A_qty + self._13_qty + \
        self._22_qty + self._20_qty + self._29_qty + self._9_qty + self._26_qty + self._35_qty
        super(workOrder, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class aiWorkOrder(Common):
    name = models.CharField(max_length=250, null=True, blank=True)
    worklist_id = models.PositiveIntegerField(default=1)
    list_order = models.CharField(max_length=250, null=True, blank=True)
    training_time = models.FloatField(default=0)

    def __str__(self):
        return str(self.name)

AI_TRAINING_STATE_CHOICES = (
    ('no_training', 'no_training'),
    ('is_training', 'is_training'),
    ('finish_training', 'finish_training'),
)

def upload_to(instance, filename):
    return os.path.join("csv_file_step2", f"{instance.unique_code}.csv")

class Order(Common):
    name = models.CharField(max_length=255, null=True, blank=True)
    unique_code = models.CharField(max_length=255, unique=True, null=True, blank=True)
    csv_file = models.FileField(upload_to=upload_to, null=True, blank=True)
    aiTraining_order = models.CharField(max_length=255, null=True, blank=True)
    aiTraining_state = models.CharField(max_length=180, choices=AI_TRAINING_STATE_CHOICES, default='no_training')
    is_today_latest = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orderItem")
    name = models.CharField(max_length=255, null=True, blank=True)
    width = models.CharField(max_length=255, null=True, blank=True)
    height = models.CharField(max_length=255, null=True, blank=True)
    depth = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    
class MultipleOrder(Common):
    name = models.CharField(max_length=255, null=True, blank=True)
    orderSelectId_str = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name
    
class MultipleOrderItem(models.Model):
    multiple_order = models.ForeignKey(MultipleOrder, on_delete=models.CASCADE, related_name="multipleOrder", null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order", null=True, blank=True)

    def __str__(self):
        return str(self.multiple_order)

class ExecutingOrder(Common):
    order_id = models.CharField(max_length=255, null=True, blank=True)
    order_name = models.CharField(max_length=255, null=True, blank=True)
    order_type = models.CharField(max_length=255, null=True, blank=True)
    executing_index = models.PositiveIntegerField(default=1)
    finished = models.BooleanField(default=False)

    def __str__(self):
        return str(self.order_id)

# class Order(Common):
#     name = models.CharField(max_length=255, null=True, blank=True)
#     unique_code = models.CharField(max_length=255, unique=True, null=False, blank=False)
#     image = models.ImageField(upload_to='qrcode', null=True, blank=True)
#     csv_file = models.FileField(upload_to=upload_to, null=True, blank=True)
#     aiTraining_order = models.CharField(max_length=255, null=True, blank=True)
#     aiTraining_state = models.CharField(max_length=180, choices=AI_TRAINING_STATE_CHOICES, default='no_training')
#     upload_qrcode_select = models.BooleanField(default=False)
#     display = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name
    
# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orderItem")
#     name = models.CharField(max_length=255, null=True, blank=True)
#     width = models.CharField(max_length=255, null=True, blank=True)
#     height = models.CharField(max_length=255, null=True, blank=True)
#     depth = models.CharField(max_length=255, null=True, blank=True)
#     quantity = models.PositiveIntegerField(default=0)

#     def __str__(self):
#         return self.name

# class QRcodeExecute(models.Model):
#     unique_code = models.CharField(max_length=255, null=True, blank=True)
#     is_execute = models.BooleanField(default=False)

#     def __str__(self):
#         return self.unique_code