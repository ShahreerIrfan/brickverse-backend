import os
import json
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds catalog products, categories, and ensures admin user exists.'

    def handle(self, *args, **options):
        # 1. Check if database has products
        prod_count = Product.objects.count()
        cat_count = Category.objects.count()
        self.stdout.write(f"Current database status: {prod_count} products, {cat_count} categories.")

        fixture_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'catalog_data.json')
        if not os.path.exists(fixture_path):
            fixture_path = '/app/catalog_data.json'

        if (prod_count == 0 or cat_count == 0) and os.path.exists(fixture_path):
            self.stdout.write(self.style.WARNING(f"Loading initial catalog data from {fixture_path}..."))
            try:
                call_command('loaddata', fixture_path)
                self.stdout.write(self.style.SUCCESS(f"Successfully loaded catalog! Now has {Product.objects.count()} products."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error loading fixture: {e}"))

        # 2. Ensure admin users exist
        admin_emails = ['kawaiisubete1@gmail.com', 'test-admin@brickverse.local']
        for email in admin_emails:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': 'Store Admin',
                    'role': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                user.set_password('Admin1234!')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created default admin account: {email} (Password: Admin1234!)"))
            else:
                user.role = 'admin'
                user.is_staff = True
                user.is_superuser = True
                user.save()
