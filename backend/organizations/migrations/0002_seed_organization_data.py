from django.db import migrations


DEPARTMENTS = [
    {
        "name": "IT Support",
        "description": "Handles network, hardware and software issues.",
    },
    {
        "name": "Maintenance",
        "description": "Handles electrical, plumbing and infrastructure issues.",
    },
    {
        "name": "Hostel",
        "description": "Handles hostel-related complaints.",
    },
    {
        "name": "Transport",
        "description": "Handles transportation-related complaints.",
    },
    {
        "name": "Security",
        "description": "Handles safety and security-related complaints.",
    },
]


CATEGORIES = [
    {
        "department": "IT Support",
        "name": "Wi-Fi",
        "description": "Issues related to Wi-Fi connectivity and internet access.",
    },
    {
        "department": "IT Support",
        "name": "Hardware",
        "description": "Issues related to computers, devices and physical IT equipment.",
    },
    {
        "department": "IT Support",
        "name": "Software",
        "description": "Issues related to software, applications and system errors.",
    },
    {
        "department": "IT Support",
        "name": "Network",
        "description": "Issues related to network connectivity and infrastructure.",
    },
    {
        "department": "Maintenance",
        "name": "Plumbing",
        "description": "Issues related to water pipes, taps, leaks and drainage.",
    },
    {
        "department": "Maintenance",
        "name": "Electrical",
        "description": "Issues related to lights, switches, wiring and electrical equipment.",
    },
    {
        "department": "Maintenance",
        "name": "Furniture",
        "description": "Issues related to desks, chairs, beds and other furniture.",
    },
    {
        "department": "Maintenance",
        "name": "Cleaning",
        "description": "Issues related to cleanliness and sanitation.",
    },
    {
        "department": "Maintenance",
        "name": "Road Damage",
        "description": "Issues related to damaged roads, potholes and unsafe road surfaces.",
    },
    {
        "department": "Maintenance",
        "name": "Street Lighting",
        "description": "Issues related to broken or inadequate street lighting.",
    },
    {
        "department": "Maintenance",
        "name": "Electricity Supply",
        "description": "Issues related to electricity outages and unstable power supply.",
    },
    {
        "department": "Maintenance",
        "name": "Water Leakage",
        "description": "Issues related to water pipeline leakage and major water leaks.",
    },
    {
        "department": "Hostel",
        "name": "Room",
        "description": "Issues related to hostel rooms and room facilities.",
    },
    {
        "department": "Hostel",
        "name": "Food",
        "description": "Issues related to hostel food and dining services.",
    },
    {
        "department": "Hostel",
        "name": "Water",
        "description": "Issues related to hostel water availability or quality.",
    },
    {
        "department": "Hostel",
        "name": "Hostel Maintenance",
        "description": "Maintenance issues specifically affecting hostel facilities.",
    },
    {
        "department": "Hostel",
        "name": "Garbage and Waste",
        "description": "Issues related to garbage accumulation, overflowing bins and waste collection.",
    },
    {
        "department": "Hostel",
        "name": "Sanitation",
        "description": "Issues related to sanitation, drainage and cleanliness.",
    },
    {
        "department": "Transport",
        "name": "Bus",
        "description": "Issues related to college bus services.",
    },
    {
        "department": "Transport",
        "name": "Driver",
        "description": "Complaints related to driver behavior or service.",
    },
    {
        "department": "Transport",
        "name": "Schedule",
        "description": "Issues related to transport schedules and timings.",
    },
    {
        "department": "Transport",
        "name": "Route",
        "description": "Issues related to bus routes and stops.",
    },
    {
        "department": "Security",
        "name": "Unauthorized Access",
        "description": "Reports of unauthorized entry or access.",
    },
    {
        "department": "Security",
        "name": "Lost and Found",
        "description": "Lost items and found-property related complaints.",
    },
    {
        "department": "Security",
        "name": "Safety",
        "description": "General safety and security concerns.",
    },
    {
        "department": "Security",
        "name": "CCTV",
        "description": "Issues related to CCTV cameras and surveillance.",
    },
]


def seed_organization_data(apps, schema_editor):
    Department = apps.get_model("organizations", "Department")
    Category = apps.get_model("organizations", "Category")

    departments = {}

    for item in DEPARTMENTS:
        department, _ = Department.objects.get_or_create(
            name=item["name"],
            defaults={
                "description": item["description"],
                "is_active": True,
            },
        )

        changed = False

        if department.description != item["description"]:
            department.description = item["description"]
            changed = True

        if not department.is_active:
            department.is_active = True
            changed = True

        if changed:
            department.save()

        departments[item["name"]] = department

    for item in CATEGORIES:
        department = departments[item["department"]]

        category, _ = Category.objects.get_or_create(
            department=department,
            name=item["name"],
            defaults={
                "description": item["description"],
                "is_active": True,
            },
        )

        changed = False

        if category.description != item["description"]:
            category.description = item["description"]
            changed = True

        if not category.is_active:
            category.is_active = True
            changed = True

        if changed:
            category.save()


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            seed_organization_data,
            migrations.RunPython.noop,
        ),
    ]