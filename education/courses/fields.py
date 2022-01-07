from django.db import models
from django.core.exceptions import ObjectDoesNotExist

class OrderField(models.PositiveIntegerField):
    """
    Inherits from PositiveIntegerField class to custom order Course models
    """
    def __init__(self, for_fields=None, *args, **kwargs):
        """
        params:
            for_fields: indicates teh fields that the order has to calculated against
        """
        self.for_fields = for_fields
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        """
        Ovrerides the pre_save method of PositiveIntegerField before saving fields to database

        params:
            model_instance: pre-existing value created for models
            add: custom order value added to model_instance 
        """
        if getattr(model_instance, self.attname) is None:
            # no current value
            try:
                qs = self.model.objects.all()
                if self.for_fields:
                    # filter by objects with the same field value
                    # for the fields in "for_fields"
                    query = {field: getattr(model_instance, field) for field in self.for_fields}
                    qs = qs.filter(**query)
                # get the order of the last item
                last_item = qs.latest(self.attname)
                value = last_item.order + 1
            except ObjectDoesNotExist:
                value = 0
            setattr(model_instance, self.attname, value)
            return value 
        else:
            return super().pre_save(model_instance, add)