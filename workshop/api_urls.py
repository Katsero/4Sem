from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'categories', views.CategoryViewSet)
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')
router.register(r'cart', views.CartViewSet, basename='cart')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'favorites', views.FavoriteViewSet, basename='favorite')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'site-settings', views.SiteSettingsViewSet, basename='site-settings')
router.register(r'analytics', views.AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', obtain_auth_token, name='api-login'),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]