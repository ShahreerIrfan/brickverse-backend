from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from decimal import Decimal, InvalidOperation
from apps.products.models import Product
from apps.users.permissions import IsAdminRole
from .models import PartnerStore, StoreProductLine, StoreTransactionLog, StorePayment
from .serializers import (
    PartnerStoreListSerializer, PartnerStoreDetailSerializer,
    PartnerStoreWriteSerializer, StoreProductLineSerializer, StorePaymentSerializer,
)


def _parse_tp(product: Product) -> Decimal:
    """Product.trade_price is a display string like '৳850.00' — parse it safely with fallbacks."""
    if not product:
        return Decimal('0')
    raw = str(product.trade_price or product.discounted_price or product.price or product.regular_price or "0").replace('৳', '').replace(',', '').strip()
    try:
        val = Decimal(raw)
        return val if val >= 0 else Decimal('0')
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


class PartnerStoreListView(generics.ListCreateAPIView):
    queryset = PartnerStore.objects.all().prefetch_related('product_lines', 'payments')
    pagination_class = None
    permission_classes = [IsAdminRole]

    def get_serializer_class(self):
        return PartnerStoreWriteSerializer if self.request.method == 'POST' else PartnerStoreListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')  # up_to_date | due_this_month | overdue
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(owner_name__icontains=search) | Q(area__icontains=search))
        if status_filter and status_filter != 'all':
            qs = [s for s in qs if s.settlement_status == status_filter]
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)

    def create(self, request, *args, **kwargs):
        # Support the "starting stock" rows the Add Store form can submit alongside the store itself.
        response = super().create(request, *args, **kwargs)
        store = PartnerStore.objects.get(id=response.data['id'])
        starting_stock = request.data.get('startingStock', [])
        for row in starting_stock:
            product_id = row.get('productId')
            product = Product.objects.filter(id=product_id).first()
            try:
                qty = int(row.get('qty', 0))
            except (TypeError, ValueError):
                qty = 0
            if not product or qty <= 0:
                continue
            line, _ = StoreProductLine.objects.get_or_create(
                store=store, product=product, defaults={'tp_at_time': _parse_tp(product)}
            )
            line.qty_given += qty
            line.save()
            StoreTransactionLog.objects.create(
                store=store, line=line, event_type='given', quantity=qty,
                created_by=request.user if request.user.is_authenticated else None,
            )
        return Response(PartnerStoreDetailSerializer(store).data, status=status.HTTP_201_CREATED)


class PartnerStoreDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PartnerStore.objects.all().prefetch_related('product_lines__product', 'payments')
    lookup_field = 'id'
    permission_classes = [IsAdminRole]

    def get_serializer_class(self):
        return PartnerStoreWriteSerializer if self.request.method in ('PUT', 'PATCH') else PartnerStoreDetailSerializer


class StoreAddProductView(APIView):
    """POST { productId, qty } -> adds/increments a StoreProductLine, snapshots TP, logs it."""
    permission_classes = [IsAdminRole]

    def post(self, request, id):
        store = PartnerStore.objects.filter(id=id).first()
        if not store:
            return Response({"error": "Store not found"}, status=status.HTTP_404_NOT_FOUND)
            
        product = Product.objects.filter(id=request.data.get('productId')).first()
        try:
            qty = int(request.data.get('qty', 0))
        except (TypeError, ValueError):
            qty = 0
            
        if not product or qty <= 0:
            return Response({"error": "productId and a positive qty are required."}, status=status.HTTP_400_BAD_REQUEST)

        line, created = StoreProductLine.objects.get_or_create(
            store=store, product=product, defaults={'tp_at_time': _parse_tp(product)}
        )
        if not created:
            line.qty_given += qty
            line.save()
        else:
            line.qty_given = qty
            line.save()

        StoreTransactionLog.objects.create(
            store=store, line=line, event_type='given', quantity=qty, created_by=request.user if request.user.is_authenticated else None,
        )
        return Response(StoreProductLineSerializer(line).data, status=status.HTTP_201_CREATED)


class StoreRecordSaleView(APIView):
    """POST { lineId, qty } -> increments qty_sold. Rejects if it would exceed qty_remaining."""
    permission_classes = [IsAdminRole]

    def post(self, request, id):
        line = StoreProductLine.objects.filter(id=request.data.get('lineId'), store_id=id).first()
        if not line:
            return Response({"error": "Product line not found for this store."}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            qty = int(request.data.get('qty', 0))
        except (TypeError, ValueError):
            qty = 0
            
        if qty <= 0 or qty > line.qty_remaining:
            return Response({"error": f"qty must be between 1 and {line.qty_remaining} (remaining stock)."}, status=status.HTTP_400_BAD_REQUEST)
        
        line.qty_sold += qty
        line.save()
        StoreTransactionLog.objects.create(
            store_id=id, line=line, event_type='sold', quantity=qty, created_by=request.user if request.user.is_authenticated else None,
        )
        return Response(StoreProductLineSerializer(line).data)


class StoreRecordReturnView(APIView):
    """POST { lineId, qty } -> increments qty_returned AND restocks Product.stock in the warehouse."""
    permission_classes = [IsAdminRole]

    def post(self, request, id):
        line = StoreProductLine.objects.filter(id=request.data.get('lineId'), store_id=id).first()
        if not line:
            return Response({"error": "Product line not found for this store."}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            qty = int(request.data.get('qty', 0))
        except (TypeError, ValueError):
            qty = 0
            
        if qty <= 0 or qty > line.qty_remaining:
            return Response({"error": f"qty must be between 1 and {line.qty_remaining} (remaining stock)."}, status=status.HTTP_400_BAD_REQUEST)
        
        line.qty_returned += qty
        line.save()
        line.product.stock = (line.product.stock or 0) + qty
        line.product.save(update_fields=['stock'])
        StoreTransactionLog.objects.create(
            store_id=id, line=line, event_type='returned', quantity=qty, created_by=request.user if request.user.is_authenticated else None,
        )
        return Response(StoreProductLineSerializer(line).data)


class StorePaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = StorePaymentSerializer
    pagination_class = None
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        return StorePayment.objects.filter(store_id=self.kwargs['id'])

    def perform_create(self, serializer):
        serializer.save(store_id=self.kwargs['id'], created_by=self.request.user if self.request.user.is_authenticated else None)


class StoreMonthlySettlementView(APIView):
    """GET -> [{month, valueSold, paymentReceived, balanceCarried}, ...] for all active months."""
    permission_classes = [IsAdminRole]

    def get(self, request, id):
        logs = StoreTransactionLog.objects.filter(store_id=id, event_type='sold').select_related('line')
        value_by_month = {}
        for log in logs:
            key = log.created_at.strftime('%Y-%m')
            value_by_month[key] = value_by_month.get(key, Decimal('0')) + (Decimal(log.quantity) * log.line.tp_at_time)

        payments = StorePayment.objects.filter(store_id=id)
        paid_by_month = {}
        for pay in payments:
            key = pay.payment_date.strftime('%Y-%m')
            paid_by_month[key] = paid_by_month.get(key, Decimal('0')) + pay.amount

        months = sorted(set(value_by_month.keys()) | set(paid_by_month.keys()))
        result = []
        running_balance = Decimal('0')
        for key in months:
            sold = value_by_month.get(key, Decimal('0'))
            paid = paid_by_month.get(key, Decimal('0'))
            running_balance += sold - paid
            result.append({
                "month": key,
                "valueSold": float(sold),
                "paymentReceived": float(paid),
                "balanceCarried": float(running_balance),
            })
        return Response(result)
