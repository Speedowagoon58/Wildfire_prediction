from django.test import TestCase
from .models import Region, WildfireEvent


class RegionModelTest(TestCase):
    def test_region_creation(self):
        region = Region.objects.create(
            name="Test Region", latitude=35.0, longitude=-5.0, elevation=1000
        )
        self.assertEqual(str(region), "Test Region")
        self.assertEqual(region.latitude, 35.0)
        self.assertEqual(region.longitude, -5.0)
        self.assertEqual(region.elevation, 1000)


class WildfireEventModelTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(
            name="Test Region", latitude=35.0, longitude=-5.0
        )

    def test_wildfire_event_creation(self):
        event = WildfireEvent.objects.create(
            region=self.region,
            start_date="2024-01-01T00:00:00Z",
            severity=WildfireEvent.MEDIUM,
            area_affected=10.5,
        )
        self.assertEqual(str(event), "Wildfire at Test Region on 2024-01-01")
        self.assertEqual(event.severity, WildfireEvent.MEDIUM)
        self.assertEqual(event.area_affected, 10.5)
