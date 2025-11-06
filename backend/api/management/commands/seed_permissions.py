"""
Management command to seed permissions and role-permission mappings
"""
from django.core.management.base import BaseCommand
from api.models import Permission, RolePermission


class Command(BaseCommand):
    help = 'Seeds permissions and role-permission mappings'

    def handle(self, *args, **options):
        self.stdout.write('Seeding permissions...')

        # Define all permissions
        permissions_data = [
            # User Management (5)
            {'name': 'view_users', 'category': 'users', 'description': 'View user list and profiles'},
            {'name': 'create_users', 'category': 'users', 'description': 'Create new users'},
            {'name': 'edit_users', 'category': 'users', 'description': 'Edit user information'},
            {'name': 'delete_users', 'category': 'users', 'description': 'Delete users'},
            {'name': 'manage_roles', 'category': 'users', 'description': 'Change user roles and permissions'},

            # Data Access (7)
            {'name': 'view_dashboard', 'category': 'data', 'description': 'View main dashboard'},
            {'name': 'view_analytics', 'category': 'data', 'description': 'View analytics and reports'},
            {'name': 'view_reports', 'category': 'data', 'description': 'View detailed reports'},
            {'name': 'export_data', 'category': 'data', 'description': 'Export data to CSV/PDF'},
            {'name': 'import_data', 'category': 'data', 'description': 'Import data from files'},
            {'name': 'create_tasks', 'category': 'data', 'description': 'Create new tasks'},
            {'name': 'manage_tasks', 'category': 'data', 'description': 'Manage all tasks'},

            # Analytics (3)
            {'name': 'view_basic_analytics', 'category': 'analytics', 'description': 'View basic analytics'},
            {'name': 'view_advanced_analytics', 'category': 'analytics', 'description': 'View advanced analytics'},
            {'name': 'generate_reports', 'category': 'analytics', 'description': 'Generate custom reports'},

            # Settings (3)
            {'name': 'view_settings', 'category': 'settings', 'description': 'View application settings'},
            {'name': 'edit_settings', 'category': 'settings', 'description': 'Edit application settings'},
            {'name': 'manage_billing', 'category': 'settings', 'description': 'Manage billing and subscriptions'},

            # System (4)
            {'name': 'manage_organizations', 'category': 'system', 'description': 'Manage organizations'},
            {'name': 'view_all_data', 'category': 'system', 'description': 'View all organization data'},
            {'name': 'manage_system_settings', 'category': 'system', 'description': 'Manage system-wide settings'},
            {'name': 'view_audit_logs', 'category': 'system', 'description': 'View audit logs'},
        ]

        # Create permissions
        created_count = 0
        for perm_data in permissions_data:
            perm, created = Permission.objects.get_or_create(
                name=perm_data['name'],
                defaults={
                    'category': perm_data['category'],
                    'description': perm_data['description']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created permission: {perm.name}'))
            else:
                self.stdout.write(f'  - Permission exists: {perm.name}')

        self.stdout.write(self.style.SUCCESS(f'\nCreated {created_count} new permissions'))
        self.stdout.write(f'Total permissions: {Permission.objects.count()}')

        # Define role-permission mappings
        role_permissions_map = {
            'superadmin': [
                # Has ALL permissions (handled in code, not database)
            ],
            'admin': [
                # User Management
                'view_users', 'create_users', 'edit_users', 'delete_users', 'manage_roles',
                # Data Access
                'view_dashboard', 'view_analytics', 'view_reports', 'export_data', 'import_data',
                'create_tasks', 'manage_tasks',
                # Analytics
                'view_basic_analytics', 'view_advanced_analytics', 'generate_reports',
                # Settings
                'view_settings', 'edit_settings', 'manage_billing',
                # System
                'view_audit_logs',
            ],
            'manager': [
                # User Management (limited)
                'view_users', 'create_users', 'edit_users',
                # Data Access
                'view_dashboard', 'view_analytics', 'view_reports', 'export_data',
                'create_tasks', 'manage_tasks',
                # Analytics
                'view_basic_analytics', 'view_advanced_analytics', 'generate_reports',
                # Settings
                'view_settings',
            ],
            'analyst': [
                # User Management
                'view_users',
                # Data Access
                'view_dashboard', 'view_analytics', 'view_reports', 'export_data',
                'create_tasks',
                # Analytics
                'view_basic_analytics', 'view_advanced_analytics', 'generate_reports',
                # Settings
                'view_settings',
            ],
            'user': [
                # Data Access (basic)
                'view_dashboard', 'create_tasks',
                # Analytics (basic)
                'view_basic_analytics',
                # Settings (view only)
                'view_settings',
            ],
            'viewer': [
                # Read-only access
                'view_dashboard', 'view_analytics',
                'view_basic_analytics',
            ],
            'volunteer': [
                # Limited access
                'view_dashboard', 'create_tasks',
            ],
        }

        # Create role-permission mappings
        self.stdout.write('\nSeeding role-permission mappings...')
        mapping_count = 0

        for role, permission_names in role_permissions_map.items():
            for perm_name in permission_names:
                try:
                    permission = Permission.objects.get(name=perm_name)
                    role_perm, created = RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission
                    )
                    if created:
                        mapping_count += 1
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  ! Permission not found: {perm_name}')
                    )

        self.stdout.write(self.style.SUCCESS(f'\nCreated {mapping_count} new role-permission mappings'))
        self.stdout.write(f'Total mappings: {RolePermission.objects.count()}')

        # Display summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('RBAC Setup Complete!'))
        self.stdout.write('='*60)

        for role in ['superadmin', 'admin', 'manager', 'analyst', 'user', 'viewer', 'volunteer']:
            perm_count = RolePermission.objects.filter(role=role).count()
            self.stdout.write(f'{role.ljust(15)}: {perm_count} permissions')

        self.stdout.write('\nTo view all permissions: python manage.py shell')
        self.stdout.write('  >>> from api.models import Permission')
        self.stdout.write('  >>> Permission.objects.all()')
