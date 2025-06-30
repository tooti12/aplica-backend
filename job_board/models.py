from django.db import models
from django.utils import timezone


class Job(models.Model):
    """
    Central Job model that serves as the main entity.
    All job data is stored in this table.
    """

    _id = models.CharField(max_length=50, primary_key=True)
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    application_link = models.TextField()
    date_posted = models.DateTimeField()
    date_created = models.DateTimeField(blank=True, null=True)
    date_validthrough = models.DateTimeField(blank=True, null=True)
    employment_type = models.JSONField(blank=True, null=True)
    location_type = models.CharField(max_length=50, blank=True, null=True)
    remote_derived = models.BooleanField(default=False)
    visa_sponsored = models.BooleanField(default=False)
    source_type = models.CharField(max_length=50, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    source_domain = models.TextField(blank=True, null=True)
    requirements_raw = models.JSONField(blank=True, null=True)
    location_requirements_raw = models.JSONField(blank=True, null=True)
    salary_raw = models.JSONField(blank=True, null=True)
    locations_alt_raw = models.JSONField(blank=True, null=True)
    locations_raw = models.JSONField(blank=True, null=True)
    locations_derived = models.JSONField(blank=True, null=True)
    cities_derived = models.JSONField(blank=True, null=True)
    regions_derived = models.JSONField(blank=True, null=True)
    countries_derived = models.JSONField(blank=True, null=True)
    timezones_derived = models.JSONField(blank=True, null=True)
    lats_derived = models.JSONField(blank=True, null=True)
    lngs_derived = models.JSONField(blank=True, null=True)
    # Organization fields
    organization = models.TextField(blank=True, null=True)
    organization_url = models.TextField(blank=True, null=True)
    organization_logo = models.TextField(blank=True, null=True)
    domain_derived = models.TextField(blank=True, null=True)
    meta = models.TextField(blank=True, null=True)
    score = models.FloatField(blank=True, null=True)

    # Additional fields for Hirebase compatibility
    job_categories = models.JSONField(blank=True, null=True)
    hirebase_job_type = models.CharField(max_length=50, blank=True, null=True)
    yoe_range = models.JSONField(blank=True, null=True)
    salary_range = models.JSONField(blank=True, null=True)
    job_board = models.CharField(max_length=100, blank=True, null=True)
    job_board_link = models.TextField(blank=True, null=True)
    requirements_summary = models.TextField(blank=True, null=True)
    company_data = models.JSONField(blank=True, null=True)
    company_slug = models.CharField(max_length=100, blank=True, null=True)
    job_slug = models.CharField(max_length=200, blank=True, null=True)
    locations = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (ID: {self._id})"
