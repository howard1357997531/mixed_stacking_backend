from django.db import models

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
