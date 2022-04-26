from dataclasses import field
from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from .models import Cart, CartItem, Customer, Order, OrderItem, Product, Collection, ProductImage, Review
from .signals import order_created


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title', 'product_count']

    product_count = serializers.SerializerMethodField(
        method_name='total_products'  # Read_only
    )

    def total_products(self, collection: Collection):
        return collection.products.count()


class ProductSerializers(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'slug', 'inventory',
                  'unit_price', 'price_with_tax', 'collection']

    price_with_tax = serializers.SerializerMethodField(
        method_name='calculate_tax')
    collection = serializers.PrimaryKeyRelatedField(
        queryset=Collection.objects.all())

    # to render collections as a hyperlink we can use HyperlinkRelatedField
    # collection = serializers.HyperlinkedRelatedField(
    #     queryset=Collection.objects.all(),
    #     view_name='collection-detail'  # hyperlink name
    # )

    # collection = serializers.StringRelatedField()
    # collection = serializers.PrimaryKeyRelatedField(
    #     queryset=Collection.objects.all()
    # ) PrimaryKeyRelatedField outputs a key integer value so we use StringRelatedField()--->to output the string representation of a class in model i.e __str__ wala

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.2)


class ReviewSerializers(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'name', 'date', 'description']

    def create(self, validated_data):
        product_id = self.context['product_id']
        Review.objects.create(product_id=product_id, **validated_data)


# Cutsom product serializer to use in cart
class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField(
        method_name='get_total_price'  # Read_only
    )

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.product.unit_price

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(
        method_name='get_total_price'  # Read_only
    )

    def get_total_price(self, cart_item: Cart):
        return sum([item.quantity * item.product.unit_price for item in cart_item.items.all()])
        # sum of all quantity of product multiply by price of cart_items which are returned by .all() queryset
        # RETURN item.quantity * item.product.unit_price
        # for item in cart

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']

    # def total_price(self, Cart):
    #     return Cart.item.all().sum('unit_price')


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    # Validate A Single field i.e product id in this case so no invalid id can be posted
    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                'No Product of Given id was Found')
        return value


# ----create one product instance even if we post same product multiple times
# which only updates the qunatity not repeat same items in the api


    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']
        try:
            cart_item = CartItem.objects.get(
                cart_id=cart_id, product_id=product_id)
        # Updating an Item
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            # Create Item if it doesnot already exist in cart
            self.instance = CartItem.objects.create(
                cart_id=cart_id, **self.validated_data)
        return self.instance

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']


class UpdateCartItems(serializers.ModelSerializer):

    class Meta:
        model = CartItem
        fields = ['quantity']


class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user_id', 'phone', 'birth_date', 'membership']


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'unit_price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'payment_status', 'placed_at', 'items']


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_status']


class CreateOrderSerializer(serializers.Serializer):
    # we are using Serializer instade of ModleSerializer we need cart_id  to Create a cart  which is not defined in the cart model
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError(
                "No Cart with given ID was Found")
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('Cart is Empty')
        return cart_id

    def save(self, **kwargs):

        # with TRANSACTION all code runs no single block will run
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            # print(self.validated_data['cart_id'])
            # print(self.context['user_id'])

            customer = Customer.objects.get_or_create(
                user_id=self.context['user_id'])
            order = Order.objects.create(customer=customer)

            cart_items = CartItem.objects\
                .select_related('product')\
                .filter(
                    cart_id=cart_id)
            # cart_item is a query_set and with query_set we get a collection
# Converting cart_item to order_item
            order_items = [
                OrderItem(
                    order=order,
                    # when retrieveing cartb item we need to eagerload(select_related) aquiring products from database
                    product=item.product,
                    unit_price=item.product.unit_price,  # from items collection
                    quantity=item.quantity

                ) for item in cart_items
            ]
            # we have to iterate all over them and save them one by one so,
            # but we are going to use bulk_create query
            OrderItem.objects.bulk_create(order_items)
            Cart.objects.filter(pk=cart_id).delete()

            order_created.send_robust(self.__class__, order=order)
            # self.__class__ returns class of current instance

            return order  # TO give to viewset


class ProductImageSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        product_id = self.context['product_id']
        return ProductImage.objects.create(product_id=product_id, **validated_data)

    class Meta:
        model = ProductImage
        fields = ['id', 'image']
