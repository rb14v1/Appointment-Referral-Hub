"""
Postgres-only migration operations that no-op gracefully on any other
database vendor (SQLite, in particular, used for local/dev/test runs on a
machine without a Postgres server — see config/settings/base.py USE_SQLITE).

Django's migration *state* (what the ORM thinks the schema looks like) is
still updated normally; only the actual DDL execution against the database
is skipped on non-Postgres backends. This lets `manage.py migrate` succeed
against SQLite while still producing the real exclusion constraint + btree_gist
extension against Postgres in the real deployment.
"""
from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations


class ConditionalBtreeGistExtension(BtreeGistExtension):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)


class ConditionalAddConstraint(migrations.AddConstraint):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)
