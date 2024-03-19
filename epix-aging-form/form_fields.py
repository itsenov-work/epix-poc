from strenum import StrEnum


class FormFields(StrEnum):
    PHYSICAL_ACTIVITY = "Physical-activity"
    SPORTS_OR_EXERCISE = "Sports-or-excercise"
    CIGARETTES = "Cigarettes"
    ALCOHOL = "Alcohol"
    HOURS_OF_SLEEP = "Hours-of-sleep"
    DAILY_DIET = "Daily-diet"
    FRUIT_AND_VEGETABLES = "Fruit-and-vegetables"
    DIAGNOSED = "Diagnosed"
    STRESS_LEVEL = "Stress-Level"
    MEDITATION = "Meditation"
    MENTAL_HEALTH_CONDITION = "Mental-health-condition"
    BLOOD_PRESSURE = "Blood-pressure"
    WELLNESS_PROGRAMS = "Wellness-programs"
    BMI = "BMI"
    WEIGHT = "Weight"
    HEIGHT = "Height"


FIELD_RELATIVE_WEIGHTS = {
    FormFields.PHYSICAL_ACTIVITY: 3,
    FormFields.SPORTS_OR_EXERCISE: 3,
    FormFields.CIGARETTES: 3,
    FormFields.ALCOHOL: 2,
    FormFields.HOURS_OF_SLEEP: 1,
    FormFields.DAILY_DIET: 3,
    FormFields.FRUIT_AND_VEGETABLES: 2,
    FormFields.DIAGNOSED: 3,
    FormFields.STRESS_LEVEL: 4,
    FormFields.MEDITATION: 2,
    FormFields.MENTAL_HEALTH_CONDITION: 3,
    FormFields.BLOOD_PRESSURE: 3,
    FormFields.WELLNESS_PROGRAMS: 2,
    FormFields.BMI: 4,
}

WEIGHTS_AVERAGE = sum(FIELD_RELATIVE_WEIGHTS.values()) / len(FIELD_RELATIVE_WEIGHTS)

FIELD_NORMALIZED_WEIGHTS = {
    k: v / WEIGHTS_AVERAGE
    for k, v in FIELD_RELATIVE_WEIGHTS.items()
}

