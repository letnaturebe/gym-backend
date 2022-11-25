import datetime

from django.db import models
from django.db.models import QuerySet, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from gym import settings
from core.models import TimeStampedModel
from lesson.models import Reservation


class CreditType(models.TextChoices):
    PURCHASE = '구매', _('구매한 크레딧')
    USE = '사용', _('사용한 크레딧')
    EXPIRED = '만료', _('만료된 크레딧')
    REFUND = '환불', _('환불된 크레딧')


class PurchaseCreditQuerySet(QuerySet):
    def filter(self, *args, **kwargs):
        return super(PurchaseCreditQuerySet, self).filter(*args, **kwargs, type=CreditType.PURCHASE)

    def expire(self):
        expired_credits: list[PurchaseCredit] = [
            PurchaseCredit(
                user=expired_credit.user,
                count=-expired_credit.remaining_count,
                start_date=timezone.now().date(),
                expired_credit=expired_credit,
                message=expired_credit.message
            ) for expired_credit in self]
        self.bulk_create(expired_credits)
        self.update(is_expired=True)


class PurchaseCreditManager(models.Manager):
    def get_queryset(self):
        return PurchaseCreditQuerySet(self.model)

    def create(self, **kwargs):
        start_date: datetime.date = kwargs.get('start_date', None)
        end_date: datetime.date = kwargs.get('end_date', None)
        price_policy: PricePolicy = kwargs.get('price_policy', None)

        assert end_date is None, "end_date must be None"
        kwargs['end_date'] = start_date + datetime.timedelta(price_policy.period)
        return super().create(**kwargs, type=CreditType.PURCHASE)

    def get_remaining_credits(self, user) -> list['PurchaseCredit']:
        queryset = PurchaseCredit.objects.filter(user=user, is_expired=False)
        remaining_credits: list[PurchaseCredit] = [purchase_credit for purchase_credit in queryset if
                                                   purchase_credit.remaining_count > 0]
        return remaining_credits


class UseCreditManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type=CreditType.USE)

    def create(self, **kwargs):
        return super().create(**kwargs, type=CreditType.USE)


class RefundCreditManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type=CreditType.REFUND)

    def create(self, **kwargs):
        return super().create(**kwargs, type=CreditType.REFUND)


class PricePolicy(TimeStampedModel):
    name = models.CharField(verbose_name=_("정책명"), max_length=32)
    price = models.PositiveIntegerField(verbose_name=_("가격(원)"))
    credit_count = models.PositiveIntegerField(verbose_name=_("크레딧 개수"))
    period = models.PositiveIntegerField(verbose_name=_('사용기간(일)'))

    class Meta:
        verbose_name = '가격정책(회원권)'

    def __str__(self):
        return f'{self.name}'

    @property
    def credit_message(self):
        return f'{self.name} 회원권 구매'


class Credit(TimeStampedModel):
    user = models.ForeignKey(
        verbose_name=_("사용자"), to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="credits")
    count = models.IntegerField(verbose_name=_("크레딧 개수"))
    type = models.CharField(
        verbose_name=_("크레딧 종류"), max_length=8, choices=CreditType.choices, default=CreditType.PURCHASE)
    start_date = models.DateField(verbose_name=_("시작일"))
    period = models.PositiveIntegerField(verbose_name=_("사용기간(일)"), null=True, blank=True)
    end_date = models.DateField(verbose_name=_("종료일"), null=True, blank=True)
    price_policy = models.ForeignKey(
        verbose_name=_("가격 정책"), to=PricePolicy, on_delete=models.SET_NULL, null=True, blank=True)
    reservation = models.ForeignKey(
        verbose_name=_("예약"), to=Reservation, on_delete=models.CASCADE, null=True, blank=True, related_name="credits")
    is_expired = models.BooleanField(default=False)
    expired_credit = models.ForeignKey(
        verbose_name=_("만료된 크레딧"), to='self', on_delete=models.CASCADE, null=True, blank=True)
    purchased_credit = models.ForeignKey(
        verbose_name=_("구매된 크레딧"), to='PurchaseCredit', on_delete=models.CASCADE,
        null=True, blank=True, related_name="used_credits")
    message = models.CharField(max_length=64)

    class Meta:
        verbose_name = '크레딧'

    def __str__(self):
        return f'[{self.user}] {self.message}'


class PurchaseCredit(Credit):
    objects = PurchaseCreditManager()

    class Meta:
        proxy = True
        ordering = ['start_date']

    @property
    def remaining_count(self) -> int:
        used_credits: dict = self.used_credits.all().aggregate(Sum('count'))
        used_credit_count: int = used_credits['count__sum'] if used_credits['count__sum'] else 0
        return self.count + used_credit_count


class UseCredit(Credit):
    objects = UseCreditManager()

    class Meta:
        proxy = True


class RefundCredit(Credit):
    objects = RefundCreditManager()

    class Meta:
        proxy = True
