from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.urls import path, reverse_lazy

from users.apps import UsersConfig
from users.views import RegisterView, edit_profile, email_verification

app_name = UsersConfig.name

urlpatterns = [
    path(
        "login/", LoginView.as_view(template_name="users/login.html"), name="login"
    ),  # надо поменять на home
    path(
        "logout/", LogoutView.as_view(next_page="mailing_service:base"), name="logout"
    ),
    path("register/", RegisterView.as_view(), name="register"),
    path("email_confirm/<str:token>/", email_verification, name="email_confirm"),
    # Password reset URLs
    path(
        "password_reset/",
        PasswordResetView.as_view(
            template_name="users/password_reset_form.html",
            email_template_name="users/password_reset_email.html",
            success_url=reverse_lazy("users:password_reset_done"),
            extra_email_context={"protocol": "http", "domain": "127.0.0.1:8000"},
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url=reverse_lazy("users:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("edit_profile/", login_required(edit_profile), name="edit_profile"),
]
