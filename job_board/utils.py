import os
import logging
import requests
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)


def fetch_hirebase_jobs(
    page: int,
    limit: int = 100,
    sort_by: str = "date_posted",
    sort_order: str = "desc",
    retries: int = 3,
) -> Optional[Dict[str, Any]]:
    endpoint: Optional[str] = os.environ.get("JOB_API_ENDPOINT")
    api_key: Optional[str] = os.environ.get("JOB_API_KEY")

    if not endpoint or not api_key:
        logger.error(
            "Missing JOB_API_ENDPOINT or JOB_API_KEY in environment variables."
        )
        return None

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }
    payload = {
        "page": page,
        "limit": limit,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=300)
        if response.status_code != 200:
            logger.error(
                f"Failed to fetch jobs from Hirebase (page {page}): {response.status_code} - {response.text}"
            )
            return None
        return response.json()
    except requests.Timeout:
        logger.error(
            f"Timeout while fetching jobs from Hirebase (page {page}): request exceeded 5 minutes."
        )
        if retries > 0:
            logger.info(f"Retrying fetch_hirebase_jobs (page {page}) after timeout.")
            time.sleep(1)
            return fetch_hirebase_jobs(page, limit, sort_by, sort_order, retries)
        return None
    except Exception as e:
        logger.error(f"Exception while fetching jobs from Hirebase (page {page}): {e}")
        if retries > 0:
            logger.info(
                f"Retrying fetch_hirebase_jobs (page {page}) in {retries} seconds..."
            )
            time.sleep(1)
            return fetch_hirebase_jobs(page, limit, sort_by, sort_order, retries - 1)
        return None
