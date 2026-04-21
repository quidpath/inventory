# Generated migration to safely change ID fields from Integer to UUID

from django.db import migrations, models, connection
import uuid


def convert_integer_to_uuid_safe(apps, schema_editor):
    """
    Safely convert integer IDs to UUIDs by clearing existing data first.
    This is necessary because integer values cannot be directly cast to UUID.
    Only clears data if tables exist.
    """
    # Check if tables exist before trying to delete
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'audit_transactionlog'
            );
        """)
        transactionlog_exists = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'audit_notification'
            );
        """)
        notification_exists = cursor.fetchone()[0]
    
    # Only delete if tables exist
    if transactionlog_exists:
        TransactionLog = apps.get_model('audit', 'TransactionLog')
        TransactionLog.objects.all().delete()
    
    if notification_exists:
        Notification = apps.get_model('audit', 'Notification')
        Notification.objects.all().delete()


def reverse_conversion(apps, schema_editor):
    """
    Reverse the conversion - clear data again since we can't convert UUID back to int
    Only clears data if tables exist.
    """
    # Check if tables exist before trying to delete
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'audit_transactionlog'
            );
        """)
        transactionlog_exists = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'audit_notification'
            );
        """)
        notification_exists = cursor.fetchone()[0]
    
    # Only delete if tables exist
    if transactionlog_exists:
        TransactionLog = apps.get_model('audit', 'TransactionLog')
        TransactionLog.objects.all().delete()
    
    if notification_exists:
        Notification = apps.get_model('audit', 'Notification')
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