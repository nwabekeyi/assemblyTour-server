from django.contrib import admin
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from .models import NewsletterRequest, Newsletter
import threading


@admin.register(NewsletterRequest)
class NewsletterRequestAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at']
    search_fields = ['email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        # Could add CSV export functionality here
        pass
    export_as_csv.short_description = "Export selected emails as CSV"


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['subject', 'created_by', 'sent_at', 'created_at']
    search_fields = ['subject', 'message']
    readonly_fields = ['created_at', 'sent_at', 'created_by']
    ordering = ['-created_at']
    actions = ['send_to_subscribers']

    fieldsets = (
        ("Content", {
            "fields": (
                "subject",
                "message",
            )
        }),
        ("Status", {
            "fields": (
                "sent_at",
                "created_at",
                "created_by",
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def send_to_subscribers(self, request, queryset):
        subscribers = list(NewsletterRequest.objects.values_list('email', flat=True))
        
        if not subscribers:
            self.message_user(request, "No subscribers found!", level=20)
            return

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Assembly Travels Newsletter</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4;">
                <tr>
                    <td align="center" style="padding: 20px;">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #059669 0%, #0d9488 100%); padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Assembly Travels</h1>
                                    <p style="color: #d1fae5; margin: 10px 0 0 0; font-size: 14px;">Your Journey Begins Here</p>
                                </td>
                            </tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px; color: #333333;">
                                    <h2 style="color: #059669; margin: 0 0 20px 0; font-size: 24px;">{{subject}}</h2>
                                    <div style="font-size: 16px; line-height: 1.6; color: #4b5563;">
                                        {{message}}
                                    </div>
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #1f2937; padding: 30px; text-align: center;">
                                    <p style="color: #9ca3af; margin: 0 0 10px 0; font-size: 12px;">
                                        Assembly Travels | Your Trusted Travel Partner
                                    </p>
                                    <p style="color: #6b7280; margin: 0; font-size: 11px;">
                                        You're receiving this because you subscribed to our newsletter.
                                    </p>
                                </td>
                            </tr>
                        </table>
                        <table width="600" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
                            <tr>
                                <td style="text-align: center; padding: 20px;">
                                    <a href="https://assemblytours.com" style="color: #059669; text-decoration: none; font-size: 12px; margin: 0 10px;">Website</a>
                                    <a href="https://assemblytours.com/contact" style="color: #059669; text-decoration: none; font-size: 12px; margin: 0 10px;">Contact</a>
                                    <a href="#" style="color: #9ca3af; text-decoration: none; font-size: 12px; margin: 0 10px;">Unsubscribe</a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        def send_newsletter_background(newsletter_id, subject, message, html_template, subscribers, user_id):
            from .models import Newsletter
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            newsletter = Newsletter.objects.get(id=newsletter_id)
            html_content = html_template.replace('{{subject}}', subject).replace('{{message}}', message.replace('\n', '<br>'))
            text_content = f"{subject}\n\n{message}\n\n---\nAssembly Travels\nYour Trusted Travel Partner"
            
            msg = EmailMultiAlternatives(
                subject=f"[Assembly Travels] {subject}",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                bcc=subscribers,
            )
            msg.attach_alternative(html_content, 'text/html')
            msg.send(fail_silently=False)
            
            newsletter.sent_at = timezone.now()
            if user_id:
                newsletter.created_by = User.objects.get(id=user_id)
            newsletter.save()

        count = 0
        for newsletter in queryset:
            try:
                thread = threading.Thread(
                    target=send_newsletter_background,
                    args=(
                        newsletter.id,
                        newsletter.subject,
                        newsletter.message,
                        html_template,
                        subscribers,
                        request.user.id,
                    )
                )
                thread.start()
                count += 1
            except Exception as e:
                self.message_user(request, f"Failed to queue: {str(e)}", level=20)
                return

        self.message_user(request, f"Queued {count} newsletter(s) to send to {len(subscribers)} subscribers! Emails will be sent in the background.")
    
    send_to_subscribers.short_description = "Send selected newsletter(s) to subscribers"