from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.products.models import Category, SubCategory, ProductSection, Product, ProductGalleryImage, ProductReview
from apps.users.models import CustomerProfile
from apps.orders.models import TrustPerk
from apps.promotions.models import HeroSlide, PromoCard, PromoBanner, Announcement

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds database with parent categories, child categories, users, products, sections, and promotions.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("==> Starting database seeding..."))

        # =========================================================================
        # 1. SEED USERS (Admin & Customer with First Name & Last Name)
        # =========================================================================
        self.stdout.write("1. Seeding users...")
        users_data = [
            {
                "email": "admin@gmail.com",
                "first_name": "Admin",
                "last_name": "User",
                "role": "admin",
                "password": "Admin1234!",
                "phone": "+8801700000001",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "admin@brickverse.com",
                "first_name": "Brickverse",
                "last_name": "Administrator",
                "role": "admin",
                "password": "Admin1234!",
                "phone": "+8801700000002",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "customer@gmail.com",
                "first_name": "MD",
                "last_name": "Wahid",
                "role": "customer",
                "password": "User1234!",
                "phone": "+8801800000001",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "alex@example.com",
                "first_name": "Alex",
                "last_name": "Miller",
                "role": "customer",
                "password": "User1234!",
                "phone": "+8801800000002",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "lisa_fan@brickverse.com",
                "first_name": "Lisa",
                "last_name": "Wong",
                "role": "customer",
                "password": "User1234!",
                "phone": "+8801800000003",
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        for u_data in users_data:
            user, _ = User.objects.get_or_create(
                email=u_data["email"],
                defaults={
                    "first_name": u_data["first_name"],
                    "last_name": u_data["last_name"],
                    "role": u_data["role"],
                    "phone": u_data["phone"],
                    "is_staff": u_data["is_staff"],
                    "is_superuser": u_data["is_superuser"],
                    "is_verified": True,
                }
            )
            user.first_name = u_data["first_name"]
            user.last_name = u_data["last_name"]
            user.role = u_data["role"]
            user.phone = u_data["phone"]
            user.is_staff = u_data["is_staff"]
            user.is_superuser = u_data["is_superuser"]
            user.set_password(u_data["password"])
            user.save()

            if user.role == "customer":
                CustomerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "shipping_address": "House 12, Road 4, Banani, Dhaka, Bangladesh",
                        "billing_address": "House 12, Road 4, Banani, Dhaka, Bangladesh",
                        "loyalty_points": 350,
                        "tier": "VIP Gold",
                    }
                )
            self.stdout.write(f"   [+] User: {user.first_name} {user.last_name} ({user.email}) [{user.role}]")

        # =========================================================================
        # 2. SEED PARENT CATEGORIES
        # =========================================================================
        self.stdout.write("2. Seeding parent categories...")
        categories_data = [
            {"id": "figure", "label": "Anime figures", "color": "#FF4D6D", "icon_type": "figure", "featured": True, "order": 1},
            {"id": "brick", "label": "Bricks & building sets", "color": "#13BFC9", "icon_type": "brick", "featured": True, "order": 2},
            {"id": "code", "label": "Coding & STEM kits", "color": "#7B5CFF", "icon_type": "code", "featured": True, "order": 3},
            {"id": "toon", "label": "Cartoon characters", "color": "#FFC93C", "icon_type": "toon", "featured": False, "order": 4},
            {"id": "robot", "label": "Robotics", "color": "#4B7BFF", "icon_type": "robot", "featured": False, "order": 5},
            {"id": "model", "label": "Model kits", "color": "#FF4D6D", "icon_type": "model", "featured": False, "order": 6},
            {"id": "plush", "label": "Plush & Toys", "color": "#FF8A5B", "icon_type": "plush", "featured": False, "order": 7},
            {"id": "statue", "label": "Collectible statues", "color": "#7B5CFF", "icon_type": "statue", "featured": False, "order": 8},
        ]

        cat_objs = {}
        for c in categories_data:
            cat_obj, _ = Category.objects.update_or_create(
                id=c["id"],
                defaults={
                    "label": c["label"],
                    "color": c["color"],
                    "icon_type": c["icon_type"],
                    "featured": c["featured"],
                    "order": c["order"],
                }
            )
            cat_objs[c["id"]] = cat_obj
            self.stdout.write(f"   [+] Category: {cat_obj.label}")

        # =========================================================================
        # 3. SEED CHILD CATEGORIES (SubCategories)
        # =========================================================================
        self.stdout.write("3. Seeding child categories (SubCategories)...")
        subcategories_data = [
            # Under Anime figures
            {"id": "scale-figures", "category": cat_objs["figure"], "label": "Scale Figures (1/7 & 1/8)", "slug": "scale-figures", "description": "High-detail hand-painted anime scale statues and figures", "order": 1},
            {"id": "deluxe-sets", "category": cat_objs["figure"], "label": "Deluxe Collector Sets", "slug": "deluxe-sets", "description": "Numbered box sets with exclusive diorama bases", "order": 2},
            {"id": "limited-editions", "category": cat_objs["figure"], "label": "Limited Edition Releases", "slug": "limited-editions", "description": "Rare variant colorways and festival exclusive figures", "order": 3},

            # Under Bricks & building sets
            {"id": "space-architecture", "category": cat_objs["brick"], "label": "Space & Sci-Fi Architecture", "slug": "space-architecture", "description": "Futuristic orbital stations, starships, and lunar bases", "order": 1},
            {"id": "vehicles-speed", "category": cat_objs["brick"], "label": "Vehicles & Turbo Racers", "slug": "vehicles-speed", "description": "Aerodynamic brick cars with functioning pull-back motors", "order": 2},
            {"id": "medieval-castles", "category": cat_objs["brick"], "label": "Medieval Castles & Forts", "slug": "medieval-castles", "description": "Modular fortresses with minifigures and siege weapons", "order": 3},
            {"id": "city-modulars", "category": cat_objs["brick"], "label": "City Architecture & Skylines", "slug": "city-modulars", "description": "Modern urban micro-cities with LED street lighting kits", "order": 4},

            # Under Coding & STEM kits
            {"id": "programmable-bots", "category": cat_objs["code"], "label": "Programmable Robot Kits", "slug": "programmable-bots", "description": "Scratch and Python compatible coding rovers", "order": 1},
            {"id": "circuits-electronics", "category": cat_objs["code"], "label": "Circuit & Sensor Labs", "slug": "circuits-electronics", "description": "Snap-on electronic modules and logic gates", "order": 2},
            {"id": "logic-puzzles", "category": cat_objs["code"], "label": "Screen-free Logic Toys", "slug": "logic-puzzles", "description": "Tangible algorithms and marble-powered puzzle solvers", "order": 3},
            {"id": "drones-robotics", "category": cat_objs["code"], "label": "STEM Drone Builders", "slug": "drones-robotics", "description": "Quadcopter kits with gyro-stabilized flight controllers", "order": 4},
        ]

        subcat_objs = {}
        for sc in subcategories_data:
            subcat_obj, _ = SubCategory.objects.update_or_create(
                id=sc["id"],
                defaults={
                    "category": sc["category"],
                    "label": sc["label"],
                    "slug": sc["slug"],
                    "description": sc["description"],
                    "order": sc["order"],
                    "is_active": True,
                }
            )
            subcat_objs[sc["id"]] = subcat_obj
            self.stdout.write(f"   [+] SubCategory: {subcat_obj.label} -> {sc['category'].label}")

        # =========================================================================
        # 4. SEED PRODUCT SECTIONS
        # =========================================================================
        self.stdout.write("4. Seeding homepage product sections...")
        sections_data = [
            {
                "id": "anime-action-figures",
                "eyebrow": "Collect them all",
                "eyebrow_color": "#FF4D6D",
                "title": "Anime action figures",
                "item_count": "128 items",
                "accent": "#FF4D6D",
                "order": 1,
            },
            {
                "id": "bricks-building-sets",
                "eyebrow": "Build your world",
                "eyebrow_color": "#13BFC9",
                "title": "Bricks & building sets",
                "item_count": "96 items",
                "accent": "#13BFC9",
                "order": 2,
            },
            {
                "id": "coding-stem-kits",
                "eyebrow": "Learn by playing",
                "eyebrow_color": "#7B5CFF",
                "title": "Coding & STEM kits",
                "item_count": "54 items",
                "accent": "#7B5CFF",
                "order": 3,
            },
        ]

        section_objs = {}
        for s in sections_data:
            sec_obj, _ = ProductSection.objects.update_or_create(
                id=s["id"],
                defaults={
                    "eyebrow": s["eyebrow"],
                    "eyebrow_color": s["eyebrow_color"],
                    "title": s["title"],
                    "item_count": s["item_count"],
                    "accent": s["accent"],
                    "order": s["order"],
                    "is_active": True,
                }
            )
            section_objs[s["id"]] = sec_obj
            self.stdout.write(f"   [+] Section: {sec_obj.title}")

        # =========================================================================
        # 5. SEED PRODUCTS (Using Frontend SVG Images)
        # =========================================================================
        self.stdout.write("5. Seeding products...")
        products_data = [
            # --- SECTION 1: Anime Figures ---
            {
                "id": "neo-samurai",
                "slug": "neo-samurai",
                "sku": "BV-SAMURAI-1001",
                "section": section_objs["anime-action-figures"],
                "category": "Anime figures",
                "category_color": "#FF4D6D",
                "subcategory": subcat_objs["scale-figures"],
                "name": "Neo Samurai",
                "description": "Premium 1/7 scale Ronin edition warrior crafted with ultra-fine vinyl sculpting, dual katana blades, and dynamic battle stance posture.",
                "image": "/images/figure-samurai-red.svg",
                "card_bg": "#FFEAF0",
                "rating": 4.8,
                "reviews": 128,
                "regular_price": "৳46.00",
                "discounted_price": "৳34.99",
                "trade_price": "৳25.00",
                "discount_percent": 24,
                "stock": 45,
                "accent": "#FF4D6D",
                "order": 1,
            },
            {
                "id": "mecha-pilot",
                "slug": "mecha-pilot",
                "sku": "BV-MECHA-1002",
                "section": section_objs["anime-action-figures"],
                "category": "Anime figures",
                "category_color": "#13BFC9",
                "subcategory": subcat_objs["deluxe-sets"],
                "name": "Mecha Pilot",
                "description": "Zero deluxe collector box set with metallic flight armor, interchangeable visor helmet, and magnetic launchpad stand.",
                "image": "/images/figure-mecha-teal.svg",
                "card_bg": "#E4F7F8",
                "rating": 4.9,
                "reviews": 94,
                "regular_price": "৳58.00",
                "discounted_price": "৳58.00",
                "trade_price": "৳42.00",
                "discount_percent": 0,
                "stock": 30,
                "accent": "#13BFC9",
                "order": 2,
            },
            {
                "id": "sky-ninja",
                "slug": "sky-ninja",
                "sku": "BV-NINJA-1003",
                "section": section_objs["anime-action-figures"],
                "category": "Anime figures",
                "category_color": "#E8A317",
                "subcategory": subcat_objs["limited-editions"],
                "name": "Sky Ninja",
                "description": "Kage limited gold colourway with aerodynamic grappling gear, smoke bomb canisters, and golden kunai holster.",
                "image": "/images/figure-ninja-gold.svg",
                "card_bg": "#FFF4DA",
                "rating": 4.6,
                "reviews": 212,
                "regular_price": "৳39.00",
                "discounted_price": "৳29.50",
                "trade_price": "৳20.00",
                "discount_percent": 24,
                "stock": 60,
                "accent": "#E8A317",
                "order": 3,
            },
            {
                "id": "star-mage",
                "slug": "star-mage",
                "sku": "BV-MAGE-1004",
                "section": section_objs["anime-action-figures"],
                "category": "Anime figures",
                "category_color": "#7B5CFF",
                "subcategory": subcat_objs["limited-editions"],
                "name": "Star Mage",
                "description": "Luna glow-in-the-dark mystic edition featuring crystal staff, UV-reactive astral cloak, and starry display base.",
                "image": "/images/figure-mage-purple.svg",
                "card_bg": "#EFE9FF",
                "rating": 4.7,
                "reviews": 76,
                "regular_price": "৳42.00",
                "discounted_price": "৳42.00",
                "trade_price": "৳30.00",
                "discount_percent": 0,
                "stock": 25,
                "accent": "#7B5CFF",
                "order": 4,
            },
            {
                "id": "shinobi-dx",
                "slug": "shinobi-dx",
                "sku": "BV-SHINOBI-1005",
                "section": section_objs["anime-action-figures"],
                "category": "Anime figures",
                "category_color": "#FF4D6D",
                "subcategory": subcat_objs["scale-figures"],
                "name": "Shinobi Ronin DX",
                "description": "Master series Ronin with articulated fabric scarf, dual tanto blades, and cherry blossom autumn base.",
                "image": "/images/figure-newarrivals.svg",
                "card_bg": "#FFF1F4",
                "rating": 4.9,
                "reviews": 53,
                "regular_price": "৳52.00",
                "discounted_price": "৳39.99",
                "trade_price": "৳28.00",
                "discount_percent": 23,
                "stock": 40,
                "accent": "#FF4D6D",
                "order": 5,
            },

            # --- SECTION 2: Bricks & Building Sets ---
            {
                "id": "galaxy-station",
                "slug": "galaxy-station",
                "sku": "BV-GALAXY-2001",
                "section": section_objs["bricks-building-sets"],
                "category": "Building sets",
                "category_color": "#FF4D6D",
                "subcategory": subcat_objs["space-architecture"],
                "name": "Galaxy Orbital Station",
                "description": "1,240 piece orbital science laboratory with rotating solar panels, airlock modules, and 4 astronaut minifigs.",
                "image": "/images/bricks-stack-navy.svg",
                "card_bg": "#FFEAF0",
                "rating": 4.9,
                "reviews": 341,
                "regular_price": "৳99.00",
                "discounted_price": "৳79.99",
                "trade_price": "৳55.00",
                "discount_percent": 19,
                "stock": 20,
                "accent": "#FF4D6D",
                "order": 1,
            },
            {
                "id": "speed-racer",
                "slug": "speed-racer",
                "sku": "BV-RACER-2002",
                "section": section_objs["bricks-building-sets"],
                "category": "Building sets",
                "category_color": "#13BFC9",
                "subcategory": subcat_objs["vehicles-speed"],
                "name": "Cyber Turbo Racer",
                "description": "High-velocity supercar kit with high-torque pull-back gearbox, aero diffuser, and custom decal racing livery.",
                "image": "/images/bricks-car-teal.svg",
                "card_bg": "#E4F7F8",
                "rating": 4.5,
                "reviews": 87,
                "regular_price": "৳34.00",
                "discounted_price": "৳34.00",
                "trade_price": "৳22.00",
                "discount_percent": 0,
                "stock": 75,
                "accent": "#13BFC9",
                "order": 2,
            },
            {
                "id": "castle-fortress",
                "slug": "castle-fortress",
                "sku": "BV-CASTLE-2003",
                "section": section_objs["bricks-building-sets"],
                "category": "Building sets",
                "category_color": "#E8A317",
                "subcategory": subcat_objs["medieval-castles"],
                "name": "Royal Castle Fortress",
                "description": "860 piece fortress complete with working drawbridge, dungeon trapdoors, knight armory, and king's banner tower.",
                "image": "/images/bricks-castle-navy.svg",
                "card_bg": "#FFF4DA",
                "rating": 4.8,
                "reviews": 156,
                "regular_price": "৳82.00",
                "discounted_price": "৳64.50",
                "trade_price": "৳45.00",
                "discount_percent": 21,
                "stock": 35,
                "accent": "#E8A317",
                "order": 3,
            },
            {
                "id": "micro-city",
                "slug": "micro-city",
                "sku": "BV-CITY-2004",
                "section": section_objs["bricks-building-sets"],
                "category": "Building sets",
                "category_color": "#7B5CFF",
                "subcategory": subcat_objs["city-modulars"],
                "name": "Neo Tokyo Micro City",
                "description": "Modular skyscraper skyline with LED light-strip channels, monorail track, and detailed micro-scale billboards.",
                "image": "/images/bricks-city-navy.svg",
                "card_bg": "#EFE9FF",
                "rating": 4.4,
                "reviews": 203,
                "regular_price": "৳32.00",
                "discounted_price": "৳24.99",
                "trade_price": "৳16.00",
                "discount_percent": 22,
                "stock": 50,
                "accent": "#7B5CFF",
                "order": 4,
            },
            {
                "id": "dragon-citadel",
                "slug": "dragon-citadel",
                "sku": "BV-DRAGON-2005",
                "section": section_objs["bricks-building-sets"],
                "category": "Building sets",
                "category_color": "#FF4D6D",
                "subcategory": subcat_objs["medieval-castles"],
                "name": "Mythic Dragon Citadel",
                "description": "Epic 1,500 piece volcano citadel with posable fire dragon, lava moat, and treasure vault chamber.",
                "image": "/images/bricks-stack-purple.svg",
                "card_bg": "#FFEAF0",
                "rating": 4.9,
                "reviews": 188,
                "regular_price": "৳110.00",
                "discounted_price": "৳89.00",
                "trade_price": "৳60.00",
                "discount_percent": 19,
                "stock": 18,
                "accent": "#FF4D6D",
                "order": 5,
            },

            # --- SECTION 3: Coding & STEM Kits ---
            {
                "id": "robo-coder",
                "slug": "robo-coder",
                "sku": "BV-ROBO-3001",
                "section": section_objs["coding-stem-kits"],
                "category": "Coding kits",
                "category_color": "#FF4D6D",
                "subcategory": subcat_objs["programmable-bots"],
                "name": "Robo Coder Alpha",
                "description": "Beginner friendly programmable educational rover equipped with ultrasonic obstacle sensors, line tracking, and Scratch block coding.",
                "image": "/images/robot-teal.svg",
                "card_bg": "#FFEAF0",
                "rating": 4.9,
                "reviews": 118,
                "regular_price": "৳89.00",
                "discounted_price": "৳89.00",
                "trade_price": "৳62.00",
                "discount_percent": 0,
                "stock": 35,
                "accent": "#FF4D6D",
                "order": 1,
            },
            {
                "id": "circuit-lab",
                "slug": "circuit-lab",
                "sku": "BV-CIRCUIT-3002",
                "section": section_objs["coding-stem-kits"],
                "category": "Coding kits",
                "category_color": "#13BFC9",
                "subcategory": subcat_objs["circuits-electronics"],
                "name": "Circuit Lab Matrix 40",
                "description": "40 hands-on snap circuits with illuminated LEDs, light meters, alarm buzzer modules, and sound amplifiers.",
                "image": "/images/robot-pink.svg",
                "card_bg": "#E4F7F8",
                "rating": 4.6,
                "reviews": 264,
                "regular_price": "৳65.00",
                "discounted_price": "৳49.99",
                "trade_price": "৳35.00",
                "discount_percent": 23,
                "stock": 45,
                "accent": "#13BFC9",
                "order": 2,
            },
            {
                "id": "pixel-bot",
                "slug": "pixel-bot",
                "sku": "BV-PIXEL-3003",
                "section": section_objs["coding-stem-kits"],
                "category": "Coding kits",
                "category_color": "#E8A317",
                "subcategory": subcat_objs["logic-puzzles"],
                "name": "Pixel Bot Logic Trainer",
                "description": "Screen-free computational thinking logic toy featuring 60 challenge puzzle cards and mechanical sequence runner.",
                "image": "/images/robot-gold.svg",
                "card_bg": "#FFF4DA",
                "rating": 4.7,
                "reviews": 62,
                "regular_price": "৳39.00",
                "discounted_price": "৳39.00",
                "trade_price": "৳26.00",
                "discount_percent": 0,
                "stock": 55,
                "accent": "#E8A317",
                "order": 3,
            },
            {
                "id": "drone-builder",
                "slug": "drone-builder",
                "sku": "BV-DRONE-3004",
                "section": section_objs["coding-stem-kits"],
                "category": "Coding kits",
                "category_color": "#7B5CFF",
                "subcategory": subcat_objs["drones-robotics"],
                "name": "Sky Drone Python STEM",
                "description": "Python-ready buildable quadcopter drone with barometric altitude hold, 720p Wi-Fi camera, and crash-resistant propeller guards.",
                "image": "/images/robot-purple.svg",
                "card_bg": "#EFE9FF",
                "rating": 4.8,
                "reviews": 45,
                "regular_price": "৳139.00",
                "discounted_price": "৳119.00",
                "trade_price": "৳85.00",
                "discount_percent": 14,
                "stock": 20,
                "accent": "#7B5CFF",
                "order": 4,
            },
            {
                "id": "bucky-mascot",
                "slug": "bucky-mascot",
                "sku": "BV-MASCOT-4001",
                "section": section_objs["anime-action-figures"],
                "category": "Cartoon characters",
                "category_color": "#FFC93C",
                "subcategory": subcat_objs["limited-editions"],
                "name": "Bucky Brickverse Mascot",
                "description": "Official Brickverse collectible vinyl mascot figure with smiling visor face and golden star trophy.",
                "image": "/images/toon-mascot.svg",
                "card_bg": "#FFF9E6",
                "rating": 5.0,
                "reviews": 89,
                "regular_price": "৳25.00",
                "discounted_price": "৳19.99",
                "trade_price": "৳12.00",
                "discount_percent": 20,
                "stock": 100,
                "accent": "#FFC93C",
                "order": 6,
            },
        ]

        for p_data in products_data:
            prod, _ = Product.objects.update_or_create(
                id=p_data["id"],
                defaults={
                    "slug": p_data["slug"],
                    "sku": p_data["sku"],
                    "section": p_data["section"],
                    "category": p_data["category"],
                    "category_color": p_data["category_color"],
                    "subcategory": p_data["subcategory"],
                    "name": p_data["name"],
                    "description": p_data["description"],
                    "image": p_data["image"],
                    "card_bg": p_data["card_bg"],
                    "rating": p_data["rating"],
                    "reviews": p_data["reviews"],
                    "regular_price": p_data["regular_price"],
                    "discounted_price": p_data["discounted_price"],
                    "trade_price": p_data["trade_price"],
                    "discount_percent": p_data["discount_percent"],
                    "stock": p_data["stock"],
                    "price": p_data["discounted_price"],
                    "original_price": p_data["regular_price"],
                    "accent": p_data["accent"],
                    "order": p_data["order"],
                    "is_active": True,
                }
            )

            # Seed gallery images
            ProductGalleryImage.objects.filter(product=prod).delete()
            ProductGalleryImage.objects.create(product=prod, image_url=prod.image, order=1)
            ProductGalleryImage.objects.create(product=prod, image_url="/images/figure-samurai-red.svg", order=2)
            ProductGalleryImage.objects.create(product=prod, image_url="/images/bricks-stack-navy.svg", order=3)

            # Seed sample reviews
            ProductReview.objects.filter(product=prod).delete()
            ProductReview.objects.create(
                product=prod,
                author_name="MD Wahid",
                rating=5,
                comment="Incredible build quality! The materials feel super premium and shipping was super fast."
            )
            ProductReview.objects.create(
                product=prod,
                author_name="Alex Miller",
                rating=5,
                comment="Very satisfied with this item. Exactly matches the description and looks stunning on display."
            )

            self.stdout.write(f"   [+] Product: {prod.name} ({prod.sku}) [Stock: {prod.stock}]")

        # =========================================================================
        # 6. SEED PROMOTIONS & TRUST PERKS
        # =========================================================================
        self.stdout.write("6. Seeding trust perks and promotions...")
        trust_perks_data = [
            {"icon_type": "truck", "title": "Next-Day Delivery", "subtitle": "Dispatched within 24h across BD", "order": 1},
            {"icon_type": "shield", "title": "100% Genuine Bricks", "subtitle": "Official licensed collector sets", "order": 2},
            {"icon_type": "refresh", "title": "30-Day Free Returns", "subtitle": "Hassle-free replacement guarantee", "order": 3},
            {"icon_type": "card", "title": "VIP Collector Club", "subtitle": "Earn points on every purchase", "order": 4},
        ]
        for tp in trust_perks_data:
            TrustPerk.objects.update_or_create(
                title=tp["title"],
                defaults={"icon_type": tp["icon_type"], "subtitle": tp["subtitle"], "order": tp["order"]}
            )

        HeroSlide.objects.update_or_create(
            id=1,
            defaults={
                "badge_text": "NEW SEASON DROP",
                "title": "Build your own universe.",
                "highlight_word": "universe.",
                "subtitle": "Anime figures, cartoon collectibles, brick sets & coding kits - shipped in 48h.",
                "primary_btn_text": "Shop now",
                "primary_btn_url": "/",
                "secondary_btn_text": "Explore sets",
                "secondary_btn_url": "/",
                "discount_badge": "40% OFF TODAY",
                "image": "/images/figure-samurai-red.svg",
                "slide_number": "01 / 03",
                "order": 1,
                "is_active": True,
            }
        )

        Announcement.objects.update_or_create(
            id=1,
            defaults={
                "message": "Free delivery over ৳500 across Bangladesh",
                "highlight_message": "Code BUILD10 saves you 10% on your first order",
                "coupon_code": "BUILD10",
                "is_active": True,
            }
        )

        PromoBanner.objects.update_or_create(
            id=1,
            defaults={
                "badge_text": "Weekend bundle",
                "title": "Buy any two brick sets, get a mini figure free",
                "subtitle": "Mix and match across bricks, robotics and STEM kits. Ends Sunday 11:59pm.",
                "button_text": "Shop bundle",
                "button_url": "/",
                "image_left": "/images/bricks-stack-sunny.svg",
                "image_right": "/images/toon-mascot.svg",
                "is_active": True,
            }
        )

        self.stdout.write(self.style.SUCCESS("==> Database seeding completed successfully!"))

