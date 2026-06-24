from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from workshop.models import (
    Category, Service, Product, Appointment,
    Cart, CartItem, Order, OrderItem,
    Review, Favorite, SiteSettings,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Заполняет БД тестовыми данными для тюнинг-ателье'

    def handle(self, *args, **kwargs):
        self.stdout.write('Начинаю заполнение БД...')
        
        # Очистка старых данных
        self.stdout.write('Очистка старых данных...')
        Favorite.objects.all().delete()
        Review.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        Appointment.objects.all().delete()
        Product.objects.all().delete()
        Service.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        
        # Создание категорий услуг
        self.stdout.write('Создание категорий услуг...')
        service_categories = [
            {'name': 'Тюнинг двигателя', 'slug': 'engine-tuning'},
            {'name': 'Тюнинг подвески', 'slug': 'suspension-tuning'},
            {'name': 'Кузовной тюнинг', 'slug': 'body-tuning'},
            {'name': 'Салон и комфорт', 'slug': 'interior-comfort'},
            {'name': 'Электрика и электроника', 'slug': 'electronics'},
            {'name': 'Выхлопные системы', 'slug': 'exhaust-systems'},
        ]
        
        for cat_data in service_categories:
            Category.objects.create(
                name=cat_data['name'],
                slug=cat_data['slug'],
                category_type='service',
                description=f'Категория услуг: {cat_data["name"]}'
            )
        
        # Создание категорий товаров
        self.stdout.write('Создание категорий товаров...')
        product_categories = [
            {'name': 'Турбины и компрессоры', 'slug': 'turbos-superchargers'},
            {'name': 'Фильтры и масла', 'slug': 'filters-oils'},
            {'name': 'Диски и шины', 'slug': 'wheels-tires'},
            {'name': 'Аудиосистемы', 'slug': 'audio-systems'},
            {'name': 'Запчасти двигателя', 'slug': 'engine-parts'},
            {'name': 'Аксессуары', 'slug': 'accessories'},
        ]
        
        for cat_data in product_categories:
            Category.objects.create(
                name=cat_data['name'],
                slug=cat_data['slug'],
                category_type='product',
                description=f'Категория товаров: {cat_data["name"]}'
            )
        
        # Создание услуг
        self.stdout.write('Создание услуг...')
        services = [
            {
                'name': 'Чип-тюнинг Stage 1',
                'category_slug': 'engine-tuning',
                'price': Decimal('15000.00'),
                'duration': 120,
                'description': 'Оптимизация работы двигателя путём перепрограммирования ЭБУ. Увеличение мощности на 10-15%.'
            },
            {
                'name': 'Чип-тюнинг Stage 2',
                'category_slug': 'engine-tuning',
                'price': Decimal('25000.00'),
                'duration': 180,
                'description': 'Продвинутый чип-тюнинг с доработкой впуска и выпуска. Увеличение мощности на 20-30%.'
            },
            {
                'name': 'Установка турбины',
                'category_slug': 'engine-tuning',
                'price': Decimal('45000.00'),
                'duration': 480,
                'description': 'Профессиональная установка турбокомпрессора с настройкой и тестированием.'
            },
            {
                'name': 'Замена масла и фильтров',
                'category_slug': 'engine-tuning',
                'price': Decimal('3500.00'),
                'duration': 60,
                'description': 'Замена моторного масла и всех фильтров (масляный, воздушный, топливный).'
            },
            {
                'name': 'Установка койловеров',
                'category_slug': 'suspension-tuning',
                'price': Decimal('18000.00'),
                'duration': 240,
                'description': 'Установка регулируемой подвески (койловеров) с настройкой высоты и жёсткости.'
            },
            {
                'name': 'Усиление стабилизаторов',
                'category_slug': 'suspension-tuning',
                'price': Decimal('12000.00'),
                'duration': 180,
                'description': 'Установка усиленных стабилизаторов поперечной устойчивости для улучшения управляемости.'
            },
            {
                'name': 'Тонировка стёкол',
                'category_slug': 'body-tuning',
                'price': Decimal('8000.00'),
                'duration': 180,
                'description': 'Тонировка задних стёкол плёнкой премиум-класса с гарантией.'
            },
            {
                'name': 'Установка спойлера',
                'category_slug': 'body-tuning',
                'price': Decimal('15000.00'),
                'duration': 240,
                'description': 'Установка аэродинамического спойлера с покраской в цвет кузова.'
            },
            {
                'name': 'Шумоизоляция салона',
                'category_slug': 'interior-comfort',
                'price': Decimal('35000.00'),
                'duration': 480,
                'description': 'Полная шумоизоляция салона: двери, пол, потолок, багажник.'
            },
            {
                'name': 'Установка аудиосистемы',
                'category_slug': 'interior-comfort',
                'price': Decimal('25000.00'),
                'duration': 360,
                'description': 'Установка премиальной аудиосистемы с сабвуфером и усилителем.'
            },
            {
                'name': 'Установка сигнализации',
                'category_slug': 'electronics',
                'price': Decimal('12000.00'),
                'duration': 240,
                'description': 'Установка охранной сигнализации с автозапуском и GPS-трекером.'
            },
            {
                'name': 'Установка камеры заднего вида',
                'category_slug': 'electronics',
                'price': Decimal('8000.00'),
                'duration': 120,
                'description': 'Установка камеры заднего вида с подключением к мультимедийной системе.'
            },
            {
                'name': 'Установка прямоточного выхлопа',
                'category_slug': 'exhaust-systems',
                'price': Decimal('28000.00'),
                'duration': 300,
                'description': 'Установка прямоточной выхлопной системы из нержавеющей стали.'
            },
            {
                'name': 'Замена катализатора на пламегаситель',
                'category_slug': 'exhaust-systems',
                'price': Decimal('18000.00'),
                'duration': 240,
                'description': 'Удаление катализатора и установка пламегасителя с перепрошивкой ЭБУ.'
            },
        ]
        
        for svc_data in services:
            category = Category.objects.get(slug=svc_data['category_slug'])
            Service.objects.create(
                name=svc_data['name'],
                category=category,
                price=svc_data['price'],
                duration_minutes=svc_data['duration'],
                description=svc_data['description'],
                is_active=True
            )
        
        # Создание товаров
        self.stdout.write('Создание товаров...')
        products = [
            {
                'name': 'Турбина Garrett GT2860R',
                'category_slug': 'turbos-superchargers',
                'manufacturer': 'Garrett',
                'price': Decimal('85000.00'),
                'stock': 3,
                'description': 'Турбокомпрессор Garrett GT2860R с двойным шарикоподшипником. Мощность до 350 л.с.'
            },
            {
                'name': 'Турбина BorgWarner EFR 6258',
                'category_slug': 'turbos-superchargers',
                'manufacturer': 'BorgWarner',
                'price': Decimal('120000.00'),
                'stock': 2,
                'description': 'Турбокомпрессор BorgWarner EFR 6258 с керамическим колесом. Мощность до 400 л.с.'
            },
            {
                'name': 'Масло Motul 8100 X-cess 5W-40',
                'category_slug': 'filters-oils',
                'manufacturer': 'Motul',
                'price': Decimal('4500.00'),
                'stock': 15,
                'description': 'Синтетическое моторное масло 5W-40, 5 литров. Для бензиновых двигателей.'
            },
            {
                'name': 'Масляный фильтр Mann W 712/75',
                'category_slug': 'filters-oils',
                'manufacturer': 'Mann',
                'price': Decimal('850.00'),
                'stock': 25,
                'description': 'Масляный фильтр Mann W 712/75. Подходит для большинства европейских автомобилей.'
            },
            {
                'name': 'Воздушный фильтр K&N 33-2304',
                'category_slug': 'filters-oils',
                'manufacturer': 'K&N',
                'price': Decimal('3200.00'),
                'stock': 10,
                'description': 'Спортивный воздушный фильтр K&N многоразового использования.'
            },
            {
                'name': 'Диски BBS RI-A 18x8.5',
                'category_slug': 'wheels-tires',
                'manufacturer': 'BBS',
                'price': Decimal('95000.00'),
                'stock': 4,
                'description': 'Кованые диски BBS RI-A 18x8.5 ET35. Комплект 4 штуки.'
            },
            {
                'name': 'Шины Michelin Pilot Sport 4 225/40 R18',
                'category_slug': 'wheels-tires',
                'manufacturer': 'Michelin',
                'price': Decimal('18000.00'),
                'stock': 8,
                'description': 'Летние шины Michelin Pilot Sport 4 225/40 R18. Цена за 1 штуку.'
            },
            {
                'name': 'Сабвуфер JL Audio 12W3v3',
                'category_slug': 'audio-systems',
                'manufacturer': 'JL Audio',
                'price': Decimal('45000.00'),
                'stock': 3,
                'description': 'Сабвуфер JL Audio 12W3v3 300мм. Мощность 500W RMS.'
            },
            {
                'name': 'Усилитель Alpine MRV-F300',
                'category_slug': 'audio-systems',
                'manufacturer': 'Alpine',
                'price': Decimal('28000.00'),
                'stock': 5,
                'description': '4-канальный усилитель Alpine MRV-F300. Мощность 4x75W.'
            },
            {
                'name': 'Свечи зажигания NGK Iridium IX',
                'category_slug': 'engine-parts',
                'manufacturer': 'NGK',
                'price': Decimal('1200.00'),
                'stock': 20,
                'description': 'Свечи зажигания NGK Iridium IX. Комплект 4 штуки.'
            },
            {
                'name': 'Катушки зажигания Bosch 0986221022',
                'category_slug': 'engine-parts',
                'manufacturer': 'Bosch',
                'price': Decimal('3500.00'),
                'stock': 12,
                'description': 'Катушка зажигания Bosch. Цена за 1 штуку.'
            },
            {
                'name': 'Коврики в салон премиум',
                'category_slug': 'accessories',
                'manufacturer': 'Premium Auto',
                'price': Decimal('8500.00'),
                'stock': 7,
                'description': 'Коврики в салон из экокожи премиум-класса. Индивидуальный пошив.'
            },
            {
                'name': 'Держатель телефона с беспроводной зарядкой',
                'category_slug': 'accessories',
                'manufacturer': 'Baseus',
                'price': Decimal('2500.00'),
                'stock': 15,
                'description': 'Автомобильный держатель телефона с беспроводной зарядкой 15W.'
            },
        ]
        
        for prod_data in products:
            category = Category.objects.get(slug=prod_data['category_slug'])
            Product.objects.create(
                name=prod_data['name'],
                category=category,
                manufacturer=prod_data['manufacturer'],
                price=prod_data['price'],
                stock=prod_data['stock'],
                description=prod_data['description'],
                is_active=True
            )
        
        # Создание пользователей
        self.stdout.write('Создание пользователей...')
        users_data = [
            {'username': 'client1', 'email': 'client1@example.com', 'role': 'client', 'first_name': 'Иван', 'last_name': 'Петров', 'phone': '+79991234567'},
            {'username': 'client2', 'email': 'client2@example.com', 'role': 'client', 'first_name': 'Мария', 'last_name': 'Сидорова', 'phone': '+79997654321'},
            {'username': 'client3', 'email': 'client3@example.com', 'role': 'client', 'first_name': 'Алексей', 'last_name': 'Козлов', 'phone': '+79991112233'},
            {'username': 'client4', 'email': 'client4@example.com', 'role': 'client', 'first_name': 'Елена', 'last_name': 'Волкова', 'phone': '+79994445566'},
            {'username': 'client5', 'email': 'client5@example.com', 'role': 'client', 'first_name': 'Дмитрий', 'last_name': 'Новиков', 'phone': '+79997778899'},
        ]
        
        users = []
        for user_data in users_data:
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password='testpass123',
                role=user_data['role'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                phone=user_data['phone'],
            )
            users.append(user)
        
        # Создание отзывов
        self.stdout.write('Создание отзывов...')
        services_list = list(Service.objects.all())
        products_list = list(Product.objects.all())
        
        reviews_data = [
            {'user_idx': 0, 'target_type': 'service', 'service_idx': 0, 'rating': 5, 'text': 'Отличный чип-тюнинг! Машина поехала совсем по-другому.', 'is_approved': True},
            {'user_idx': 1, 'target_type': 'service', 'service_idx': 0, 'rating': 4, 'text': 'Хорошая работа, но долго делали.', 'is_approved': True},
            {'user_idx': 2, 'target_type': 'service', 'service_idx': 2, 'rating': 5, 'text': 'Установили турбину профессионально. Всё работает идеально!', 'is_approved': True},
            {'user_idx': 0, 'target_type': 'product', 'product_idx': 0, 'rating': 5, 'text': 'Турбина Garrett - качество на высоте.', 'is_approved': True},
            {'user_idx': 3, 'target_type': 'product', 'product_idx': 6, 'rating': 4, 'text': 'Шины Michelin отличные, но дороговато.', 'is_approved': True},
            {'user_idx': 4, 'target_type': 'service', 'service_idx': 8, 'rating': 5, 'text': 'Шумоизоляция супер! В салоне стало намного тише.', 'is_approved': True},
            {'user_idx': 1, 'target_type': 'product', 'product_idx': 8, 'rating': 5, 'text': 'Усилитель Alpine звучит потрясающе!', 'is_approved': False},
        ]
        
        for review_data in reviews_data:
            user = users[review_data['user_idx']]
            if review_data['target_type'] == 'service':
                service = services_list[review_data['service_idx']]
                Review.objects.create(
                    user=user,
                    target_type='service',
                    service=service,
                    rating=review_data['rating'],
                    text=review_data['text'],
                    is_approved=review_data['is_approved'],
                )
            else:
                product = products_list[review_data['product_idx']]
                Review.objects.create(
                    user=user,
                    target_type='product',
                    product=product,
                    rating=review_data['rating'],
                    text=review_data['text'],
                    is_approved=review_data['is_approved'],
                )
        
        # Создание записей на услуги
        self.stdout.write('Создание записей на услуги...')
        appointments_data = [
            {'user_idx': 0, 'service_idx': 0, 'days_ahead': 2, 'hours': 10, 'status': 'confirmed', 'note': 'Хочу на утро'},
            {'user_idx': 1, 'service_idx': 2, 'days_ahead': 5, 'hours': 14, 'status': 'pending', 'note': 'Установка турбины'},
            {'user_idx': 2, 'service_idx': 8, 'days_ahead': 7, 'hours': 9, 'status': 'confirmed', 'note': 'Шумоизоляция салона'},
        ]
        
        for appt_data in appointments_data:
            user = users[appt_data['user_idx']]
            service = services_list[appt_data['service_idx']]
            appointment_datetime = timezone.now() + timedelta(days=appt_data['days_ahead'], hours=appt_data['hours'])
            Appointment.objects.create(
                user=user,
                service=service,
                appointment_datetime=appointment_datetime,
                status=appt_data['status'],
                note=appt_data['note'],
            )
        
        # Создание заказов
        self.stdout.write('Создание заказов...')
        orders_data = [
            {'user_idx': 0, 'items': [(0, 2), (6, 4)], 'address': 'ул. Ленина, д. 1, Москва, 101000', 'phone': '+79991234567', 'payment': 'card', 'status': 'completed'},
            {'user_idx': 1, 'items': [(2, 1), (4, 2)], 'address': 'пр. Мира, д. 15, кв. 10, Москва, 102000', 'phone': '+79997654321', 'payment': 'cash', 'status': 'shipped'},
            {'user_idx': 2, 'items': [(8, 1)], 'address': 'ул. Пушкина, д. 5, Санкт-Петербург, 190000', 'phone': '+79991112233', 'payment': 'online', 'status': 'processing'},
        ]
        
        for order_data in orders_data:
            user = users[order_data['user_idx']]
            order = Order.objects.create(
                user=user,
                address=order_data['address'],
                phone=order_data['phone'],
                payment_method=order_data['payment'],
                status=order_data['status'],
            )
            
            for item_data in order_data['items']:
                product = products_list[item_data[0]]
                quantity = item_data[1]
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price_at_purchase=product.price,
                )
            
            order.recalculate_total()
            order.save()
        
        # Создание настроек сайта
        self.stdout.write('Создание настроек сайта...')
        SiteSettings.objects.create(
            company_name='Tuning Atelier',
            description='Профессиональное тюнинг-ателье. Работаем с 2010 года. Гарантия на все виды работ.',
            phone='+7 (495) 123-45-67',
            email='info@tuning-atelier.ru',
            address='г. Москва, ул. Автомобильная, д. 15',
            privacy_policy='Мы не передаём ваши данные третьим лицам. Все персональные данные обрабатываются в соответствии с ФЗ-152.',
        )
        
        self.stdout.write(self.style.SUCCESS('БД успешно заполнена тестовыми данными!'))
        self.stdout.write(f'Создано категорий: {Category.objects.count()}')
        self.stdout.write(f'Создано услуг: {Service.objects.count()}')
        self.stdout.write(f'Создано товаров: {Product.objects.count()}')
        self.stdout.write(f'Создано пользователей: {User.objects.filter(is_superuser=False).count()}')
        self.stdout.write(f'Создано отзывов: {Review.objects.count()}')
        self.stdout.write(f'Создано записей: {Appointment.objects.count()}')
        self.stdout.write(f'Создано заказов: {Order.objects.count()}')
        self.stdout.write(f'Создано настроек: {SiteSettings.objects.count()}')