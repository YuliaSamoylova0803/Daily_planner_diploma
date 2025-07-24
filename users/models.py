from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        unique=True, verbose_name="Электронный адрес", help_text="Введите свою почту"
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(r"^\+?1?\d{9,15}$")],
    )
    city = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Родной город",
        help_text="Введите город, в котором проживаете",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Изображение пользователя",
        help_text="Изображение должно быть квадратным (рекомендуемый размер 200x200)",
    )
    tg_nick = models.CharField(
        max_length=50,
        verbose_name="Ник телеграмм",
        blank=True,
        null=True,
        help_text="Введите ник телеграмм",
    )

    token = models.CharField(
        max_length=100, verbose_name="Token", blank=True, null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "username",
    ]

    def __str__(self):
        return f"{self.username} {self.email})"

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
