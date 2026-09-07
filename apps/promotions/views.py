from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Announcement, HeroSlide, PromoCard, PromoBanner
from .serializers import (
    AnnouncementSerializer,
    HeroSlideSerializer,
    PromoCardSerializer,
    PromoBannerSerializer,
)

class AnnouncementDetailView(APIView):
    def get(self, request):
        announcement = Announcement.objects.filter(is_active=True).first()
        if not announcement:
            return Response({})
        return Response(AnnouncementSerializer(announcement).data)


class HeroSlideListView(generics.ListAPIView):
    queryset = HeroSlide.objects.filter(is_active=True).order_by('order')
    serializer_class = HeroSlideSerializer
    pagination_class = None


class PromoCardListView(generics.ListAPIView):
    queryset = PromoCard.objects.filter(is_active=True).order_by('order')
    serializer_class = PromoCardSerializer
    pagination_class = None


class PromoBannerDetailView(APIView):
    def get(self, request):
        banner = PromoBanner.objects.filter(is_active=True).first()
        if not banner:
            return Response({})
        return Response(PromoBannerSerializer(banner).data)


class AllPromotionsView(APIView):
    def get(self, request):
        announcement = Announcement.objects.filter(is_active=True).first()
        hero_slides = HeroSlide.objects.filter(is_active=True).order_by('order')
        promo_cards = PromoCard.objects.filter(is_active=True).order_by('order')
        promo_banner = PromoBanner.objects.filter(is_active=True).first()

        return Response({
            "announcement": AnnouncementSerializer(announcement).data if announcement else None,
            "heroSlides": HeroSlideSerializer(hero_slides, many=True).data,
            "promoCards": PromoCardSerializer(promo_cards, many=True).data,
            "promoBanner": PromoBannerSerializer(promo_banner).data if promo_banner else None,
        })
