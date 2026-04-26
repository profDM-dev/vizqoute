from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .serializers import *
from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Sum, F
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import VizqouteQuotation, VizqouteQuoteItem, VizqoutePreview
from django.views.generic import ListView, View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

# ViewSets for CRUD operations on each model


@login_required
def admin_panel(request):
    return render(request, "admin.html")


class VizqouteUserViewSet(viewsets.ModelViewSet):
    queryset = VizqouteUser.objects.all()
    serializer_class = VizqouteUserSerializer

#


class VizqouteClientViewSet(viewsets.ModelViewSet):
    queryset = VizqouteClient.objects.all()
    serializer_class = VizqouteClientSerializer


class VizqouteQuotationViewSet(viewsets.ModelViewSet):
    queryset = VizqouteQuotation.objects.all()
    serializer_class = VizqouteQuotationSerializer


class VizqouteQuoteItemViewSet(viewsets.ModelViewSet):
    queryset = VizqouteQuoteItem.objects.all()
    serializer_class = VizqouteQuoteItemSerializer


class VizqouteRoofingSpecViewSet(viewsets.ModelViewSet):
    queryset = VizqouteRoofingSpec.objects.all()
    serializer_class = VizqouteRoofingSpecSerializer


class VizqoutePreviewViewSet(viewsets.ModelViewSet):
    queryset = VizqoutePreview.objects.all()
    serializer_class = VizqoutePreviewSerializer

# Custom views for specific actions


class vizqoutequotationretrieveupdateview(generics.RetrieveUpdateAPIView):
    queryset = VizqouteQuotation.objects.all()
    serializer_class = VizqouteQuotationSerializer

# custom views for analytics and actions

# List quotes by contractor


class ContractorQuotesListView(generics.ListAPIView):
    serializer_class = ContractorQuotesSerializer

    def get_queryset(self):
        contractor_id = self.request.query_params.get('contractor_id')
        if not contractor_id:
            return VizqouteQuotation.objects.none()  # Return empty if no ID
        return VizqouteQuotation.objects.filter(contractorid_id=contractor_id).order_by('-createdat')[:20]
# List quotes by client


class ClientQuotesListView(generics.ListAPIView):
    serializer_class = ClientQuotesSerializer

    def get_queryset(self):
        client_id = self.request.query_params.get('client_id')
        return VizqouteQuotation.objects.filter(clientid_id=client_id)

# List quotes by status


class StatusQuotesListView(generics.ListAPIView):
    serializer_class = VizqouteQuotationSerializer

    def get_queryset(self):
        status_param = self.request.query_params.get('status')
        return VizqouteQuotation.objects.filter(status=status_param)

# List quotes by date range


class DashboardStatsView(generics.ListAPIView):
    serializer_class = DashboardStatsSerializer

    def get_queryset(self):
        return (
            VizqouteQuotation.objects
            .values('status')
            .annotate(count=Count('id'))
        )

# Calculate total price for a quote


class QuoteTotalView(generics.RetrieveAPIView):
    serializer_class = QuoteTotalSerializer

    def get_object(self):
        quote = get_object_or_404(VizqouteQuotation, pk=self.kwargs['pk'])
        total = VizqouteQuoteItem.objects.filter(
            quotationid=quote
        ).aggregate(total_price=Sum('totalprice'))

        return {
            "quotation_id": quote.id,
            "total_price": total['total_price'] or 0
        }

# Generate revenue report


class RevenueReportView(generics.ListAPIView):
    serializer_class = RevenueReportSerializer

    def get_queryset(self):
        total = VizqouteQuoteItem.objects.aggregate(
            total_revenue=Sum('totalprice')
        )
        return [total]

# Analyze material usage


class MaterialAnalyticsView(generics.ListAPIView):
    serializer_class = MaterialAnalyticsSerializer

    def get_queryset(self):
        return (
            VizqouteRoofingSpec.objects
            .values('materialtype')
            .annotate(count=Count('id'))
        )

# List recent quotes


class RecentQuotesView(generics.ListAPIView):
    serializer_class = VizqouteQuotationSerializer

    def get_queryset(self):
        return VizqouteQuotation.objects.order_by('-createdat')[:10]

# Track quote preview access


class TrackPreviewView(generics.UpdateAPIView):
    queryset = VizqoutePreview.objects.all()
    serializer_class = VizqoutePreviewSerializer

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.accesscount += 1
        instance.save()


class QuoteLocationsView(generics.ListAPIView):
    serializer_class = VizqouteQuotationSerializer  # Reuse, it has lat/long

    def get_queryset(self):
        return VizqouteQuotation.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)[:50]


class ClientQuotesListView(ListView):
    model = VizqouteQuotation
    template_name = 'client_quotes.html'


class StatusQuotesListView(ListView):
    model = VizqouteQuotation
    template_name = 'status_quotes.html'


class DashboardStatsView(View):
    def get(self, request):
        return JsonResponse({'stats': {}})


class QuoteTotalView(View):
    def get(self, request, pk):
        return JsonResponse({'total': 0})


class RevenueReportView(View):
    def get(self, request):
        return JsonResponse({'revenue': 0})


class MaterialAnalyticsView(View):
    def get(self, request):
        return JsonResponse({'materials': {}})


class RecentQuotesView(View):
    def get(self, request):
        return JsonResponse({'quotes': []})


class TrackPreviewView(View):
    def get(self, request, pk):
        return JsonResponse({'preview': {}})


class QuoteLocationsView(View):
    def get(self, request):
        return JsonResponse({'locations': []})


def blueprint_ocr(request):
    return JsonResponse({'success': False})


def landing(request):
    return render(request, "landingpage.html")


def login_view(request):
    return render(request, "login.html")


def signup(request):
    return render(request, "signup.html")


def dashboard(request):
    clients = VizqouteClient.objects.all()[:10]
    context = {
        'clients': clients,
    }
    return render(request, "dash.html", context)


def contractor_dashboard(request):
    clients = VizqouteClient.objects.all()[:10]
    context = {'clients': clients}
    return render(request, "contractordash.html")


def client_portal(request):
    return render(request, "clientportal.html")


def quote_builder(request):
    return render(request, "quotebuilder.html")


def view_3d(request):
    return render(request, "3dview.html")


def admin_panel(request):
    clients = VizqouteClient.objects.all()[:10]
    context = {'clients': clients}
    return render(request, "admin.html")

# Add to your views.py


@csrf_exempt
def blueprint_ocr(request):
    if request.method == 'POST':
        file = request.FILES.get('blueprint')
        if file:
            # Mock OCR - replace with pytesseract later
            ocr_data = {
                'roof_area': 2450,
                'labor_hours': 48,
                'pitch_angle': '6:12',
                'material_type': 'Architectural Shingles',
                'waste_factor': 10,
                'success': True
            }
            return JsonResponse(ocr_data)
        return JsonResponse({'error': 'No file'}, status=400)
    return JsonResponse({'error': 'POST required'}, status=405)


def create_quote(request):
    if request.method == "POST":
        quote = VizqouteQuotation.objects.create(
            clientname=request.POST.get("clientname"),
            address=request.POST.get("address"),
            roofarea=request.POST.get("roofarea") or 0,
            status=request.POST.get("status")
        )
        return JsonResponse({"success": True, "id": quote.id})
    return JsonResponse({"error": "POST method required"}, status=400)


def client_portal(request, client_id):
    # ✅ Use correct ForeignKey field
    client_quotes = VizqouteQuotation.objects.filter(
        clientid__name__icontains=client_id  # Fixed: clientid__name
    ).order_by('-createdat')

    paginator = Paginator(client_quotes, 10)
    page_number = request.GET.get('page')
    quotes_page = paginator.get_page(page_number)

    stats = {
        'pending_count': client_quotes.filter(status='draft').count(),
        'total_value': 0,  # Add total field to model later
        'status': client_quotes.first().status if client_quotes.exists() else 'No Projects'
    }

    context = {
        'client_quotes': quotes_page,
        'stats': stats,
        'client_id': client_id
    }
    return render(request, 'clientportal.html', context)


def dashboard(request):
    clients = VizqouteClient.objects.all()[:5]  # Top 5 clients
    context = {
        'clients': clients,  # Pass to template
    }
    return render(request, "dash.html", context)


def quote_detail(request, quote_id):
    quote = get_object_or_404(VizqouteQuotation, id=quote_id)
    items = VizqouteQuoteItem.objects.filter(quotationid=quote)
    roofing_specs = VizqouteRoofingSpec.objects.filter(quotationid=quote)

    context = {
        'quote': quote,
        'items': items,
        'roofing_specs': roofing_specs,
    }
    return render(request, 'quote_detail.html', context)
