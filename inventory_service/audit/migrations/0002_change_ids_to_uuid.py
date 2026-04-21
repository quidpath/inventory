# Generated migration to change ID fields from Integer to UUID

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
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
