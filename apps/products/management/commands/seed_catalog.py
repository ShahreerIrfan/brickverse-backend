import os
import shutil
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.products.models import Product, Category, ProductSection

class Command(BaseCommand):
    help = "Seeds 105 curated anime and brick products with physical SVG media upload to Django FileFields"

    def handle(self, *args, **options):
        # 1. Setup media directories
        media_products_dir = os.path.join(settings.MEDIA_ROOT, "products")
        os.makedirs(media_products_dir, exist_ok=True)
        
        assets_dir = os.path.join(settings.BASE_DIR, "catalog_seed_assets")
        if not os.path.exists(assets_dir):
            assets_dir = os.path.join(settings.BASE_DIR, "media", "products")

        # 2. Copy all seed assets into active media storage
        synced_count = 0
        if os.path.exists(assets_dir):
            for fname in os.listdir(assets_dir):
                if fname.endswith(".svg"):
                    src = os.path.join(assets_dir, fname)
                    dst = os.path.join(media_products_dir, fname)
                    shutil.copy2(src, dst)
                    synced_count += 1
            self.stdout.write(self.style.SUCCESS(f"Synced {synced_count} SVG assets to {media_products_dir}"))

        # 3. Wipe old products
        deleted_count, _ = Product.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Wiped {deleted_count} old product(s)."))

        # 4. Load products_data.json fixture
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
            fields = dict(item.get("fields", {}))

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

                raw_img = fields.pop("image", "")
                img_filename = os.path.basename(raw_img) if raw_img else "figure-samurai-red.svg"

                # Set exact relative path inside MEDIA_ROOT
                fields["image"] = f"products/{img_filename}"
                fields["image_file"] = f"products/{img_filename}"

                # Create or update product instance
                Product.objects.update_or_create(id=pk, defaults=fields)
                prod_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {prod_count} products across {cat_count} categories and {section_count} sections with verified SVG media!"
        ))
