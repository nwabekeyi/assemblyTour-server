# urls.py
from django.urls import path
from .views import (
    MyHajjRegistrationView,
    AccountSetupView,
    RegistrationFormView,
    DocumentUploadView,
    AdminApproveDocumentReviewView,
    AdminUploadTravelDocumentView,
    UserUploadPaymentProofView,
    MyTravelDocumentsView,
    AdminListRegistrationsView,
    AdminUpdateJourneyDetailsView,
    MySupportTicketsView,
    CreateSupportTicketView,
    SupportTicketDetailView,
    SupportTicketReplyView,
    UserStatsView,
    RegistrationProgressView,
    ManasikGuidanceView,
    EmergencyContactsView,
    TravelHistoryView,
    CancelRegistrationView,
    StartNewRegistrationView,
    AdminSupportTicketListView,
    AdminAssignTicketView,
    AdminCloseTicketView,
)

urlpatterns = [
    # ─── Current / existing endpoint ─────────────────────────────────────
    path('registration/my/', MyHajjRegistrationView.as_view(), name='my-hajj-registration'),

    # ─── Step 1 – Change username & password ─────────────────────────────
    path('hajj/step/account-setup/', AccountSetupView.as_view(), name='hajj-account-setup'),

    # ─── Step 2 – Fill personal details (user model) ─────────────────────
    path('hajj/step/registration-form/', RegistrationFormView.as_view(), name='hajj-registration-form'),

    # ─── Step 3 – Upload passport & yellow card ──────────────────────────
    path('hajj/step/document-upload/', DocumentUploadView.as_view(), name='hajj-document-upload'),

    # ─── Travel Documents (User) ─────────────────────────────────────────
    path('hajj/travel-documents/', MyTravelDocumentsView.as_view(), name='my-travel-documents'),

    # ─── Payment Step (User) ─────────────────────────────────────────
    path('hajj/step/payment-upload/', UserUploadPaymentProofView.as_view(), name='user-payment-upload'),

    # ─── Admin: List all registrations ────────────────────────────────────
    path('admin/hajj/registrations/', AdminListRegistrationsView.as_view(), name='admin-list-registrations'),

    # ─── Admin: Approve/Reject Document Review ───────────────────────────
    path('admin/hajj/<str:registration_id>/document-review/', AdminApproveDocumentReviewView.as_view(), name='admin-document-review'),

    # ─── Admin: Upload Travel Documents for User ────────────────────────
    path('admin/hajj/<str:registration_id>/travel-document/', AdminUploadTravelDocumentView.as_view(), name='admin-upload-travel-document'),

    # ─── Admin: Update Journey Details ───────────────────────────────────
    path('admin/hajj/<str:registration_id>/journey-details/', AdminUpdateJourneyDetailsView.as_view(), name='admin-journey-details'),

    # ─── Support Tickets ─────────────────────────────────────────────
    path('support/tickets/', MySupportTicketsView.as_view(), name='my-support-tickets'),
    path('support/tickets/create/', CreateSupportTicketView.as_view(), name='create-support-ticket'),
    path('support/tickets/<int:ticket_id>/', SupportTicketDetailView.as_view(), name='support-ticket-detail'),
    path('support/tickets/<int:ticket_id>/reply/', SupportTicketReplyView.as_view(), name='support-ticket-reply'),

    # ─── User Stats & Travel History ───────────────────────────────
    path('user/stats/', UserStatsView.as_view(), name='user-stats'),
    path('user/progress/', RegistrationProgressView.as_view(), name='registration-progress'),

    # ─── Manasik Guidance ─────────────────────────────────────
    path('guidance/manasik/', ManasikGuidanceView.as_view(), name='manasik-guidance'),

    # ─── Emergency Contacts ────────────────────────────────
    path('emergency/contacts/', EmergencyContactsView.as_view(), name='emergency-contacts'),

    # ─── Travel History (Paginated) ─────────────────────
    path('travel/history/', TravelHistoryView.as_view(), name='travel-history'),

    # ─── Cancel Registration (Admin Only) ──────────────
    path('admin/registration/<int:registration_id>/cancel/', CancelRegistrationView.as_view(), name='cancel-registration'),

    # ─── Start New Registration (User) ──────────────
    path('registration/start/', StartNewRegistrationView.as_view(), name='start-new-registration'),

    # ─── Admin: Support Ticket Management ──────────────
    path('admin/support/tickets/', AdminSupportTicketListView.as_view(), name='admin-support-tickets'),
    path('admin/support/tickets/<int:ticket_id>/assign/', AdminAssignTicketView.as_view(), name='admin-assign-ticket'),
    path('admin/support/tickets/<int:ticket_id>/close/', AdminCloseTicketView.as_view(), name='admin-close-ticket'),
]