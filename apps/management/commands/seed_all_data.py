from django.core.management.base import BaseCommand
from apps.users.models import User, AdminUser, CustomerUser, CustomerProfile
from apps.products.models import Category, SubCategory, ProductSection, Product, ProductReview
from apps.promotions.models import Announcement, HeroSlide, PromoCard, PromoBanner
from apps.orders.models import TrustPerk
from apps.marketing.models import NavLink, StoreInfo, FooterColumn, FooterLink

CATEGORIES = [
    {
        "id": "figure",
        "label": "Anime figures",
        "color": "#FF4D6D",
        "icon_type": "figure",
        "featured": True,
        "order": 1,
        "subcategories": [
            { "id": "scale-figures", "label": "1/7 & 1/4 Scale Figures", "slug": "scale-figures", "order": 1 },
            { "id": "action-figures", "label": "Articulated Action Figures", "slug": "action-figures", "order": 2 },
            { "id": "nendoroid", "label": "Chibi & Nendoroid", "slug": "nendoroid", "order": 3 },
            { "id": "limited-editions", "label": "Limited Rare Editions", "slug": "limited-editions", "order": 4 },
        ]
    },
    {
        "id": "toon",
        "label": "Cartoon characters",
        "color": "#7B5CFF",
        "icon_type": "toon",
        "featured": False,
        "order": 2,
        "subcategories": [
            { "id": "retro-toons", "label": "Retro Cartoon Toys", "slug": "retro-toons", "order": 1 },
            { "id": "modern-animation", "label": "Modern Animated Heroes", "slug": "modern-animation", "order": 2 },
            { "id": "mascot-vinyls", "label": "Vinyl Mascots", "slug": "mascot-vinyls", "order": 3 },
        ]
    },
    {
        "id": "brick",
        "label": "Bricks & building sets",
        "color": "#13BFC9",
        "icon_type": "brick",
        "featured": False,
        "order": 3,
        "subcategories": [
            { "id": "space-sci-fi", "label": "Space & Sci-Fi Sets", "slug": "space-sci-fi", "order": 1 },
            { "id": "vehicles-motors", "label": "Vehicles & Pull-Back", "slug": "vehicles-motors", "order": 2 },
            { "id": "castles-medieval", "label": "Castles & Medieval", "slug": "castles-medieval", "order": 3 },
            { "id": "city-architect", "label": "City & Architecture", "slug": "city-architect", "order": 4 },
        ]
    },
    {
        "id": "code",
        "label": "Coding & STEM kits",
        "color": "#FFC93C",
        "icon_type": "code",
        "featured": False,
        "order": 4,
        "subcategories": [
            { "id": "robotics-coding", "label": "Programmable Robots", "slug": "robotics-coding", "order": 1 },
            { "id": "circuit-electronics", "label": "Electronics & Circuits", "slug": "circuit-electronics", "order": 2 },
            { "id": "logic-screen-free", "label": "Screen-Free Logic Kits", "slug": "logic-screen-free", "order": 3 },
            { "id": "drones-aerospace", "label": "DIY STEM Drones", "slug": "drones-aerospace", "order": 4 },
        ]
    },
    {
        "id": "robot",
        "label": "Robotics",
        "color": "#4B7BFF",
        "icon_type": "robot",
        "featured": False,
        "order": 5,
        "subcategories": [
            { "id": "bipedal-bots", "label": "Bipedal Robots", "slug": "bipedal-bots", "order": 1 },
            { "id": "ai-vision-kits", "label": "AI & Computer Vision", "slug": "ai-vision-kits", "order": 2 },
        ]
    },
    {
        "id": "model",
        "label": "Model kits",
        "color": "#FF4D6D",
        "icon_type": "model",
        "featured": False,
        "order": 6,
        "subcategories": [
            { "id": "gundam-mecha", "label": "Mecha & Gunpla", "slug": "gundam-mecha", "order": 1 },
            { "id": "military-aviation", "label": "Aviation & Vehicles", "slug": "military-aviation", "order": 2 },
        ]
    },
    {
        "id": "plush",
        "label": "Plush toys",
        "color": "#FF8A5B",
        "icon_type": "plush",
        "featured": False,
        "order": 7,
        "subcategories": [
            { "id": "giant-plush", "label": "Jumbo Plushies", "slug": "giant-plush", "order": 1 },
            { "id": "keychain-plush", "label": "Keychain Companions", "slug": "keychain-plush", "order": 2 },
        ]
    },
    {
        "id": "statue",
        "label": "Collectible statues",
        "color": "#7B5CFF",
        "icon_type": "statue",
        "featured": False,
        "order": 8,
        "subcategories": [
            { "id": "polystone-statues", "label": "Polystone & Resin", "slug": "polystone-statues", "order": 1 },
            { "id": "busts-dioramas", "label": "Dioramas & Busts", "slug": "busts-dioramas", "order": 2 },
        ]
    },
    {
        "id": "puzzle",
        "label": "Puzzles",
        "color": "#13BFC9",
        "icon_type": "puzzle",
        "featured": False,
        "order": 9,
        "subcategories": [
            { "id": "3d-wooden-puzzles", "label": "3D Mechanical Puzzles", "slug": "3d-wooden-puzzles", "order": 1 },
            { "id": "jigsaw-1000", "label": "1000+ Piece Jigsaws", "slug": "jigsaw-1000", "order": 2 },
        ]
    },
    {
        "id": "game",
        "label": "Board games",
        "color": "#2ECC8F",
        "icon_type": "game",
        "featured": False,
        "order": 10,
        "subcategories": [
            { "id": "strategy-games", "label": "Strategy & TCG", "slug": "strategy-games", "order": 1 },
            { "id": "party-family-games", "label": "Party & Family", "slug": "party-family-games", "order": 2 },
        ]
    },
    {
        "id": "acc",
        "label": "Parts & accessories",
        "color": "#736E9B",
        "icon_type": "acc",
        "featured": False,
        "order": 11,
        "subcategories": [
            { "id": "led-display-cases", "label": "LED Display Cases", "slug": "led-display-cases", "order": 1 },
            { "id": "stand-accessories", "label": "Figure Stands & Brackets", "slug": "stand-accessories", "order": 2 },
        ]
    },
]

SECTIONS = [
    {
        "id": "anime-action-figures",
        "eyebrow": "Collect them all",
        "eyebrow_color": "#FF4D6D",
        "title": "Anime action figures",
        "item_count": "128 items",
        "accent": "#FF4D6D",
        "order": 1,
        "products": [
            {
                "id": "neo-samurai",
                "category": "Anime figures",
                "category_color": "#FF4D6D",
                "subcategory_id": "scale-figures",
                "name": "Neo Samurai",
                "subtitle": "Ronin edition · 1/7 scale",
                "description": "Premium 1/7 scale hand-painted collectible with interchangeable katana accessories.",
                "image": "/images/figure-samurai-red.svg",
                "card_bg": "#FFEAF0",
                "badge": "NEW",
                "badge_color": "#FF4D6D",
                "rating": 4.8,
                "reviews": 128,
                "price": "৳34.99",
                "original_price": "৳46.00",
                "accent": "#FF4D6D",
                "order": 1,
            },
            {
                "id": "mecha-pilot",
                "category": "Anime figures",
                "category_color": "#13BFC9",
                "subcategory_id": "action-figures",
                "name": "Mecha Pilot",
                "subtitle": "Zero deluxe box set",
                "description": "High-articulation collectible figure with LED visor and cockpit display stand.",
                "image": "/images/figure-mecha-teal.svg",
                "card_bg": "#E4F7F8",
                "badge": "HOT",
                "badge_color": "#13BFC9",
                "rating": 4.9,
                "reviews": 94,
                "price": "৳58.00",
                "original_price": None,
                "accent": "#13BFC9",
                "order": 2,
            },
            {
                "id": "sky-ninja",
                "category": "Anime figures",
                "category_color": "#E8A317",
                "subcategory_id": "limited-editions",
                "name": "Sky Ninja",
                "subtitle": "Kage limited colourway",
                "description": "Exclusive gold-edition stealth ninja collectible.",
                "image": "/images/figure-ninja-gold.svg",
                "card_bg": "#FFF4DA",
                "badge": "-25%",
                "badge_color": "#E8A317",
                "rating": 4.6,
                "reviews": 212,
                "price": "৳29.50",
                "original_price": "৳39.00",
                "accent": "#E8A317",
                "order": 3,
            },
            {
                "id": "star-mage",
                "category": "Anime figures",
                "category_color": "#7B5CFF",
                "subcategory_id": "scale-figures",
                "name": "Star Mage",
                "subtitle": "Luna glow-in-the-dark",
                "description": "Special edition glow-in-the-dark mage figure with crystal staff.",
                "image": "/images/figure-mage-purple.svg",
                "card_bg": "#EFE9FF",
                "badge": "LIMITED",
                "badge_color": "#7B5CFF",
                "rating": 4.7,
                "reviews": 76,
                "price": "৳42.00",
                "original_price": None,
                "accent": "#7B5CFF",
                "order": 4,
            },
        ],
    },
    {
        "id": "bricks-building-sets",
        "eyebrow": "Build your world",
        "eyebrow_color": "#13BFC9",
        "title": "Bricks & building sets",
        "item_count": "96 items",
        "accent": "#13BFC9",
        "order": 2,
        "products": [
            {
                "id": "galaxy-station",
                "category": "Building sets",
                "category_color": "#FF4D6D",
                "subcategory_id": "space-sci-fi",
                "name": "Galaxy Station",
                "subtitle": "1,240 pieces · ages 9+",
                "description": "Interstellar orbital station building kit with modular docking pods.",
                "image": "/images/bricks-stack-navy.svg",
                "card_bg": "#FFEAF0",
                "badge": "-20%",
                "badge_color": "#FF4D6D",
                "rating": 4.9,
                "reviews": 341,
                "price": "৳79.99",
                "original_price": "৳99.00",
                "accent": "#FF4D6D",
                "order": 1,
            },
            {
                "id": "speed-racer",
                "category": "Building sets",
                "category_color": "#13BFC9",
                "subcategory_id": "vehicles-motors",
                "name": "Speed Racer",
                "subtitle": "Turbo pull-back kit",
                "description": "Aerodynamic brick supercar featuring high-velocity pull-back motor.",
                "image": "/images/bricks-car-teal.svg",
                "card_bg": "#E4F7F8",
                "badge": "NEW",
                "badge_color": "#13BFC9",
                "rating": 4.5,
                "reviews": 87,
                "price": "৳34.00",
                "original_price": None,
                "accent": "#13BFC9",
                "order": 2,
            },
            {
                "id": "castle-fortress",
                "category": "Building sets",
                "category_color": "#E8A317",
                "subcategory_id": "castles-medieval",
                "name": "Castle Fortress",
                "subtitle": "860 pieces · 4 minifigs",
                "description": "Medieval stronghold kit with working drawbridge and catapults.",
                "image": "/images/bricks-castle-navy.svg",
                "card_bg": "#FFF4DA",
                "badge": "HOT",
                "badge_color": "#E8A317",
                "rating": 4.8,
                "reviews": 156,
                "price": "৳64.50",
                "original_price": "৳82.00",
                "accent": "#E8A317",
                "order": 3,
            },
            {
                "id": "micro-city",
                "category": "Building sets",
                "category_color": "#7B5CFF",
                "subcategory_id": "city-architect",
                "name": "Micro City",
                "subtitle": "Starter blocks · ages 5+",
                "description": "Colourful city layout starter block set for young builders.",
                "image": "/images/bricks-city-navy.svg",
                "card_bg": "#EFE9FF",
                "badge": "SALE",
                "badge_color": "#7B5CFF",
                "rating": 4.4,
                "reviews": 203,
                "price": "৳24.99",
                "original_price": "৳32.00",
                "accent": "#7B5CFF",
                "order": 4,
            },
        ],
    },
    {
        "id": "coding-stem-kits",
        "eyebrow": "Learn by playing",
        "eyebrow_color": "#7B5CFF",
        "title": "Coding & STEM kits",
        "item_count": "54 items",
        "accent": "#7B5CFF",
        "order": 3,
        "products": [
            {
                "id": "robo-coder",
                "category": "Coding kits",
                "category_color": "#FF4D6D",
                "subcategory_id": "robotics-coding",
                "name": "Robo Coder",
                "subtitle": "Starter robot · block coding",
                "description": "Hands-on programmable rover with drag-and-drop visual coding app.",
                "image": "/images/robot-teal.svg",
                "card_bg": "#FFEAF0",
                "badge": "TOP",
                "badge_color": "#FF4D6D",
                "rating": 4.9,
                "reviews": 118,
                "price": "৳89.00",
                "original_price": None,
                "accent": "#FF4D6D",
                "order": 1,
            },
            {
                "id": "circuit-lab",
                "category": "Coding kits",
                "category_color": "#13BFC9",
                "subcategory_id": "circuit-electronics",
                "name": "Circuit Lab",
                "subtitle": "40 build-along projects",
                "description": "Safe snap-together electronic modules for lights, sensors, and sound.",
                "image": "/images/robot-pink.svg",
                "card_bg": "#E4F7F8",
                "badge": "-23%",
                "badge_color": "#13BFC9",
                "rating": 4.6,
                "reviews": 264,
                "price": "৳49.99",
                "original_price": "৳65.00",
                "accent": "#13BFC9",
                "order": 2,
            },
            {
                "id": "pixel-bot",
                "category": "Coding kits",
                "category_color": "#E8A317",
                "subcategory_id": "logic-screen-free",
                "name": "Pixel Bot",
                "subtitle": "Screen-free logic toy",
                "description": "Tangible algorithmic puzzle bot for early computational thinking.",
                "image": "/images/robot-gold.svg",
                "card_bg": "#FFF4DA",
                "badge": "NEW",
                "badge_color": "#E8A317",
                "rating": 4.7,
                "reviews": 62,
                "price": "৳39.00",
                "original_price": None,
                "accent": "#E8A317",
                "order": 3,
            },
            {
                "id": "drone-builder",
                "category": "Coding kits",
                "category_color": "#7B5CFF",
                "subcategory_id": "drones-aerospace",
                "name": "Drone Builder",
                "subtitle": "Python-ready STEM edition",
                "description": "Build and code your own quadcopter with Python and auto-hover.",
                "image": "/images/robot-purple.svg",
                "card_bg": "#EFE9FF",
                "badge": "PRO",
                "badge_color": "#7B5CFF",
                "rating": 4.8,
                "reviews": 45,
                "price": "৳119.00",
                "original_price": "৳139.00",
                "accent": "#7B5CFF",
                "order": 4,
            },
        ],
    },
]

TRUST_PERKS = [
    {
        "title": "Free delivery over ৳500",
        "subtitle": "Australia-wide, 2–4 days",
        "icon_type": "truck",
        "color": "#FF4D6D",
        "order": 1,
    },
    {
        "title": "7-day easy returns",
        "subtitle": "Unopened boxes, no fuss",
        "icon_type": "return",
        "color": "#13BFC9",
        "order": 2,
    },
    {
        "title": "100% authentic stock",
        "subtitle": "Licensed importers only",
        "icon_type": "shield",
        "color": "#7B5CFF",
        "order": 3,
    },
    {
        "title": "Secure checkout",
        "subtitle": "Card, PayPal, Afterpay",
        "icon_type": "card",
        "color": "#FFC93C",
        "order": 4,
    },
]

NAV_LINKS = [
    { "label": "Home", "url": "/", "is_active": True, "is_hot": False, "order": 1 },
    { "label": "Shop all", "url": "/shop", "is_active": False, "is_hot": False, "order": 2 },
    { "label": "Anime figures", "url": "/category/figure", "is_active": False, "is_hot": False, "order": 3 },
    { "label": "Cartoon toys", "url": "/category/toon", "is_active": False, "is_hot": False, "order": 4 },
    { "label": "Bricks & sets", "url": "/category/brick", "is_active": False, "is_hot": False, "order": 5 },
    { "label": "Deals", "url": "/deals", "is_active": False, "is_hot": True, "order": 6 },
    { "label": "Blog", "url": "/blog", "is_active": False, "is_hot": False, "order": 7 },
]

FOOTER_COLUMNS = [
    {
        "title": "Shop",
        "order": 1,
        "links": ["Anime figures", "Cartoon toys", "Brick sets", "Coding kits", "New arrivals"]
    },
    {
        "title": "Support",
        "order": 2,
        "links": ["Help centre", "Delivery info", "Returns policy", "Track my order", "FAQ"]
    },
    {
        "title": "Company",
        "order": 3,
        "links": ["About us", "Careers", "Blog", "Affiliates", "Contact"]
    }
]

class Command(BaseCommand):
    help = "Seed all database models across users, products, promotions, orders, and marketing apps"

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Seeding Users (Admin & Customer Roles) ---")
        admin_user, _ = AdminUser.objects.update_or_create(
            email="admin@brickverse.com",
            defaults={
                "first_name": "Brickverse",
                "last_name": "Administrator",
                "role": User.ROLE_ADMIN,
                "is_staff": True,
                "is_superuser": True,
            }
        )
        admin_user.set_password("admin1234")
        admin_user.save()

        customer_user, _ = CustomerUser.objects.update_or_create(
            email="alex@example.com",
            defaults={
                "first_name": "Alex",
                "last_name": "Miller",
                "phone": "+61 400 123 456",
                "role": User.ROLE_CUSTOMER,
                "is_staff": False,
                "is_superuser": False,
            }
        )
        customer_user.set_password("customer1234")
        customer_user.save()
        CustomerProfile.objects.filter(user=customer_user).update(
            loyalty_points=350,
            tier="Silver"
        )
        self.stdout.write(self.style.SUCCESS("Created Admin User (admin@brickverse.com) and Customer User (alex@example.com)."))

        self.stdout.write("--- Seeding Products, Categories & Subcategories ---")
        total_subcategories = 0
        for cat_data in CATEGORIES:
            subcats = cat_data.pop("subcategories", [])
            category, _ = Category.objects.update_or_create(id=cat_data["id"], defaults=cat_data)
            for sub_data in subcats:
                SubCategory.objects.update_or_create(
                    id=sub_data["id"],
                    defaults={**sub_data, "category": category}
                )
                total_subcategories += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(CATEGORIES)} categories and {total_subcategories} subcategories."))

        for sec_data in SECTIONS:
            products_data = sec_data.pop("products")
            section, _ = ProductSection.objects.update_or_create(id=sec_data["id"], defaults=sec_data)
            for prod_data in products_data:
                subcat_id = prod_data.pop("subcategory_id", None)
                subcategory = SubCategory.objects.filter(id=subcat_id).first() if subcat_id else None
                p, _ = Product.objects.update_or_create(
                    id=prod_data["id"],
                    defaults={**prod_data, "section": section, "subcategory": subcategory}
                )
                if not p.reviews_list.exists():
                    ProductReview.objects.create(
                        product=p,
                        author_name="Alex M.",
                        rating=5,
                        comment=f"Incredible quality! Exceeded my expectations for {p.name}."
                    )
        self.stdout.write(self.style.SUCCESS("Seeded sections, products with subcategories, and sample reviews."))

        self.stdout.write("--- Seeding Promotions ---")
        Announcement.objects.update_or_create(
            id=1,
            defaults={
                "message": "Free delivery over ৳500",
                "highlight_message": "Code BUILD10 saves you 10% on your first order",
                "coupon_code": "BUILD10",
                "is_active": True,
            }
        )

        HeroSlide.objects.update_or_create(
            id=1,
            defaults={
                "badge_text": "✦ New season drop",
                "title": "Build your own universe.",
                "highlight_word": "universe.",
                "subtitle": "Anime figures, cartoon collectibles, brick sets & coding kits — shipped in 48h.",
                "primary_btn_text": "Shop now",
                "primary_btn_url": "/shop",
                "secondary_btn_text": "Explore sets",
                "secondary_btn_url": "/shop/bricks",
                "discount_badge": "40% OFF TODAY",
                "image": "/images/figure-samurai-red.svg",
                "slide_number": "01 / 03",
                "order": 1,
                "is_active": True,
            }
        )

        PromoCard.objects.update_or_create(
            id=1,
            defaults={
                "card_type": "new_arrivals",
                "badge_text": "New arrivals",
                "title": "Anime figure collection",
                "highlight_word": "collection",
                "subtitle": "Limited runs · From ৳2,499",
                "button_text": "Shop now",
                "button_url": "/category/figure",
                "image": "/images/figure-newarrivals.svg",
                "has_timer": False,
                "gradient_type": "purple",
                "order": 1,
                "is_active": True,
            }
        )

        PromoCard.objects.update_or_create(
            id=2,
            defaults={
                "card_type": "deal_of_the_week",
                "badge_text": "Deal of the week",
                "title": "Up to 40% off brick sets",
                "highlight_word": "",
                "subtitle": "",
                "button_text": "Grab deal",
                "button_url": "/deals",
                "image": "/images/bricks-stack-navy.svg",
                "has_timer": True,
                "timer_days": "02",
                "timer_hours": "14",
                "timer_minutes": "36",
                "timer_seconds": "09",
                "gradient_type": "yellow",
                "order": 2,
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
                "button_url": "/shop/bundles",
                "image_left": "/images/bricks-stack-sunny.svg",
                "image_right": "/images/toon-mascot.svg",
                "is_active": True,
            }
        )
        self.stdout.write(self.style.SUCCESS("Seeded all promotion banners & slides."))

        self.stdout.write("--- Seeding Orders & Trust Perks ---")
        for perk_data in TRUST_PERKS:
            TrustPerk.objects.update_or_create(
                title=perk_data["title"],
                defaults=perk_data
            )
        self.stdout.write(self.style.SUCCESS("Seeded trust perks."))

        self.stdout.write("--- Seeding Marketing & Navigation ---")
        for nav_data in NAV_LINKS:
            NavLink.objects.update_or_create(label=nav_data["label"], defaults=nav_data)

        StoreInfo.objects.update_or_create(
            id=1,
            defaults={
                "name": "Brickverse",
                "tagline": "figures · bricks · code kits",
                "phone": "1800 246 010",
                "email": "hi@brickverse.com.au",
                "address": "14 Maribyrnong St, Footscray VIC 3011",
                "about_text": "Authentic anime figures, cartoon collectibles, brick sets and coding kits. Shipping Australia-wide from our Melbourne warehouse since 2019.",
                "facebook_url": "https://facebook.com",
                "instagram_url": "https://instagram.com",
                "linkedin_url": "https://linkedin.com",
                "youtube_url": "https://youtube.com",
            }
        )

        for col_data in FOOTER_COLUMNS:
            links = col_data.pop("links")
            col, _ = FooterColumn.objects.update_or_create(title=col_data["title"], defaults=col_data)
            for i, l in enumerate(links, start=1):
                FooterLink.objects.update_or_create(column=col, label=l, defaults={"order": i})

        self.stdout.write(self.style.SUCCESS("Successfully seeded all users, subcategories, products, and marketing data!"))
