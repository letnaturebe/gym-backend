import datetime

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from core.tests import BaseTest
from credit.models import PricePolicy
from lesson.exceptions import NotEnoughCredit, ExceedMaxCapacity, AlreadyRegistered, InvalidCancelDate, \
    AlreadyCanceled, NotYourReservation, InvalidEndTime, InvalidReservationType
from lesson.models import Lesson, Gym, LessonType, Reservation
from lesson.serializers import LessonSerializer


class LessonTestCase(BaseTest):
    lesson_data = {
        'gym': Gym.SEOUL,
        'type': LessonType.YOGA,
        'credit_count': 100,
        'max_capacity': 10,
        'start_date': BaseTest.ten_day_later,
        'start_time': datetime.time(13, 0),
        'end_time': datetime.time(15, 0),
    }

    def test_lesson_model(self):
        lesson = Lesson.objects.create(**self.lesson_data)

        for key in self.lesson_data:
            self.assertEqual(getattr(lesson, key), self.lesson_data[key])

    def test_lesson_serializer(self):
        expected = {
            **self.lesson_data,
            'start_date': str(self.lesson_data['start_date']),
            'start_time': str(self.lesson_data['start_time']),
            'end_time': str(self.lesson_data['end_time']),
        }

        lesson = Lesson.objects.create(**self.lesson_data)
        serializer = LessonSerializer(lesson)

        for key in self.lesson_data:
            self.assertEqual(expected[key], serializer.data[key])

    def test_lesson_create_serializer(self):
        serializer = LessonSerializer(data=self.lesson_data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save()
        self.assertIsNotNone(lesson)

    def test_lesson_serializer_InvalidEndTime(self):
        invalid_data = {
            **self.lesson_data,
            'start_date': str(self.lesson_data['start_date']),
            'start_time': str(self.lesson_data['end_time']),
            'end_time': str(self.lesson_data['start_time']),
        }

        serializer = LessonSerializer(data=invalid_data)
        self.assertRaises(InvalidEndTime, serializer.is_valid, raise_exception=True)

    def test_lesson_view(self):
        response: Response = self.admin_client.post(reverse('lesson'), data=self.lesson_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response: Response = self.admin_client.get(reverse('lesson'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_lesson_detail_view(self):
        # Given
        price_policy = PricePolicy.objects.create(**self.policy_data)
        lesson = Lesson.objects.create(**self.lesson_data)
        self.user.buy_credit(price_policy, self.today)
        reservation = Reservation.objects.reserve(self.user, lesson)

        # When
        response: Response = self.user_client.get(reverse('lesson-detail', kwargs={'pk': lesson.id}))

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['reservations']), 1)

        # Given
        reservation.cancel(self.user)
        Reservation.objects.reserve(self.user, lesson)
        # When
        response: Response = self.user_client.get(reverse('lesson-detail', kwargs={'pk': lesson.id}))
        # Then
        self.assertEqual(len(response.data['reservations']), 3)

    def test_lesson_detail_view_N_Plus_1(self):
        price_policy = PricePolicy.objects.create(**self.policy_data)
        lesson = Lesson.objects.create(**self.lesson_data)
        self.user.buy_credit(price_policy, self.today)
        reservation = Reservation.objects.reserve(self.user, lesson)

        with CaptureQueriesContext(connection) as expected_num_queries:
            self.user_client.get(reverse('lesson-detail', kwargs={'pk': lesson.id}))

        for _ in range(10):
            reservation.cancel(self.user)
            reservation = Reservation.objects.reserve(self.user, lesson)

        with CaptureQueriesContext(connection) as checked_num_queries:
            self.user_client.get(reverse('lesson-detail', kwargs={'pk': lesson.id}))

        self.assertEqual(len(expected_num_queries), len(checked_num_queries))

    def test_lesson_is_close(self):
        PricePolicy.objects.create(**self.policy_data)
        future_lesson = Lesson.objects.create(**{**self.lesson_data, 'max_capacity': 1})
        self.assertFalse(future_lesson.is_close())
        past_lesson = Lesson.objects.create(
            **{**self.lesson_data,
               'start_date': self.ten_day_ago,
               'start_time': datetime.time(9, 0),
               'end_time': datetime.time(11, 0)
               })
        self.assertTrue(past_lesson.is_close())

    def test_lesson_is_full(self):
        # Given
        price_policy = PricePolicy.objects.create(**self.policy_data)
        lesson = Lesson.objects.create(**{**self.lesson_data, 'max_capacity': 1})
        self.assertFalse(lesson.is_full())
        self.user.buy_credit(price_policy, self.today)
        self.admin.buy_credit(price_policy, self.today)

        reservation = Reservation.objects.reserve(self.user, lesson)
        self.assertTrue(lesson.is_full())

        self.assertRaises(ExceedMaxCapacity, Reservation.objects.reserve, self.admin, lesson)

        reservation.cancel(self.user)
        self.assertFalse(lesson.is_full())

        Reservation.objects.reserve(self.admin, lesson)
        self.assertTrue(lesson.is_full())

    def test_lesson_is_cancelable(self):
        PricePolicy.objects.create(**self.policy_data)
        lesson = Lesson.objects.create(**self.lesson_data)
        self.assertTrue(lesson.is_cancelable())

        expired_lesson = Lesson.objects.create(**{**self.lesson_data, 'start_date': self.ten_day_ago})
        self.assertFalse(expired_lesson.is_cancelable())

    def test_lesson_get_cancel_credit(self):
        today = timezone.now().date()
        PricePolicy.objects.create(**self.policy_data)

        lesson = Lesson.objects.create(**self.lesson_data)
        self.assertEqual(lesson.get_cancel_credit(), lesson.credit_count)

        expired_lesson = Lesson.objects.create(**{**self.lesson_data, 'start_date': self.ten_day_ago})
        self.assertRaises(InvalidCancelDate, expired_lesson.get_cancel_credit)

        tomorrow_lesson = Lesson.objects.create(
            **{**self.lesson_data, 'start_date': today + datetime.timedelta(1)})
        self.assertEqual(tomorrow_lesson.get_cancel_credit(), lesson.credit_count // 2)

        two_day_later_lesson = Lesson.objects.create(
            **{**self.lesson_data, 'start_date': today + datetime.timedelta(2)})
        self.assertEqual(two_day_later_lesson.get_cancel_credit(), lesson.credit_count // 2)

        three_day_later_lesson = Lesson.objects.create(
            **{**self.lesson_data, 'start_date': today + datetime.timedelta(3)})
        self.assertEqual(three_day_later_lesson.get_cancel_credit(), lesson.credit_count)

        four_day_later_lesson = Lesson.objects.create(
            **{**self.lesson_data, 'start_date': today + datetime.timedelta(4)})
        self.assertEqual(four_day_later_lesson.get_cancel_credit(), lesson.credit_count)


class ReservationTestCase(BaseTest):
    lesson_data = {
        'gym': Gym.SEOUL,
        'type': LessonType.YOGA,
        'credit_count': 100,
        'max_capacity': 10,
        'start_date': BaseTest.ten_day_later,
        'start_time': datetime.time(13, 0),
        'end_time': datetime.time(15, 0),
    }

    def _buy_credit_create_lesson(self, lesson_data: dict):
        price_policy = PricePolicy.objects.create(**self.policy_data)
        lesson = Lesson.objects.create(**lesson_data)
        self.user.buy_credit(price_policy, self.today)
        return lesson

    def test_reservation_model(self):
        lesson = Lesson.objects.create(**self.lesson_data)
        reservation = Reservation.objects.create(user=self.user, lesson=lesson)
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.lesson, lesson)

    def test_reservation_NotEnoughCredit(self):
        PricePolicy.objects.create(**self.policy_data)
        lesson = Lesson.objects.create(**self.lesson_data)
        self.assertRaises(NotEnoughCredit, Reservation.objects.reserve, self.user, lesson)

    def test_reservation_ExceedMaxCapacity(self):
        lesson = self._buy_credit_create_lesson({**self.lesson_data, 'max_capacity': 0})
        self.assertRaises(ExceedMaxCapacity, Reservation.objects.reserve, self.user, lesson)

    def test_reservation_AlreadyRegistered(self):
        lesson = self._buy_credit_create_lesson(self.lesson_data)
        self.assertTrue(Reservation.objects.reserve(self.user, lesson) is not None)
        self.assertRaises(AlreadyRegistered, Reservation.objects.reserve, self.user, lesson)

    def test_reservation_cancel_NotYourReservation(self):
        lesson = self._buy_credit_create_lesson(self.lesson_data)
        reservation = Reservation.objects.reserve(self.user, lesson)
        self.assertRaises(NotYourReservation, reservation.cancel, self.admin)

    def test_reservation_cancel_AlreadyCanceled(self):
        lesson = self._buy_credit_create_lesson(self.lesson_data)
        reservation = Reservation.objects.reserve(self.user, lesson)
        cancel_reservation = reservation.cancel(self.user)
        self.assertIsNotNone(cancel_reservation)
        self.assertRaises(AlreadyCanceled, reservation.cancel, self.user)

    def test_reservation_cancel_InvalidReservationType(self):
        lesson = self._buy_credit_create_lesson(self.lesson_data)
        reservation = Reservation.objects.reserve(self.user, lesson)
        cancel_reservation = reservation.cancel(self.user)
        self.assertRaises(InvalidReservationType, cancel_reservation.cancel, self.user)

    def test_reserve_view(self):
        lesson = self._buy_credit_create_lesson(self.lesson_data)
        response: Response = self.user_client.post(reverse('reservation', kwargs={'pk': lesson.id}))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cancel_view(self):
        lesson = self._buy_credit_create_lesson(self.lesson_data)
        response: Response = self.user_client.post(reverse('reservation', kwargs={'pk': lesson.id}))
        reservation_id: int = response.data['id']
        self.assertIsNone(Reservation.objects.get(id=reservation_id).cancel_reservation)

        response: Response = self.user_client.delete(reverse('reservation-detail', kwargs={'pk': reservation_id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNotNone(Reservation.objects.get(id=reservation_id).cancel_reservation)

    def test_reserve_cancel(self):
        # Given
        lesson = Lesson.objects.create(**self.lesson_data)
        price_policy = PricePolicy.objects.create(**self.policy_data)
        self.user.buy_credit(price_policy, self.today)
        self.user.buy_credit(price_policy, self.today)
        self.admin.buy_credit(price_policy, self.today)
        self.admin.buy_credit(price_policy, self.today)

        user_remaining_credits = self.user.remaining_credits
        admin_remaining_credits = self.user.remaining_credits
        self.assertEqual(len(user_remaining_credits), 2)
        self.assertEqual(len(admin_remaining_credits), 2)
        init_user_credit_count: int = self.user.credit_count
        init_admin_credit_count: int = self.admin.credit_count

        # When
        user_reservation = Reservation.objects.reserve(self.user, lesson)
        admin_reservation = Reservation.objects.reserve(self.admin, lesson)

        # Then
        self.assertEqual(self.user.credit_count, init_user_credit_count - lesson.credit_count)
        self.assertEqual(user_remaining_credits[0].remaining_count,
                         user_remaining_credits[0].count - lesson.credit_count)
        self.assertEqual(self.admin.credit_count, init_admin_credit_count - lesson.credit_count)
        self.assertEqual(admin_remaining_credits[0].remaining_count,
                         admin_remaining_credits[0].count - lesson.credit_count)

        # When
        user_reservation.cancel(self.user)
        admin_reservation.cancel(self.admin)

        # Then
        self.assertEqual(self.user.credit_count, init_user_credit_count)
        self.assertEqual(user_remaining_credits[0].remaining_count, user_remaining_credits[0].count)
        self.assertEqual(self.admin.credit_count, init_admin_credit_count)
        self.assertEqual(admin_remaining_credits[0].remaining_count, admin_remaining_credits[0].count)

        user_reservation = Reservation.objects.reserve(self.user, lesson)
        user_reservation.cancel(self.user)

        self.assertEqual(self.user.credit_count, init_user_credit_count)
