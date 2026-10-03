CATEGORIES = ["Roads", "Drainage", "Waste management", "Water supply", "Streetlights", "Public safety", "Other"]
URGENCIES = ["High", "Medium", "Low"]
STATUSES = ["Submitted", "Assigned", "In Progress", "Resolved"]

DEPARTMENT_BY_CATEGORY = {
    "Roads": "Road Maintenance",
    "Drainage": "Drainage & Sewerage",
    "Waste management": "Sanitation",
    "Water supply": "Water Services",
    "Streetlights": "Electrical Maintenance",
    "Public safety": "Public Safety",
    "Other": "General Municipal Services",
}

# Demo areas with illustrative coordinates. Replace with your city's real list, or with a geocoder later.
AREAS = {
    "Madina Town": (31.418, 73.112),
    "People's Colony": (31.4265, 73.092),
    "D Ground": (31.421, 73.077),
    "Susan Road": (31.405, 73.115),
    "Gulberg": (31.438, 73.129),
}
