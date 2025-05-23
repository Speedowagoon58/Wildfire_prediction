# Generated by Django 5.0.1 on 2025-04-04 14:20

from django.db import migrations


def create_initial_data(apps, schema_editor):
    SoilType = apps.get_model("core", "SoilType")
    Region = apps.get_model("core", "Region")

    # Create soil types
    sandy = SoilType.objects.create(
        name="Sandy",
        description="Sandy soil common in desert regions",
        fire_risk_factor=1.5,
        moisture_retention=0.2,
        organic_matter=0.8,
    )

    clay = SoilType.objects.create(
        name="Clay",
        description="Clay soil found in agricultural regions",
        fire_risk_factor=0.7,
        moisture_retention=0.8,
        organic_matter=2.0,
    )

    loam = SoilType.objects.create(
        name="Loam",
        description="Mixed soil ideal for vegetation",
        fire_risk_factor=1.0,
        moisture_retention=0.6,
        organic_matter=3.0,
    )

    # Create regions with more detailed data
    atlas_mountains = Region.objects.create(
        name="Atlas Mountains",
        latitude=31.2128,
        longitude=-7.2622,
        elevation=2500,
        area=100000,
        population=2500000,
        soil_type=loam,
        vegetation_density=0.6,
        climate_zone="mediterranean",
        description="Mountain range with diverse ecosystems and traditional Berber villages",
    )

    middle_atlas = Region.objects.create(
        name="Middle Atlas",
        latitude=33.2333,
        longitude=-5.0000,
        elevation=2000,
        area=23000,
        population=1200000,
        soil_type=loam,
        vegetation_density=0.7,
        climate_zone="mediterranean",
        description="Sub-range of the Atlas Mountains known for its cedar forests and lakes",
    )

    rif_mountains = Region.objects.create(
        name="Rif Mountains",
        latitude=35.0700,
        longitude=-4.5000,
        elevation=1500,
        area=30000,
        population=3000000,
        soil_type=clay,
        vegetation_density=0.8,
        climate_zone="mediterranean",
        description="Coastal mountain range with dense forests and high rainfall",
    )

    sahara_region = Region.objects.create(
        name="Sahara Region",
        latitude=31.7917,
        longitude=-4.0833,
        elevation=400,
        area=150000,
        population=1500000,
        soil_type=sandy,
        vegetation_density=0.1,
        climate_zone="semi_arid",
        description="Arid desert region with oases and nomadic communities",
    )

    anti_atlas = Region.objects.create(
        name="Anti Atlas",
        latitude=29.7000,
        longitude=-8.8833,
        elevation=2000,
        area=45000,
        population=800000,
        soil_type=sandy,
        vegetation_density=0.3,
        climate_zone="semi_arid",
        description="Rugged mountain range marking the beginning of the Sahara Desert",
    )

    souss_valley = Region.objects.create(
        name="Souss Valley",
        latitude=30.4500,
        longitude=-9.1333,
        elevation=500,
        area=16000,
        population=2200000,
        soil_type=loam,
        vegetation_density=0.5,
        climate_zone="mediterranean",
        description="Fertile valley known for its argan forests and agricultural production",
    )


def remove_initial_data(apps, schema_editor):
    SoilType = apps.get_model("core", "SoilType")
    Region = apps.get_model("core", "Region")
    Region.objects.all().delete()
    SoilType.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_initial_data, remove_initial_data),
    ]
