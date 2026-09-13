import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.products.models import Product, Category, ProductSection

class Command(BaseCommand):
    help = "Deletes existing products and seeds 105 curated anime and brick products with SVG media"

    def handle(self, *args, **options):
        self.stdout.write("Deleting existing products...")
        deleted_count, _ = Product.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing product(s)."))

        fixture_path = os.path.join(settings.BASE_DIR, "products_data.json")
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f"Fixture file not found: {fixture_path}"))
            return

        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        section_count = 0
        cat_count = 0
        prod_count = 0

        for item in data:
            model = item.get("model")
            pk = item.get("pk")
            fields = item.get("fields", {})

            if model == "products.productsection":
                ProductSection.objects.update_or_create(id=pk, defaults=fields)
                section_count += 1
            elif model == "products.category":
                Category.objects.update_or_create(id=pk, defaults=fields)
                cat_count += 1
            elif model == "products.product":
                sec_id = fields.pop("section", None)
                sec_obj = None
                if sec_id:
                    sec_obj = ProductSection.objects.filter(id=sec_id).first()
                fields["section"] = sec_obj
                Product.objects.update_or_create(id=pk, defaults=fields)
                prod_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {prod_count} products across {cat_count} categories and {section_count} sections!"
        ))
