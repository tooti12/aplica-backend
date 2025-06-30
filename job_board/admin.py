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
        "job_title",
        "company_name",
        "date_posted",
    ]
    list_filter = [
        "date_posted",
        "job_type",
        "location_type",
    ]
    search_fields = [
        "_id",
        "job_title",
        "description",
        "company_name",
        "job_categories",
    ]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "date_posted"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "_id",
                    "job_title",
                    "description",
                    "application_link",
                    "date_posted",
                )
            },
        ),
        (
            "Company Information",
            {
                "fields": (
                    "company_name",
                    "company_link",
                    "company_logo",
                )
            },
        ),
        (
            "Job Details",
            {
                "fields": (
                    "job_type",
                    "job_categories",
                    "location_type",
                    "yoe_range",
                    "salary_range",
                    "requirements_summary",
                )
            },
        ),
        (
            "Location Information",
            {"fields": ("locations",)},
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )
