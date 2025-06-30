import os
import logging
import requests
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, datetime
from typing import Optional
from pytz import UTC
from job_board.models import Job
from pathlib import Path
import glob

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
        from Aplika_backend.settings import LOGS_DIR

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
def hirebase_task():
    """Main task to fetch and process job data from Hirebase API with pagination."""
    endpoint: Optional[str] = os.environ.get("JOB_API_ENDPOINT")
    api_key: Optional[str] = os.environ.get("JOB_API_KEY")

    if not endpoint or not api_key:
        logger.error(
            "Missing JOB_API_ENDPOINT or JOB_API_KEY in environment variables."
        )
        return

    logger.info("Starting Hirebase task with pagination")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    page = 1
    limit = 100
    total_processed = 0
    total_created = 0
    total_updated = 0
    total_pages = None

    while True:
        payload = {"page": page, "limit": limit}
        response = requests.post(endpoint, headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(f"Failed to fetch jobs from Hirebase (page {page}): {response.status_code} - {response.text}")
            break

        data = response.json()
        jobs = data.get("jobs", [])
        if not jobs:
            logger.info(f"No jobs found on page {page}. Stopping pagination.")
            break

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
                    date_created = parse_datetime(job_data.get("date_created"))
                    date_validthrough = parse_datetime(job_data.get("date_validthrough"))

                    _, created = Job.objects.update_or_create(
                        _id=job_id,
                        defaults={
                            "title": job_data.get("job_title") or job_data.get("title", ""),
                            "description": job_data.get("description", ""),
                            "application_link": job_data.get("application_link") or job_data.get("url", ""),
                            "date_posted": date_posted or timezone.now(),
                            "date_created": date_created,
                            "date_validthrough": date_validthrough,
                            "employment_type": job_data.get("employment_type"),
                            "location_type": job_data.get("location_type"),
                            "remote_derived": job_data.get("remote_derived", False),
                            "visa_sponsored": job_data.get("visa_sponsored", False),
                            "source_type": job_data.get("source_type"),
                            "source": job_data.get("source"),
                            "source_domain": job_data.get("source_domain"),
                            "requirements_raw": job_data.get("requirements_raw"),
                            "location_requirements_raw": job_data.get("location_requirements_raw"),
                            "salary_raw": job_data.get("salary_raw"),
                            "locations_alt_raw": job_data.get("locations_alt_raw"),
                            "locations_raw": job_data.get("locations_raw"),
                            "locations_derived": job_data.get("locations_derived"),
                            "cities_derived": job_data.get("cities_derived"),
                            "regions_derived": job_data.get("regions_derived"),
                            "countries_derived": job_data.get("countries_derived"),
                            "timezones_derived": job_data.get("timezones_derived"),
                            "lats_derived": job_data.get("lats_derived"),
                            "lngs_derived": job_data.get("lngs_derived"),
                            "organization": job_data.get("organization") or job_data.get("company_name"),
                            "organization_url": job_data.get("organization_url") or job_data.get("company_link"),
                            "organization_logo": job_data.get("organization_logo") or job_data.get("company_logo"),
                            "domain_derived": job_data.get("domain_derived"),
                            "meta": job_data.get("meta"),
                            "score": job_data.get("score"),
                            "job_categories": job_data.get("job_categories"),
                            "hirebase_job_type": job_data.get("job_type"),
                            "yoe_range": job_data.get("yoe_range"),
                            "salary_range": job_data.get("salary_range"),
                            "job_board": job_data.get("job_board"),
                            "job_board_link": job_data.get("job_board_link"),
                            "requirements_summary": job_data.get("requirements_summary"),
                            "company_data": job_data.get("company_data"),
                            "company_slug": job_data.get("company_slug"),
                            "job_slug": job_data.get("job_slug"),
                            "locations": job_data.get("locations"),
                        },
                    )

                    total_processed += 1
                    if created:
                        page_created_count += 1
                    else:
                        page_updated_count += 1

            except Exception as e:
                logger.error(
                    f"Error processing Hirebase job {job_data.get('id', job_data.get('_id', 'unknown'))}: {e}"
                )
                logger.info(f"Page {page}: Created {page_created_count} jobs, Updated {page_updated_count} jobs.")
                total_created += page_created_count
                total_updated += page_updated_count
                continue

        logger.info(f"Page {page}: Created {page_created_count} jobs, Updated {page_updated_count} jobs.")
        total_created += page_created_count
        total_updated += page_updated_count

        # Pagination: check if there are more pages
        if total_pages is None:
            total_pages = data.get("total_pages")
            if not total_pages:
                logger.info("No total_pages info in response; will stop if jobs run out.")
                total_pages = page + 1  # fallback: stop if jobs run out
        if page >= total_pages:
            logger.info(f"Reached last page ({page}) of {total_pages}.")
            break
        page += 1

    logger.info(f"Hirebase task completed! Processed {total_processed} jobs. (Total Created: {total_created}, Total Updated: {total_updated})")


@shared_task
def salary_task():
    """Deprecated: Use hirebase_task instead."""
    logger.warning("Warning: salary_task is deprecated. Use hirebase_task instead.")
    return hirebase_task.delay()
