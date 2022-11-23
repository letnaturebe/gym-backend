from django.db.models import Prefetch
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny

from lesson.models import Reservation
from user.models import CustomUser
from user.serializers import UserSerializer, UserDetailSerializer


class UserAPIView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()

    @swagger_auto_schema(
        operation_summary="유저 목록 가져오기",
    )
    def get(self, request, *args, **kwargs):
        return super(UserAPIView, self).get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="유저 생성",
    )
    def post(self, request, *args, **kwargs):
        return super(UserAPIView, self).post(request, *args, **kwargs)


class UserDetailAPIView(generics.RetrieveAPIView):
    serializer_class = UserDetailSerializer
    queryset = CustomUser.objects.all().prefetch_related(
        Prefetch('reservations', queryset=(Reservation.objects.select_related('lesson').prefetch_related('credits')))
    )

    @swagger_auto_schema(
        operation_summary="유저 정보, 예약(취소)리스트 및 크레딧 조회",
    )
    def get(self, request, *args, **kwargs):
        return super(UserDetailAPIView, self).retrieve(request, *args, **kwargs)


class UserReservationAPIView(generics.RetrieveAPIView):
    serializer_class = UserDetailSerializer
    queryset = CustomUser.objects.all()

    @swagger_auto_schema(
        operation_summary="유저 상세 목록 가져오기",
    )
    def get(self, request, *args, **kwargs):
        return super(UserReservationAPIView, self).retrieve(request, *args, **kwargs)
