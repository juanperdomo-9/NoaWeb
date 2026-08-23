import os
import secrets

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Crea el superusuario inicial a partir de variables de entorno (no hardcodea la contraseña)."

    def handle(self, *args, **kwargs):

        username = os.environ.get("ADMIN_USERNAME", "admin")
        email = os.environ.get("ADMIN_EMAIL", "")
        password = os.environ.get("ADMIN_PASSWORD")

        if User.objects.filter(username=username).exists():
            self.stdout.write("El superuser ya existe")
            return

        if not password:
            password = secrets.token_urlsafe(16)
            self.stdout.write(self.style.WARNING(
                "ADMIN_PASSWORD no estaba seteada. Se generó una contraseña "
                "temporal, cambiala apenas entres:"
            ))
            self.stdout.write(self.style.WARNING(f"  usuario: {username}"))
            self.stdout.write(self.style.WARNING(f"  contraseña: {password}"))

        User.objects.create_superuser(username, email, password)
        self.stdout.write(self.style.SUCCESS("Superuser creado"))
