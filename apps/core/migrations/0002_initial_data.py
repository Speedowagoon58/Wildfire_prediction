from django.db import migrations


def add_initial_data(apps, schema_editor):
    SoilType = apps.get_model("core", "SoilType")
    Region = apps.get_model("core", "Region")

    # Create soil types
    clay = SoilType.objects.create(
        name="Clay",
        description="Dense soil with high water retention and low drainage",
        fire_risk_factor=0.8,
        moisture_retention=0.8,
        organic_matter=5.0,
    )

    sandy = SoilType.objects.create(
        name="Sandy",
        description="Loose soil with low water retention and high drainage",
        fire_risk_factor=1.2,
        moisture_retention=0.3,
        organic_matter=2.0,
    )

    loam = SoilType.objects.create(
        name="Loam",
        description="Balanced soil with moderate water retention and drainage",
        fire_risk_factor=1.0,
        moisture_retention=0.6,
        organic_matter=4.0,
    )

    # Create regions
    Region.objects.create(
        name="Atlas Mountains",
        latitude=31.5,
        longitude=-6.5,
        elevation=2500,
        area=100000,
        population=500000,
        soil_type=clay,
        vegetation_density=0.7,
        climate_zone="mediterranean",
        description="Mountain range spanning Morocco with diverse ecosystems",
    )

    Region.objects.create(
        name="Rif Region",
        latitude=35.0,
        longitude=-5.0,
        elevation=1500,
        area=20000,
        population=300000,
        soil_type=loam,
        vegetation_density=0.8,
        climate_zone="mediterranean",
        description="Northern coastal region with Mediterranean climate",
    )

    Region.objects.create(
        name="Anti-Atlas",
        latitude=29.7,
        longitude=-8.8,
        elevation=2000,
        area=75000,
        population=200000,
        soil_type=sandy,
        vegetation_density=0.4,
        climate_zone="semi_arid",
        description="Southern mountain range bordering the Sahara",
    )

    Region.objects.create(
        name="Middle Atlas",
        latitude=33.0,
        longitude=-5.0,
        elevation=2000,
        area=23000,
        population=400000,
        soil_type=loam,
        vegetation_density=0.6,
        climate_zone="mediterranean",
        description="Central mountain range with diverse vegetation",
    )


def remove_initial_data(apps, schema_editor):
    SoilType = apps.get_model("core", "SoilType")
    Region = apps.get_model("core", "Region")
    SoilType.objects.all().delete()
    Region.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_initial_data, remove_initial_data),
    ]
