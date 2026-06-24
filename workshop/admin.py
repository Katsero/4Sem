from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Category, Service, Product, Appointment,
    Cart, CartItem, Order, OrderItem,
    Favorite, Review,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('role', 'phone')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category_type', 'description']
    list_filter = ['category_type']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration_minutes', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['name', 'description', 'category__name']
    raw_id_fields = ['category']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'manufacturer', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'manufacturer', 'created_at']
    search_fields = ['name', 'description', 'manufacturer', 'category__name']
    raw_id_fields = ['category']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    raw_id_fields = ['product']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'created_at']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ['product']
    readonly_fields = ['price_at_purchase']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'payment_method', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'user__email', 'address', 'phone']
    raw_id_fields = ['user']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'appointment_datetime', 'status', 'created_at']
    list_filter = ['status', 'appointment_datetime', 'created_at']
    search_fields = ['user__username', 'service__name', 'note']
    raw_id_fields = ['user', 'service']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'service__name', 'product__name']
    raw_id_fields = ['user', 'service', 'product']
    readonly_fields = ['added_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'target_type', 'service', 'product', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'target_type', 'rating', 'created_at']
    search_fields = ['user__username', 'text', 'service__name', 'product__name']
    raw_id_fields = ['user', 'service', 'product']
    readonly_fields = ['created_at']
    list_editable = ['is_approved']


admin.site.site_header = 'Tuning Atelier Administration'
admin.site.site_title = 'Tuning Atelier Admin'
admin.site.index_title = 'Добро пожаловать в панель администратора'