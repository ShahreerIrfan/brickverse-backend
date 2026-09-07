from django.urls import path
from .views import (
    NewsletterSubscribeView,
    NavLinkListView,
    StoreInfoView,
    FooterColumnListView,
    ContactMessageCreateView,
)

urlpatterns = [
    path('newsletter/subscribe/', NewsletterSubscribeView.as_view(), name='newsletter-subscribe'),
    path('nav-links/', NavLinkListView.as_view(), name='nav-links'),
    path('store-info/', StoreInfoView.as_view(), name='store-info'),
    path('footer/', FooterColumnListView.as_view(), name='footer-columns'),
    path('contact/', ContactMessageCreateView.as_view(), name='contact-create'),
]
