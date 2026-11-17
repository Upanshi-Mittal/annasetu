import csv

from django.conf import settings
from django.contrib import admin
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils.html import format_html

from accounts.models import User


def export_users_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="annasetu_users.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Email', 'Role', 'Organization', 'Verified', 'Reliability'])
    for u in queryset:
        writer.writerow([u.id, u.username, u.email, u.role, u.organization_name, u.is_verified, u.reliability_score])
    return response

export_users_csv.short_description = "Export Selected Users to CSV"


@admin.action(description="Approve selected organizations/users")
def approve_verification(modeladmin, request, queryset):
    for user in queryset:
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        if user.email:
            send_mail(
                subject="[AnnaSetu] Verification Approved",
                message=f"Hello {user.display_name},\n\nYour organization verification on AnnaSetu has been approved. You can now claim or post donations freely.\n\nThank you,\nAnnaSetu Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )


@admin.action(description="Reject verification for selected users")
def reject_verification(modeladmin, request, queryset):
    for user in queryset:
        user.is_verified = False
        user.save(update_fields=['is_verified'])
        if user.email:
            send_mail(
                subject="[AnnaSetu] Verification Update",
                message=f"Hello {user.display_name},\n\nYour organization verification request on AnnaSetu requires additional details. Please re-upload your valid registration certificate.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'role', 'organization_name', 'phone', 'is_verified', 'document_preview', 'reliability_score']
    list_filter = ['role', 'is_verified', 'is_active']
    search_fields = ['username', 'email', 'organization_name', 'phone']
    actions = [approve_verification, reject_verification, export_users_csv]

    def document_preview(self, obj):
        if obj.verification_doc:
            return format_html('<a href="{}" target="_blank" class="button">View Doc</a>', obj.verification_doc.url)
        return "No Document"
    document_preview.short_description = "Verification Doc"
