from django.contrib import admin

from credit.models import PricePolicy, Credit

models = [PricePolicy]
for model in models:
    admin.site.register(model)


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_filter = (
        ('reservation__lesson', admin.RelatedOnlyFieldListFilter),
        ('reservation', admin.RelatedOnlyFieldListFilter),
        ('user', admin.RelatedOnlyFieldListFilter),
    )
