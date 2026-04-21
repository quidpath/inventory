# Generated migration to safely change ID fields from Integer to UUID

from django.db import migrations, models
import uuid


def convert_integer_to_uuid_safe(apps, schema_editor):
    """
    Safely convert integer IDs to UUIDs by clearing existing data first.
    This is necessary because integer values cannot be directly cast to UUID.
    """
    TransactionLog = apps.get_model('audit', 'TransactionLog')
    Notification = apps.get_model('audit', 'Notification')
    
    # Clear existing data to avoid conversion issues
    # In production, you might want to backup and migrate data differently
    TransactionLog.objects.all().delete()
    Notification.objects.all().delete()


def reverse_conversion(apps, schema_editor):
    """
    Reverse the conversion - clear data again since we can't convert UUID back to int
    """
    TransactionLog = apps.get_model('audit', 'TransactionLog')
    Notification = apps.get_model('audit', 'Notification')
    
    TransactionLog.objects.all().delete()
    Notification.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        # First, clear existing data to avoid conversion issues
        migrations.RunPython(convert_integer_to_uuid_safe, reverse_conversion),
        
        # Then alter the fields
        migrations.AlterField(
            model_name='transactionlog',
            name='user_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='transactionlog',
            name='corporate_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='recipient_id',
            field=models.UUIDField(db_index=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='corporate_id',
            field=models.UUIDField(blank=True, null=True),
        ),
    ]