import datetime
from unittest import mock

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from core.tests import BaseTest
from credit.models import PricePolicy
from lesson.models import Gym, LessonType, Lesson, Reservation


class UserTestCase(BaseTest):
    lesson_data = {
        'gym': Gym.SEOUL,
        'type': LessonType.YOGA,
        'credit_count': 100,
        'max_capacity': 10,
        'start_date': BaseTest.ten_day_later,
        'start_time': datetime.time(13, 0),
        'end_time': datetime.time(15, 0),
    }

    def test_user_buy_credit(self):
        price_policy = PricePolicy.objects.create(**self.policy_data)

        for _ in range(2):
            self.user.buy_credit(price_policy, self.ten_day_later)

        self.assertEqual(self.user.credit_count, price_policy.credit_count * 2)

    def test_user_use_credit(self):
        price_policy = PricePolicy.objects.create(**self.policy_data)
        lesson = Lesson.objects.create(**self.lesson_data)
        reservation = Reservation.objects.create(user=self.user, lesson=lesson)
        self.assertFalse(self.user.use_credit(reservation))
        self.user.buy_credit(price_policy, self.ten_day_ago)
        self.assertTrue(self.user.use_credit(reservation))
        self.assertEqual(self.user.credit_count, price_policy.credit_count - lesson.credit_count)

    def test_expire_user_credit(self):
        year_ago = timezone.now().date() - datetime.timedelta(365)
        price_policy = PricePolicy.objects.create(**self.policy_data)
        self.user.buy_credit(price_policy, year_ago)
        self.assertEqual(self.user.credit_count, 0)

    def test_complex_expire_user_credit(self):
        year_ago = timezone.now().date() - datetime.timedelta(365)
        price_policy = PricePolicy.objects.create(**self.policy_data)
        lesson = Lesson.objects.create(**{**self.lesson_data})
        self.user.buy_credit(price_policy, year_ago)

        with mock.patch(
                "user.models.CustomUser.expire_credit"
        ) as magic_mock:
            Reservation.objects.reserve(self.user, lesson)
            current_credit_count = price_policy.credit_count - lesson.credit_count
            self.assertTrue(magic_mock.called)
            self.assertEqual(self.user.credit_count, current_credit_count)
            self.assertEqual(len(self.user.remaining_credits), 1)
            self.assertEqual(self.user.remaining_credits[0].remaining_count, current_credit_count)

        self.user.expire_credit()
        self.assertEqual(self.user.credit_count, 0)
        self.assertEqual(len(self.user.remaining_credits), 0)

    def test_user_remaining_credit(self):
        year_ago = timezone.now().date() - datetime.timedelta(365)
        price_policy = PricePolicy.objects.create(**self.policy_data)
        self.user.buy_credit(price_policy, self.today)
        self.assertEqual(len(self.user.remaining_credits), 1)
        for _ in range(10):
            self.user.buy_credit(price_policy, year_ago)
        self.assertEqual(len(self.user.remaining_credits), 1)

    def test_user_detail_view(self):
        price_policy = PricePolicy.objects.create(**self.policy_data)
        lesson = Lesson.objects.create(**self.lesson_data)
        self.user.buy_credit(price_policy, self.today)
        response: Response = self.user_client.get(reverse('user-detail', kwargs={'pk': self.user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('reservations')), 0)

        reservation = Reservation.objects.reserve(self.user, lesson)
        reservation.cancel(self.user)
        Reservation.objects.reserve(self.user, lesson)

        response: Response = self.user_client.get(reverse('user-detail', kwargs={'pk': self.user.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('reservations')), 3)

    def test_user_detail_view_N_Plus_1(self):
        price_policy = PricePolicy.objects.create(**self.policy_data)
        lesson = Lesson.objects.create(**self.lesson_data)
        self.user.buy_credit(price_policy, self.today)
        reservation = Reservation.objects.reserve(self.user, lesson)
        with CaptureQueriesContext(connection) as expected_num_queries:
            self.user_client.get(reverse('user-detail', kwargs={'pk': self.user.id}))

        for _ in range(10):
            reservation.cancel(self.user)
            reservation = Reservation.objects.reserve(self.user, lesson)

        with CaptureQueriesContext(connection) as checked_num_queries:
            self.user_client.get(reverse('user-detail', kwargs={'pk': self.user.id}))
        self.assertEqual(len(expected_num_queries), len(checked_num_queries))
