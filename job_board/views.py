# Create your views here.

from rest_framework import generics
from .models import Job
from .serializers import JobSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db import models
from rest_framework.views import APIView
import redis
import os
from django.utils import timezone

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)


class JobPagination(PageNumberPagination):
    """
    Custom pagination class for jobs API.

    Attributes:
        page_query_param (str): Query parameter for page number (page).
        page_size_query_param (str): Query parameter for page size (limit).
        max_page_size (int): Maximum allowed page size.
        page_size (int): Default page size.
    """

    page_query_param = "page"
    page_size_query_param = "limit"
    max_page_size = 100
    page_size = 10

    def get_paginated_response(self, data):
        """
        Return a paginated response with pagination info and results.

        Args:
            data (list): Serialized data for the current page.

        Returns:
            Response: DRF Response with pagination metadata and results.
        """
        return Response(
            {
                "pagination": {
                    "count": self.page.paginator.count,
                    "page": self.page.number,
                    "limit": self.get_page_size(self.request),
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "total_pages": self.page.paginator.num_pages,
                },
                "results": data,
            }
        )


class JobListView(generics.ListAPIView):
    """
    ListAPIView for retrieving jobs with filtering, search, and pagination.

    Query Parameters:
        q (str): Search by job title or company name (case-insensitive, partial match).
        location (str): Filter by city, country, region (comma-separated: city,country,region).
        job_type (str): Filter by job type (case-insensitive, partial match).
        location_type (str): Filter by location type (case-insensitive, partial match).
        job_posted (str): Filter by posting date ('last_24_hour', 'last_3_days', 'last_7_days').
        salary_min (float): Filter jobs with minimum salary >= this value.
        salary_max (float): Filter jobs with maximum salary <= this value.
        page (int): Page number for pagination.
        limit (int): Page size for pagination.

    Returns:
        Paginated list of jobs with applied filters and search.
    """

    serializer_class = JobSerializer
    pagination_class = JobPagination

    def get_queryset(self):
        """
        Get the queryset for jobs, applying all filters and search.

        Returns:
            QuerySet: Filtered queryset of Job objects.
        """
        queryset = Job.objects.all().order_by("-date_posted")
        q = self.request.query_params.get("q")
        if q:
            queryset = queryset.filter(
                models.Q(job_title__icontains=q) | models.Q(company_name__icontains=q)
            )
        location = self.request.query_params.get("location")
        if location:
            # Expecting format: city,country,region (any can be omitted)
            parts = [p.strip() for p in location.split(",")]
            city = parts[0] if len(parts) > 0 and parts[0] else None
            country = parts[1] if len(parts) > 1 and parts[1] else None
            region = parts[2] if len(parts) > 2 and parts[2] else None
            location_filters = models.Q()
            if city:
                location_filters &= models.Q(locations__contains=[{"city": city}])
            if country:
                location_filters &= models.Q(locations__contains=[{"country": country}])
            if region:
                location_filters &= models.Q(locations__contains=[{"region": region}])
            queryset = queryset.filter(location_filters)
        job_type = self.request.query_params.get("job_type")
        if job_type:
            queryset = queryset.filter(job_type__icontains=job_type)
        location_type = self.request.query_params.get("location_type")
        if location_type:
            queryset = queryset.filter(location_type__icontains=location_type)
        job_posted = self.request.query_params.get("job_posted")
        if job_posted:
            now = timezone.now()
            if job_posted == "last_24_hour":
                since = now - timezone.timedelta(hours=24)
                queryset = queryset.filter(date_posted__gte=since)
            elif job_posted == "last_3_days":
                since = now - timezone.timedelta(days=3)
                queryset = queryset.filter(date_posted__gte=since)
            elif job_posted == "last_7_days":
                since = now - timezone.timedelta(days=7)
                queryset = queryset.filter(date_posted__gte=since)
        salary_min = self.request.query_params.get("salary_min")
        salary_max = self.request.query_params.get("salary_max")
        if salary_min is not None:
            try:
                salary_min = float(salary_min)
                queryset = queryset.filter(salary_range__min__gte=salary_min)
            except ValueError:
                pass
        if salary_max is not None:
            try:
                salary_max = float(salary_max)
                queryset = queryset.filter(salary_range__max__lte=salary_max)
            except ValueError:
                pass
        return queryset


class LocationListView(APIView):
    """
    API view to return all unique locations from the Job model.

    Query Parameters:
        search (str): Optional. Case-insensitive substring to filter locations.

    Returns:
        JSON response with a list of unique locations in the format 'city,country,region'.
        Only non-empty fields are included in each entry. Limited to 100 results.
    """

    CACHE_KEY = "job_board:unique_locations"
    CACHE_TIMEOUT = 60 * 30  # 30 minutes

    def get(self, request, *args, **kwargs):
        """
        Get all unique locations, using Redis cache if available.

        Returns:
            Response: JSON response with a list of unique locations.
        """
        search = request.query_params.get("search", "").strip().lower()
        locations_list = redis_client.lrange(self.CACHE_KEY, 0, -1)
        if not locations_list:
            locations_set = set()
            for job in Job.objects.exclude(locations=None):
                for loc in job.locations:
                    city = (loc.get("city") or "").strip()
                    country = (loc.get("country") or "").strip()
                    region = (loc.get("region") or "").strip()
                    fields = [city, country, region]
                    filtered_fields = [f for f in fields if f]
                    if filtered_fields:
                        locations_set.add(",".join(filtered_fields))
            locations_list = sorted(list(locations_set))
            if locations_list:
                # Store in Redis as a list
                redis_client.delete(self.CACHE_KEY)
                redis_client.rpush(self.CACHE_KEY, *locations_list)
                redis_client.expire(self.CACHE_KEY, self.CACHE_TIMEOUT)
        # Filter by search if provided
        if search:
            locations_list = [loc for loc in locations_list if search in loc.lower()]
        return Response({"locations": locations_list[:100]})


class LocationFieldListView(APIView):
    """
    API view to return a unique list of cities, countries, or regions from the Job model.

    Query Parameters:
        field (str): Required. One of 'city', 'country', or 'region'.
        search (str): Optional. Case-insensitive substring to filter results.

    Returns:
        JSON response with a list of unique values for the requested field. Limited to 100 results.
    """

    CACHE_KEY_PREFIX = "job_board:unique_location:"
    CACHE_TIMEOUT = 60 * 30  # 30 minutes
    VALID_FIELDS = {"city", "country", "region"}

    def get(self, request, *args, **kwargs):
        """
        Get all unique values for the requested field, using Redis cache if available.

        Returns:
            Response: JSON response with a list of unique values for the field.
        """
        field = request.query_params.get("field", "").strip().lower()
        search = request.query_params.get("search", "").strip().lower()
        if field not in self.VALID_FIELDS:
            return Response(
                {
                    "error": f"Invalid field. Must be one of: {', '.join(self.VALID_FIELDS)}"
                },
                status=400,
            )
        cache_key = f"{self.CACHE_KEY_PREFIX}_{field}"
        values_list = redis_client.lrange(cache_key, 0, -1)
        if not values_list:
            values_set = set()
            for job in Job.objects.exclude(locations=None):
                for loc in job.locations:
                    value = (loc.get(field) or "").strip()
                    if value:
                        values_set.add(value)
            values_list = sorted(list(values_set))
            if values_list:
                redis_client.delete(cache_key)
                redis_client.rpush(cache_key, *values_list)
                redis_client.expire(cache_key, self.CACHE_TIMEOUT)
        if search:
            values_list = [v for v in values_list if search in v.lower()]
        return Response({f"{field}s": values_list[:100]})
