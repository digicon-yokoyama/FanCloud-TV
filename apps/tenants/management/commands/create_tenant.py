from django.core.management.base import BaseCommand
from apps.tenants.models import Tenant, Domain


class Command(BaseCommand):
    help = 'Create a new tenant with domain'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Tenant name')
        parser.add_argument('domain', type=str, help='Domain name')
        parser.add_argument('schema', type=str, help='Schema name')

    def handle(self, *args, **options):
        tenant_name = options['name']
        domain_name = options['domain']
        schema_name = options['schema']

        # Create tenant
        tenant = Tenant(
            name=tenant_name,
            schema_name=schema_name,
        )
        tenant.save()

        # Create domain
        domain = Domain(
            domain=domain_name,
            tenant=tenant,
            is_primary=True
        )
        domain.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created tenant "{tenant_name}" with domain "{domain_name}"'
            )
        )