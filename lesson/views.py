from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from lesson.serializers import LessonSerializer, ReservationDetailSerializer, LessonDetailSerializer
from lesson.models import Reservation, Lesson


class LessonAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()

    @swagger_auto_schema(
        operation_summary="수업 목록 가져오기",
    )
    def get(self, request, *args, **kwargs):
        return super(LessonAPIView, self).get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="수업 생성",
    )
    def post(self, request, *args, **kwargs):
        return super(LessonAPIView, self).post(request, *args, **kwargs)


class LessonDetailAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="수업 예약 확인",
        responses={status.HTTP_200_OK: LessonDetailSerializer()}
    )
    def get(self, request: Request, pk: int):
        lesson: Lesson = get_object_or_404(Lesson, pk=pk)
        serializer = LessonDetailSerializer(lesson)
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class ReservationAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="수업 예약 하기",
        responses={status.HTTP_201_CREATED: ReservationDetailSerializer()},
    )
    def post(self, request: Request, pk: int):
        lesson: Lesson = get_object_or_404(Lesson, pk=pk)
        reservation = Reservation.objects.reserve(request.user, lesson)
        serializer = ReservationDetailSerializer(reservation)
        return Response(status=status.HTTP_201_CREATED, data=serializer.data)


class ReservationDetailAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="수업 취소 하기",
        responses={status.HTTP_204_NO_CONTENT: ''},
    )
    def delete(self, request: Request, pk: int):
        reservation: Reservation = get_object_or_404(Reservation, pk=pk)
        reservation.cancel(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
