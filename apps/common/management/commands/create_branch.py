from django.core.management.base import BaseCommand
from apps.acounts.models import Branch


class Command(BaseCommand):
    help = 'Create a new branch'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, help='Branch name (e.g., "Kathmandu Branch")')
        parser.add_argument('--code', type=str, help='Branch code (e.g., "KTM")')
        parser.add_argument('--address', type=str, help='Branch address', default='')
        parser.add_argument('--phone', type=str, help='Branch phone', default='')
        parser.add_argument('--email', type=str, help='Branch email', default='')

    def handle(self, *args, **options):
        name = options.get('name')
        code = options.get('code')
        address = options.get('address', '')
        phone = options.get('phone', '')
        email = options.get('email', '')

        if not name or not code:
            self.stdout.write(self.style.ERROR('❌ Branch name and code are required!'))
            self.stdout.write(self.style.WARNING('\nUsage:'))
            self.stdout.write('  python manage.py create_branch --name "Branch Name" --code "CODE"')
            self.stdout.write('\nOptional arguments:')
            self.stdout.write('  --address "Branch Address"')
            self.stdout.write('  --phone "+977-1234567"')
            self.stdout.write('  --email "branch@example.com"')
            return

        # Check if branch already exists
        if Branch.objects.filter(code=code).exists():
            self.stdout.write(self.style.ERROR(f'❌ Branch with code "{code}" already exists!'))
            return

        # Create branch
        branch = Branch.objects.create(
            name=name,
            code=code,
            address=address,
            phone=phone,
            email=email,
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS('\n✅ Branch created successfully!'))
        self.stdout.write(f'   ID: {branch.id}')
        self.stdout.write(f'   Name: {branch.name}')
        self.stdout.write(f'   Code: {branch.code}')
        if address:
            self.stdout.write(f'   Address: {branch.address}')
        if phone:
            self.stdout.write(f'   Phone: {branch.phone}')
        if email:
            self.stdout.write(f'   Email: {branch.email}')
        self.stdout.write(f'   Status: {"Active" if branch.is_active else "Inactive"}')
