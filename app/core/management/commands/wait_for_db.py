from django.core.management.base import BaseCommand

from psycopg2 import OperationalError as PE

from django.db.utils import OperationalError
import time


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write('waiting database')
        dp_up = False

        while dp_up is False:
            try:
                self.check(databases=['default'])
                dp_up = True
            except (PE, OperationalError):
                self.stdout.write('database unavailable waiting one sec')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database is available'))
