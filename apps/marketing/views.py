from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import NewsletterSubscriber, NavLink, StoreInfo, FooterColumn, ContactMessage, HeroSlide, Coupon, PromoBanner
from .serializers import (
    NewsletterSubscriberSerializer,
    NavLinkSerializer,
    StoreInfoSerializer,
    FooterColumnSerializer,
    ContactMessageSerializer,
    HeroSlideSerializer,
    CouponSerializer,
    PromoBannerSerializer,
)

class NewsletterSubscribeView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        source = request.data.get('source', 'footer_banner')

        if not email or '@' not in email:
            return Response({"error": "Please provide a valid email address."}, status=status.HTTP_400_BAD_REQUEST)

        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={'source': source}
        )

        if created:
            return Response(
                {"message": "Thank you for subscribing to restock alerts!", "email": email, "created": True},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"message": "You are already subscribed to restock alerts!", "email": email, "created": False},
            status=status.HTTP_200_OK
        )


class NavLinkListView(generics.ListAPIView):
    queryset = NavLink.objects.all().order_by('order')
    serializer_class = NavLinkSerializer
    pagination_class = None


class StoreInfoView(APIView):
    def get(self, request):
        info = StoreInfo.objects.first()
        if not info:
            info = StoreInfo.objects.create()
        return Response(StoreInfoSerializer(info).data)


class FooterColumnListView(generics.ListAPIView):
    queryset = FooterColumn.objects.prefetch_related('links').all().order_by('order')
    serializer_class = FooterColumnSerializer
    pagination_class = None


class ContactMessageCreateView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer


class HeroSlideListView(generics.ListAPIView):
    """Public: active slides only, in display order - what the homepage
    hero carousel renders."""
    queryset = HeroSlide.objects.filter(is_active=True).order_by('order', 'id')
    serializer_class = HeroSlideSerializer
    pagination_class = None


class HeroSlideAdminListView(generics.ListCreateAPIView):
    """Admin: every slide, active or not, for the Hero Slide manager."""
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = HeroSlide.objects.all().order_by('order', 'id')
    serializer_class = HeroSlideSerializer
    pagination_class = None


class HeroSlideDetailView(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = HeroSlide.objects.all()
    serializer_class = HeroSlideSerializer


class CouponListCreateView(generics.ListCreateAPIView):
    """Admin: List and Create Coupons"""
    serializer_class = CouponSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Coupon.objects.all().order_by('-created_at')
        search = self.request.query_params.get('search', '').strip()
        status_param = self.request.query_params.get('status', '').strip()
        if search:
            queryset = queryset.filter(code__icontains=search) | queryset.filter(description__icontains=search)
        if status_param == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_param == 'inactive':
            queryset = queryset.filter(is_active=False)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'code' in data and isinstance(data['code'], str):
            data['code'] = data['code'].strip().upper()
        # Handle blank/null numeric/date values
        for f in ['max_discount', 'usage_limit', 'per_user_limit', 'end_date', 'start_date']:
            if f in data and (data[f] == '' or data[f] is None):
                data[f] = None
        if 'min_order_amount' in data and (data['min_order_amount'] == '' or data['min_order_amount'] is None):
            data['min_order_amount'] = 0

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin: Retrieve, Update, Delete Coupon"""
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        if 'code' in data and isinstance(data['code'], str):
            data['code'] = data['code'].strip().upper()
        for f in ['max_discount', 'usage_limit', 'per_user_limit', 'end_date', 'start_date']:
            if f in data and (data[f] == '' or data[f] is None):
                data[f] = None
        if 'min_order_amount' in data and (data['min_order_amount'] == '' or data['min_order_amount'] is None):
            data['min_order_amount'] = 0

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class CouponValidateView(APIView):
    """Customer: Validate Coupon Code against cart subtotal"""
    def post(self, request):
        raw_code = request.data.get('code', '')
        if not raw_code:
            return Response({"valid": False, "error": "Please provide a coupon code."}, status=status.HTTP_400_BAD_REQUEST)

        code = str(raw_code).strip().upper()
        subtotal = float(request.data.get('subtotal', 0) or 0)

        coupon = Coupon.objects.filter(code__iexact=code).first()
        if not coupon:
            return Response({"valid": False, "error": f'Coupon code "{code}" not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_valid, reason = coupon.is_valid_now()
        if not is_valid:
            return Response({"valid": False, "error": reason}, status=status.HTTP_400_BAD_REQUEST)

        discount_amount, calc_error = coupon.calculate_discount(subtotal)
        if calc_error:
            return Response({"valid": False, "error": calc_error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "valid": True,
            "id": coupon.id,
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "value": float(coupon.value),
            "discount_amount": discount_amount,
            "min_order_amount": float(coupon.min_order_amount or 0),
            "max_discount": float(coupon.max_discount) if coupon.max_discount else None,
            "message": f"Coupon {coupon.code} applied successfully!",
        }, status=status.HTTP_200_OK)


class PromoBannerListView(generics.ListAPIView):
    """Public: active promo banners only (up to 2), in display order for homepage."""
    serializer_class = PromoBannerSerializer
    pagination_class = None

    def get_queryset(self):
        return PromoBanner.objects.filter(is_active=True).order_by('order', 'id')[:2]


class PromoBannerAdminListView(generics.ListCreateAPIView):
    """Admin: all promo banners with strict maximum 2 banners limit."""
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = PromoBanner.objects.all().order_by('order', 'id')
    serializer_class = PromoBannerSerializer
    pagination_class = None

    def create(self, request, *args, **kwargs):
        current_count = PromoBanner.objects.count()
        if current_count >= 2:
            return Response(
                {"error": "Maximum 2 promo banners allowed. You can edit, reorder, or delete existing banners."},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'countdown_end' in data and not data['countdown_end']:
            data['countdown_end'] = None
        if 'countdownEnd' in data and not data['countdownEnd']:
            data['countdownEnd'] = None

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PromoBannerDetailView(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = PromoBanner.objects.all()
    serializer_class = PromoBannerSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'countdown_end' in data and not data['countdown_end']:
            data['countdown_end'] = None
        if 'countdownEnd' in data and not data['countdownEnd']:
            data['countdownEnd'] = None
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

