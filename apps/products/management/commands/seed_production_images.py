import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Seeds active media directory with all catalog and branding SVG/raster assets'

    def handle(self, *args, **options):
        media_img_dir = Path(settings.MEDIA_ROOT) / 'images'
        media_prod_dir = Path(settings.MEDIA_ROOT) / 'products'

        os.makedirs(media_img_dir, exist_ok=True)
        os.makedirs(media_prod_dir, exist_ok=True)

        catalog_assets_dir = Path(settings.BASE_DIR) / 'catalog_seed_assets'
        seed_dir = Path(settings.BASE_DIR) / 'seed_data' / 'images'

        copied_count = 0
        if catalog_assets_dir.exists():
            for f in os.listdir(catalog_assets_dir):
                src = catalog_assets_dir / f
                if src.is_file() and f.endswith('.svg'):
                    shutil.copy2(src, media_prod_dir / f)
                    copied_count += 1
            self.stdout.write(self.style.SUCCESS(f"Synced {copied_count} SVG catalog assets to {media_prod_dir}"))

        if seed_dir.exists():
            for f in os.listdir(seed_dir):
                src = seed_dir / f
                if src.is_file():
                    shutil.copy2(src, media_img_dir / f)
                    shutil.copy2(src, media_prod_dir / f)
            self.stdout.write(self.style.SUCCESS(f"Synced legacy seed images to {media_img_dir}"))
