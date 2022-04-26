from urllib import request
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
# from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from store.permisions import FullDjangoModelPermissions, ViewCustomerHistoryPermission, isAdminReadOrOnly
from store.product_filter import ProductFilter
from .models import Cart, CartItem, Collection, Customer, Order, OrderItem, Product, ProductImage, Review
from .serializers import AddCartItemSerializer, CartItemSerializer, CartSerializer, CreateOrderSerializer, CustomerSerializer, OrderSerializer, ProductImageSerializer, ProductSerializers, CollectionSerializer, ReviewSerializers, UpdateCartItems, UpdateOrderSerializer
from store import serializers
# from store import serializers


# Create your views here.


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializers
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    ordering_fields = ['unit_price', 'last_update']
    permission_classes = [isAdminReadOrOnly]
    pagination_class = PageNumberPagination
    search_fields = ['title', 'description']

    # def get_queryset(self):
    #     queryset = Product.objects.all()

    #     collection_id = self.request.query_params.get('collection_id')

    #     if collection_id is not None:
    #         queryset = queryset.filter(collection_id=collection_id)
    #     return queryset

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk']).count() > 0:
            return Response({"error": "Product cannot be deleted because it is associated with an order item"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)

    # def delete(self, request, pk):
    #     # data recieve from product
    #     product = get_object_or_404(Product, pk=pk)
    #     product.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(product_count=Count('products'))
    serializer_class = CollectionSerializer
    permission_classes = [isAdminReadOrOnly]

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection_id=kwargs['pk']).count() > 0:
            return Response({'error': 'Collection can not be deleted because this collection have Products in it'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    # queryset = Review.objects.all() the problem with this is even if we want to view reviews of a particular product we will get all the reviews of every product instead we will overwrite get_method
    serializer_class = ReviewSerializers

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

    # to extract product_id from urls
    # we can set context for additional info

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}
        # our urls have 2 parameters product_pk and pk(review id)


class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):

    # queryset = Cart.objects.all()     #due to .all() we have to make seperate query to retrieve iems in cart so we will use prefetch
    queryset = Cart.objects.prefetch_related('items__product').all()
# -------------------QUERY EXPLAIN
    # first cart is retreived
    # Then cart items are retrieved
    # then all Products refrenced in this cart are Retreived from item/Product table/model

    serializer_class = CartSerializer


class CartItemsViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    serializer_class = CartItemSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItems
        return CartItemSerializer

    def get_serializer_context(self):
        # sending cart id to serializers
        return {'cart_id': self.kwargs['cart_pk']}

    def get_queryset(self):
        return CartItem.objects\
            .filter(cart_id=self.kwargs['cart_pk'])\
            .select_related('product')


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]
    # permission_classes = [FullDjangoModelPermissions]

    # different permissions for different methods

    # with this method we return permissions objects() not classes
    # def get_permissions(self):
    #     if self.request.method == 'GET':
    #         return [AllowAny()]
    #     return [IsAuthenticated()]

    @action(detail=True, permission_classes=[ViewCustomerHistoryPermission])
    def history(self, request, pk):
        return Response("OK")

    # we have to specify if this function is a action just like any other mixin
    # details=false ==> store/customer/me ----available on list view
    # details=True ==> store/customer/1/me

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        # IF user dosnot exit in database we will create new customer
        customer = Customer.objects.get_or_create(
            user_id=request.user.id)

        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class OrderViewSet(ModelViewSet):
    # queryset = Order.objects.all()
    # serializer_class = OrderSerializer
    # permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return[IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        # when creating the serializer we need to give the context so we can
        # have access to the user_id
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'user_id': self.request.user.id})

        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        # NOw create another serializer to show order items
        serializer = OrderSerializer()
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateOrderSerializer
        elif self.request.method == "PATCH":
            return UpdateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        customer_id = Customer.objects.get_or_create(user_id=user)
        Order.objects.filter(customer_id=customer_id)


class ProductImageViewSet(ModelViewSet):
    serializer_class = ProductImageSerializer

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}

    def get_queryset(self):
        return ProductImage.objects.filter(product_id=self.kwargs['product_pk'])
