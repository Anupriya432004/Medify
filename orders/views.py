import json
from decimal import Decimal

from django.db.models import F, Sum
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from medicines.models import Medicine
from .models import Cart, CartItem, Order, OrderItem


def _cart_count(cart):
    return cart.items.aggregate(total=Sum("quantity"))["total"] or 0


def _cart_data(user_cart):
    items = list(user_cart.items.select_related("medicine").order_by("id"))
    serialized_items = [
        {
            "id": item.id,
            "medicine_id": item.medicine_id,
            "name": item.medicine.name,
            "price": str(item.medicine.price),
            "quantity": item.quantity,
            "subtotal": str(item.medicine.price * item.quantity),
        }
        for item in items
    ]
    total = sum(
        (item.medicine.price * item.quantity for item in items),
        start=Decimal("0.00"),
    )
    return {
        "success": True,
        "cart_count": sum(item.quantity for item in items),
        "items": serialized_items,
        "total": str(total),
    }


@require_http_methods(["GET", "POST", "DELETE"])
def cart(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"success": False, "error": "Please log in to use your cart."},
            status=401,
        )

    if request.method == "GET":
        try:
            user_cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return JsonResponse(
                {"success": True, "cart_count": 0, "items": [], "total": "0.00"}
            )
        return JsonResponse(_cart_data(user_cart))

    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            item_id = data.get("item_id")
            cart_item = CartItem.objects.get(
                id=item_id, cart__user=request.user
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            return JsonResponse(
                {"success": False, "error": "Invalid cart item."}, status=400
            )
        except CartItem.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Cart item was not found."}, status=404
            )

        cart_item.delete()
        user_cart = Cart.objects.get(user=request.user)
        return JsonResponse(_cart_data(user_cart))

    try:
        data = json.loads(request.body)
        medicine_id = data.get("medicine_id")
        medicine = Medicine.objects.get(id=medicine_id, is_active=True)
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse(
            {"success": False, "error": "Invalid medicine selection."}, status=400
        )
    except Medicine.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Medicine is not available."}, status=404
        )

    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(
        cart=user_cart, medicine=medicine, defaults={"quantity": 1}
    )
    if not created:
        CartItem.objects.filter(pk=item.pk).update(quantity=F("quantity") + 1)

    return JsonResponse({"success": True, "cart_count": _cart_count(user_cart)})


@csrf_exempt
def create_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"success": False, "error": "Please log in to place an order."},
            status=401,
        )
    try:
        data = json.loads(request.body)
        med_id = data.get("medicine_id")
        patient_name = data.get("patient_name", "Guest")
        payment_id = data.get("payment_id")

        if data.get("cart_checkout"):
            try:
                with transaction.atomic():
                    user_cart = Cart.objects.select_for_update().get(user=request.user)
                    cart_items = list(
                        user_cart.items.select_related("medicine").order_by("id")
                    )
                    if not cart_items:
                        return JsonResponse(
                            {"success": False, "error": "Your cart is empty."},
                            status=400,
                        )

                    total_amount = sum(
                        (
                            item.medicine.price * item.quantity
                            for item in cart_items
                        ),
                        start=Decimal("0.00"),
                    )
                    order = Order.objects.create(
                        user=request.user,
                        patient_name=patient_name,
                        total_amount=total_amount,
                        razorpay_payment_id=payment_id,
                        is_paid=True,
                    )
                    OrderItem.objects.bulk_create(
                        [
                            OrderItem(
                                order=order,
                                medicine=item.medicine,
                                quantity=item.quantity,
                                price=item.medicine.price,
                            )
                            for item in cart_items
                        ]
                    )
                    user_cart.items.all().delete()
            except Cart.DoesNotExist:
                return JsonResponse(
                    {"success": False, "error": "Your cart is empty."},
                    status=400,
                )
            return JsonResponse({"success": True, "cart_count": 0})

        amount = data.get("amount")
        med = Medicine.objects.get(id=med_id)
        order = Order.objects.create(
            user=request.user,
            patient_name=patient_name,
            total_amount=amount,
            razorpay_payment_id=payment_id,
            is_paid=True,
        )
        OrderItem.objects.create(
            order=order,
            medicine=med,
            quantity=1,
            price=amount,
        )

        try:
            cart_item = CartItem.objects.get(cart__user=request.user, medicine=med)
        except CartItem.DoesNotExist:
            pass
        else:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save(update_fields=["quantity"])
            else:
                cart_item.delete()

        user_cart = Cart.objects.filter(user=request.user).first()
        return JsonResponse(
            {
                "success": True,
                "cart_count": _cart_count(user_cart) if user_cart else 0,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
