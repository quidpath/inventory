# Generated migration to safely change ID fields from Integer to UUID
# NOTE: This migration is only needed for existing databases with integer IDs.
# For fresh databases, 0001_initial already creates UUID fields.

from django.db import migrations, models, connection
from django.db.utils import ProgrammingError
import uuid


def convert_integer_to_uuid_safe(apps, schema_editor):
    """
    Safely convert integer IDs to UUIDs by clearing existing data first.
    This is necessary because integer values cannot be directly cast to UUID.
    Only clears data if tables exist and fields need conversion.
    """
    # Check if tables exist
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'audit_transactionlog'
            );
        """)
        transactionlog_exists = cursor.fetchone()[0]
        
        if not transactionlog_exists:
            # Tables don't exist yet, skip this migration
            return
        
        # Check if the field is already UUID type
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'audit_transactionlog' 
            AND column_name = 'user_id';
        """)
        result = cursor.fetchone()
        if result and result[0] == 'uuid':
            # Already UUID, nothing to do
            return
    
    # Only clear data if we need to convert
    TransactionLog = apps.get_model('audit', 'TransactionLog')
    TransactionLog.objects.all().delete()
    
    Notification = apps.get_model('audit', 'Notification')
    Notification.objects.all().delete()


def reverse_conversion(apps, schema_editor):
    """
    Reverse the conversion - clear data again since we can't convert UUID back to int
    """
    pass  # No-op for reverse


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