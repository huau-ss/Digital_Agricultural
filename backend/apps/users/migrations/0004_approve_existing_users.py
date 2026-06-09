# Generated manually - approve all existing active users
from django.db import migrations


def approve_active_users(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    # 只批准已经激活的现有用户，避免彻底封禁
    CustomUser.objects.filter(is_active=True).update(is_approved=True)


def unapprove_all(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    CustomUser.objects.all().update(is_approved=False)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_add_is_approved'),
    ]

    operations = [
        migrations.RunPython(approve_active_users, unapprove_all),
    ]
