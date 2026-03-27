from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db import transaction
from django.core.cache import cache
from django.db.models import F
from .models import *
from .serializers import *


class ItemListView(generics.ListAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [AllowAny]

"""
v1의 기록
class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    from drf_spectacular.utils import extend_schema
    @extend_schema(request=OrderSerializer, responses={201: OrderSerializer})
    def post(self, request, *args, **kwargs):
        serializers = OrderSerializer(data=request.data)
        serializers.is_valid(raise_exception=True)

        item = serializers.validated_data['item']

        # ? v1 (실패 유도), 일반적인 RDBMS 조회 -> 예상 효과: 수천 명이 동시에 실행하면 모두가 stock > 0 이라고 판단 (초과 판매 발생)
        if item.stock > 0:
            item.stock -= 1
            item.save()

            order = Order.objects.create(
                user=request.user,
                item=item,
                status=Order.Status.COMPLETED
            )

            return Response(
                {"message": "주문이 완료되었습니다.", "order_id": order.id, "remain_stock": item.stock},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {"error": "재고가 소진되었습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
"""

"""
v2의 기록
# ? v2, 데이버베이스 락: select_for_update 적용
class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request,*args, **kwargs):
        serializers = OrderSerializer(data=request.data)
        serializers.is_valid(raise_exception=True)

        item = Item.objects.select_for_update().get(id=serializers.validated_data['item'].id)

        if item.stock > 0:
            item.stock -= 1
            item.save()

            order = Order.objects.create(
                user=request.user,
                item=item,
                status=Order.Status.COMPLETED
            )

            return Response(
                {"message": "주문 완료", "order_id": order.id, "remain_stock": item.stock},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response({"error": "재고 부족"}, status=status.HTTP_400_BAD_REQUEST)
"""

# ! 최종 v3
class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializers = OrderSerializer(data=request.data)
        serializers.is_valid(raise_exception=True)

        item_id = serializers.validated_data['item'].id
        redis_key = f'item_stock_{item_id}'

        try:
            remain_stock_in_redis = cache.decr(redis_key)
        except ValueError:
            item = Item.objects.get(id=item_id)
            cache.set(redis_key, item.stock, timeout=None)
            remain_stock_in_redis = cache.decr(redis_key)

        if remain_stock_in_redis < 0:
            return Response({"error": "재고 부족 (Redis)"}, status=status.HTTP_400_BAD_REQUEST)
        
        order = Order.objects.create(
            user=request.user,
            item_id=item_id,
            status=Order.Status.COMPLETED
        )

        Item.objects.filter(id=item_id).update(stock=F('stock') - 1)

        return Response(
            {"message": "성공", "order_id": order.id, "remain_stock": remain_stock_in_redis},
            status=status.HTTP_201_CREATED
        )