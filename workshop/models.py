from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    ROLE_CHOICES = [
        ('client', _('Клиент')),
        ('admin', _('Администратор')),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='client',
        verbose_name=_('Роль'),
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Телефон'),
    )

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser


class Category(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ('service', _('Услуга')),
        ('product', _('Товар')),
    ]
    name = models.CharField(max_length=150, verbose_name=_('Название'))
    slug = models.SlugField(max_length=150, unique=True, verbose_name=_('Слаг'))
    category_type = models.CharField(
        max_length=10,
        choices=CATEGORY_TYPE_CHOICES,
        verbose_name=_('Тип категории'),
    )
    description = models.TextField(blank=True, verbose_name=_('Описание'))

    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        unique_together = ('name', 'category_type')
        ordering = ['name']

    def __str__(self):
        return f"{self.get_category_type_display()}: {self.name}"


class Service(models.Model):
    name = models.CharField(max_length=200, verbose_name=_('Название услуги'))
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        limit_choices_to={'category_type': 'service'},
        verbose_name=_('Категория'),
    )
    description = models.TextField(verbose_name=_('Описание'))
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Цена'),
    )
    duration_minutes = models.PositiveIntegerField(
        verbose_name=_('Длительность (мин)'),
        help_text=_('Примерная длительность услуги в минутах'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Активна'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Услуга')
        verbose_name_plural = _('Услуги')
        unique_together = ('name', 'category')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def clean(self):
        if self.price <= 0:
            raise ValidationError({'price': _('Цена должна быть положительной.')})
        if self.duration_minutes <= 0:
            raise ValidationError({'duration_minutes': _('Длительность должна быть > 0.')})

    def get_formatted_price(self):
        return f"{self.price:,.2f} ₽".replace(',', ' ').replace('.', ',')


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name=_('Название товара'))
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        limit_choices_to={'category_type': 'product'},
        verbose_name=_('Категория'),
    )
    manufacturer = models.CharField(max_length=200, blank=True, verbose_name=_('Производитель'))
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Цена'),
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Остаток на складе'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Активен'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Товар')
        verbose_name_plural = _('Товары')
        unique_together = ('name', 'category')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def clean(self):
        if self.price <= 0:
            raise ValidationError({'price': _('Цена должна быть положительной.')})

    def get_formatted_price(self):
        return f"{self.price:,.2f} ₽".replace(',', ' ').replace('.', ',')


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Ожидает подтверждения')),
        ('confirmed', _('Подтверждено')),
        ('completed', _('Завершено')),
        ('cancelled', _('Отменено')),
    ]
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name=_('Клиент'),
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name=_('Услуга'),
    )
    appointment_datetime = models.DateTimeField(verbose_name=_('Дата и время записи'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Статус'),
    )
    note = models.TextField(blank=True, verbose_name=_('Комментарий'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Запись на услугу')
        verbose_name_plural = _('Записи на услуги')
        ordering = ['-appointment_datetime']

    def __str__(self):
        return f"{self.user} → {self.service} ({self.appointment_datetime:%d.%m.%Y %H:%M})"

    def clean(self):
        if self.appointment_datetime and timezone.is_aware(self.appointment_datetime):
            if self.appointment_datetime < timezone.now():
                raise ValidationError(
                    {'appointment_datetime': _('Нельзя записаться в прошедшее время.')}
                )

        if self.service_id and self.appointment_datetime:
            overlapping = Appointment.objects.filter(
                service=self.service,
                appointment_datetime=self.appointment_datetime,
                status__in=['pending', 'confirmed'],
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError(
                    {'appointment_datetime': _(
                        'На это время уже есть запись на данную услугу. '
                        'Выберите другое время.'
                    )}
                )


class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('Владелец корзины'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Корзина')
        verbose_name_plural = _('Корзины')

    def __str__(self):
        return f"Корзина {self.user}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Количество'),
    )

    class Meta:
        verbose_name = _('Позиция корзины')
        verbose_name_plural = _('Позиции корзины')
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} × {self.product}"

    @property
    def total_price(self):
        return self.product.price * self.quantity

    def clean(self):
        if self.quantity and self.quantity > self.product.stock:
            raise ValidationError(
                {'quantity': _(
                    f'Недостаточно товара на складе. Доступно: {self.product.stock}.'
                )}
            )


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', _('Новый')),
        ('processing', _('В обработке')),
        ('confirmed', _('Подтверждён')),
        ('shipped', _('Отправлен')),
        ('completed', _('Завершён')),
        ('cancelled', _('Отменён')),
    ]
    PAYMENT_CHOICES = [
        ('cash', _('Наличные')),
        ('card', _('Банковская карта')),
        ('online', _('Онлайн-перевод')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Клиент'),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name=_('Статус'),
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='cash',
        verbose_name=_('Способ оплаты'),
    )
    address = models.CharField(
        max_length=500,
        verbose_name=_('Адрес доставки'),
        validators=[
            RegexValidator(
                regex=r'^[а-яА-ЯёЁa-zA-Z\s\-\.,]+,\s*д\.\s*\d+[а-яА-Яa-zA-Z]?(?:,\s*кв\.\s*\d+)?,\s*[а-яА-ЯёЁa-zA-Z\s\-]+,\s*\d{6}$',
                message=_('Адрес должен быть в формате: "ул. Примерная, д. 1, Москва, 101000".'),
            )
        ],
    )
    phone = models.CharField(max_length=20, verbose_name=_('Контактный телефон'))
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Итоговая сумма'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.pk} от {self.user} ({self.get_status_display()})"

    def clean(self):
        if self.total_amount is not None and self.total_amount <= 0:
            raise ValidationError(
                {'total_amount': _('Сумма заказа должна быть положительной.')}
            )

    def recalculate_total(self):
        self.total_amount = sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _('Позиция заказа')
        verbose_name_plural = _('Позиции заказа')

    def __str__(self):
        return f"{self.quantity} × {self.product}"

    @property
    def total_price(self):
        return self.price_at_purchase * self.quantity


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='favorites',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='favorites',
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Избранное')
        verbose_name_plural = _('Избранное')

    def clean(self):
        if not self.service and not self.product:
            raise ValidationError(_('Нужно указать товар или услугу.'))
        if self.service and self.product:
            raise ValidationError(_('Можно указать только что-то одно: товар ИЛИ услугу.'))


class Review(models.Model):
    TARGET_CHOICES = [
        ('service', _('Услуга')),
        ('product', _('Товар')),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Оценка (1-5)'),
    )
    text = models.TextField(verbose_name=_('Текст отзыва'))
    is_approved = models.BooleanField(default=False, verbose_name=_('Одобрен админом'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Отзыв')
        verbose_name_plural = _('Отзывы')
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.user} ({self.rating}/5)"

    def clean(self):
        if not self.service and not self.product:
            raise ValidationError(_('Нужно указать товар или услугу.'))
        if self.service and self.product:
            raise ValidationError(_('Отзыв может быть либо к услуге, либо к товару.'))
        if self.rating < 1 or self.rating > 5:
            raise ValidationError({'rating': _('Оценка должна быть от 1 до 5.')})
        
class SiteSettings(models.Model):
    company_name = models.CharField(max_length=200, default='Tuning Atelier')
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    privacy_policy = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Настройки сайта')
        verbose_name_plural = _('Настройки сайта')

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj