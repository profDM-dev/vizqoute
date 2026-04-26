from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from . import views
from django.contrib.auth import views as auth_views
# router = DefaultRouter()
# router.register(r'users', VizqouteUserViewSet)
# router.register(r'clients', VizqouteClientViewSet)
# router.register(r'quotations', VizqouteQuotationViewSet)
# router.register(r'quoteitems', VizqouteQuoteItemViewSet)
# router.register(r'roofingspecs', VizqouteRoofingSpecViewSet)
# router.register(r'previews', VizqoutePreviewViewSet)


# Base router for CRUD operations
router = DefaultRouter()
router.register(r'users', views.VizqouteUserViewSet, basename='users')
router.register(r'clients', views.VizqouteClientViewSet, basename='clients')
router.register(r'quotations', views.VizqouteQuotationViewSet,
                basename='quotations')
router.register(r'quoteitems', views.VizqouteQuoteItemViewSet,
                basename='quoteitems')
router.register(r'roofingspecs', views.VizqouteRoofingSpecViewSet,
                basename='roofingspecs')
router.register(r'previews', views.VizqoutePreviewViewSet, basename='previews')


# Custom endpoint patterns

urlpatterns = [

    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # FRONTEND ROUTES
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('quote/', views.quote_builder, name='quote'),
    path('admin/', views.admin_panel, name='admin'),
    path('client/<str:client_id>/', views.client_portal, name='client'),
    path('contractor/', views.contractor_dashboard, name='contractor'),
    path('3Dview/', views.view_3d, name='3dview'),



    # API ROUTES
    path('api/', include(router.urls)),

    # path('contractor/', views.ContractorQuotesListView.as_view()),
    # path('quotes/client/', views.ClientQuotesListView.as_view()),
    # path('quotes/status/', views.StatusQuotesListView.as_view()),
    # path('quotes/dashboard/', views.DashboardStatsView.as_view()),

    # path('quotes/<int:pk>/total/', views.QuoteTotalView.as_view()),
    # path('quotes/revenue/', views.RevenueReportView.as_view()),

    # path('quotes/materials/', views.MaterialAnalyticsView.as_view()),
    # path('quotes/recent/', views.RecentQuotesView.as_view()),

    # path('quotes/<int:pk>/track_preview/', views.TrackPreviewView.as_view()),
    # path('quotes/locations/', views.QuoteLocationsView.as_view()),
    # path('quotes/blueprint-ocr/', views.blueprint_ocr, name='blueprint_ocr'),

    # Quote API routes (GROUPED - no more repetition!)
    path('quotes/', include([
        # Client & Status
        path('client/', views.ClientQuotesListView.as_view(), name='client_quotes'),
        path('status/', views.StatusQuotesListView.as_view(), name='status_quotes'),
        path('dashboard/', views.DashboardStatsView.as_view(),
             name='dashboard_stats'),


        # Quote operations
        path('<int:pk>/total/', views.QuoteTotalView.as_view(), name='quote_total'),
        path('revenue/', views.RevenueReportView.as_view(), name='revenue'),
        path('materials/', views.MaterialAnalyticsView.as_view(), name='materials'),
        path('recent/', views.RecentQuotesView.as_view(), name='recent'),
        path('<int:pk>/track_preview/',
             views.TrackPreviewView.as_view(), name='track_preview'),
        path('locations/', views.QuoteLocationsView.as_view(), name='locations'),
        path('blueprint-ocr/', views.blueprint_ocr, name='blueprint_ocr'),
        path('client/<str:client_id>/', views.client_portal, name='client_portal'),
        path('quote/<int:quote_id>/', views.quote_detail, name='quote_detail'),
    ])),

]
