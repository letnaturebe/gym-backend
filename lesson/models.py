import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from gym import settings
from core.models import TimeStampedModel
from lesson.exceptions import NotEnoughCredit, ExceedMaxCapacity, AlreadyRegistered, NotYourReservation, \
    InvalidCancelDate, AlreadyCanceled, ExceedLessonTime, InvalidReservationType


class Gym(models.TextChoices):
    SEOUL = '서울', _('서울')
    BUSAN = '부산', _('부산')


class LessonType(models.TextChoices):
    WEIGHT = '웨이트', _('웨이트')
    CROSSFIT = '크로스핏', _('크로스핏')
    SWIM = '수영', _('수영')
    YOGA = '요가', _('요가')


class ReservationType(models.TextChoices):
    RESERVATION = '예약', _('예약')
    CANCEL = '취소', _('취소')


class Lesson(TimeStampedModel):
    gym = models.CharField(
        verbose_name=_("장소"), max_length=16, choices=Gym.choices, default=Gym.SEOUL)
    type = models.CharField(
        verbose_name=_("수업종류"), max_length=16, choices=LessonType.choices, default=LessonType.WEIGHT)
    credit_count = models.PositiveIntegerField(verbose_name=_("크레딧 개수"))
    max_capacity = models.PositiveIntegerField(verbose_name=_("정원"))
    start_date = models.DateField(verbose_name=_("수업날짜"))
    start_time = models.TimeField(verbose_name=_("시작시간"))
    end_time = models.TimeField(verbose_name=_("종료시간"))

    class Meta:
        verbose_name = '수업'

    def __str__(self):
        return f'[{self.gym}] {self.type} {self.start_date}'

    def is_full(self) -> bool:
        return (Reservation.objects
                .filter(lesson=self, type=ReservationType.RESERVATION, cancel_reservation__isnull=True)
                .count() >= self.max_capacity)

    def is_close(self) -> bool:
        now = timezone.now()
        start_datetime = datetime.datetime.combine(self.start_date, self.start_time)
        return now > start_datetime

    def is_cancelable(self) -> bool:
        now = timezone.now().date()
        diff = self.start_date - now
        return diff.days > 0

    def get_cancel_credit(self) -> int:
        now = timezone.now().date()
        diff = self.start_date - now
        if diff.days >= 3:
            return self.credit_count
        elif 0 < diff.days <= 2:
            return self.credit_count // 2
        raise InvalidCancelDate


class ReservationManager(models.Manager):
    def reserve(self, user, lesson: Lesson) -> 'Reservation':
        from user.models import CustomUser
        user: CustomUser

        if lesson.is_full():
            raise ExceedMaxCapacity

        if lesson.is_close():
            raise ExceedLessonTime

        if (Reservation
                .objects
                .filter(lesson=lesson, user=user, type=ReservationType.RESERVATION,
                        cancel_reservation__isnull=True)
                .exists()):
            raise AlreadyRegistered

        if not user.has_enough_credit(lesson):
            raise NotEnoughCredit

        reservation = Reservation.objects.create(lesson=lesson, user=user)
        user.use_credit(reservation)
        return reservation


class Reservation(TimeStampedModel):
    user = models.ForeignKey(
        verbose_name=_('예약자'), to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")
    lesson = models.ForeignKey(
        verbose_name=_("수업"), to=Lesson, on_delete=models.CASCADE, related_name="reservations")
    type = models.CharField(
        verbose_name=_("예약/취소"), max_length=8, choices=ReservationType.choices, default=ReservationType.RESERVATION)
    cancel_reservation = models.ForeignKey(
        verbose_name=_('취소 예약'), to='self', on_delete=models.CASCADE, null=True, blank=True)
    objects = ReservationManager()

    class Meta:
        verbose_name = '예약'

    def __str__(self):
        return f'{self.created.strftime("%Y-%m-%d %H:%M")} / [{self.type}]건'

    @property
    def credit_message(self):
        message = f'{self.lesson.type} 수업 예약'
        if self.type == ReservationType.CANCEL:
            message = f'{self.lesson.type} 수업 예약 취소'
        return message

    def cancel(self, user) -> 'Reservation':
        from user.models import CustomUser
        from credit.models import UseCredit

        self.user: CustomUser

        if self.type == ReservationType.CANCEL:
            raise InvalidReservationType

        if self.user != user:
            raise NotYourReservation

        if self.cancel_reservation is not None:
            raise AlreadyCanceled

        if not self.lesson.is_cancelable():
            raise InvalidCancelDate

        refund_credit_count = self.lesson.get_cancel_credit()
        cancel_reservation = Reservation.objects.create(
            type=ReservationType.CANCEL, user=user, lesson=self.lesson)
        use_credit: UseCredit = self.credits.first()
        self.user.refund_credit(cancel_reservation, refund_credit_count, use_credit.purchased_credit)
        self.cancel_reservation = cancel_reservation
        self.save()
        return cancel_reservation
