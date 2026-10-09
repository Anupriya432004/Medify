from decimal import Decimal

from django.core.management.base import BaseCommand

from medicines.models import Category, Medicine


class Command(BaseCommand):
    help = "Seed the default medicine catalog used by the storefront"

    def handle(self, *args, **options):
        categories = {
            "Pain Relief": "Pain relief and anti-inflammatory medicines",
            "Cold & Flu": "Cold, flu, and cough medicines",
            "Skin Care": "Skin treatment and topical care",
            "First Aid": "Emergency and basic medical supplies",
            "Diabetes": "Diabetes support and monitoring medicines",
            "Heart Health": "Cardiovascular and heart health products",
        }

        for name, description in categories.items():
            Category.objects.get_or_create(name=name, defaults={"description": description})

        sample_medicines = [
            ("Pain Relief", "Paracetamol 500mg", "Effective fever and pain relief medicine.", Decimal("45.00"), 120),
            ("Pain Relief", "Ibuprofen 200mg", "Reduces inflammation and relieves body pain.", Decimal("78.00"), 90),
            ("Cold & Flu", "Cough Syrup", "Soothes dry cough and throat irritation.", Decimal("120.00"), 80),
            ("Cold & Flu", "Vitamin C Tablets", "Boosts immunity during cold and flu season.", Decimal("95.00"), 100),
            ("Skin Care", "Hydrocortisone Cream", "Helps relieve itchy and inflamed skin.", Decimal("130.00"), 70),
            ("Skin Care", "Antiseptic Ointment", "Protects cuts and minor skin irritations.", Decimal("110.00"), 65),
            ("First Aid", "Bandage Kit", "Basic first aid essentials for home and travel.", Decimal("210.00"), 50),
            ("First Aid", "Antiseptic Lotion", "Disinfects minor wounds and scrapes.", Decimal("140.00"), 60),
            ("Diabetes", "Diabetic Support Tablets", "Supports daily wellness for diabetes management.", Decimal("260.00"), 40),
            ("Diabetes", "Blood Sugar Monitor", "Helps track glucose readings with ease.", Decimal("850.00"), 30),
            ("Heart Health", "Omega 3 Capsules", "Supports heart and cardiovascular health.", Decimal("320.00"), 55),
            ("Heart Health", "Cholesterol Support", "Helps maintain healthy cholesterol levels.", Decimal("290.00"), 48),
        ]

        created = 0
        for category_name, name, description, price, stock in sample_medicines:
            category = Category.objects.get(name=category_name)
            Medicine.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "description": description,
                    "price": price,
                    "stock": stock,
                    "is_active": True,
                },
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} medicines successfully."))
