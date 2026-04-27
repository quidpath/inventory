"""
Management command to create default storage locations for warehouses that don't have any
"""
from django.core.management.base import BaseCommand
from inventory_service.warehouse.models import Warehouse, StorageLocation


class Command(BaseCommand):
    help = 'Create default storage locations for warehouses without any locations'

    def handle(self, *args, **options):
        warehouses = Warehouse.objects.filter(is_active=True)
        created_count = 0
        
        for warehouse in warehouses:
            # Check if warehouse has any locations
            if not warehouse.locations.exists():
                # Create default location
                StorageLocation.objects.create(
                    warehouse=warehouse,
                    name="Main Storage",
                    complete_name="Main Storage",
                    location_type="internal",
                    is_active=True,
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created default location for warehouse: {warehouse.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} default storage locations')
        )
