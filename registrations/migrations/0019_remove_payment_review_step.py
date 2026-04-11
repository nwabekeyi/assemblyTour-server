from django.db import migrations


def remove_payment_review_step(apps, schema_editor):
    RegistrationStep = apps.get_model('registrations', 'RegistrationStep')
    HajjRegistration = apps.get_model('registrations', 'HajjRegistration')

    payment_review_step = RegistrationStep.objects.filter(code='payment_review').first()
    document_upload_step = RegistrationStep.objects.filter(code='document_upload').first()

    if payment_review_step and document_upload_step:
        HajjRegistration.objects.filter(current_step=payment_review_step).update(current_step=document_upload_step)

    if payment_review_step:
        payment_review_step.is_active = False
        payment_review_step.save(update_fields=['is_active'])


def restore_payment_review_step(apps, schema_editor):
    RegistrationStep = apps.get_model('registrations', 'RegistrationStep')
    RegistrationStep.objects.filter(code='payment_review').update(is_active=True)


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0018_supportticket_assigned_to_alter_supportticket_status'),
    ]

    operations = [
        migrations.RunPython(remove_payment_review_step, restore_payment_review_step),
    ]
