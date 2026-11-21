from django.db import models

from goods.models import CPU, RAM, Case, CoolingSystem, GraphicsCard, HardDrive, Motherboard, PowerSupply
from users.models import User


class Build(models.Model):
    """The PC that a user is building. One build per user, each slot holds one part."""

    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name='build')
    # The slot names are the same as in builder.rules.SLOTS.
    # If a product is deleted from the shop, its slot just becomes empty.
    cpu = models.ForeignKey(to=CPU, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    motherboard = models.ForeignKey(to=Motherboard, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    ram = models.ForeignKey(to=RAM, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    gpu = models.ForeignKey(to=GraphicsCard, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    storage = models.ForeignKey(to=HardDrive, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    psu = models.ForeignKey(to=PowerSupply, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    case = models.ForeignKey(to=Case, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    cooling = models.ForeignKey(to=CoolingSystem, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'build'

    def __str__(self):
        return f'Build of {self.user}'
