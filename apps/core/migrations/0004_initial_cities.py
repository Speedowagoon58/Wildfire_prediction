from django.db import migrations


def add_initial_cities(apps, schema_editor):
    Region = apps.get_model("core", "Region")
    City = apps.get_model("core", "City")

    # Get regions
    rif = Region.objects.get(name="Rif Mountains")
    middle_atlas = Region.objects.get(name="Middle Atlas")
    high_atlas = Region.objects.get(name="High Atlas")
    anti_atlas = Region.objects.get(name="Anti-Atlas")
    oriental = Region.objects.get(name="Oriental Region")

    # Cities for each region
    cities = [
        # Rif Mountains
        {
            "name": "Chefchaouen",
            "region": rif,
            "latitude": 35.1714,
            "longitude": -5.2697,
            "population": 45000,
        },
        {
            "name": "Tetouan",
            "region": rif,
            "latitude": 35.5769,
            "longitude": -5.3686,
            "population": 380000,
        },
        {
            "name": "Al Hoceima",
            "region": rif,
            "latitude": 35.2500,
            "longitude": -3.9333,
            "population": 56000,
        },
        # Middle Atlas
        {
            "name": "Ifrane",
            "region": middle_atlas,
            "latitude": 33.5333,
            "longitude": -5.1167,
            "population": 30000,
        },
        {
            "name": "Azrou",
            "region": middle_atlas,
            "latitude": 33.4333,
            "longitude": -5.2167,
            "population": 47000,
        },
        {
            "name": "Meknes",
            "region": middle_atlas,
            "latitude": 33.9000,
            "longitude": -5.5500,
            "population": 632000,
        },
        # High Atlas
        {
            "name": "Marrakech",
            "region": high_atlas,
            "latitude": 31.6295,
            "longitude": -7.9811,
            "population": 928000,
        },
        {
            "name": "Ouarzazate",
            "region": high_atlas,
            "latitude": 30.9333,
            "longitude": -6.9167,
            "population": 71000,
        },
        {
            "name": "Tinghir",
            "region": high_atlas,
            "latitude": 31.5167,
            "longitude": -5.5333,
            "population": 42000,
        },
        # Anti-Atlas
        {
            "name": "Tafraoute",
            "region": anti_atlas,
            "latitude": 29.7167,
            "longitude": -9.0000,
            "population": 5000,
        },
        {
            "name": "Tiznit",
            "region": anti_atlas,
            "latitude": 29.7000,
            "longitude": -9.7333,
            "population": 74000,
        },
        {
            "name": "Tata",
            "region": anti_atlas,
            "latitude": 29.7500,
            "longitude": -7.9667,
            "population": 15000,
        },
        # Oriental Region
        {
            "name": "Oujda",
            "region": oriental,
            "latitude": 34.6867,
            "longitude": -1.9114,
            "population": 494000,
        },
        {
            "name": "Berkane",
            "region": oriental,
            "latitude": 34.9167,
            "longitude": -2.3167,
            "population": 109000,
        },
        {
            "name": "Nador",
            "region": oriental,
            "latitude": 35.1667,
            "longitude": -2.9333,
            "population": 161000,
        },
    ]

    for city_data in cities:
        City.objects.create(**city_data)


def remove_initial_cities(apps, schema_editor):
    City = apps.get_model("core", "City")
    City.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_city"),
    ]

    operations = [
        migrations.RunPython(add_initial_cities, remove_initial_cities),
    ]
