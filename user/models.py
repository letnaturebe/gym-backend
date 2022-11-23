from datetime import date

from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.db.models import QuerySet, Sum
from django.utils import timezone

from core.models import TimeStampedModel
from credit.models import Credit, PricePolicy, PurchaseCredit, UseCredit, PurchaseCreditQuerySet, RefundCredit
from lesson.models import Reservation, Lesson
from user.managers import CustomUserManager


class CustomUser(TimeStampedModel, AbstractUser):
    phone_number = models.CharField(max_length=11)

    objects = CustomUserManager()

    class Meta:
        verbose_name = '사용자'

    def __str__(self):
        return f'{self.username}'

    def buy_credit(self, price_policy: PricePolicy, start_date: date) -> PurchaseCredit:
        return PurchaseCredit.objects.create(
            user=self,
            count=price_policy.credit_count,
            start_date=start_date,
            period=price_policy.period,
            price_policy=price_policy,
            message=f'{price_policy.credit_message}'
        )

    @transaction.atomic
    def use_credit(self, reservation: Reservation) -> bool:
        if not self.has_enough_credit(reservation.lesson):
            return False

        lesson_credit_count: int = reservation.lesson.credit_count

        for purchase_credit in self.remaining_credits:
            purchase_credit: PurchaseCredit
            remaining_count = purchase_credit.remaining_count
            use_credit = UseCredit.objects.create(
                user=self,
                purchased_credit=purchase_credit,
                count=-remaining_count,
                start_date=timezone.now().date(),
                reservation=reservation,
                message=f'{reservation.credit_message}'
            )
            if lesson_credit_count > remaining_count:
                lesson_credit_count -= remaining_count
            else:
                use_credit.count = -lesson_credit_count
                use_credit.save()
                break

        return True

    def refund_credit(self, cancel_reservation: Reservation, credit_count: int,
                      purchased_credit: PurchaseCredit) -> RefundCredit:
        return RefundCredit.objects.create(
            user=self,
            purchased_credit=purchased_credit,
            count=credit_count,
            start_date=purchased_credit.start_date,
            price_policy=purchased_credit.price_policy,
            reservation=cancel_reservation,
            message=f'{cancel_reservation.credit_message}'
        )

    def has_enough_credit(self, lesson: Lesson) -> bool:
        if lesson.credit_count > self.credit_count:
            return False
        return True

    def expire_credit(self) -> None:
        now = timezone.now().date()
        expired_credits: PurchaseCreditQuerySet[Credit] = PurchaseCredit.objects.filter(
            user=self, end_date__lt=now, is_expired=False).select_related('user')
        expired_credits.expire()

    @property
    def credit_count(self) -> int:
        self.expire_credit()
        queryset: QuerySet[Credit] = self.credits.all()
        current_credit: dict = queryset.aggregate(Sum('count'))
        return current_credit['count__sum'] if current_credit['count__sum'] else 0

    @property
    def remaining_credits(self) -> list['PurchaseCredit']:
        self.expire_credit()
        return PurchaseCredit.objects.get_remaining_credits(self)
