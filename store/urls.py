# from django.urls import URLPattern, path
from . import views
from rest_framework_nested import routers


router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='products')
router.register('collections', views.CollectionViewSet)
router.register('carts', views.CartViewSet)
router.register('customers', views.CustomerViewSet)
router.register('orders', views.OrderViewSet, basename='orders')


products_router = routers.NestedDefaultRouter(
    router, 'products', lookup='product')
products_router.register('reviews', views.ReviewViewSet,
                         basename='product-reviews')
products_router.register(
    'images', views.ProductImageViewSet, basename='product-images')


cart_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
cart_router.register('items', views.CartItemsViewSet, basename='cart-items')

# URLConf

urlpatterns = router.urls + products_router.urls+cart_router.urls


# urlpatterns = [
#     # path('products/', views.ProductList.as_view()),
#     # path('products/<int:pk>/', views.ProductDetails.as_view()),
#     # path('collections/', views.CollectionList.as_view()),
#     # path('collections/<int:pk>/', views.CollectionDetails.as_view(),
#     #      name='collection-detail'),
# ]
