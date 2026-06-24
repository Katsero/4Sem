from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'workshop'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    
    path('services/', views.ServiceListView.as_view(), name='service_list'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    
    path('appointment/', views.AppointmentView.as_view(), name='appointment'),
    path('appointment/create/', views.create_appointment, name='create_appointment'),
    
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/orders/', views.OrderListView.as_view(), name='order_list'),
    path('profile/appointments/', views.UserAppointmentListView.as_view(), name='user_appointment_list'),
    
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='workshop:home'), name='logout'),
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
]