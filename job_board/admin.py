from django.contrib import admin
from .models import Job


class EmploymentTypeFilter(admin.SimpleListFilter):
    title = "Employment Type"
    parameter_name = "employment_type"

    def lookups(self, request, model_admin):
        # Get unique employment types from the database
        employment_types = set()
        for job in Job.objects.all():
            if job.employment_type:
                if isinstance(job.employment_type, list):
                    for emp_type in job.employment_type:
                        if emp_type:
                            employment_types.add(emp_type)
                else:
                    employment_types.add(job.employment_type)

        return [(emp_type, emp_type) for emp_type in sorted(employment_types)]

    def queryset(self, request, queryset):
        if self.value():
            # Filter jobs where employment_type contains the selected value
            return queryset.filter(employment_type__contains=[self.value()])
        return queryset


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "_id",
        "title",
        "organization",
        "date_posted",
        "source",
        "remote_derived",
        "score",
    ]
    list_filter = [
        "date_posted",
        EmploymentTypeFilter,
        "location_type",
        "remote_derived",
        "visa_sponsored",
        "source",
        "job_board",
        "hirebase_job_type",
    ]
    search_fields = ["_id", "title", "description", "organization", "job_categories"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "date_posted"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "_id",
                    "title",
                    "description",
                    "application_link",
                    "date_posted",
                    "date_created",
                    "date_validthrough",
                )
            },
        ),
        (
            "Organization",
            {
                "fields": (
                    "organization",
                    "organization_url",
                    "organization_logo",
                    "domain_derived",
                )
            },
        ),
        (
            "Job Details",
            {
                "fields": (
                    "employment_type",
                    "hirebase_job_type",
                    "job_categories",
                    "location_type",
                    "remote_derived",
                    "visa_sponsored",
                    "yoe_range",
                    "salary_range",
                    "requirements_summary",
                )
            },
        ),
        (
            "Location Information",
            {
                "fields": (
                    "locations",
                    "locations_raw",
                    "locations_derived",
                    "cities_derived",
                    "regions_derived",
                    "countries_derived",
                    "timezones_derived",
                    "lats_derived",
                    "lngs_derived",
                    "locations_alt_raw",
                )
            },
        ),
        (
            "Source Information",
            {
                "fields": (
                    "source_type",
                    "source",
                    "source_domain",
                    "job_board",
                    "job_board_link",
                )
            },
        ),
        (
            "Raw Data",
            {
                "fields": (
                    "requirements_raw",
                    "location_requirements_raw",
                    "salary_raw",
                    "company_data",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "meta",
                    "score",
                    "company_slug",
                    "job_slug",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )
