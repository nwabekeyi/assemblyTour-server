from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_registration_email(user_email, step_title, step_status, registration_id):
    """Send email notification for registration step events.
    
    Args:
        user_email: User's email address
        step_title: The title of the step
        step_status: Status of the step - 'passed', 'failed', or 'cancelled'
        registration_id: The registration ID
    """
    if not user_email:
        logger.warning(f"Cannot send email: no email address for registration {registration_id}")
        return False

    status_messages = {
        'passed': {
            'subject': f'✅ Registration Step Passed - {step_title}',
            'body': f'''Congratulations!

Your registration (ID: {registration_id}) has progressed past the "{step_title}" step.

What happens next?
- Continue completing the remaining steps
- Your application is being processed

If you have any questions, please contact support.

Best regards,
Assembly Travels Team''',
        },
        'failed': {
            'subject': f'❌ Registration Step Revision Needed - {step_title}',
            'body': f'''Hello,

We need some additional information for your registration (ID: {registration_id}).

The "{step_title}" step requires revision. Please log in to your dashboard to review and make the necessary corrections.

If you believe this is an error, please contact support.

Best regards,
Assembly Travels Team''',
        },
        'cancelled': {
            'subject': '❌ Registration Cancelled',
            'body': f'''Hello,

Your registration (ID: {registration_id}) has been cancelled.

If you would like to start a new registration, please visit our packages page.

Best regards,
Assembly Travels Team''',
        },
    }

    if step_status not in status_messages:
        logger.warning(f"Unknown step status: {step_status}")
        return False

    message = status_messages[step_status]

    try:
        send_mail(
            subject=message['subject'],
            message=message['body'],
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info(f"Email sent to {user_email} for registration {registration_id}, status: {step_status}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {str(e)}")
        return False


def send_step_approved_email(user_email, step_title, registration_id):
    """Send email when a step is approved by admin."""
    return send_registration_email(user_email, step_title, 'passed', registration_id)


def send_step_rejected_email(user_email, step_title, registration_id):
    """Send email when a step is rejected by admin."""
    return send_registration_email(user_email, step_title, 'failed', registration_id)


def send_registration_cancelled_email(user_email, registration_id):
    """Send email when registration is cancelled."""
    return send_registration_email(user_email, '', 'cancelled', registration_id)


def send_support_ticket_email(admin_email, user_email, user_name, subject, message, category, ticket_id):
    """Send email notification to admin when a support ticket is created."""
    if not admin_email:
        logger.warning("Cannot send support ticket email: no admin email configured")
        return False

    category_labels = {
        'general': 'General Inquiry',
        'payment': 'Payment Issue',
        'document': 'Document Issue',
        'visa': 'Visa Inquiry',
        'package': 'Package/Booking',
        'technical': 'Technical Issue',
        'other': 'Other',
    }

    email_subject = f"🎫 New Support Ticket #{ticket_id} - {category_labels.get(category, category)}"
    email_body = f'''New Support Ticket Created

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TICKET DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticket ID: #{ticket_id}
Category: {category_labels.get(category, category)}
Status: OPEN
Created: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━���━━━━━━━━━━━
Name: {user_name}
Email: {user_email}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MESSAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subject: {subject}

{message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reply to this ticket in the admin dashboard.
'''

    try:
        send_mail(
            subject=email_subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        logger.info(f"Support ticket email sent to {admin_email} for ticket #{ticket_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send support ticket email: {str(e)}")
        return False


def send_support_ticket_closed_email(user_email, ticket_id, subject, response):
    """Send email to user when their support ticket is closed."""
    if not user_email:
        logger.warning("Cannot send ticket closed email: no user email")
        return False

    email_subject = f"✅ Support Ticket Closed - #{ticket_id}"
    email_body = f'''Hello,

Your support ticket has been closed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TICKET DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticket ID: #{ticket_id}
Subject: {subject}
Status: CLOSED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{response}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If you need further assistance, please create a new support ticket.

Best regards,
Assembly Travels Team'''

    try:
        send_mail(
            subject=email_subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info(f"Ticket closed email sent to {user_email} for ticket #{ticket_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send ticket closed email: {str(e)}")
        return False


def send_admin_notification_email(admin_email, subject, message_body):
    """Send email notification to admin."""
    if not admin_email:
        logger.warning("Cannot send admin notification: no admin email")
        return False

    try:
        send_mail(
            subject=subject,
            message=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        logger.info(f"Admin notification sent to {admin_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send admin notification: {str(e)}")
        return False


def notify_admins_of_registration_event(admin_emails, event_type, user_name, registration_id, step_title=""):
    """Notify admins when user completes a registration step or uploads documents."""
    if not admin_emails:
        return False

    event_info = {
        'registration': {
            'subject': f'📝 New Registration - {user_name}',
            'body': f'''New user registration created.

User: {user_name}
Registration ID: {registration_id}
Step: {step_title}

Please review in admin dashboard.''',
        },
        'document_upload': {
            'subject': f'📄 Documents Uploaded - {user_name}',
            'body': f'''User has uploaded documents.

User: {user_name}
Registration ID: {registration_id}

Please review in admin dashboard.''',
        },
        'payment_upload': {
            'subject': f'💳 Payment Submitted - {user_name}',
            'body': f'''User has submitted payment proof.

User: {user_name}
Registration ID: {registration_id}

Please review and approve in admin dashboard.''',
        },
        'step_completed': {
            'subject': f'✅ Step Completed - {user_name}',
            'body': f'''User has completed a step.

User: {user_name}
Registration ID: {registration_id}
Step: {step_title}

Please review in admin dashboard.''',
        },
    }

    event = event_info.get(event_type)
    if not event:
        return False

    for admin_email in admin_emails:
        send_admin_notification_email(admin_email, event['subject'], event['body'])

    return True


def send_login_credentials_email(user_email, username, temp_password, package_name):
    """Send login credentials to user after registration."""
    if not user_email:
        logger.warning("Cannot send login credentials: no user email")
        return False

    email_subject = "🔐 Your Assembly Travels Login Credentials"
    email_body = f'''Welcome to Assembly Travels!

Thank you for registering for the {package_name} package.

Here are your login credentials:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USERNAME: {username}
PASSWORD: {temp_password}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please login and change your password immediately for security purposes.

Login URL: https://assemblytravels.com/login

If you did not initiate this registration, please contact support immediately.

Best regards,
Assembly Travels Team'''

    try:
        send_mail(
            subject=email_subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info(f"Login credentials sent to {user_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send login credentials to {user_email}: {str(e)}")
        return False

    email_subject = f"✅ Support Ticket Closed - #{ticket_id}"
    email_body = f'''Hello,

Your support ticket has been closed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TICKET DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticket ID: #{ticket_id}
Subject: {subject}
Status: CLOSED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{response}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If you need further assistance, please create a new support ticket.

Best regards,
Assembly Travels Team'''

    try:
        send_mail(
            subject=email_subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info(f"Ticket closed email sent to {user_email} for ticket #{ticket_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send ticket closed email: {str(e)}")
        return False