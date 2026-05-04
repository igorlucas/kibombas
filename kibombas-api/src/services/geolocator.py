from geopy.geocoders import Nominatim
from src.core.config import settings

class GeolocatorService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent=settings.NOMINATIM_USER_AGENT)

    def reverse_geocode(self, lat: float, long: float):
        location = self.geolocator.reverse(f"{lat},{long}", language="pt")
        address = location.raw.get("address", {})
        return address
