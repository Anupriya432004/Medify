import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from medicines.models import Category, Medicine
from .models import Cart, CartItem, Order, OrderItem


class CartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cartpatient", password="SafePassword_123"
        )
        self.category = Category.objects.create(name="Pain relief")
        self.medicine = Medicine.objects.create(
            category=self.category,
            name="Pain Relief Tablet",
            description="Test medicine",
            price="10.00",
            stock=10,
        )
        self.cart_url = reverse("cart")

    def test_adding_medicine_updates_persisted_cart_count(self):
        self.client.force_login(self.user)

        first_response = self.client.post(
            self.cart_url,
            data=json.dumps({"medicine_id": self.medicine.id}),
            content_type="application/json",
        )
        second_response = self.client.post(
            self.cart_url,
            data=json.dumps({"medicine_id": self.medicine.id}),
            content_type="application/json",
        )
        count_response = self.client.get(self.cart_url)

        self.assertEqual(first_response.json()["cart_count"], 1)
        self.assertEqual(second_response.json()["cart_count"], 2)
        self.assertEqual(count_response.json()["cart_count"], 2)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(
            CartItem.objects.get(cart=cart, medicine=self.medicine).quantity, 2
        )

    def test_guest_cannot_add_to_cart(self):
        response = self.client.post(
            self.cart_url,
            data=json.dumps({"medicine_id": self.medicine.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Cart.objects.exists())

    def test_cart_details_include_items_quantities_and_total(self):
        self.client.force_login(self.user)
        self.client.post(
            self.cart_url,
            data=json.dumps({"medicine_id": self.medicine.id}),
            content_type="application/json",
        )

        cart_item = CartItem.objects.get(cart__user=self.user)
        details_response = self.client.get(self.cart_url)
        payload = details_response.json()

        self.assertEqual(payload["cart_count"], 1)
        self.assertEqual(payload["total"], "10.00")
        self.assertEqual(
            payload["items"],
            [
                {
                    "id": cart_item.id,
                    "medicine_id": self.medicine.id,
                    "name": self.medicine.name,
                    "price": "10.00",
                    "quantity": 1,
                    "subtotal": "10.00",
                }
            ],
        )

    def test_removing_cart_item_updates_saved_cart_and_count(self):
        self.client.force_login(self.user)
        self.client.post(
            self.cart_url,
            data=json.dumps({"medicine_id": self.medicine.id}),
            content_type="application/json",
        )
        cart_item = CartItem.objects.get(cart__user=self.user)

        response = self.client.delete(
            self.cart_url,
            data=json.dumps({"item_id": cart_item.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["cart_count"], 0)
        self.assertEqual(response.json()["items"], [])
        self.assertEqual(response.json()["total"], "0.00")
        self.assertFalse(CartItem.objects.filter(pk=cart_item.pk).exists())

    def test_user_cannot_remove_another_users_cart_item(self):
        other_user = User.objects.create_user(
            username="anotherpatient", password="SafePassword_123"
        )
        other_cart = Cart.objects.create(user=other_user)
        other_item = CartItem.objects.create(
            cart=other_cart, medicine=self.medicine, quantity=1
        )
        self.client.force_login(self.user)

        response = self.client.delete(
            self.cart_url,
            data=json.dumps({"item_id": other_item.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(CartItem.objects.filter(pk=other_item.pk).exists())

    def test_cart_checkout_creates_order_for_all_items_and_clears_cart(self):
        self.client.force_login(self.user)
        user_cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=user_cart, medicine=self.medicine, quantity=2
        )
        second_medicine = Medicine.objects.create(
            category=self.category,
            name="Cold Relief Tablet",
            description="Another test medicine",
            price="5.50",
            stock=10,
        )
        CartItem.objects.create(
            cart=user_cart, medicine=second_medicine, quantity=3
        )

        response = self.client.post(
            reverse("create_order"),
            data=json.dumps(
                {
                    "cart_checkout": True,
                    "patient_name": "Test Patient",
                    "payment_id": "pay_test_cart",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "cart_count": 0})
        order = Order.objects.get(user=self.user)
        self.assertEqual(str(order.total_amount), "36.50")
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(
            {
                item.medicine.name: item.quantity
                for item in order.items.all()
            },
            {"Pain Relief Tablet": 2, "Cold Relief Tablet": 3},
        )
        self.assertFalse(user_cart.items.exists())

    def test_cart_checkout_rejects_empty_cart(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("create_order"),
            data=json.dumps({"cart_checkout": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Your cart is empty.")
        self.assertFalse(Order.objects.exists())

# Create your tests here.
