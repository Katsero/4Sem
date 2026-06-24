from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.generic import TemplateView, ListView, DetailView, View, CreateView
from django.contrib import messages

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    User, Category, Service, Product, Appointment,
    Cart, CartItem, Order, OrderItem,
    Favorite, Review,
)
from .serializers import (
    UserSerializer, UserAdminSerializer,
    CategorySerializer, ServiceSerializer, ProductSerializer,
    AppointmentSerializer, CartSerializer, CartItemSerializer,
    OrderSerializer, OrderItemSerializer,
    FavoriteSerializer, ReviewSerializer,
)
from .filters import (
    ServiceFilter, ProductFilter, AppointmentFilter, OrderFilter, ReviewFilter,
)
from .permissions import IsAdminOrReadOnly, IsAdminUser, IsOwnerOrAdmin
from .forms import AppointmentForm, CheckoutForm, SignUpForm
from django.urls import reverse


# ==================== API ViewSets ====================

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username']

    def get_queryset(self):
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
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def change_role(self, request, pk=None):
        user = self.get_object()
        new_role = request.data.get('role')
        if new_role not in dict(User.ROLE_CHOICES):
            return Response({'error': 'Недопустимая роль.'}, status=400)
        user.role = new_role
        user.save(update_fields=['role'])
        return Response(UserAdminSerializer(user, context={'request': request}).data)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    filterset_fields = ['category_type']


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
        qs = Appointment.objects.select_related('user', 'service', 'service__category')
        if self.request.user.is_admin:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
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
        qs = Order.objects.select_related('user').prefetch_related('items__product')
        if self.request.user.is_admin:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        items = cart.items.select_related('product').all()
        if not items.exists():
            raise DRFValidationError({'cart': 'Корзина пуста.'})

        for item in items:
            if item.quantity > item.product.stock:
                raise DRFValidationError(
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
            return Response(
                {'error': 'Нельзя отменить отправленный/завершённый заказ.'},
                status=400,
            )

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



# ==================== HTML Views ====================

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = Service.objects.filter(is_active=True)[:6]
        context['products'] = Product.objects.filter(is_active=True, stock__gt=0)[:6]
        context['categories'] = Category.objects.all()
        return context


class ServiceListView(ListView):
    model = Service
    template_name = 'services/list.html'
    context_object_name = 'services'
    paginate_by = 12

    def get_queryset(self):
        qs = Service.objects.filter(is_active=True).select_related('category')
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)
        min_price = self.request.GET.get('min_price')
        if min_price:
            qs = qs.filter(price__gte=min_price)
        max_price = self.request.GET.get('max_price')
        if max_price:
            qs = qs.filter(price__lte=max_price)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(category_type='service')
        return context


class ServiceDetailView(DetailView):
    model = Service
    template_name = 'services/detail.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.filter(is_approved=True)
        context['avg_rating'] = self.object.reviews.filter(is_approved=True).aggregate(
            avg=Avg('rating')
        )['avg'] or 0
        return context


class ProductListView(ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related('category')
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)
        min_price = self.request.GET.get('min_price')
        if min_price:
            qs = qs.filter(price__gte=min_price)
        max_price = self.request.GET.get('max_price')
        if max_price:
            qs = qs.filter(price__lte=max_price)
        in_stock = self.request.GET.get('in_stock')
        if in_stock:
            qs = qs.filter(stock__gt=0)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(category_type='product')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.filter(is_approved=True)
        context['avg_rating'] = self.object.reviews.filter(is_approved=True).aggregate(
            avg=Avg('rating')
        )['avg'] or 0
        return context


class CartView(LoginRequiredMixin, View):
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product').all()
        return render(request, 'cart.html', {'cart': cart, 'items': items})


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('workshop:login')
    product = get_object_or_404(Product, pk=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={'quantity': 1}
    )
    if not created:
        item.quantity += 1
    item.save()
    messages.success(request, f'Товар "{product.name}" добавлен в корзину.')
    return redirect(request.META.get('HTTP_REFERER', 'workshop:cart'))


def remove_from_cart(request, item_id):
    if not request.user.is_authenticated:
        return redirect('workshop:login')
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.delete()
    messages.success(request, 'Товар удалён из корзины.')
    return redirect('workshop:cart')


def update_cart_item(request, item_id):
    if not request.user.is_authenticated:
        return redirect('workshop:login')
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        item.quantity = quantity
        item.save()
    return redirect('workshop:cart')


class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product').all()
        form = CheckoutForm()
        return render(request, 'checkout.html', {'cart': cart, 'items': items, 'form': form})

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product').all()
        if not items.exists():
            messages.error(request, 'Корзина пуста.')
            return redirect('workshop:cart')

        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                address=form.cleaned_data['address'],
                phone=form.cleaned_data['phone'],
                payment_method=form.cleaned_data['payment_method'],
            )
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price_at_purchase=item.product.price,
                )
                item.product.stock -= item.quantity
                item.product.save()
            order.recalculate_total()
            order.save()
            cart.items.all().delete()
            messages.success(request, f'Заказ #{order.pk} оформлен!')
            return redirect('workshop:order_list')
        return render(request, 'checkout.html', {'cart': cart, 'items': items, 'form': form})


class AppointmentView(LoginRequiredMixin, View):
    def get(self, request, service_id=None):
        services = Service.objects.filter(is_active=True)
        initial = {}
        if service_id:
            initial['service'] = service_id
        form = AppointmentForm(initial=initial)
        return render(request, 'appointment.html', {'services': services, 'form': form})


def create_appointment(request):
    if not request.user.is_authenticated:
        return redirect('workshop:login')
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.save()
            messages.success(request, 'Запись создана! Ожидайте подтверждения.')
            return redirect('workshop:user_appointment_list')
    services = Service.objects.filter(is_active=True)
    form = AppointmentForm()
    return render(request, 'appointment.html', {'services': services, 'form': form})


def create_review(request):
    if not request.user.is_authenticated:
        return redirect('workshop:login')
    if request.method == 'POST':
        target_type = request.POST.get('target_type')
        service_id = request.POST.get('service')
        product_id = request.POST.get('product')
        rating = request.POST.get('rating')
        text = request.POST.get('text', '').strip()

        if not text or not rating:
            messages.error(request, 'Заполните все поля.')
            return redirect(request.META.get('HTTP_REFERER', 'workshop:home'))

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Оценка должна быть от 1 до 5.')
            return redirect(request.META.get('HTTP_REFERER', 'workshop:home'))

        review = Review(
            user=request.user,
            target_type=target_type,
            rating=rating,
            text=text,
            is_approved=False,
        )

        if target_type == 'service' and service_id:
            review.service = get_object_or_404(Service, pk=service_id)
            redirect_url = reverse('workshop:service_detail', kwargs={'pk': service_id})
        elif target_type == 'product' and product_id:
            review.product = get_object_or_404(Product, pk=product_id)
            redirect_url = reverse('workshop:product_detail', kwargs={'pk': product_id})
        else:
            messages.error(request, 'Не указан товар или услуга.')
            return redirect('workshop:home')

        try:
            review.full_clean()
            review.save()
            messages.success(request, 'Отзыв отправлен на модерацию.')
        except ValidationError as e:
            messages.error(request, str(e))

        return redirect(redirect_url)
    return redirect('workshop:home')


@login_required
def toggle_favorite(request, content_type, object_id):
    if content_type == 'service':
        obj = get_object_or_404(Service, pk=object_id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, service=obj
        )
        redirect_url = reverse('workshop:service_detail', kwargs={'pk': object_id})
    elif content_type == 'product':
        obj = get_object_or_404(Product, pk=object_id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, product=obj
        )
        redirect_url = reverse('workshop:product_detail', kwargs={'pk': object_id})
    else:
        return redirect('workshop:home')

    if not created:
        favorite.delete()
        messages.success(request, 'Удалено из избранного.')
    else:
        messages.success(request, 'Добавлено в избранное.')

    return redirect(redirect_url)


class FavoriteListView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = 'favorites.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('service', 'product')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders_count'] = self.request.user.orders.count()
        context['appointments_count'] = self.request.user.appointments.count()
        return context


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')


class UserAppointmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'appointments.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user).select_related('service')


class RegisterView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/register.html'
    success_url = '/'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)