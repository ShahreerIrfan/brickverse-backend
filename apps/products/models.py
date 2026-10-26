import os
import random
import uuid
from django.db import models
from django.utils.text import slugify


ALLOWED_UPLOAD_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}


def _safe_upload_path(folder, filename):
    # Real photos (phone/WhatsApp/camera) routinely have filenames far longer
    # than FileField's 100-char limit, or with spaces/unicode/#, which SVG
    # assets never did. Store under a short sanitized name + random suffix.
    stem, ext = os.path.splitext(os.path.basename(filename))
    clean_ext = ext.strip().lower()
    if clean_ext not in ALLOWED_UPLOAD_EXTENSIONS:
        clean_ext = '.jpg'
    stem = slugify(stem)[:40] or "image"
    return f"{folder}/{stem}-{uuid.uuid4().hex[:8]}{clean_ext}"


def product_image_upload_to(instance, filename):
    return _safe_upload_path("products", filename)


def product_gallery_upload_to(instance, filename):
    return _safe_upload_path("products/gallery", filename)


def category_icon_upload_to(instance, filename):
    return _safe_upload_path("categories/icons", filename)


def category_subtree_ids(root_id):
    """A category's own id plus every descendant's id."""
    ids = {root_id}
    frontier = [root_id]
    while frontier:
        children = list(Category.objects.filter(parent_id__in=frontier).values_list('id', flat=True))
        new_ids = [c for c in children if c not in ids]
        if not new_ids:
            break
        ids.update(new_ids)
        frontier = new_ids
    return ids


class Category(models.Model):
    """A single, self-referential category tree. A category with no parent
    is a top-level category (what the storefront's mega menu and category
    rail show); any category can itself have children, to any depth, via
    the parent field - this replaced the old fixed two-level
    Category/SubCategory split so the admin can nest categories as deep as
    they need (Parent > Subcategory > Sub-subcategory > ...)."""

    id = models.CharField(max_length=100, primary_key=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children', on_delete=models.SET_NULL
    )
    label = models.CharField(max_length=150)
    slug = models.CharField(max_length=150, blank=True)
    color = models.CharField(max_length=20, default="#FF4D6D")
    icon_type = models.CharField(max_length=50, blank=True, help_text="e.g. figure, toon, brick, code")
    category_icon = models.CharField(max_length=500, blank=True, default="", help_text="Category icon name, SVG path, or image URL")
    category_icon_file = models.FileField(upload_to=category_icon_upload_to, max_length=255, blank=True, null=True)
    featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_in_mega_menu = models.BooleanField(default=True, help_text="Show this category in the homepage hero mega menu")
    mega_menu_order = models.IntegerField(default=0, help_text="Display order within the homepage mega menu")
    show_on_homepage = models.BooleanField(default=False, help_text="Show this top-level category as a product section on the homepage")
    homepage_order = models.IntegerField(default=0, help_text="Display order among the homepage category sections")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'label']
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug and self.label:
            self.slug = slugify(self.label)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.parent.label} > {self.label}" if self.parent_id else self.label


class ProductSection(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    eyebrow = models.CharField(max_length=100)
    eyebrow_color = models.CharField(max_length=20, default="#FF4D6D")
    title = models.CharField(max_length=150)
    item_count = models.CharField(max_length=50, default="0 items")
    accent = models.CharField(max_length=20, default="#FF4D6D")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class Product(models.Model):
    id = models.CharField(max_length=150, primary_key=True)
    slug = models.SlugField(max_length=200, blank=True)
    sku = models.CharField(max_length=100, blank=True, null=True)
    section = models.ForeignKey(ProductSection, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=100)
    category_color = models.CharField(max_length=20, default="#FF4D6D")
    subcategory = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=product_image_upload_to, max_length=255, blank=True, null=True)
    image_file = models.ImageField(upload_to=product_image_upload_to, max_length=255, blank=True, null=True)
    card_bg = models.CharField(max_length=20, default="#FFEAF0")
    rating = models.FloatField(default=5.0)
    reviews = models.IntegerField(default=0)
    
    # Pricing & Stock (4 key fields + discount percentage)
    regular_price = models.CharField(max_length=50, blank=True, default="৳0.00")
    discounted_price = models.CharField(max_length=50, blank=True, default="৳0.00")
    trade_price = models.CharField(max_length=50, blank=True, default="৳0.00")
    discount_percent = models.IntegerField(default=0, blank=True)
    stock = models.IntegerField(default=100)

    TYPE_SIMPLE = 'simple'
    TYPE_GROUPED = 'grouped'
    PRODUCT_TYPE_CHOICES = [(TYPE_SIMPLE, 'Simple'), (TYPE_GROUPED, 'Grouped')]
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default=TYPE_SIMPLE)
    
    # Backward compatibility helpers
    price = models.CharField(max_length=50, blank=True, default="৳0.00")
    original_price = models.CharField(max_length=50, blank=True, null=True)
    accent = models.CharField(max_length=20, default="#FF4D6D")
    is_active = models.BooleanField(default=True, verbose_name="Is active", help_text="Designates whether this product is active and visible on the website.")
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        if not self.id:
            self.id = self.slug or f"prod-{random.randint(1000, 9999)}"
        if not self.sku:
            clean_part = slugify(self.name).upper()[:6].replace('-', '') or "PROD"
            self.sku = f"KS-{clean_part}-{random.randint(1000, 9999)}"
            
        # Synchronize regular_price & original_price
        if self.regular_price and self.regular_price != "৳0.00":
            self.original_price = self.regular_price
        elif self.original_price and not self.regular_price:
            self.regular_price = self.original_price
            
        # Synchronize discounted_price & price
        if self.discounted_price and self.discounted_price != "৳0.00":
            self.price = self.discounted_price
        elif self.price and not self.discounted_price:
            self.discounted_price = self.price
            
        # Calculate discount percentage if not manually set
        try:
            reg_clean = float(str(self.regular_price).replace('৳', '').replace(',', '').strip())
            disc_clean = float(str(self.discounted_price).replace('৳', '').replace(',', '').strip())
            if reg_clean > disc_clean > 0:
                self.discount_percent = round(((reg_clean - disc_clean) / reg_clean) * 100)
        except (ValueError, TypeError, ZeroDivisionError):
            pass

        super().save(*args, **kwargs)

    @property
    def is_grouped(self):
        return self.product_type == self.TYPE_GROUPED

    @property
    def available_stock(self):
        """Simple products: their own stock. Grouped products never hold
        stock of their own - how many whole bundles can be sold is limited
        by whichever child product runs out first."""
        if not self.is_grouped:
            return self.stock
        counts = [
            max(0, (item.child.stock or 0) // item.quantity)
            for item in self.group_items.all()
        ]
        return min(counts) if counts else 0

    @property
    def has_lots(self):
        return self.lots.filter(is_active=True).exists()

    @property
    def active_lot(self):
        return self.lots.filter(is_active=True, remaining_quantity__gt=0).order_by('created_at', 'id').first()

    def sync_from_active_lot(self):
        return sync_product_from_active_lot(self)

    def __str__(self):
        return self.name


class ProductLot(models.Model):
    """A batch / lot of inventory for a product, tracking its specific Trade Price
    (TP), MRP / Selling Price, and quantity.
    Sales follow FIFO (First-In, First-Out): stock is deducted from the oldest active lot.
    When an older lot runs out, the product automatically transitions to the next active lot,
    updating the product's active trade price and regular price / MRP.
    """
    product = models.ForeignKey(Product, related_name='lots', on_delete=models.CASCADE)
    lot_number = models.CharField(max_length=100, blank=True, help_text="Lot / Batch identifier (e.g. LOT-20261026-001)")
    trade_price = models.CharField(max_length=50, blank=True, default="৳0.00", help_text="Wholesale / purchase price for this lot")
    mrp = models.CharField(max_length=50, blank=True, default="৳0.00", help_text="Selling price / MRP for this lot")
    discounted_price = models.CharField(max_length=50, blank=True, default="৳0.00", help_text="Discounted selling price for this lot (optional)")
    initial_quantity = models.PositiveIntegerField(default=0, help_text="Initial quantity received in this lot")
    remaining_quantity = models.IntegerField(default=0, help_text="Remaining quantity left to sell in this lot")
    is_active = models.BooleanField(default=True, help_text="Active status of this lot")
    notes = models.TextField(blank=True, default="", help_text="Optional supplier or batch notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at', 'id']
        verbose_name = 'Product Lot'
        verbose_name_plural = 'Product Lots'

    def save(self, *args, **kwargs):
        if not self.lot_number:
            date_str = self.created_at.strftime('%Y%m%d') if self.created_at else ''
            if not date_str:
                from django.utils import timezone
                date_str = timezone.now().strftime('%Y%m%d')
            rand_suffix = random.randint(100, 999)
            self.lot_number = f"LOT-{date_str}-{rand_suffix}"

        # Standardize price formatting
        if self.trade_price and not str(self.trade_price).startswith('৳') and str(self.trade_price).strip():
            self.trade_price = f"৳{self.trade_price.strip()}"
        if self.mrp and not str(self.mrp).startswith('৳') and str(self.mrp).strip():
            self.mrp = f"৳{self.mrp.strip()}"
        if self.discounted_price and not str(self.discounted_price).startswith('৳') and str(self.discounted_price).strip():
            self.discounted_price = f"৳{self.discounted_price.strip()}"

        if self.remaining_quantity <= 0:
            self.remaining_quantity = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lot_number} for {self.product.name} (Remaining: {self.remaining_quantity}/{self.initial_quantity})"


class ProductGalleryImage(models.Model):
    product = models.ForeignKey(Product, related_name='gallery_images', on_delete=models.CASCADE)
    image_file = models.ImageField(upload_to=product_gallery_upload_to, max_length=255, blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name_plural = 'Product Gallery Images'

    def __str__(self):
        return f"Gallery image for {self.product.name}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, related_name='reviews_list', on_delete=models.CASCADE)
    author_name = models.CharField(max_length=100)
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author_name} on {self.product.name} ({self.rating}★)"


class GroupedProductItem(models.Model):
    """One line of a grouped product: `quantity` units of an existing simple
    product. Buying the group deducts quantity x bundles-bought from the
    child's stock."""

    group = models.ForeignKey(Product, related_name='group_items', on_delete=models.CASCADE)
    # RESTRICT (not PROTECT): a child can't be deleted while a bundle still
    # uses it, but deleting a bundle and its children in one go is allowed.
    child = models.ForeignKey(Product, related_name='used_in_groups', on_delete=models.RESTRICT)
    quantity = models.PositiveIntegerField(default=1)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['group', 'child'], name='unique_child_per_group'),
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name='group_item_quantity_gte_1'),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.child.name} in {self.group.name}"


class InsufficientStock(Exception):
    """A requested quantity can't be fulfilled from current stock."""


def sync_product_from_active_lot(product):
    """Sync product stock and prices with active lots.
    If the product has active lots with remaining_quantity > 0:
      - Oldest active lot (FIFO) determines the active trade_price, regular_price, and price.
      - product.stock becomes sum of remaining_quantity of all active lots.
    If all lots have remaining_quantity == 0:
      - product.stock = 0.
    If product has NO lots:
      - No changes to product stock or prices (preserves backward compatibility).
    """
    if not product or product.is_grouped:
        return

    lots_qs = product.lots.filter(is_active=True).order_by('created_at', 'id')
    if not lots_qs.exists():
        return

    total_remaining = sum(max(0, lot.remaining_quantity) for lot in lots_qs)
    active_lot = lots_qs.filter(remaining_quantity__gt=0).first()

    update_fields = ['stock']
    product.stock = total_remaining

    if active_lot:
        if active_lot.trade_price and active_lot.trade_price != "৳0.00":
            product.trade_price = active_lot.trade_price
            update_fields.append('trade_price')
        if active_lot.mrp and active_lot.mrp != "৳0.00":
            product.regular_price = active_lot.mrp
            product.original_price = active_lot.mrp
            update_fields.extend(['regular_price', 'original_price'])

            # Discounted price handling
            lot_disc = str(active_lot.discounted_price or '').replace('৳', '').replace(',', '').strip()
            try:
                disc_val = float(lot_disc)
            except ValueError:
                disc_val = 0.0

            if disc_val > 0 and active_lot.discounted_price != active_lot.mrp:
                product.discounted_price = active_lot.discounted_price
                product.price = active_lot.discounted_price
            else:
                product.discounted_price = active_lot.mrp
                product.price = active_lot.mrp
            update_fields.extend(['discounted_price', 'price'])

            # Recalculate discount percentage
            try:
                reg_clean = float(str(product.regular_price).replace('৳', '').replace(',', '').strip())
                disc_clean = float(str(product.discounted_price).replace('৳', '').replace(',', '').strip())
                if reg_clean > disc_clean > 0:
                    product.discount_percent = round(((reg_clean - disc_clean) / reg_clean) * 100)
                else:
                    product.discount_percent = 0
                update_fields.append('discount_percent')
            except (ValueError, TypeError, ZeroDivisionError):
                pass

    product.save(update_fields=list(set(update_fields)))


def deduct_stock(product, qty):
    """Deduct stock for `qty` units of `product`. Call inside
    transaction.atomic(): rows are locked so concurrent orders can't
    oversell a bundle's children or lots.

    Grouped: strict and all-or-nothing - every child must cover
    child_quantity x qty, otherwise InsufficientStock is raised before
    anything is changed.
    Simple with lots: deducts from oldest active lot first (FIFO).
    When an older lot runs out (remaining_quantity reaches 0), the system
    automatically transitions to the next lot, updating trade_price and MRP.
    Simple without lots: keeps the store's existing behaviour of
    clamping at zero instead of refusing the order.

    Returns: list of deduction dicts:
    [{'lot': lot_obj, 'lot_id': lot.id, 'lot_number': lot.lot_number, 'quantity': qty, 'trade_price': lot.trade_price, 'mrp': lot.mrp}]
    """
    if product.is_grouped:
        items = list(product.group_items.select_related('child'))
        if not items:
            raise InsufficientStock(f'"{product.name}" has no products in its bundle.')
        locked = {
            p.id: p
            for p in Product.objects.select_for_update().filter(id__in=[i.child_id for i in items])
        }
        for item in items:
            need = item.quantity * qty
            have = locked[item.child_id].stock or 0
            if have < need:
                raise InsufficientStock(
                    f'Not enough stock for "{product.name}": it needs {need} x {item.child.name} '
                    f'but only {have} available.'
                )
        deductions = []
        for item in items:
            child = locked[item.child_id]
            child_deductions = deduct_stock(child, item.quantity * qty)
            deductions.extend(child_deductions)
        return deductions

    locked = Product.objects.select_for_update().get(pk=product.pk)

    # Check if this product has active lots
    active_lots = list(ProductLot.objects.select_for_update().filter(
        product=locked, is_active=True, remaining_quantity__gt=0
    ).order_by('created_at', 'id'))

    if active_lots:
        remaining_to_deduct = qty
        deductions = []
        for lot in active_lots:
            if remaining_to_deduct <= 0:
                break
            take = min(lot.remaining_quantity, remaining_to_deduct)
            lot.remaining_quantity -= take
            remaining_to_deduct -= take
            lot.save(update_fields=['remaining_quantity', 'updated_at'])
            deductions.append({
                'lot': lot,
                'lot_id': lot.id,
                'lot_number': lot.lot_number,
                'quantity': take,
                'trade_price': lot.trade_price,
                'mrp': lot.mrp,
            })

        # Sync the product's active lot, prices, and stock
        sync_product_from_active_lot(locked)
        return deductions

    # Fallback for products without lots
    if locked.stock is not None:
        locked.stock = max(0, locked.stock - qty)
        locked.save(update_fields=['stock'])
    return []


def restock_product(product, qty, bundle_items=None, lot_id=None):
    """Restores stock for `qty` units of `product` when an order is cancelled.
    If product is grouped, restores stock for each child product.
    If product is simple with lots: restores into the specific lot (if lot_id given)
    or into the most recent active lot, then re-syncs active prices & stock.
    If product is simple without lots: restores directly to product.stock.
    """
    if not product or qty <= 0:
        return

    if product.is_grouped:
        # If saved bundle_items is passed (from OrderItem snapshot), use child names / IDs
        if bundle_items and isinstance(bundle_items, list) and len(bundle_items) > 0:
            for bi in bundle_items:
                bi_qty = int(bi.get('quantity', 1))
                bi_name = bi.get('name')
                child = Product.objects.filter(name=bi_name).first() if bi_name else None
                if child:
                    restock_product(child, bi_qty * qty)
            return

        items = list(product.group_items.select_related('child'))
        if items:
            for item in items:
                child = Product.objects.filter(pk=item.child_id).first()
                if child:
                    restock_product(child, item.quantity * qty)
            return

    locked = Product.objects.select_for_update().get(pk=product.pk)

    # Check if product has lots
    lots_qs = ProductLot.objects.select_for_update().filter(product=locked)
    if lots_qs.exists():
        target_lot = None
        if lot_id:
            target_lot = lots_qs.filter(id=lot_id).first()
        if not target_lot:
            target_lot = lots_qs.filter(is_active=True).order_by('-created_at', '-id').first() or lots_qs.order_by('-created_at', '-id').first()

        if target_lot:
            target_lot.remaining_quantity += qty
            target_lot.save(update_fields=['remaining_quantity', 'updated_at'])
            sync_product_from_active_lot(locked)
            return

    # Fallback direct stock restore
    if locked.stock is not None:
        locked.stock = (locked.stock or 0) + qty
        locked.save(update_fields=['stock'])
