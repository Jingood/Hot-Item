from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db import transaction
from .models import *
from .serializers import *


class ItemListView(generics.ListAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [AllowAny]


class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    from drf_spectacular.utils import extend_schema
    @extend_schema(request=OrderSerializer, responses={201: OrderSerializer})
    def post(self, request, *args, **kwargs):
        serializers = OrderSerializer(data=request.data)
        serializers.is_valid(raise_exception=True)

        item = serializers.validated_data['item']

        # ? v1, 일반적인 RDBMS 조회 -> 예상 효과: 수천 명이 동시에 실행하면 모두가 stock > 0 이라고 판단 (초과 판매 발생)
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

