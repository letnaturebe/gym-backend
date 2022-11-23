from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from credit.models import Credit
from lesson.serializers import LessonSerializer
from lesson.models import Reservation
from user.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'phone_number', 'password', ]

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return super(UserSerializer, self).create(validated_data)


class ReservationCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Credit
        fields = ('id', 'type', 'count', 'message', )


class UserReservationSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer()
    credits = ReservationCreditSerializer(many=True)

    class Meta:
        model = Reservation
        fields = ('lesson', 'type', 'credits', )


class UserDetailSerializer(UserSerializer):
    credit_count = serializers.SerializerMethodField()
    reservations = UserReservationSerializer(many=True)

    class Meta:
        model = CustomUser
        fields = UserSerializer.Meta.fields + ['credit_count', 'reservations', ]

    def get_credit_count(self, user: CustomUser) -> int:
        return user.credit_count
