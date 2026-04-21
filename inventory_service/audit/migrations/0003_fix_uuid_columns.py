# Generated migration to fix UUID columns that are still integer type
from django.db import migrations


def fix_uuid_columns(apps, schema_editor):
    """
    Force convert integer columns to UUID using raw SQL.
    This is necessary because AlterField doesn't always work for integer->UUID conversion.
    """
    with schema_editor.connection.cursor() as cursor:
        # Check if columns are still integer type
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'audit_transactionlog' 
            AND column_name = 'user_id';
        """)
        result = cursor.fetchone()
        
        if result and result[0] != 'uuid':
            # Clear existing data first (can't convert integer to UUID)
            cursor.execute("TRUNCATE TABLE audit_transactionlog CASCADE;")
            cursor.execute("TRUNCATE TABLE audit_notification CASCADE;")
            
            # Drop constraints that reference the columns
            cursor.execute("""
                ALTER TABLE audit_transactionlog 
                DROP CONSTRAINT IF EXISTS audit_transactionlog_user_id_check;
            """)
            cursor.execute("""
                ALTER TABLE audit_transactionlog 
                DROP CONSTRAINT IF EXISTS audit_transactionlog_corporate_id_check;
            """)
            
            # Convert columns to UUID
            cursor.execute("""
                ALTER TABLE audit_transactionlog 
                ALTER COLUMN user_id DROP DEFAULT,
                ALTER COLUMN user_id TYPE uuid USING NULL;
            """)
            cursor.execute("""
                ALTER TABLE audit_transactionlog 
                ALTER COLUMN corporate_id DROP DEFAULT,
                ALTER COLUMN corporate_id TYPE uuid USING NULL;
            """)
            cursor.execute("""
                ALTER TABLE audit_notification 
                ALTER COLUMN recipient_id DROP DEFAULT,
                ALTER COLUMN recipient_id TYPE uuid USING NULL;
            """)
            cursor.execute("""
                ALTER TABLE audit_notification 
                ALTER COLUMN corporate_id DROP DEFAULT,
                ALTER COLUMN corporate_id TYPE uuid USING NULL;
            """)


def reverse_fix(apps, schema_editor):
    """Reverse is not supported - would lose data"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0002_change_ids_to_uuid'),
    ]

    operations = [
        migrations.RunPython(fix_uuid_columns, reverse_fix),
    ]
