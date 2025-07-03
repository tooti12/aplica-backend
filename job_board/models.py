from django.db import models
from django.utils import timezone


class Job(models.Model):
    """
    Central Job model that serves as the main entity.
    All job data is stored in this table.
    """

    _id = models.CharField(max_length=50, primary_key=True)
    job_title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    application_link = models.TextField()
    job_categories = models.JSONField(blank=True, null=True)
    job_type = models.CharField(max_length=100, blank=True, null=True)
    location_type = models.CharField(max_length=50, blank=True, null=True)
    yoe_range = models.JSONField(blank=True, null=True)
    date_posted = models.DateTimeField()
    company_name = models.TextField(blank=True, null=True)
    company_link = models.TextField(blank=True, null=True)
    company_logo = models.TextField(blank=True, null=True)
    requirements_summary = models.TextField(blank=True, null=True)
    locations = models.JSONField(blank=True, null=True)
    salary_range = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    company_data = models.JSONField(blank=True, null=True)
    visa_sponsored = models.BooleanField(default=False)
    company_slug = models.TextField(max_length=100, blank=True, null=True)
    job_slug = models.TextField(max_length=100, blank=True, null=True)
    job_meta = models.TextField(max_length=100, blank=True, null=True)
    score = models.TextField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.job_title} (ID: {self._id})"
