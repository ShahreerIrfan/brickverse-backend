from django.db import migrations
from django.utils.text import slugify


def copy_subcategories_into_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    SubCategory = apps.get_model('products', 'SubCategory')
    Product = apps.get_model('products', 'Product')

    # Existing top-level categories predate the slug field - backfill so
    # every category has one once this app relies on slugs for display.
    for cat in Category.objects.filter(slug=""):
        cat.slug = slugify(cat.label) or cat.id
        cat.save(update_fields=['slug'])

    existing_category_ids = set(Category.objects.values_list('id', flat=True))

    for sub in SubCategory.objects.all().order_by('order', 'label'):
        new_id = sub.id
        if new_id in existing_category_ids:
            # A SubCategory id colliding with an existing top-level Category
            # id (unlikely given the two id schemes, but guarded anyway).
            candidate = f"{sub.category_id}-{sub.id}"
            suffix = 2
            while candidate in existing_category_ids:
                candidate = f"{sub.category_id}-{sub.id}-{suffix}"
                suffix += 1
            new_id = candidate

        parent = Category.objects.filter(id=sub.category_id).first()

        Category.objects.create(
            id=new_id,
            parent=parent,
            label=sub.label,
            slug=sub.slug or slugify(sub.label),
            color=parent.color if parent else "#FF4D6D",
            icon_type="",
            category_icon="",
            featured=False,
            order=sub.order,
            is_active=sub.is_active,
            show_in_mega_menu=False,
            mega_menu_order=0,
        )
        existing_category_ids.add(new_id)

        if new_id != sub.id:
            # Products pointed at the old SubCategory.id; keep that link
            # working by moving them onto the newly-created Category with
            # the id we actually ended up using.
            Product.objects.filter(subcategory_id=sub.id).update(subcategory_id=new_id)


def noop_reverse(apps, schema_editor):
    # Data migration only; nothing safe to undo automatically.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_category_hierarchy'),
    ]

    operations = [
        migrations.RunPython(copy_subcategories_into_categories, noop_reverse),
    ]
