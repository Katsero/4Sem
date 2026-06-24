import django_filters
from .models import Service, Product, Appointment, Order, Review


class ServiceFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.NumberFilter(field_name='category_id')
    category_slug = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = Service
        fields = ['category', 'category_slug', 'is_active', 'min_price', 'max_price']


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.NumberFilter(field_name='category_id')
    category_slug = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')
    manufacturer = django_filters.CharFilter(field_name='manufacturer', lookup_expr='icontains')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = Product
        fields = [
            'category', 'category_slug', 'manufacturer',
            'min_price', 'max_price', 'in_stock', 'is_active',
        ]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)


class AppointmentFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status')
    service = django_filters.NumberFilter(field_name='service_id')
    date_from = django_filters.DateTimeFilter(field_name='appointment_datetime', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='appointment_datetime', lookup_expr='lte')

    class Meta:
        model = Appointment
        fields = ['status', 'service', 'date_from', 'date_to']


class OrderFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status')
    payment_method = django_filters.CharFilter(field_name='payment_method')
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    min_amount = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')

    class Meta:
        model = Order
        fields = ['status', 'payment_method', 'date_from', 'date_to', 'min_amount', 'max_amount']


class ReviewFilter(django_filters.FilterSet):
    target_type = django_filters.CharFilter(field_name='target_type')
    service = django_filters.NumberFilter(field_name='service_id')
    product = django_filters.NumberFilter(field_name='product_id')
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    is_approved = django_filters.BooleanFilter(field_name='is_approved')

    class Meta:
        model = Review
        fields = ['target_type', 'service', 'product', 'min_rating', 'is_approved']