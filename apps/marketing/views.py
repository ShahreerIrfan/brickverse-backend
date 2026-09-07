from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import NewsletterSubscriber, NavLink, StoreInfo, FooterColumn, ContactMessage
from .serializers import (
    NewsletterSubscriberSerializer,
    NavLinkSerializer,
    StoreInfoSerializer,
    FooterColumnSerializer,
    ContactMessageSerializer,
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
