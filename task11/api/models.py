# api/models.py

from django.db import models
from django.contrib.auth import get_user_model

# Получаем активную модель пользователя (в нашем случае это users.LegacyUser)
# Это нужно для динамических связей, если они потребуются в будущем.
UserModel = get_user_model()

# --- Справочные таблицы ---
# Все эти модели неуправляемые (managed=False), так как таблицы уже существуют в БД.

class Address(models.Model):
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50, blank=True)

    class Meta:
        managed = False
        db_table = 'addresses'

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}"


class Coordinates(models.Model):
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'coordinates'

    def __str__(self):
        return f"{self.latitude}, {self.longitude}"


class SocialLinks(models.Model):
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    website_link = models.URLField(blank=True)

    class Meta:
        managed = False
        db_table = 'social_links'

    def __str__(self):
        return "Social Links"


class PaymentOptions(models.Model):
    credit_cards = models.BooleanField(default=False)
    wic = models.BooleanField(default=False)
    wic_cash = models.BooleanField(default=False)
    sfmnp = models.BooleanField(default=False)
    snap = models.BooleanField(default=False)
    ebt = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'payment_options'

    def __str__(self):
        return "Payment Options"


class Products(models.Model):
    organic = models.BooleanField(default=False)
    baked_goods = models.BooleanField(default=False)
    cheese = models.BooleanField(default=False)
    crafts = models.BooleanField(default=False)
    flowers = models.BooleanField(default=False)
    eggs = models.BooleanField(default=False)
    seafood = models.BooleanField(default=False)
    herbs = models.BooleanField(default=False)
    vegetables = models.BooleanField(default=False)
    honey = models.BooleanField(default=False)
    jams = models.BooleanField(default=False)
    maple = models.BooleanField(default=False)
    meat = models.BooleanField(default=False)
    nursery = models.BooleanField(default=False)
    nuts = models.BooleanField(default=False)
    plants = models.BooleanField(default=False)
    poultry = models.BooleanField(default=False)
    prepared = models.BooleanField(default=False)
    soap = models.BooleanField(default=False)
    trees = models.BooleanField(default=False)
    wine = models.CharField(max_length=10, blank=True) # Изменено на CharField для совместимости с БД
    coffee = models.BooleanField(default=False)
    beans = models.BooleanField(default=False)
    fruits = models.BooleanField(default=False)
    grains = models.BooleanField(default=False)
    juices = models.BooleanField(default=False)
    mushrooms = models.BooleanField(default=False)
    pet_food = models.BooleanField(default=False)
    tofu = models.BooleanField(default=False)
    wild_harvested = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'products'

    def __str__(self):
        return "Products List"


class OperatingSchedule(models.Model):
    season_number = models.IntegerField()
    season_date = models.CharField(max_length=100, blank=True)
    season_time = models.CharField(max_length=100, blank=True)
    
    # Дополнительные поля для расписания (часто встречаются в БД)
    season_enddate = models.CharField(max_length=100, blank=True) 
    
    day_of_week = models.CharField(max_length=20, blank=True) 
    
    time_open = models.CharField(max_length=20, blank=True) 
    
    class Meta:
        managed = False
        db_table = 'operating_schedule'
        ordering = ['season_number']

# --- Основные модели ---

class Market(models.Model):
    # Указываем FMID как первичный ключ, так как в БД нет поля 'id'
    FMID = models.CharField(max_length=50, primary_key=True) 
    
    market_name = models.CharField(max_length=255)
    
    # Связи с другими таблицами
    address = models.OneToOneField(Address, on_delete=models.DO_NOTHING, db_column='address_id')
                 
    coordinates = models.OneToOneField(Coordinates, on_delete=models.DO_NOTHING, db_column='coordinate_id')
    
    social_links = models.OneToOneField(SocialLinks, on_delete=models.DO_NOTHING, db_column='social_links_id')
    
     # --- ИСПРАВЛЕНИЕ ТИПА ДАННЫХ ---
     # Если в БД поле 'wine' имеет тип VARCHAR/TEXT, а не BOOLEAN,
     # модель не будет работать. Изменено на CharField.
     # Проверьте типы данных в вашей БД для других полей при необходимости.
     
    payment_options = models.OneToOneField(PaymentOptions, on_delete=models.DO_NOTHING, db_column='payment_options_id')
    
    products = models.OneToOneField(Products, on_delete=models.DO_NOTHING, db_column='products_id')
     
     # График работы (ManyToMany связь через таблицу-связку)
     # Имя связующей таблицы может отличаться. Укажите реальное имя из вашей БД.
     # Часто это что-то вроде 'market_schedule' или 'market_operating_schedule'.
     # Если возникают ошибки, проверьте точное имя таблицы в вашей БД.
     
    schedule = models.ManyToManyField(OperatingSchedule,
                                       db_table='market_operating_schedule') 
     
     # Дополнительные поля (примеры), которые часто бывают в таблицах рынков
    website = models.URLField(blank=True)
    update_date_raw = models.CharField(max_length=50, blank=True) # Если дата хранится как строка

    class Meta:
        managed = False
        db_table = 'markets'

    def __str__(self):
        return self.market_name


class Review(models.Model):
     fmid = models.ForeignKey(Market, on_delete=models.DO_NOTHING, db_column='FMID')
     
     # --- ИСПРАВЛЕННАЯ СВЯЗЬ С ПОЛЬЗОВАТЕЛЕМ ---
     # Используем строковую ссылку на новую модель LegacyUser.
     # db_column='author' критически важен! Он указывает Django,
     # что в таблице 'reviews' колонка с именем пользователя называется 'author',
     # а не 'author_id' (как Django ожидает по умолчанию).
     author = models.ForeignKey('users.LegacyUser', on_delete=models.DO_NOTHING, db_column='author')
     
     rating = models.IntegerField()
     comment = models.TextField()
     
     class Meta:
         managed = False
         db_table = 'reviews'
         unique_together = ('fmid', 'author') # Один пользователь - один отзыв на рынок

     def __str__(self):
         return f"Отзыв от {self.author} на {self.fmid.market_name}"