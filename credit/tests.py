import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from core.tests import BaseTest
from credit.models import PricePolicy, Credit, PurchaseCredit, CreditType
from credit.serializers import PricePolicySerializer, CreditBuySerializer


class CreditTestCase(BaseTest):
    def test_price_policy_model(self):
        price_policy = PricePolicy.objects.create(**self.policy_data)
        for key in self.policy_data:
            self.assertEqual(getattr(price_policy, key), self.policy_data[key])

    def test_price_policy_serializer(self):
        price_policy = PricePolicy.objects.create(**self.policy_data)
        serializer = PricePolicySerializer(price_policy)
        data = serializer.data
        for key in self.policy_data:
            self.assertEqual(self.policy_data[key], data[key])

    def test_credit_model(self):
        price_policy = PricePolicy.objects.create(**self.policy_data)
        credit = PurchaseCredit.objects.create(
            user=self.admin,
            count=price_policy.credit_count,
            start_date=self.start_date,
            period=price_policy.period,
            price_policy=price_policy,
            message=price_policy.credit_message,
        )
        self.assertEqual(credit.user, self.admin)
        self.assertEqual(credit.type, CreditType.PURCHASE)
        self.assertEqual(credit.count, price_policy.credit_count)
        self.assertEqual(credit.start_date, self.start_date)
        self.assertEqual(credit.period, price_policy.period)
        self.assertEqual(credit.end_date, self.start_date + datetime.timedelta(credit.period))
        self.assertEqual(credit.price_policy, price_policy)
        self.assertEqual(credit.message, price_policy.credit_message)

    def test_credit_buy_serializer(self):
        price_policy = PricePolicy.objects.create(**self.policy_data)
        data = {
            'start_date': self.start_date,
            'price_policy': price_policy.id
        }

        serializer = CreditBuySerializer(data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        credit: Credit = serializer.save(user=self.admin)
        self.assertEqual(credit.user, self.admin)
        self.assertEqual(credit.type, CreditType.PURCHASE)
        self.assertEqual(credit.count, price_policy.credit_count)
        self.assertEqual(credit.start_date, self.start_date)
        self.assertEqual(credit.period, price_policy.period)
        self.assertEqual(credit.end_date, credit.start_date + datetime.timedelta(credit.period))
        self.assertEqual(credit.price_policy, price_policy)
        self.assertEqual(credit.message, price_policy.credit_message)

    def test_credit_buy_view(self):
        price_policy = PricePolicy.objects.create(**self.policy_data)
        data = {
            'start_date': str(self.start_date),
            'price_policy': price_policy.id,
        }
        response: Response = self.admin_client.post(reverse('credit'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in data:
            self.assertEqual(response.data[key], data[key])

