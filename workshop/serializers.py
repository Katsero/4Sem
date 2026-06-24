from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, Service, Product, Appointment,
    Cart, CartItem, Order, OrderItem,
    Favorite, Review, SiteSettings,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    orders_count = serializers.IntegerField(read_only=True, required=False)
    appointments_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'full_name', 'date_joined',
            'orders_count', 'appointments_count',
        ]
        read_only_fields = ['date_joined', 'role']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserAdminSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = ['date_joined']
        fields = UserSerializer.Meta.fields + ['is_active', 'last_login']


class CategorySerializer(serializers.ModelSerializer):
    items_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'category_type', 'description', 'items_count']


class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    formatted_price = serializers.SerializerMethodField()
    avg_rating = serializers.FloatField(read_only=True, required=False)
    favorites_count = serializers.IntegerField(read_only=True, required=False)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'category', 'category_name', 'description',
            'price', 'formatted_price', 'duration_minutes', 'is_active',
            'avg_rating', 'favorites_count', 'is_favorite',
            'created_at', 'updated_at',
        ]

    def get_formatted_price(self, obj):
        return obj.get_formatted_price()

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, service=obj).exists()
        return False


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    formatted_price = serializers.SerializerMethodField()
    avg_rating = serializers.FloatField(read_only=True, required=False)
    favorites_count = serializers.IntegerField(read_only=True, required=False)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_name', 'manufacturer',
            'description', 'price', 'formatted_price', 'stock', 'is_active',
            'avg_rating', 'favorites_count', 'is_favorite',
            'created_at', 'updated_at',
        ]

    def get_formatted_price(self, obj):
        return obj.get_formatted_price()

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, product=obj).exists()
        return False


class AppointmentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_price = serializers.DecimalField(
        source='service.price', max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Appointment
        fields = [
            'id', 'user', 'user_username', 'service', 'service_name',
            'service_price', 'appointment_datetime', 'status', 'note',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'status']

    def validate(self, attrs):
        instance = Appointment(**attrs)
        if self.instance:
            instance.pk = self.instance.pk
        instance.clean()
        return attrs


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price', max_digits=12, decimal_places=2, read_only=True
    )
    product_stock = serializers.IntegerField(source='product.stock', read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_price',
            'product_stock', 'quantity', 'total_price',
        ]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Количество должно быть >= 1.")
        return value

    def validate(self, attrs):
        product = attrs.get('product') or getattr(self.instance, 'product', None)
        quantity = attrs.get('quantity', getattr(self.instance, 'quantity', 1))
        if product and quantity > product.stock:
            raise serializers.ValidationError(
                {'quantity': f"Недостаточно товара на складе. Доступно: {product.stock}."}
            )
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'total_items', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'quantity',
            'price_at_purchase', 'total_price',
        ]
        read_only_fields = ['price_at_purchase']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_username', 'status', 'status_display',
            'payment_method', 'payment_method_display', 'address', 'phone',
            'total_amount', 'items', 'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'total_amount', 'status']

    def validate_address(self, value):
        from django.core.validators import RegexValidator
        from django.core.exceptions import ValidationError
        import re
        
        regex = r'^[а-яА-ЯёЁa-zA-Z\s\-\.,]+,\s*д\.\s*\d+[а-яА-Яa-zA-Z]?(?:,\s*кв\.\s*\d+)?,\s*[а-яА-ЯёЁa-zA-Z\s\-]+,\s*\d{6}$'
        if not re.match(regex, value):
            raise serializers.ValidationError(
                'Адрес должен быть в формате: "ул. Примерная, д. 1, Москва, 101000".'
            )
        return value


class FavoriteSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True, default=None)
    product_name = serializers.CharField(source='product.name', read_only=True, default=None)

    class Meta:
        model = Favorite
        fields = [
            'id', 'user', 'service', 'service_name',
            'product', 'product_name', 'added_at',
        ]
        read_only_fields = ['user', 'added_at']

    def validate(self, attrs):
        instance = Favorite(**attrs)
        if self.instance:
            instance.pk = self.instance.pk
        instance.clean()
        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_username', 'target_type', 'service',
            'product', 'rating', 'text', 'is_approved', 'is_author',
            'created_at',
        ]
        read_only_fields = ['user', 'is_approved']

    def get_is_author(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

    def validate(self, attrs):
        instance = Review(**attrs)
        if self.instance:
            instance.pk = self.instance.pk
        instance.clean()
        return attrs
    
class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            'company_name', 'description', 'phone',
            'email', 'address', 'privacy_policy',
        ]