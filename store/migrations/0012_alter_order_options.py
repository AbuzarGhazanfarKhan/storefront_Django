# Generated by Django 4.0.2 on 2022-02-10 20:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0011_alter_customer_options_remove_customer_email_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'permissions': [('cancel_order', 'can cancel order')]},
        ),
    ]
