from django.shortcuts import get_object_or_404
from django.db.models import Count
# from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Collection, Product
from .serializers import ProductSerializers, CollectionSerializer
from store import serializers


# Create your views here.


class ProductList(ListCreateAPIView):

    queryset = Product.objects.select_related('collection').all()
    serializer_class = ProductSerializers

    def get_serializer_context(self):
        return {'request': self.request}

    # -------------------------------CAN BE USED IF YOU WANT TO IMPLEMENT MORE COMPLEX FUNCTIONALITY LIKE ADMIN PRIVELAGES ETC
    # # --------GET--------
    # def get_queryset(self, request):
    #   return Product.objects.select_related('collection').all()
    # def get_queryset(self, request):
    #   return ProductSerializers
    # def get_serializer_context(self):
    #     return {'request': self.request}


class ProductDetails(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializers

    def delete(self, request, pk):
        # data recieve from product
        product = get_object_or_404(Product, pk=pk)
        if product.orderitems.count() > 0:
            return Response({"error": "Product cannot be deleted because it is associated with an order item"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # def get(self, request, id):
    #     # data recieve from product
    #     product = get_object_or_404(Product, pk=id)
    #     # Convert product object into a dictionary
    #     serializer = ProductSerializers(product)
    #     return Response(serializer.data)

    # def put(self, request, id):
    #     # data recieve from product
    #     product = get_object_or_404(Product, pk=id)
    #     serializer = ProductSerializers(product, data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data)


class CollectionList(ListCreateAPIView):
    queryset = Collection.objects.annotate(product_count=Count('products'))
    serializer_class = CollectionSerializer

    def get_serializer_context(self):
        return {'request': self.request}


# @api_view(['Get', 'POST'])
# def collection_list(request):
#     if request.method == 'GET':
#         queryset = Collection.objects.annotate(product_count=Count('products'))
#         serializer = CollectionSerializer(
#             queryset, many=True, context={'request': request})
#         return Response(serializer.data)
#     elif request.method == 'POST':
#         serializer = CollectionSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         # serializer.validated_data
#         return Response(serializer.data, status=status.HTTP_201_CREATED)


class CollectionDetails(RetrieveUpdateDestroyAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

    def delete(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk)
        if collection.products.count() > 0:
            return Response({'error': 'Collection can not be deleted because this collection have Products in it'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
