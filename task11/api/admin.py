# api/admin.py
from django.contrib import admin
from .models import Market, Review, Address

admin.site.register(Market)
admin.site.register(Review)
admin.site.register(Address)