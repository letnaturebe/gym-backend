from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from lesson.models import Lesson, Reservation

models = [Lesson]
for model in models:
    admin.site.register(model)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_filter = (
        ('lesson', admin.RelatedOnlyFieldListFilter),
        ('created', DateRangeFilter),
    )
