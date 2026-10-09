from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def _safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        return next_url
    return "/"


def register(request):
    if request.user.is_authenticated:
        return redirect("/")

    form = UserCreationForm(
        request.POST if request.method == "POST" else None
    )
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect(_safe_next_url(request))

    return render(
        request,
        "users/register.html",
        {"form": form, "next": _safe_next_url(request)},
    )
