"""
Haversine distance calculation — pure Python, works with any database.
"""
import math
from typing import Optional


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (degrees).
        lat2, lon2: Latitude and longitude of point 2 (degrees).

    Returns:
        Distance in kilometres.
    """
    R = 6371.0  # Earth's radius in km

    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def bounding_box(
    lat: float, lon: float, radius_km: float
) -> tuple[float, float, float, float]:
    """
    Return a (min_lat, max_lat, min_lon, max_lon) bounding box for quick
    database filtering before exact Haversine calculation.
    """
    delta_lat = radius_km / 111.0  # ~111 km per degree of latitude
    delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))

    return (
        lat - delta_lat,
        lat + delta_lat,
        lon - delta_lon,
        lon + delta_lon,
    )


def filter_by_distance(queryset, lat: float, lon: float, radius_km: float, lat_field: str = "latitude", lon_field: str = "longitude"):
    """
    Filter a queryset by bounding box, then annotate with exact distance.
    Returns list of (obj, distance_km) tuples sorted by distance.
    """
    min_lat, max_lat, min_lon, max_lon = bounding_box(lat, lon, radius_km)

    # Bounding box filter (fast, uses indexes)
    qs = queryset.filter(
        **{
            f"{lat_field}__gte": min_lat,
            f"{lat_field}__lte": max_lat,
            f"{lon_field}__gte": min_lon,
            f"{lon_field}__lte": max_lon,
            f"{lat_field}__isnull": False,
            f"{lon_field}__isnull": False,
        }
    )

    # Exact distance calculation in Python
    results = []
    for obj in qs:
        obj_lat = getattr(obj, lat_field)
        obj_lon = getattr(obj, lon_field)
        if obj_lat is not None and obj_lon is not None:
            dist = haversine_distance(lat, lon, obj_lat, obj_lon)
            if dist <= radius_km:
                results.append((obj, round(dist, 1)))

    results.sort(key=lambda x: x[1])
    return results


def get_nearby_users(
    lat: float, lon: float, radius_km: float, role: Optional[str] = None,
    verified_only: bool = False, exclude_user_id: Optional[int] = None,
):
    """Get nearby users with distance, optionally filtered by role."""
    from accounts.models import User

    qs = User.objects.filter(is_active=True)
    if role:
        qs = qs.filter(role=role)
    if verified_only:
        qs = qs.filter(is_verified=True)
    if exclude_user_id:
        qs = qs.exclude(pk=exclude_user_id)

    return filter_by_distance(qs, lat, lon, radius_km)
