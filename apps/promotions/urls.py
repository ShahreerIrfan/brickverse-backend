from django.urls import path
from .views import (
    AnnouncementDetailView,
    HeroSlideListView,
    PromoCardListView,
    PromoBannerDetailView,
    AllPromotionsView,
)

urlpatterns = [
    path('all/', AllPromotionsView.as_view(), name='promotions-all'),
    path('announcement/', AnnouncementDetailView.as_view(), name='promotions-announcement'),
    path('hero-slides/', HeroSlideListView.as_view(), name='promotions-hero-slides'),
    path('promo-cards/', PromoCardListView.as_view(), name='promotions-promo-cards'),
    path('promo-banner/', PromoBannerDetailView.as_view(), name='promotions-promo-banner'),
]
