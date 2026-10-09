from django.core.management import call_command
from django.test import TestCase

from medicines.models import Medicine


class SeedMedicinesTests(TestCase):
    def test_seed_medicines_creates_default_catalog(self):
        call_command("seed_medicines")

        self.assertGreater(Medicine.objects.count(), 0)
