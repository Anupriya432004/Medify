from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def test_empty_registration_submission_shows_required_field_errors(self):
        response = self.client.post(reverse("users:register"), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertTrue(response.context["form"].is_bound)

    def test_registration_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "newpatient",
                "password1": "SafePassword_123",
                "password2": "SafePassword_123",
                "next": "/",
            },
        )

        self.assertRedirects(response, "/")
        self.assertTrue(User.objects.filter(username="newpatient").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_page_is_available(self):
        response = self.client.get(reverse("users:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log In")

    def test_logout_button_and_logout_flow(self):
        user = User.objects.create_user(
            username="signedinpatient", password="SafePassword_123"
        )
        self.client.force_login(user)

        response = self.client.get("/")
        self.assertContains(response, "Log Out")
        self.assertContains(response, reverse("users:logout"))

        response = self.client.post(reverse("users:logout"))

        self.assertRedirects(response, "/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_guest_cannot_create_order(self):
        response = self.client.post(reverse("create_order"))

        self.assertEqual(response.status_code, 401)
        self.assertJSONEqual(
            response.content,
            {"success": False, "error": "Please log in to place an order."},
        )
