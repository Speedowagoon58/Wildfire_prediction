from django.db import migrations


def add_initial_regions(apps, schema_editor):
    Region = apps.get_model("core", "Region")

    # List of initial regions with their coordinates for Morocco
    regions = [
        {
            "name": "Rif Mountains",
            "latitude": 35.0405,
            "longitude": -5.1167,
            "elevation": 2456,  # Tidighine peak
        },
        {
            "name": "Middle Atlas",
            "latitude": 33.4721,
            "longitude": -5.0144,
            "elevation": 3340,  # Jbel Bou Naceur
        },
        {
            "name": "High Atlas",
            "latitude": 31.0595,
            "longitude": -7.9162,
            "elevation": 4167,  # Mount Toubkal
        },
        {
            "name": "Anti-Atlas",
            "latitude": 30.2500,
            "longitude": -7.8667,
            "elevation": 2712,  # Jebel Sirwa
        },
        {
            "name": "Oriental Region",
            "latitude": 34.6833,
            "longitude": -1.9000,
            "elevation": 1000,
        },
    ]

    for region_data in regions:
        Region.objects.create(**region_data)


def remove_initial_regions(apps, schema_editor):
    Region = apps.get_model("core", "Region")
    Region.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_initial_regions, remove_initial_regions),
    ]
