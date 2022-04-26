import collections
from decimal import Decimal
from turtle import title
from django.forms import IntegerField
from rest_framework import serializers

from store.models import Product, Collection


class CollectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)


class ProductSerializers(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    price = serializers.DecimalField(
        max_digits=6, decimal_places=2, source="unit_price")  # by default serializer will target field of name price but it does not have a field of price so we define the source of taget field
    unit_price_with_tax = serializers.SerializerMethodField(
        method_name='calculate_tax')
    # to render collections as a hyperlink we can use HyperlinkRelatedField
    collection = serializers.HyperlinkedRelatedField(
        queryset=Collection.objects.all(),
        view_name='collection-detail'  # hyperlink name
    )

    # collection = CollectionSerializer()

    # collection = serializers.StringRelatedField()
    # collection = serializers.PrimaryKeyRelatedField(
    #     queryset=Collection.objects.all()
    # ) PrimaryKeyRelatedField outputs a key integer value so we use StringRelatedField()--->to output the string representation of a class in model i.e __str__ wala

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.2)
