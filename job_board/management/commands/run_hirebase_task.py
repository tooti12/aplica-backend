from django.core.management.base import BaseCommand
from job_board.tasks import hirebase_task


class Command(BaseCommand):
    help = "Enqueue the hirebase_task Celery task to fetch jobs from Hirebase API."

    def handle(self, *args, **options):
        result = hirebase_task.delay(first_run=True)
        self.stdout.write(
            self.style.SUCCESS(f"hirebase_task enqueued! Task ID: {result.id}")
        )
