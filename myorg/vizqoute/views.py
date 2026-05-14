import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from django.core.paginator import Paginator
from django.db.models import Count, Sum

from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import (
    VizqouteClient,
    VizqoutePreview,
    VizqouteQuotation,
    VizqouteQuoteItem,
    VizqouteRoofingSpec,
    VizqouteUser,
)
from .serializers import (
    ContractorQuotesSerializer,
    DashboardStatsSerializer,
    VizqouteClientSerializer,
    VizqoutePreviewSerializer,
    VizqouteQuotationSerializer,
    VizqouteQuoteItemSerializer,
    VizqouteRoofingSpecSerializer,
    VizqouteUserSerializer,
)


def _get_profile_or_403(request) -> VizqouteUser:
    if not request.user.is_authenticated:
        raise PermissionError("login_required")
    profile = getattr(request.user, "vizqoute_profile", None)
    if not profile:
        raise PermissionError("no_profile")
    return profile


def _is_contractor(profile: VizqouteUser) -> bool:
    return profile.role == "contractor"


# ----------------------------
# Template pages (HTML)
# ----------------------------


def landing(request):
    return render(request, "landingpage.html")


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "GET":
        return render(request, "login.html")

    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""
    user = authenticate(request, username=username, password=password)
    if user is None:
        messages.error(request, "Invalid username or password.")
        return render(request, "login.html", status=400)

    login(request, user)
    return redirect("dashboard")


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.method == "GET":
        return render(request, "signup.html")

    from django.contrib.auth.models import User

    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""
    name = (request.POST.get("name") or username or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    companyname = (request.POST.get("companyname") or "").strip()

    if not username or not password:
        return render(request, "signup.html", {"error": "Username and password are required."}, status=400)

    if User.objects.filter(username=username).exists():
        return render(request, "signup.html", {"error": "Username already exists."}, status=400)

    user = User.objects.create_user(username=username, password=password)
    VizqouteUser.objects.get_or_create(
        user=user,
        defaults={
            "name": name or username,
            "phone": phone or "-",
            "companyname": companyname or None,
            "role": "contractor",
        }
    )
    login(request, user)
    return redirect("dashboard")


@login_required
def dashboard(request):
    profile = _get_profile_or_403(request)
    if not _is_contractor(profile):
        return redirect("client_portal_self")

    clients = VizqouteClient.objects.filter(
        contractor=profile).order_by("-createdat")[:10]
    return render(request, "dash.html", {"clients": clients})


@login_required
def contractor_dashboard(request):
    profile = _get_profile_or_403(request)
    if not _is_contractor(profile):
        return HttpResponseForbidden("Only contractors can access this page.")
    clients = VizqouteClient.objects.filter(
        contractor=profile).order_by("-createdat")[:10]
    return render(request, "contractordash.html", {"clients": clients})


@login_required
def analytics_panel(request):
    profile = _get_profile_or_403(request)
    if not _is_contractor(profile):
        return HttpResponseForbidden("Only contractors can access this page.")
    clients = VizqouteClient.objects.filter(
        contractor=profile).order_by("-createdat")[:10]
    return render(request, "admin.html", {"clients": clients})


@login_required
@require_http_methods(["GET", "POST"])
def quote_builder(request):
    profile = _get_profile_or_403(request)
    if not _is_contractor(profile):
        return HttpResponseForbidden("Only contractors can create quotes.")

    if request.method == "GET":
        clients = VizqouteClient.objects.filter(
            contractor=profile).order_by("-createdat")[:50]
        return render(request, "quotebuilder.html", {"clients": clients})

    clientname = (request.POST.get("clientname") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    status_value = (request.POST.get("status") or "draft").strip()
    if status_value not in {"draft", "sent"}:
        return JsonResponse({"error": "Invalid status"}, status=400)
    if not clientname:
        return JsonResponse({"error": "Client name is required"}, status=400)

    client, _ = VizqouteClient.objects.get_or_create(
        contractor=profile,
        name=clientname,
        defaults={"phone": phone or "-"},
    )
    if phone and client.phone != phone:
        client.phone = phone
        client.save(update_fields=["phone"])

    quote = VizqouteQuotation.objects.create(
        contractorid=profile,
        clientid=client,
        status=status_value,
    )

    roofarea = request.POST.get("roofarea")
    labor_hours = request.POST.get("labor_hours")
    material_type = request.POST.get(
        "material_type") or "Architectural Shingles"
    waste_factor = request.POST.get("wastefactor")
    pitch_angle = request.POST.get("pitchangle")

    try:
        roofarea_val = float(roofarea) if roofarea else 0.0
    except ValueError:
        roofarea_val = 0.0
    try:
        labor_val = float(labor_hours) if labor_hours else 0.0
    except ValueError:
        labor_val = 0.0
    try:
        waste_val = float(waste_factor) if waste_factor else 10.0
    except ValueError:
        waste_val = 10.0
    try:
        pitch_val = float(pitch_angle) if pitch_angle else 6.0
    except ValueError:
        pitch_val = 6.0

    VizqouteRoofingSpec.objects.create(
        quotationid=quote,
        roofarea=roofarea_val,
        pitchangle=pitch_val,
        materialtype=material_type,
        laborhours=labor_val,
        wastefactor=waste_val,
    )

    if status_value == "sent":
        token = uuid.uuid4().hex
        VizqoutePreview.objects.create(
            quotationid=quote,
            sharelink=token,
            expirydate=timezone.now() + timedelta(days=14),
        )

    return redirect("quote_detail", quote_id=quote.id)


@login_required
def client_portal(request, client_id: str):
    profile = _get_profile_or_403(request)
    if not _is_contractor(profile):
        return HttpResponseForbidden("Only contractors can access this page.")

    qs = (
        VizqouteQuotation.objects.filter(contractorid=profile)
        .select_related("clientid")
        .order_by("-createdat")
    )
    if client_id.isdigit():
        qs = qs.filter(clientid_id=int(client_id))
        client_obj = VizqouteClient.objects.filter(
            contractor=profile, id=int(client_id)).first()
    else:
        qs = qs.filter(clientid__name__icontains=client_id)
        client_obj = VizqouteClient.objects.filter(
            contractor=profile, name__icontains=client_id).first()

    paginator = Paginator(qs, 10)
    quotes_page = paginator.get_page(request.GET.get("page"))

    stats = {
        "pending_count": qs.filter(status="draft").count(),
        "total_value": 0,
        "status": qs.first().status if qs.exists() else "No Projects",
    }

    return render(
        request,
        "clientportal.html",
        {"client_quotes": quotes_page, "stats": stats,
            "client_id": client_id, "client_obj": client_obj},
    )


@login_required
def client_portal_self(request):
    return render(request, "clientportal.html", {"client_quotes": [], "stats": {}, "client_id": "me"})


@login_required
def quote_detail(request, quote_id: int):
    profile = _get_profile_or_403(request)
    quote = get_object_or_404(VizqouteQuotation, id=quote_id)
    if quote.contractorid_id != profile.id and not request.user.is_staff:
        return HttpResponseForbidden("Not allowed.")

    items = VizqouteQuoteItem.objects.filter(quotationid=quote)
    roofing_specs = VizqouteRoofingSpec.objects.filter(quotationid=quote)
    preview = VizqoutePreview.objects.filter(
        quotationid=quote).order_by("-createdat").first()
    return render(request, "quote_detail.html", {"quote": quote, "items": items, "roofing_specs": roofing_specs, "preview": preview})


def quote_preview_public(request, token: str):
    preview = get_object_or_404(VizqoutePreview, sharelink=token)
    if preview.expirydate and preview.expirydate < timezone.now():
        return HttpResponseForbidden("This link has expired.")
    preview.accesscount = (preview.accesscount or 0) + 1
    preview.save(update_fields=["accesscount"])

    quote = preview.quotationid
    items = VizqouteQuoteItem.objects.filter(quotationid=quote)
    specs = VizqouteRoofingSpec.objects.filter(quotationid=quote)
    return render(request, "quote_detail.html", {"quote": quote, "items": items, "roofing_specs": specs, "preview": preview, "public": True})


@require_http_methods(["POST"])
def quote_decision_public(request, token: str):
    preview = get_object_or_404(VizqoutePreview, sharelink=token)
    if preview.expirydate and preview.expirydate < timezone.now():
        return JsonResponse({"error": "expired"}, status=403)

    decision = (request.POST.get("decision") or "").strip().lower()
    if decision not in {"approved", "rejected"}:
        return JsonResponse({"error": "decision must be approved or rejected"}, status=400)

    quote = preview.quotationid
    quote.status = decision
    quote.save(update_fields=["status"])
    return JsonResponse({"success": True, "status": quote.status})


@login_required
def view_3d(request):
    return render(request, "3dview.html")


@login_required
def materials_calc(request, quote_id: int):
    """
    Lightweight materials calculation based on latest roofing spec.
    This is a functional baseline you can refine later.
    """
    profile = _get_profile_or_403(request)
    quote = get_object_or_404(VizqouteQuotation, id=quote_id)
    if quote.contractorid_id != profile.id and not request.user.is_staff:
        return HttpResponseForbidden("Not allowed.")

    spec = VizqouteRoofingSpec.objects.filter(
        quotationid=quote).order_by("-createdat").first()
    if not spec:
        return JsonResponse({"error": "No roofing specs for this quote"}, status=400)

    roof_area = float(spec.roofarea or 0)
    waste_pct = float(spec.wastefactor or 0)
    effective_area = roof_area * (1.0 + waste_pct / 100.0)

    squares = effective_area / 100.0  # roofing square = 100 sq ft
    bundles = squares * 3.0  # typical 3 bundles per square for shingles

    # Very rough, configurable later
    underlayment_roll_coverage = 400.0  # sq ft per roll
    underlayment_rolls = effective_area / underlayment_roll_coverage

    nails_per_square_lbs = 1.5
    nails_lbs = squares * nails_per_square_lbs

    return JsonResponse(
        {
            "roof_area_sqft": roof_area,
            "waste_percent": waste_pct,
            "effective_area_sqft": round(effective_area, 2),
            "squares": round(squares, 2),
            "shingle_bundles": int(round(bundles)),
            "underlayment_rolls": int(max(1, round(underlayment_rolls))),
            "roofing_nails_lbs": round(nails_lbs, 1),
            "material_type": spec.materialtype,
            "labor_hours": float(spec.laborhours or 0),
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def blueprint_ocr(request):
    file = request.FILES.get("blueprint")
    if not file:
        return JsonResponse({"error": "No file"}, status=400)
    return JsonResponse(
        {
            "roof_area": 2450,
            "labor_hours": 48,
            "pitch_angle": "6:12",
            "material_type": "Architectural Shingles",
            "waste_factor": 10,
            "success": True,
        }
    )


# ----------------------------
# DRF API (CRUD + analytics)
# ----------------------------


class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def _profile(self) -> VizqouteUser:
        return _get_profile_or_403(self.request)


class VizqouteUserViewSet(TenantScopedViewSet):
    serializer_class = VizqouteUserSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return VizqouteUser.objects.all()
        profile = self._profile()
        return VizqouteUser.objects.filter(id=profile.id)


class VizqouteClientViewSet(TenantScopedViewSet):
    serializer_class = VizqouteClientSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return VizqouteClient.objects.all()
        profile = self._profile()
        return VizqouteClient.objects.filter(contractor=profile)

    def perform_create(self, serializer):
        profile = self._profile()
        serializer.save(contractor=profile)


class VizqouteQuotationViewSet(TenantScopedViewSet):
    serializer_class = VizqouteQuotationSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return VizqouteQuotation.objects.all()
        profile = self._profile()
        if _is_contractor(profile):
            return VizqouteQuotation.objects.filter(contractorid=profile)
        return VizqouteQuotation.objects.none()

    def perform_create(self, serializer):
        profile = self._profile()
        serializer.save(contractorid=profile)


class VizqouteQuoteItemViewSet(TenantScopedViewSet):
    serializer_class = VizqouteQuoteItemSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return VizqouteQuoteItem.objects.all()
        profile = self._profile()
        return VizqouteQuoteItem.objects.filter(quotationid__contractorid=profile)


class VizqouteRoofingSpecViewSet(TenantScopedViewSet):
    serializer_class = VizqouteRoofingSpecSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return VizqouteRoofingSpec.objects.all()
        profile = self._profile()
        return VizqouteRoofingSpec.objects.filter(quotationid__contractorid=profile)


class VizqoutePreviewViewSet(TenantScopedViewSet):
    serializer_class = VizqoutePreviewSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return VizqoutePreview.objects.all()
        profile = self._profile()
        return VizqoutePreview.objects.filter(quotationid__contractorid=profile)


class ContractorQuotesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ContractorQuotesSerializer

    def get_queryset(self):
        profile = _get_profile_or_403(self.request)
        return VizqouteQuotation.objects.filter(contractorid=profile).order_by("-createdat")[:20]


class ClientQuotesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VizqouteQuotationSerializer

    def get_queryset(self):
        profile = _get_profile_or_403(self.request)
        client_id = self.request.query_params.get("client_id")
        qs = VizqouteQuotation.objects.filter(contractorid=profile)
        if client_id and client_id.isdigit():
            qs = qs.filter(clientid_id=int(client_id))
        return qs.order_by("-createdat")


class StatusQuotesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VizqouteQuotationSerializer

    def get_queryset(self):
        profile = _get_profile_or_403(self.request)
        status_param = self.request.query_params.get("status")
        qs = VizqouteQuotation.objects.filter(contractorid=profile)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.order_by("-createdat")


class DashboardStatsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DashboardStatsSerializer

    def get_queryset(self):
        profile = _get_profile_or_403(self.request)
        return (
            VizqouteQuotation.objects.filter(contractorid=profile)
            .values("status")
            .annotate(count=Count("id"))
        )


class QuoteTotalView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        profile = _get_profile_or_403(request)
        quote = get_object_or_404(
            VizqouteQuotation, pk=kwargs["pk"], contractorid=profile)
        total = VizqouteQuoteItem.objects.filter(
            quotationid=quote).aggregate(total_price=Sum("totalprice"))
        return JsonResponse({"quotation_id": quote.id, "total_price": float(total["total_price"] or 0)})


class RevenueReportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        profile = _get_profile_or_403(request)
        total = VizqouteQuoteItem.objects.filter(
            quotationid__contractorid=profile).aggregate(total_revenue=Sum("totalprice"))
        return JsonResponse({"total_revenue": float(total["total_revenue"] or 0)})


class MaterialAnalyticsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        profile = _get_profile_or_403(request)
        data = (
            VizqouteRoofingSpec.objects.filter(
                quotationid__contractorid=profile)
            .values("materialtype")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return JsonResponse({"materials": list(data)})


class RecentQuotesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VizqouteQuotationSerializer

    def get_queryset(self):
        profile = _get_profile_or_403(self.request)
        return VizqouteQuotation.objects.filter(contractorid=profile).order_by("-createdat")[:10]


class QuoteLocationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VizqouteQuotationSerializer

    def get_queryset(self):
        profile = _get_profile_or_403(self.request)
        return (
            VizqouteQuotation.objects.filter(contractorid=profile)
            .exclude(latitude__isnull=True)
            .exclude(longitude__isnull=True)[:50]
        )


class TrackPreviewView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VizqoutePreviewSerializer

    def get_queryset(self):
        profile = _get_profile_or_403(self.request)
        return VizqoutePreview.objects.filter(quotationid__contractorid=profile)

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.accesscount = (instance.accesscount or 0) + 1
        instance.save(update_fields=["accesscount"])
