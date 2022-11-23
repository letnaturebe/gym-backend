import datetime

from rest_framework import serializers

from lesson.exceptions import InvalidEndTime
from lesson.models import Lesson, Reservation
from user.models import CustomUser


class LessonUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'phone_number', ]


class ReservationSerializer(serializers.ModelSerializer):
    user = LessonUserSerializer()

    class Meta:
        model = Reservation
        exclude = ('lesson', 'cancel_reservation',)


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

    def validate(self, attrs: dict):
        start_time: datetime.time = attrs.get('start_time')
        end_time: datetime.time = attrs.get('end_time')
        if end_time < start_time:
            raise InvalidEndTime
        return attrs


class LessonDetailSerializer(serializers.ModelSerializer):
    reservations = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = '__all__'

    def get_reservations(self, lesson: Lesson) -> ReservationSerializer(many=True):
        queryset = Reservation.objects.filter(lesson=lesson).select_related('user')
        s = ReservationSerializer(queryset, many=True, read_only=True, context=self.context)
        return s.data


class ReservationDetailSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer()
    user = LessonUserSerializer()

    class Meta:
        model = Reservation
        fields = '__all__'
