"""Minimal delivery optimizer library - all in one file"""
import math

class Location:
    def __init__(self, lat, lon, address=""):
        self.lat = lat
        self.lon = lon
        self.address = address

class DistanceCalculator:
    @staticmethod
    def calculate(loc1, loc2):
        """Haversine distance in km"""
        R = 6371
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return round(R * c, 2)

class PricingEngine:
    def __init__(self, base_price=5.0, price_per_km=2.0):
        self.base_price = base_price
        self.price_per_km = price_per_km
    
    def calculate(self, distance_km, weight_kg=1.0):
        price = self.base_price + (distance_km * self.price_per_km)
        price += weight_kg * 0.5  # weight multiplier
        return round(price, 2)
