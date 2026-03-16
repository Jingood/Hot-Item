from django.urls import path
from .views import *

urlpatterns = [
    path('items/', ItemListView.as_view(), name='item-list'),
    path('orders/', OrderCreateView.as_view(), name='order-create'),
]
