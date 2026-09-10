from django.urls import path
from .views import (
    PartnerStoreListView, PartnerStoreDetailView, StoreAddProductView,
    StoreRecordSaleView, StoreRecordReturnView, StorePaymentListCreateView,
    StoreMonthlySettlementView,
)

urlpatterns = [
    path('', PartnerStoreListView.as_view(), name='store-list'),
    path('<int:id>/', PartnerStoreDetailView.as_view(), name='store-detail'),
    path('<int:id>/add-product/', StoreAddProductView.as_view(), name='store-add-product'),
    path('<int:id>/record-sale/', StoreRecordSaleView.as_view(), name='store-record-sale'),
    path('<int:id>/record-return/', StoreRecordReturnView.as_view(), name='store-record-return'),
    path('<int:id>/payments/', StorePaymentListCreateView.as_view(), name='store-payments'),
    path('<int:id>/settlement/', StoreMonthlySettlementView.as_view(), name='store-settlement'),
]
