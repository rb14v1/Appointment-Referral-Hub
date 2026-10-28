"""
Adds the PostgreSQL-only overlap-prevention exclusion constraint for
Appointment (see appointments/models.py for the full rationale).

Both operations are wrapped in the guarded classes from
common/migration_operations.py: on a non-PostgreSQL backend (e.g. SQLite,
used for local/dev/test runs on a machine without Postgres - see
config/settings/base.py USE_SQLITE) they update Django's migration *state*
as normal but skip the actual DDL, so `manage.py migrate`/`test` still
succeed. On real PostgreSQL they behave exactly like the stock
BtreeGistExtension / AddConstraint operations they wrap.
"""
import django.contrib.postgres.constraints
from django.db import migrations, models

from common.migration_operations import ConditionalAddConstraint, ConditionalBtreeGistExtension


class Migration(migrations.Migration):

    dependencies = [
        ("appointments", "0001_initial"),
    ]

    operations = [
        ConditionalBtreeGistExtension(),
        ConditionalAddConstraint(
            model_name="appointment",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                name="exclude_overlapping_active_appointments_per_provider",
                expressions=[
                    ("provider", "="),
                    (models.Func("start_time", "end_time", function="tstzrange"), "&&"),
                ],
                condition=models.Q(("status__in", ["requested", "confirmed", "checked_in"])),
            ),
        ),
    ]
