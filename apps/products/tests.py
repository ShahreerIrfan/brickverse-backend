import io
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict
from apps.products.models import Product, ProductGalleryImage
from apps.products.serializers import ProductSerializer


class ProductSvgUploadTestCase(TestCase):
    def test_product_svg_upload_primary_and_gallery(self):
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><circle cx="32" cy="32" r="30" fill="#FF4D6D"/></svg>'
        primary_file = SimpleUploadedFile("figure.svg", svg_content, content_type="image/svg+xml")
        gallery_file = SimpleUploadedFile("gallery_detail.svg", svg_content, content_type="image/svg+xml")

        data = {
            "id": "test-svg-brick-figure",
            "name": "Test SVG Brick Figure",
            "category": "Figures",
            "stock": 15,
            "regularPrice": "150",
            "discountedPrice": "120",
            "tradePrice": "80",
            "image_file": primary_file,
        }

        files = MultiValueDict({
            "image": [primary_file],
            "image_file": [primary_file],
            "gallery_files": [gallery_file],
        })
        request_mock = type("Req", (), {"FILES": files, "method": "POST", "build_absolute_uri": lambda self, u: u})()

        serializer = ProductSerializer(data=data, context={"request": request_mock})
        self.assertTrue(serializer.is_valid(), f"Serializer validation failed: {serializer.errors}")

        instance = serializer.save()
        self.assertEqual(instance.id, "test-svg-brick-figure")
        self.assertTrue(instance.image.name.endswith(".svg"))
        self.assertTrue(instance.image_file.name.endswith(".svg"))

        # Gallery image check
        self.assertEqual(instance.gallery_images.count(), 1)
        gal = instance.gallery_images.first()
        self.assertTrue(gal.image_file.name.endswith(".svg"))

        # Serializer representation check
        rep = serializer.data
        self.assertTrue(".svg" in rep["image"])
        self.assertEqual(len(rep["gallery_images"]), 1)
        self.assertTrue(".svg" in rep["gallery_images"][0]["imageUrl"])
