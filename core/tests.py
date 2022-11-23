import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from user.models import CustomUser


class BaseTest(TestCase):
    admin: CustomUser = None
    user: CustomUser = None
    admin_client: APIClient = None
    user_client = None
    policy_data = {
        'name': '팀버핏 800 크레딧',
        'price': 300000,
        'credit_count': 800,
        'period': 30,
    }

    today: datetime.date = timezone.now().date()
    ten_day_ago: datetime.date = today - datetime.timedelta(10)
    ten_day_later: datetime.date = today + datetime.timedelta(10)
    start_date = ten_day_ago

    @classmethod
    def setUpTestData(cls):
        cls.admin: CustomUser = CustomUser.objects.create_superuser("admin")
        cls.user: CustomUser = CustomUser.objects.create_superuser("user")
        cls.admin.set_password("admin")
        cls.user.set_password("user")
        cls.admin.phone_number = '01011113333'
        cls.user.phone_number = '01022223333'
        cls.admin.save()
        cls.user.save()
        cls.admin_client = APIClient()
        cls.admin_client.login(username='admin', password='admin')
        cls.user_client = APIClient()
        cls.user_client.login(username='user', password='user')
