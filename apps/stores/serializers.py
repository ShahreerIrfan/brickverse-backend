from rest_framework import serializers
from decimal import Decimal
from apps.products.models import Product
from .models import PartnerStore, StoreProductLine, StoreTransactionLog, StorePayment


class StoreProductLineSerializer(serializers.ModelSerializer):
    productId = serializers.CharField(source='product_id', read_only=True)
    productName = serializers.CharField(source='product.name', read_only=True)
    productSku = serializers.CharField(source='product.sku', read_only=True)
    productImage = serializers.SerializerMethodField()
    tp = serializers.DecimalField(source='tp_at_time', max_digits=10, decimal_places=2, read_only=True)
    qtyGiven = serializers.IntegerField(source='qty_given', read_only=True)
    qtySold = serializers.IntegerField(source='qty_sold', read_only=True)
    qtyReturned = serializers.IntegerField(source='qty_returned', read_only=True)
    qtyRemaining = serializers.SerializerMethodField()
    valueGiven = serializers.SerializerMethodField()
    valueSold = serializers.SerializerMethodField()

    class Meta:
        model = StoreProductLine
        fields = ['id', 'productId', 'productName', 'productSku', 'productImage', 'tp',
                  'qtyGiven', 'qtySold', 'qtyReturned', 'qtyRemaining', 'valueGiven', 'valueSold']

    def get_productImage(self, obj):
        if obj.product and obj.product.image:
            return obj.product.image.url
        return "/images/figure-samurai-red.svg"

    def get_qtyRemaining(self, obj):
        return obj.qty_remaining

    def get_valueGiven(self, obj):
        return obj.value_given

    def get_valueSold(self, obj):
        return obj.value_sold


class PartnerStoreListSerializer(serializers.ModelSerializer):
    """For the store list page — aggregates only, no line-by-line detail."""
    productsCount = serializers.SerializerMethodField()
    valueGiven = serializers.SerializerMethodField()
    valueRemaining = serializers.SerializerMethodField()
    amountDue = serializers.SerializerMethodField()
    settlementStatus = serializers.SerializerMethodField()
    lastSettlementDate = serializers.SerializerMethodField()

    class Meta:
        model = PartnerStore
        fields = ['id', 'name', 'owner_name', 'phone', 'area', 'is_active',
                  'productsCount', 'valueGiven', 'valueRemaining', 'amountDue',
                  'settlementStatus', 'lastSettlementDate', 'created_at']

    def get_productsCount(self, obj):
        return obj.lines.count()

    def get_valueGiven(self, obj):
        return obj.value_given

    def get_valueRemaining(self, obj):
        return obj.value_remaining

    def get_amountDue(self, obj):
        return obj.amount_due

    def get_settlementStatus(self, obj):
        return obj.settlement_status

    def get_lastSettlementDate(self, obj):
        last = obj.payments.order_by('-payment_date').first()
        return last.payment_date if last else None


class PartnerStoreDetailSerializer(PartnerStoreListSerializer):
    """For the single store page — includes every product line."""
    productLines = StoreProductLineSerializer(source='lines', many=True, read_only=True)

    class Meta(PartnerStoreListSerializer.Meta):
        fields = PartnerStoreListSerializer.Meta.fields + ['address', 'notes', 'productLines']


class PartnerStoreWriteSerializer(serializers.ModelSerializer):
    """For create/update of the store record itself (not its stock)."""
    class Meta:
        model = PartnerStore
        fields = ['id', 'name', 'owner_name', 'phone', 'area', 'address', 'notes', 'is_active']


class StorePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorePayment
        fields = ['id', 'store', 'amount', 'payment_date', 'method', 'note', 'created_at']
        extra_kwargs = {'store': {'required': False}}
