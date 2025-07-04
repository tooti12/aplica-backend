# Generated by Django 4.2.23 on 2025-07-01 08:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("job_board", "0004_rename_domain_derived_job_company_link_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="company_data",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="company_slug",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="job_meta",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="job_slug",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="score",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="visa_sponsored",
            field=models.BooleanField(default=False),
        ),
    ]
