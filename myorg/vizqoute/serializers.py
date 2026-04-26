from rest_framework import serializers
from .models import *
from django.db.models import Count, Sum, F


class VizqouteUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = VizqouteUser
        fields = '__all__'


class VizqouteClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = VizqouteClient
        fields = '__all__'


class VizqouteQuoteItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = VizqouteQuoteItem
        fields = '__all__'


class VizqouteRoofingSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = VizqouteRoofingSpec
        fields = '__all__'


class VizqoutePreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = VizqoutePreview
        fields = '__all__'


class VizqouteQuotationSerializer(serializers.ModelSerializer):
    items = VizqouteQuoteItemSerializer(many=True, read_only=True)
    roofingspecs = VizqouteRoofingSpecSerializer(many=True, read_only=True)
    previews = VizqoutePreviewSerializer(many=True, read_only=True)

    class Meta:
        model = VizqouteQuotation
        fields = '__all__'


class VizqouteQuotationCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VizqouteQuotation
        fields = '__all__'

# These serializers are for specific views and may include additional fields or methods as needed


class ContractorQuotesSerializer(serializers.ModelSerializer):
    """Contractor dashboard quotes"""
    class Meta(VizqouteQuotationSerializer.Meta):
        model = VizqouteQuotation


class ClientQuotesSerializer(serializers.ModelSerializer):
    """Client history quotes"""
    class Meta(VizqouteQuotationSerializer.Meta):
        model = VizqouteQuotation


class DashboardStatsSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class QuoteTotalSerializer(serializers.Serializer):
    quotation_id = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)


class RevenueReportSerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class MaterialAnalyticsSerializer(serializers.Serializer):
    materialtype = serializers.CharField()
    count = serializers.IntegerField()
