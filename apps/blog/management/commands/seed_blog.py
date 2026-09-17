import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.blog.models import Category, Tag, BlogPost, ContentBlock
from apps.users.models import User
from apps.products.models import Product

ASSETS_DIR = os.path.join(settings.BASE_DIR, "blog_seed_assets")
DEST_MEDIA_DIR = os.path.join(settings.MEDIA_ROOT, "blog")
os.makedirs(DEST_MEDIA_DIR, exist_ok=True)


def _sync_image(filename):
    """Copy one bundled seed asset (backend/blog_seed_assets/<filename>) into
    media/blog/ and return the relative /media/ path the frontend's
    getMediaUrl() understands. Assets are committed to the repo (unlike raw
    project source images) so this also works from a fresh production
    container with no other files present."""
    src = os.path.join(ASSETS_DIR, filename)
    dst = os.path.join(DEST_MEDIA_DIR, filename)
    if os.path.exists(src):
        shutil.copy2(src, dst)
    return f"/media/blog/{filename}"


POSTS = [
    {
        "title": "Inside the Studio: How We Pick Every Anime Figure",
        "excerpt": "A look behind the curtain at how Brickverse sources, inspects and grades every figure before it reaches your shelf.",
        "category": "Behind the Scenes",
        "tags": ["anime-figures", "guide"],
        "featured_image": "naruto3.jpg",
        "blocks": [
            ("heading", {"text": "Sourcing starts long before the box arrives", "level": 2}),
            ("text", {
                "text": (
                    "Every figure in the Brickverse catalog goes through the same three checks: sculpt "
                    "accuracy against the official reference art, paint-line consistency, and joint "
                    "durability after a hundred pose cycles.\n\n"
                    "Our team works directly with licensed importers rather than grey-market resellers, "
                    "which is slower and pricier but means what you see in photos is exactly what ships."
                ),
            }),
            ("image", {"url": _sync_image("naruto1.jpg"), "caption": "First-pass quality check on a new shipment.", "alt": "Anime figure quality check"}),
            ("text", {"text": "Once a batch clears inspection, it moves to our Melbourne warehouse for the final photography pass you see on every product page."}),
            ("gallery", {"images": [
                {"url": _sync_image("naruto2.jpg"), "caption": "Detail pass"},
                {"url": _sync_image("naruto4.jpg"), "caption": "Pose test"},
                {"url": _sync_image("aot1.jpg"), "caption": "Packaging check"},
                {"url": _sync_image("aot2.jpg"), "caption": "Studio lighting"},
            ]}),
            ("quote", {"text": "If it wouldn't pass our own shelf test, it doesn't go up for sale.", "author": "Brickverse QA Team"}),
            ("button", {"text": "Shop anime figures", "url": "/shop?category=anime-figures", "style": "primary"}),
        ],
    },
    {
        "title": "Brick Building 101: Your First Custom Set",
        "excerpt": "New to brick building? Here's how to plan, buy and build your first custom set without wasting a single piece.",
        "category": "Guides",
        "tags": ["bricks", "guide", "beginners"],
        "featured_image": "houseB_brick.jpg",
        "blocks": [
            ("heading", {"text": "Plan the shape before you buy pieces", "level": 2}),
            ("text", {
                "text": (
                    "The single biggest mistake first-time builders make is buying bricks before sketching "
                    "the build. Spend ten minutes with graph paper first — it saves you from ending up with "
                    "forty of one colour and none of another.\n\n"
                    "Start small: a single-storey house, a simple vehicle, or a two-colour tower is enough "
                    "to learn how our building sets snap together before you commit to a 1,000-piece kit."
                ),
            }),
            ("gallery", {"images": [
                {"url": _sync_image("houseB2_brick.jpg"), "caption": "Starter house build"},
                {"url": _sync_image("houseB3_brick.jpg"), "caption": "Roof detail"},
                {"url": _sync_image("houseS_brick.jpg"), "caption": "Smaller starter kit"},
                {"url": _sync_image("car1.jpg"), "caption": "Vehicle build"},
                {"url": _sync_image("car3.jpg"), "caption": "Vehicle, alt angle"},
                {"url": _sync_image("car5.jpg"), "caption": "Finished vehicle set"},
            ]}),
            ("divider", {"style": "dots"}),
            ("heading", {"text": "Sort before you build", "level": 3}),
            ("text", {"text": "Tip most beginners skip: sort loose bricks by colour first, not by shape. It cuts build time roughly in half once a set gets past 200 pieces."}),
            ("image", {"url": _sync_image("houseB4_brick.jpg"), "caption": "A finished custom build from our community.", "alt": "Finished brick house build"}),
            ("button", {"text": "Explore bricks & sets", "url": "/shop?category=bricks-building-sets", "style": "outline"}),
        ],
    },
    {
        "title": "Demon Slayer Collection Spotlight",
        "excerpt": "Tanjiro, Nezuko, Zenitsu and more — a closer look at our full Demon Slayer figure lineup and what makes each edition different.",
        "category": "Collection Spotlight",
        "tags": ["anime-figures", "new-arrivals", "demon-slayer"],
        "featured_image": "demon_figure1.jpg",
        "blocks": [
            ("heading", {"text": "A lineup five years in the making", "level": 2}),
            ("text", {"text": "Demon Slayer remains one of our most requested lines, and this season's restock brings back three previously sold-out sculpts alongside two brand-new limited colourways."}),
            ("gallery", {"images": [
                {"url": _sync_image("demon_figure2.jpg"), "caption": "Tanjiro — Water Breathing pose"},
                {"url": _sync_image("demon_figure3.jpg"), "caption": "Nezuko — box form"},
                {"url": _sync_image("demon_figure4.jpg"), "caption": "Zenitsu — Thunder Breathing"},
                {"url": _sync_image("demon_figure5.jpg"), "caption": "Inosuke — beast mask"},
                {"url": _sync_image("demon_figure6.jpg"), "caption": "Giyu — limited colourway"},
                {"url": _sync_image("demonf01.jpg"), "caption": "Full set, shelf display"},
            ]}),
            ("quote", {"text": "The Giyu colourway sold through its first restock in under six hours last time — we've doubled the run this round.", "author": "Brickverse Merchandising"}),
            ("text", {"text": "Every figure ships in a magnetic-close display box, so you can keep it sealed for resale value or displayed straight out of the box."}),
            ("button", {"text": "View the full lineup", "url": "/shop?category=anime-figures", "style": "primary"}),
        ],
    },
    {
        "title": "5 Coding Kits That Make STEM Actually Fun",
        "excerpt": "Screen-free logic toys, block-coding robots and Python-ready kits — five picks for kids who'd rather build than watch.",
        "category": "Guides",
        "tags": ["coding-kits", "stem", "guide"],
        "featured_image": "steampunk_figure.jpg",
        "blocks": [
            ("heading", {"text": "Start screen-free, graduate to code", "level": 2}),
            ("text", {
                "text": (
                    "The kits that stick around longest in a kid's room aren't the flashiest ones — they're "
                    "the ones with a clear next step. Start with a screen-free logic toy, move to block "
                    "coding, and only then introduce a text-based language like Python.\n\n"
                    "Below are five kits from our Coding & STEM range, ordered roughly by age and difficulty."
                ),
            }),
            ("image", {"url": _sync_image("jjk1.jpg"), "caption": "Weekend build session at one of our workshop meet-ups.", "alt": "Kids building a coding kit"}),
            ("text", {"text": "Robo Coder and Pixel Bot are our two best beginner sellers, while Drone Builder is aimed squarely at kids already comfortable with block coding and ready for real Python."}),
            ("product_grid", {"title": "Coding & STEM picks", "productIds": []}),
            ("button", {"text": "Browse coding kits", "url": "/shop?category=coding-kits", "style": "outline"}),
        ],
    },
    {
        "title": "One Piece Fan Guide: Luffy, Zoro & the Crew",
        "excerpt": "A collector's guide to our One Piece lineup, from Luffy's Gear Fifth pose to the Straw Hat brick-built pirate ship.",
        "category": "Collection Spotlight",
        "tags": ["anime-figures", "one-piece", "bricks"],
        "featured_image": "luffy.jpg",
        "blocks": [
            ("heading", {"text": "The crew, one figure at a time", "level": 2}),
            ("text", {"text": "We've slowly built out a full Straw Hat crew across the last three restocks — this guide rounds up every figure and brick set currently in stock, plus what's coming next quarter."}),
            ("gallery", {"images": [
                {"url": _sync_image("onepiece1.jpg"), "caption": "Luffy — Gear Fifth"},
                {"url": _sync_image("onepiece2.jpg"), "caption": "Crew lineup, shelf display"},
                {"url": _sync_image("onepiece3.jpg"), "caption": "Detail shot"},
                {"url": _sync_image("zoro_brick.jpg"), "caption": "Zoro brick-built figure"},
                {"url": _sync_image("sanji_brick.jpg"), "caption": "Sanji brick-built figure"},
            ]}),
            ("divider", {"style": "line"}),
            ("text", {"text": "The brick-built crew (Zoro, Sanji, and soon Nami) are designed to click onto the same base plate as our pirate ship set, so the whole crew can display together."}),
            ("quote", {"text": "We get more custom display photos from the One Piece line than any other collection — keep tagging us, we love seeing the builds.", "author": "Brickverse Community Team"}),
        ],
    },
    {
        "title": "New Arrivals: This Season's Drop",
        "excerpt": "A first look at everything landing in the warehouse this month, from restocked favourites to brand-new brick sets.",
        "category": "Store News",
        "tags": ["new-arrivals", "store-news"],
        "featured_image": "store3.jpg",
        "blocks": [
            ("heading", {"text": "What's new this month", "level": 2}),
            ("text", {"text": "Between restocks and genuinely new sculpts, this is one of our biggest drops of the year. Here's a walk-through of what just landed on the shelves."}),
            ("gallery", {"images": [
                {"url": _sync_image("store1.jpg"), "caption": "Warehouse floor, new stock"},
                {"url": _sync_image("store5.jpg"), "caption": "Unboxing station"},
                {"url": _sync_image("shop2.jpg"), "caption": "Front of store display"},
                {"url": _sync_image("shop4.jpg"), "caption": "New arrivals shelf"},
            ]}),
            ("text", {"text": "As always, restocked figures are limited to the quantity we received — once a batch sells out, it may not come back until next quarter's shipment."}),
            ("button", {"text": "Shop new arrivals", "url": "/shop", "style": "primary"}),
        ],
    },
    {
        "title": "Jujutsu Kaisen Restock: Gojo, Sukuna & the Squad",
        "excerpt": "Our biggest Jujutsu Kaisen restock yet lands this week — here's what's back in stock and what's brand new.",
        "category": "Collection Spotlight",
        "tags": ["anime-figures", "jujutsu-kaisen", "new-arrivals"],
        "featured_image": "gojo.jpg",
        "blocks": [
            ("heading", {"text": "The squad is finally back in stock", "level": 2}),
            ("text", {"text": "Gojo has been our single most-requested restock for two quarters running. This drop also brings two sculpts that have never been in the Australian market before."}),
            ("gallery", {"images": [
                {"url": _sync_image("jjk2.jpg"), "caption": "Domain Expansion pose"},
                {"url": _sync_image("jjk3.jpg"), "caption": "Detail shot"},
                {"url": _sync_image("jjk_figuree.jpg"), "caption": "Full set, shelf display"},
                {"url": _sync_image("demonf02.jpg"), "caption": "Side-by-side scale comparison"},
            ]}),
            ("quote", {"text": "We ordered triple our usual run this time — last restock sold out in under an hour.", "author": "Brickverse Merchandising"}),
            ("button", {"text": "Shop anime figures", "url": "/shop?category=anime-figures", "style": "primary"}),
        ],
    },
    {
        "title": "Pokémon Corner: Building Our Starter Lineup",
        "excerpt": "How we chose the first five Pokémon in our new collectibles corner, and what's coming next.",
        "category": "Collection Spotlight",
        "tags": ["pokemon", "new-arrivals"],
        "featured_image": "pokemon1.jpg",
        "blocks": [
            ("heading", {"text": "Starting small, on purpose", "level": 2}),
            ("text", {"text": "Rather than launch with fifty figures at once, we picked five fan favourites to gauge demand before committing to a full line. All five sold through their first batch in the first week."}),
            ("gallery", {"images": [
                {"url": _sync_image("pokemon2.jpg"), "caption": "Starter lineup, shelf display"},
                {"url": _sync_image("pokemon3.jpg"), "caption": "Detail shot"},
                {"url": _sync_image("pokemon4.jpg"), "caption": "Packaging"},
                {"url": _sync_image("pokemon5.jpg"), "caption": "Full set"},
            ]}),
            ("text", {"text": "Based on how quickly this corner sold through, we're expanding to a full 20-figure lineup next quarter — sign up to our newsletter to get first access."}),
            ("button", {"text": "Shop all figures", "url": "/shop?category=anime-figures", "style": "outline"}),
        ],
    },
    {
        "title": "Doraemon & Friends: Cartoon Corner Restock",
        "excerpt": "The Cartoon Corner restock is here — Doraemon and the full cast are back on shelves after months of being sold out.",
        "category": "Store News",
        "tags": ["cartoon-toys", "new-arrivals"],
        "featured_image": "doremon1.jpg",
        "blocks": [
            ("heading", {"text": "The most-requested restock of the year", "level": 2}),
            ("text", {"text": "Doraemon has been out of stock since our first shipment sold through in under a week. This restock triples our previous order size, plus adds two characters we've never carried before."}),
            ("gallery", {"images": [
                {"url": _sync_image("doremon2.jpg"), "caption": "Full cast, shelf display"},
                {"url": _sync_image("doremon3.jpg"), "caption": "Detail shot"},
                {"url": _sync_image("doremon4.jpg"), "caption": "Packaging"},
                {"url": _sync_image("doremon5.jpg"), "caption": "Character close-up"},
                {"url": _sync_image("doremon6.jpg"), "caption": "Full lineup"},
            ]}),
            ("button", {"text": "Shop cartoon toys", "url": "/shop?category=cartoon-characters", "style": "primary"}),
        ],
    },
    {
        "title": "Brick-Built Icons: When Marvel Meets Anime",
        "excerpt": "Our brick-built crossover line puts Iron Man, Deadpool and Venom on the same shelf as Goku, Tanjiro and Zenitsu.",
        "category": "Collection Spotlight",
        "tags": ["bricks", "new-arrivals"],
        "featured_image": "ironman_brick.jpg",
        "blocks": [
            ("heading", {"text": "One shelf, two universes", "level": 2}),
            ("text", {"text": "The brick-built crossover line started as an experiment — would collectors want Marvel and anime characters displayed side by side, built from the same compatible brick system? The answer, from our sales numbers, is a clear yes."}),
            ("gallery", {"images": [
                {"url": _sync_image("deadpool_brick.jpg"), "caption": "Deadpool, brick-built"},
                {"url": _sync_image("venom_brick.jpg"), "caption": "Venom, brick-built"},
                {"url": _sync_image("goku_brick.jpg"), "caption": "Goku, brick-built"},
                {"url": _sync_image("tanjiro_brick.jpg"), "caption": "Tanjiro, brick-built"},
                {"url": _sync_image("zenitsu_brick.jpg"), "caption": "Zenitsu, brick-built"},
            ]}),
            ("quote", {"text": "Every figure in this line uses the same base plate size, so they all click together on one display shelf regardless of universe.", "author": "Brickverse Product Team"}),
            ("button", {"text": "Explore bricks & sets", "url": "/shop?category=bricks-building-sets", "style": "primary"}),
        ],
    },
]


class Command(BaseCommand):
    help = "Seeds sample blog categories, tags and posts with real images and multi-image galleries."

    def handle(self, *args, **options):
        author = User.objects.filter(role="admin").first()

        deleted, _ = BlogPost.objects.all().delete()
        if deleted:
            self.stdout.write(self.style.WARNING(f"Wiped {deleted} existing blog row(s)."))

        product_ids = list(Product.objects.values_list("id", flat=True)[:4])

        created = 0
        now = timezone.now()

        for i, item in enumerate(POSTS):
            category, _ = Category.objects.get_or_create(name=item["category"])
            tags = []
            for tag_name in item["tags"]:
                tag, _ = Tag.objects.get_or_create(slug=tag_name, defaults={"name": tag_name.replace("-", " ").title()})
                tags.append(tag)

            post = BlogPost.objects.create(
                title=item["title"],
                excerpt=item["excerpt"],
                category=category,
                author=author,
                status="published",
                published_at=now - timedelta(days=(len(POSTS) - i) * 3),
                featured_image=_sync_image(item["featured_image"]).replace("/media/", ""),
            )
            post.tags.set(tags)

            for order, (block_type, data) in enumerate(item["blocks"]):
                if block_type == "product_grid" and not data.get("productIds"):
                    data = {**data, "productIds": product_ids}
                ContentBlock.objects.create(post=post, order=order, block_type=block_type, data=data)

            created += 1
            self.stdout.write(f"  + {post.title}")

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created} blog posts across {Category.objects.count()} categories and {Tag.objects.count()} tags."
        ))
