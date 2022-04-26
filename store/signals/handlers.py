# signal is used to listen any actions and do some actions by listenig to it
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import Customer


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_for_new_user(sender, **kwargs):  # SIGNAL HANDLER
    if kwargs['created']:
        Customer.objects.create(user=kwargs['instance'])
