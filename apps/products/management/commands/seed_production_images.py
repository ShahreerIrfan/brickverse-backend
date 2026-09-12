import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.products.models import Product

PRODUCT_IMAGE_MAPPING = {
    'galaxy-station': 'bricks-stack-purple.svg',
    'neo-samurai': 'figure-samurai-red.svg',
    'circuit-lab': 'robot-purple.svg',
    'mecha-pilot': 'figure-mecha-teal.svg',
    'speed-racer': 'bricks-car-teal.svg',
    'sky-ninja': 'figure-ninja-gold.svg',
    'pixel-bot': 'robot-gold.svg',
    'castle-fortress': 'bricks-castle-navy.svg',
    'star-mage': 'figure-mage-purple.svg',
    'micro-city': 'bricks-city-navy.svg',
    'drone-builder': 'robot-pink.svg',
    'shinobi-dx': 'figure-newarrivals.svg',
    'dragon-citadel': 'bricks-stack-sunny.svg',
    'aero-drone-pro': 'robot-pink.svg',
    'crimson-blade-knight': 'figure-samurai-red.svg',
    'lunar-apollo-lander': 'bricks-stack-purple.svg',
    'smart-rover-ai': 'robot-teal.svg',
    'iot-weather-station': 'robot-purple.svg',
    'cyber-valkyrie-01': 'figure-mecha-teal.svg',
    'hyper-sonic-hypercar': 'bricks-car-teal.svg',
    'imperial-grand-fortress': 'bricks-castle-navy.svg',
    'turing-logic-maze': 'robot-gold.svg',
    'shadow-assassin-kage': 'figure-ninja-gold.svg',
    'astral-sorceress-luna': 'figure-mage-purple.svg',
    'metropolis-skyscraper': 'bricks-city-navy.svg',
    'bionic-robotic-arm': 'robot-teal.svg',
    'solar-bug-micro-bot': 'robot-gold.svg',
    'apex-mecha-striker': 'figure-newarrivals.svg',
    'solar-zenith-hub': 'bricks-stack-sunny.svg',
    'bucky-mascot': 'toon-mascot.svg',
    'robo-coder': 'robot-purple.svg',
    'testing': 'figure-samurai-red.svg',
}

class Command(BaseCommand):
    help = 'Seeds media directory with SVG/raster assets and links products to their image files'

    def handle(self, *args, **options):
        seed_dir = Path(settings.BASE_DIR) / 'seed_data' / 'images'
        media_img_dir = Path(settings.MEDIA_ROOT) / 'images'
        media_prod_dir = Path(settings.MEDIA_ROOT) / 'products'

        os.makedirs(media_img_dir, exist_ok=True)
        os.makedirs(media_prod_dir, exist_ok=True)

        if seed_dir.exists():
            for f in os.listdir(seed_dir):
                src = seed_dir / f
                if src.is_file():
                    shutil.copy2(src, media_img_dir / f)
                    shutil.copy2(src, media_prod_dir / f)
            self.stdout.write(self.style.SUCCESS(f"Copied seed images to {media_img_dir} and {media_prod_dir}"))
        else:
            self.stdout.write(self.style.WARNING(f"Seed dir not found at {seed_dir}"))

        updated_count = 0
        for prod in Product.objects.all():
            current_img = str(prod.image or '')
            target_filename = None

            # 1. Match from explicit mapping
            if prod.id in PRODUCT_IMAGE_MAPPING:
                target_filename = PRODUCT_IMAGE_MAPPING[prod.id]
            # 2. Extract from existing path
            elif current_img:
                clean_name = os.path.basename(current_img)
                if (media_prod_dir / clean_name).exists() or (media_img_dir / clean_name).exists():
                    target_filename = clean_name
            # 3. Default fallback
            if not target_filename:
                target_filename = 'figure-samurai-red.svg'

            prod.image = f"products/{target_filename}"
            prod.save(update_fields=['image'])
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} products with media image paths"))
