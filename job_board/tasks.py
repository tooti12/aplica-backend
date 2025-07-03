import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, datetime
from typing import Optional
from pytz import UTC
from job_board.models import Job
from pathlib import Path
import glob
from aplica_backend.settings import LOGS_DIR
from .utils import fetch_hirebase_jobs

# Get logger for this module
logger = logging.getLogger(__name__)


@shared_task
def dummy_task():
    logger.info("This is a dummy Celery task!")


@shared_task
def delete_old_jobs():
    cutoff = timezone.now() - timedelta(days=7)
    old_jobs = Job.objects.filter(created_at__lt=cutoff)
    count = old_jobs.count()
    old_jobs.delete()
    logger.info(f"Deleted {count} jobs older than 7 days.")


@shared_task
def cleanup_old_logs():
    """Clean up log files older than 3 days."""
    try:
        # Calculate cutoff date (3 days ago)
        cutoff_date = timezone.now() - timedelta(days=3)
        deleted_count = 0

        logger.info(f"Starting log cleanup. Removing files older than {cutoff_date}")

        # Get all log files in the logs directory
        log_patterns = [
            str(LOGS_DIR / "*.log.*"),  # Rotated log files
            str(LOGS_DIR / "*.log"),  # Current log files (will be skipped)
        ]

        for pattern in log_patterns:
            for log_file in glob.glob(pattern):
                file_path = Path(log_file)

                # Skip current log files (without date suffix)
                if not file_path.name.endswith(".log"):
                    continue

                # Get file modification time
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if timezone.is_naive(mtime):
                        mtime = timezone.make_aware(mtime, timezone=UTC)

                    # Delete if older than 3 days
                    if mtime < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old log file: {file_path.name}")

                except Exception as e:
                    logger.error(f"Error processing log file {file_path}: {e}")
                    continue

        logger.info(f"Log cleanup completed. Deleted {deleted_count} old log files.")

    except Exception as e:
        logger.error(f"Error during log cleanup: {e}")


def parse_datetime(date_string: str) -> Optional[datetime]:
    """Parse datetime string to Django datetime object with timezone awareness."""
    if not date_string:
        return None

    # Handle different datetime formats
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            parsed_datetime = datetime.strptime(date_string, fmt)
            # Make timezone-aware if it's naive
            if timezone.is_naive(parsed_datetime):
                parsed_datetime = timezone.make_aware(parsed_datetime, timezone=UTC)
            return parsed_datetime
        except Exception:
            continue

    return None


@shared_task
def hirebase_page_task(page: int, limit: int = 100):
    """Fetch and process a single page of job data from Hirebase API."""
    data = fetch_hirebase_jobs(page, limit)
    if not data:
        return
    jobs = data.get("jobs", [])
    if not jobs:
        logger.info(f"No jobs found on page {page}.")
        return
    date_posted = jobs[0].get("date_posted")
    parsed_date = parse_datetime(date_posted)
    if parsed_date:
        days_diff = (timezone.now() - parsed_date).days
        logger.info(
            f"First job on page {page} has date_posted: {parsed_date} ({days_diff} days old)"
        )
        if days_diff > 8:
            logger.info(
                f"First job on page {page} is more than 8 days old. Stopping further processing."
            )
            return "stop"
    else:
        logger.warning(
            f"Could not parse date_posted for first job on page {page}. Proceeding with page."
        )

    page_created_count = 0
    page_updated_count = 0
    for job_data in jobs:
        try:
            with transaction.atomic():
                job_id = job_data.get("_id") or job_data.get("id")
                if not job_id:
                    logger.warning(f"Skipping job without ID: {job_data}")
                    continue
                date_posted = parse_datetime(job_data.get("date_posted"))
                _, created = Job.objects.update_or_create(
                    _id=job_id,
                    defaults={
                        "job_title": job_data.get("job_title"),
                        "description": job_data.get("description", ""),
                        "application_link": job_data.get("application_link")
                        or job_data.get("url", ""),
                        "job_categories": job_data.get("job_categories"),
                        "job_type": job_data.get("job_type"),
                        "location_type": job_data.get("location_type"),
                        "yoe_range": job_data.get("yoe_range"),
                        "date_posted": date_posted or timezone.now(),
                        "company_name": job_data.get("company_name"),
                        "company_link": job_data.get("company_link"),
                        "company_logo": job_data.get("company_logo"),
                        "requirements_summary": job_data.get("requirements_summary"),
                        "locations": job_data.get("locations"),
                        "salary_range": job_data.get("salary_range"),
                        "company_data": job_data.get("company_data"),
                        "visa_sponsored": job_data.get("visa_sponsored"),
                        "company_slug": job_data.get("company_slug"),
                        "job_slug": job_data.get("job_slug"),
                        "job_meta": job_data.get("meta"),
                        "score": job_data.get("score"),
                    },
                )
                if created:
                    page_created_count += 1
                else:
                    page_updated_count += 1
        except Exception as e:
            logger.error(
                f"Error processing Hirebase job {job_data.get('id', job_data.get('_id', 'unknown'))}: {e}"
            )
            continue
    logger.info(
        f"Page {page}: Created {page_created_count} jobs, Updated {page_updated_count} jobs."
    )
    return page_created_count, page_updated_count


@shared_task
def hirebase_task(first_run: bool = False):
    """Main task to fetch pagination info and process each page one by one."""
    data = fetch_hirebase_jobs(1, 100)
    if not data:
        logger.error("Failed to fetch initial pagination info from Hirebase.")
        return
    total_pages = data.get("total_pages")
    if not total_pages:
        logger.info("No total_pages info in response; will only process first page.")
        total_pages = 1
    logger.info(f"Processing {total_pages} pages one by one.")
    limit = 100
    total_created = 0
    total_updated = 0
    updated_counter = 0
    for page in range(1, total_pages + 1):
        logger.info(f"Processing page {page}.")
        result = hirebase_page_task(page, limit)
        if result == "stop":
            logger.info("Stopping Hirebase task. 8 days old jobs found.")
            break
        elif result:
            page_created_count, page_updated_count = result
            total_created += page_created_count
            total_updated += page_updated_count
            if page_updated_count == 100:
                updated_counter += 1
            else:
                updated_counter = 0
            if updated_counter == 5 and not first_run:
                logger.info(
                    "Stopping Hirebase task. 5 consecutive pages with 100 updated jobs found."
                )
                break

    logger.info(f"Completed processing {total_pages} pages.")
    logger.info(f"Total created: {total_created}")
    logger.info(f"Total updated: {total_updated}")


@shared_task
def salary_task():
    """Deprecated: Use hirebase_task instead."""
    logger.warning("Warning: salary_task is deprecated. Use hirebase_task instead.")
    return hirebase_task.delay()
