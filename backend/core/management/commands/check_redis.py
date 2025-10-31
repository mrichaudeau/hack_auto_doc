from django.core.management.base import BaseCommand
from core.utils.redis_health import check_redis_health


class Command(BaseCommand):
    help = 'Check Redis connectivity for broker and cache'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Redis Health Check'))
        self.stdout.write('=' * 50)

        results = check_redis_health()
        exit_code = 0

        for db_name, status in results.items():
            if status['connected']:
                self.stdout.write(self.style.SUCCESS(
                    f"{db_name.upper()}: Connected ({status['latency_ms']}ms)"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"{db_name.upper()}: Failed - {status['error']}"
                ))
                exit_code = 1

        if exit_code == 0:
            self.stdout.write(self.style.SUCCESS('\nAll Redis connections healthy!'))
        else:
            self.stdout.write(self.style.ERROR('\nSome Redis connections failed!'))

        return exit_code
