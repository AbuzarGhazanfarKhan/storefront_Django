# Generated by Django 4.0.2 on 2022-02-17 12:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0016_alter_orderitem_order_productimage'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productimage',
            old_name='post',
            new_name='product',
        ),
    ]
