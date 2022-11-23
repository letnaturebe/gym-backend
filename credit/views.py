from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from credit.models import Credit, PricePolicy
from credit.serializers import CreditBuySerializer, CreditSerializer, PricePolicySerializer


class PricePolicyAPIView(generics.ListCreateAPIView):
    serializer_class = PricePolicySerializer
    queryset = PricePolicy.objects.all()

    @swagger_auto_schema(
        operation_summary="가격 정책(회원권) 목록 가져오기",
    )
    def get(self, request, *args, **kwargs):
        return super(PricePolicyAPIView, self).get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="가격 정책(회원권) 생성",
        operation_description="크레딧을 만들기 위한 선조건입니다."
                              "팀버핏 800크레딧과 같은 가격 정책(회원권)을 생성합니다."
    )
    def post(self, request, *args, **kwargs):
        return super(PricePolicyAPIView, self).post(request, *args, **kwargs)


class CreditAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="크레딧 목록 보기",
        responses={status.HTTP_200_OK: CreditSerializer(many=True)},
    )
    def get(self, request: Request):
        queryset = Credit.objects.all().select_related('user')
        return Response(
            status=status.HTTP_200_OK, data=CreditSerializer(queryset, many=True).data)

    @swagger_auto_schema(
        request_body=CreditBuySerializer,
        operation_summary="크레딧 구매하기",
        operation_description="크레딧 정책 생성 후 body에 price_policy ID를 넣어주세요",
        responses={status.HTTP_201_CREATED: CreditSerializer()},
    )
    def post(self, request: Request):
        serializer = CreditBuySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credit: Credit = serializer.save(user=request.user)
        return Response(status=status.HTTP_201_CREATED, data=CreditSerializer(credit).data)
