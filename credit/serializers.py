from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from credit.models import PricePolicy, Credit, PurchaseCredit
from user.models import CustomUser
from user.serializers import UserSerializer


class PricePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PricePolicy
        fields = '__all__'


class CreditSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Credit
        fields = '__all__'


class CreditBuySerializer(serializers.ModelSerializer):
    price_policy = PrimaryKeyRelatedField(
        queryset=PricePolicy.objects.all(), required=True, label="가격정책")

    class Meta:
        model = PurchaseCredit
        fields = ('start_date', 'price_policy',)

    def save(self, **kwargs):
        user: CustomUser = kwargs.get('user', None)
        assert user is not None
        return user.buy_credit(**self.validated_data)
