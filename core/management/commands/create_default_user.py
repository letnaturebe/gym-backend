from django.core.management.base import BaseCommand

from user.models import CustomUser


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write('starting add user list')
        if not CustomUser.objects.filter(username="admin").exists():
            user = CustomUser.objects.create_superuser("admin")
            user.set_password("admin")
            user.save()
            self.stdout.write(self.style.SUCCESS('Complete!'))
