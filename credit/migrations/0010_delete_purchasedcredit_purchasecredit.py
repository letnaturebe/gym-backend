# Generated by Django 4.1.1 on 2022-10-03 10:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0009_alter_credit_remaining_count_delete_purchasedcredit_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PurchasedCredit',
        ),
        migrations.CreateModel(
            name='PurchaseCredit',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('credit.credit',),
        ),
    ]
