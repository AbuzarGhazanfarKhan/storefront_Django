from django.dispatch import receiver
from store.signals import order_created


@receiver(order_created)
def on_order_created(sender, **kwarg):
    print(kwarg['order'])  # we need to load this module when the app is ready
