from complaints.services.ai_evaluation_service import (
    EvaluationCase,
)


BENCHMARK_CASES = (
    EvaluationCase(
        name="water_leakage_critical",
        title="Major water pipeline leakage",
        description=(
            "A major water pipeline has burst near a "
            "residential area. Large amounts of water are "
            "flooding the road and nearby properties. The "
            "leak is continuing and immediate intervention "
            "is required to prevent further damage and "
            "protect residents."
        ),
        category_name="Water Leakage",
        expected_priority="CRITICAL",
        expected_urgency=90,
    ),

    EvaluationCase(
        name="road_damage_high",
        title="Large pothole causing road hazard",
        description=(
            "A large and deep pothole has developed on a "
            "busy residential road. Vehicles are having "
            "difficulty passing safely and the damaged road "
            "could cause accidents, especially for "
            "two-wheelers."
        ),
        category_name="Road Damage",
        expected_priority="HIGH",
        expected_urgency=75,
    ),

    EvaluationCase(
        name="garbage_medium",
        title="Garbage accumulation in residential area",
        description=(
            "Garbage has been accumulating for several days "
            "near the residential community. Waste bins are "
            "overflowing and the area needs collection. "
            "The accumulated waste is creating an "
            "unpleasant environment for residents."
        ),
        category_name="Garbage and Waste",
        expected_priority="MEDIUM",
        expected_urgency=55,
    ),

    EvaluationCase(
        name="street_lighting_medium",
        title="Broken street light",
        description=(
            "A street light near a residential road has "
            "stopped working. The road becomes poorly lit "
            "during the night, making it difficult for "
            "pedestrians and vehicles to travel safely."
        ),
        category_name="Street Lighting",
        expected_priority="MEDIUM",
        expected_urgency=50,
    ),

    EvaluationCase(
        name="electricity_high",
        title="Repeated electricity outage",
        description=(
            "The residential area is experiencing repeated "
            "electricity outages. Power is being interrupted "
            "multiple times and the outages are disrupting "
            "daily activities and essential services."
        ),
        category_name="Electricity Supply",
        expected_priority="HIGH",
        expected_urgency=70,
    ),

    EvaluationCase(
        name="sanitation_low",
        title="Drain cleaning required",
        description=(
            "A residential drainage area needs cleaning. "
            "Waste and dirt have accumulated in the drain, "
            "but there is currently no major flooding or "
            "immediate danger to residents."
        ),
        category_name="Sanitation",
        expected_priority="LOW",
        expected_urgency=30,
    ),
)