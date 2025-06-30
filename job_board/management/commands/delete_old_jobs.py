from django.core.management.base import BaseCommand
from job_board.tasks import delete_old_jobs


class Command(BaseCommand):
    help = "Enqueue the delete_old_jobs Celery task."

    def handle(self, *args, **options):
        result = delete_old_jobs.delay()
        self.stdout.write(
            self.style.SUCCESS(f"delete_old_jobs task enqueued! Task ID: {result.id}")
        )
