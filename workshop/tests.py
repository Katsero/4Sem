from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from .models import (
    Category, Service, Product, Appointment,
    Cart, CartItem, Order, OrderItem,
    Review,
)

User = get_user_model()


class ModelValidationTests(TestCase):
    """Тесты валидации моделей."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='client'
        )
        self.category_service = Category.objects.create(
            name='Тюнинг двигателя',
            slug='engine-tuning',
            category_type='service'
        )
        self.category_product = Category.objects.create(
            name='Запчасти',
            slug='parts',
            category_type='product'
        )

    def test_01_order_negative_amount_validation(self):
        """Тест 1: Валидация Order — сумма заказа не может быть ≤ 0."""
        order = Order(
            user=self.user,
            address='ул. Ленина, д. 1, Москва, 101000',
            phone='+79991234567',
            total_amount=-100,
        )
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_02_service_formatted_price(self):
        """Тест 2: Метод get_formatted_price правильно форматирует цену."""
        service = Service.objects.create(
            name='Чип-тюнинг',
            category=self.category_service,
            price=15000.50,
            duration_minutes=120,
        )
        self.assertEqual(service.get_formatted_price(), '15 000,50 ₽')

    def test_03_product_formatted_price(self):
        """Тест 3: Метод get_formatted_price для товара."""
        product = Product.objects.create(
            name='Турбина',
            category=self.category_product,
            price=45000,
            stock=5,
        )
        self.assertEqual(product.get_formatted_price(), '45 000,00 ₽')

    def test_04_service_unique_together_validation(self):
        """Тест 4: Уникальность услуги в рамках категории."""
        Service.objects.create(
            name='Чип-тюнинг',
            category=self.category_service,
            price=15000,
            duration_minutes=120,
        )
        duplicate = Service(
            name='Чип-тюнинг',
            category=self.category_service,
            price=20000,
            duration_minutes=180,
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_05_product_stock_validation(self):
        """Тест 5: Валидация наличия товара на складе в корзине."""
        product = Product.objects.create(
            name='Фильтр',
            category=self.category_product,
            price=1000,
            stock=2,
        )
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem(
            cart=cart,
            product=product,
            quantity=5,
        )
        with self.assertRaises(ValidationError):
            cart_item.full_clean()

    def test_06_appointment_past_datetime_validation(self):
        """Тест 6: Нельзя записаться на услугу в прошлое."""
        service = Service.objects.create(
            name='Диагностика',
            category=self.category_service,
            price=2000,
            duration_minutes=60,
        )
        appointment = Appointment(
            user=self.user,
            service=service,
            appointment_datetime=timezone.now() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            appointment.full_clean()

    def test_07_appointment_duplicate_time_validation(self):
        """Тест 7: Валидация доступности времени для записи."""
        service = Service.objects.create(
            name='Замена масла',
            category=self.category_service,
            price=3000,
            duration_minutes=90,
        )
        dt = timezone.now() + timedelta(days=1, hours=10)
        Appointment.objects.create(
            user=self.user,
            service=service,
            appointment_datetime=dt,
            status='confirmed',
        )
        duplicate = Appointment(
            user=User.objects.create_user(username='user2', password='pass'),
            service=service,
            appointment_datetime=dt,
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_08_order_address_format_validation(self):
        """Тест 8: Валидация формата адреса доставки."""
        order = Order(
            user=self.user,
            address='Неправильный адрес',
            phone='+79991234567',
            total_amount=5000,
        )
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_09_review_rating_validation(self):
        """Тест 9: Оценка отзыва должна быть от 1 до 5."""
        service = Service.objects.create(
            name='Тест',
            category=self.category_service,
            price=1000,
            duration_minutes=30,
        )
        review = Review(
            user=self.user,
            target_type='service',
            service=service,
            rating=6,
            text='Отлично',
        )
        with self.assertRaises(ValidationError):
            review.full_clean()

    def test_10_product_price_validation(self):
        """Тест 10: Цена товара должна быть положительной."""
        product = Product(
            name='Тест',
            category=self.category_product,
            price=-100,
            stock=10,
        )
        with self.assertRaises(ValidationError):
            product.full_clean()


class APITests(APITestCase):
    """Тесты API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apiuser',
            password='apipass123',
            role='client'
        )
        self.admin = User.objects.create_user(
            username='adminuser',
            password='adminpass123',
            role='admin'
        )
        self.category = Category.objects.create(
            name='Тюнинг',
            slug='tuning',
            category_type='service'
        )
        self.service = Service.objects.create(
            name='Чип-тюнинг',
            category=self.category,
            price=15000,
            duration_minutes=120,
        )
        self.product = Product.objects.create(
            name='Турбина',
            category=Category.objects.create(
                name='Запчасти',
                slug='parts',
                category_type='product'
            ),
            price=45000,
            stock=5,
        )

    def test_11_service_list_view(self):
        """Тест 11: ServiceListView возвращает корректный список услуг."""
        response = self.client.get('/api/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Чип-тюнинг')

    def test_12_add_product_to_cart(self):
        """Тест 12: Добавление товара в корзину."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/cart/add/', {
            'product': self.product.id,
            'quantity': 2,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['total_items'], 2)

    def test_13_create_order(self):
        """Тест 13: Оформление заказа."""
        self.client.force_authenticate(user=self.user)
        Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=self.user.cart,
            product=self.product,
            quantity=1,
        )
        response = self.client.post('/api/orders/', {
            'address': 'ул. Ленина, д. 1, Москва, 101000',
            'phone': '+79991234567',
            'payment_method': 'card',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'new')
        self.assertIsNotNone(response.data['total_amount'])

    def test_14_create_appointment(self):
        """Тест 14: Запись на услугу."""
        self.client.force_authenticate(user=self.user)
        dt = timezone.now() + timedelta(days=1, hours=10)
        response = self.client.post('/api/appointments/', {
            'service': self.service.id,
            'appointment_datetime': dt.isoformat(),
            'note': 'Хочу на утро',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')

    def test_15_product_filter_by_price(self):
        """Тест 15: Фильтрация товаров по цене."""
        response = self.client.get('/api/products/?min_price=40000&max_price=50000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_16_create_review(self):
        """Тест 16: Создание отзыва."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/reviews/', {
            'target_type': 'service',
            'service': self.service.id,
            'rating': 5,
            'text': 'Отличная услуга!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 5)

    def test_17_user_me_endpoint(self):
        """Тест 17: Получение данных текущего пользователя."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'apiuser')

    def test_18_cart_total_calculation(self):
        """Тест 18: Расчёт общей суммы корзины."""
        self.client.force_authenticate(user=self.user)
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_total = self.product.price * 2
        self.assertEqual(float(response.data['total_price']), float(expected_total))

    def test_19_service_avg_rating_annotation(self):
        """Тест 19: Аннотация среднего рейтинга услуги."""
        Review.objects.create(
            user=self.user,
            target_type='service',
            service=self.service,
            rating=5,
            text='Отлично',
            is_approved=True,
        )
        Review.objects.create(
            user=User.objects.create_user(username='user2', password='pass'),
            target_type='service',
            service=self.service,
            rating=4,
            text='Хорошо',
            is_approved=True,
        )
        response = self.client.get(f'/api/services/{self.service.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['avg_rating'], 4.5)

    def test_20_admin_change_order_status(self):
        """Тест 20: Админ меняет статус заказа."""
        self.client.force_authenticate(user=self.admin)
        order = Order.objects.create(
            user=self.user,
            address='ул. Ленина, д. 1, Москва, 101000',
            phone='+79991234567',
            total_amount=5000,
            status='new',
        )
        response = self.client.post(f'/api/orders/{order.id}/change_status/', {
            'status': 'confirmed',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'confirmed')