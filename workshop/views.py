from django.db.models import Avg, Count, Q, F
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    User, Category, Service, Product, Appointment,
    Cart, CartItem, Order, OrderItem,
    Favorite, Review, SiteSettings,
)
from .serializers import (
    UserSerializer, UserAdminSerializer,
    CategorySerializer, ServiceSerializer, ProductSerializer,
    AppointmentSerializer, CartSerializer, CartItemSerializer,
    OrderSerializer, OrderItemSerializer,
    FavoriteSerializer, ReviewSerializer, SiteSettingsSerializer,
)
from .filters import (
    ServiceFilter, ProductFilter, AppointmentFilter, OrderFilter, ReviewFilter,
)
from .permissions import IsAdminOrReadOnly, IsAdminUser, IsOwnerOrAdmin


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username']

    def get_queryset(self):
        # Аннотации: количество заказов и записей у каждого пользователя
        return User.objects.annotate(
            orders_count=Count('orders', distinct=True),
            appointments_count=Count('appointments', distinct=True),
        )

    def get_serializer_class(self):
        if self.request.user.is_authenticated and self.request.user.is_admin:
            return UserAdminSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'me']:
            return [IsAuthenticated()]
        if self.action in ['destroy', 'block', 'unblock', 'create', 'update', 'partial_update']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        if request.method == 'PATCH':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def block(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'blocked'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def unblock(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'unblocked'})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    filterset_fields = ['category_type']

    def get_queryset(self):
        return Category.objects.all()


class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    filterset_class = ServiceFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'duration_minutes', 'avg_rating']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def get_queryset(self):
        # select_related: услуга → категория (одним SQL-запросом)
        # annotate: средний рейтинг + количество добавлений в избранное
        return Service.objects.select_related('category').annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            favorites_count=Count('favorites', distinct=True),
        )


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'manufacturer', 'category__name']
    ordering_fields = ['price', 'created_at', 'stock', 'avg_rating']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def get_queryset(self):
        # select_related: товар → категория
        # annotate: средний рейтинг + избранное
        return Product.objects.select_related('category').annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            favorites_count=Count('favorites', distinct=True),
        )


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    filterset_class = AppointmentFilter
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['appointment_datetime', 'created_at']

    def get_queryset(self):
        # select_related: запись → пользователь + услуга → категория
        qs = Appointment.objects.select_related('user', 'service', 'service__category')
        if self.request.user.is_admin:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        # select_related + prefetch_related для корзины и её позиций
        cart, _ = Cart.objects.select_related('user').prefetch_related(
            'items__product', 'items__product__category'
        ).get_or_create(user=request.user)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product')
        quantity = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, pk=product_id)
        item, created = CartItem.objects.select_related('product').get_or_create(
            cart=cart, product=product, defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
        item.full_clean()
        item.save()

        cart.refresh_from_db()
        return Response(CartSerializer(cart, context={'request': request}).data)

    @action(detail=False, methods=['post'], url_path='update/(?P<item_id>[0-9]+)')
    def update_item(self, request, item_id=None):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        quantity = int(request.data.get('quantity', item.quantity))
        item.quantity = quantity
        item.full_clean()
        item.save()
        cart.refresh_from_db()
        return Response(CartSerializer(cart, context={'request': request}).data)

    @action(detail=False, methods=['post'], url_path='remove/(?P<item_id>[0-9]+)')
    def remove_item(self, request, item_id=None):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        item.delete()
        cart.refresh_from_db()
        return Response(CartSerializer(cart, context={'request': request}).data)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response(CartSerializer(cart, context={'request': request}).data)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    filterset_class = OrderFilter
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'total_amount']

    def get_queryset(self):
        # select_related: заказ → пользователь
        qs = Order.objects.select_related('user').prefetch_related('items__product')
        if self.request.user.is_admin:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        items = cart.items.select_related('product').all()
        if not items.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'cart': 'Корзина пуста.'})

        for item in items:
            if item.quantity > item.product.stock:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(
                    {'product': f'Недостаточно "{item.product.name}" на складе.'}
                )

        order = serializer.save(user=self.request.user)

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=item.product.price,
            )
            item.product.stock -= item.quantity
            item.product.save(update_fields=['stock'])

        order.recalculate_total()
        order.save(update_fields=['total_amount'])

        cart.items.all().delete()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def change_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Недопустимый статус.'}, status=400)
        order.status = new_status
        order.save(update_fields=['status'])
        return Response(OrderSerializer(order, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status in ['shipped', 'completed']:
            return Response({'error': 'Нельзя отменить отправленный/завершённый заказ.'}, status=400)

        for item in order.items.select_related('product').all():
            item.product.stock += item.quantity
            item.product.save(update_fields=['stock'])

        order.status = 'cancelled'
        order.save(update_fields=['status'])
        return Response(OrderSerializer(order, context={'request': request}).data)


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        # select_related: избранное → пользователь, услуга, товар
        qs = Favorite.objects.select_related('user', 'service', 'product')
        if self.request.user.is_admin:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    filterset_class = ReviewFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating']

    def get_permissions(self):
        if self.action in ['approve', 'reject', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # select_related: отзыв → пользователь, услуга, товар
        return Review.objects.select_related('user', 'service', 'product')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        review = self.get_object()
        review.is_approved = True
        review.save(update_fields=['is_approved'])
        return Response(ReviewSerializer(review, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        review = self.get_object()
        review.is_approved = False
        review.save(update_fields=['is_approved'])
        return Response(ReviewSerializer(review, context={'request': request}).data)


class SiteSettingsViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        settings = SiteSettings.load()
        serializer = SiteSettingsSerializer(settings)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'put'], permission_classes=[IsAdminUser])
    def manage(self, request):
        settings = SiteSettings.load()
        if request.method == 'PUT':
            serializer = SiteSettingsSerializer(settings, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = SiteSettingsSerializer(settings)
        return Response(serializer.data)