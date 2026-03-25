from django.db import models
from django.conf import settings

class Item(models.Model):
    name = models.CharField(max_length=100, verbose_name="상품명")
    price = models.PositiveIntegerField(verbose_name="가격")
    # v1: RDBMS에 의존하는 재고 관리
    stock = models.PositiveIntegerField(default=0, verbose_name="잔여 재고")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (재고: {self.stock})"
    
    class Meta:
        db_table = 'items'


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = 'PENDING', '결제 대기'
        COMPLETED = 'COMPLETED', '결제 완료'
        FAILED = 'FAILED', '결제 실패'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    order_number = models.CharField(max_length=50, unique=True, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username} - {self.item.name}"

    class Meta:
        db_table = 'orders' 
        