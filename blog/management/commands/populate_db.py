from django.core.management.base import BaseCommand
from faker import Faker
import random
from blog.models import UserProfile, Address, Category, Brand, Product, Color, ProductVariant, ProductColor, Review, Basket, Order, BasketOrder, ProductOrder
from django.contrib.auth.models import User

# Инициализация Faker с русской локализацией
fake = Faker('ru_RU')

# Списки для категорий
CATEGORIES = [
 "Куртки", "Футболки", "Штаны", "Обувь", "Шапки", "Рюкзаки", "Аксессуары", "Худи",
"Джинсы", "Ветровки"
]


class Command(BaseCommand):
    help = 'Populates the database with fake data'
    def handle(self, *args, **kwargs):
        self.create_users(20)
        self.create_categories()
        self.create_brands()
        self.create_products(50)
        self.create_colors()
        self.create_product_variants()
        self.create_product_colors()
        self.create_reviews(200)
        self.create_baskets(50)
        self.create_orders(30)
        self.create_basket_orders(100)
        self.create_product_orders(100)
    def create_users(self, number):
        for _ in range(number):
            user = User.objects.create(
            username=fake.unique.user_name(),
            email=fake.unique.email(),
            password=fake.password()
            )
            UserProfile.objects.create(
            user=user,
            phone=fake.phone_number(),
            role=random.choice(['consumer', 'seller', 'admin'])
            )
            Address.objects.create(
            user=user,
            country="Россия",
            city=fake.city_name(),
            street=fake.street_name(),
            index=fake.postcode()
            )

    def create_categories(self):
        for category in CATEGORIES: # Для каждой категории из массива создается объект со случайными фото и слагом
            Category.objects.create(
            name=category,
            photo=fake.image(),
            slug=fake.unique.slug()
            )
    # Другие методы для создания категорий, брендов, продуктов и т.д.

    