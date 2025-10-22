"""Configuration for the repository app."""
import sys
from django.apps import AppConfig
from django.db import connection, OperationalError


class RepositoryConfig(AppConfig):
    """Configuration for the repository app.
    
    params:
        AppConfig (django.apps): Base class for configuring a Django app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "repository"

    def ready(self):
        # Don't run on management commands like makemigrations/migrate/test
        if any(cmd in sys.argv for cmd in ("makemigrations", "migrate", "test", "collectstatic")):
            return

        sql = """
        CREATE OR REPLACE FUNCTION reset_users_id_seq() RETURNS trigger AS $$
        BEGIN
          -- if table empty: set sequence value to 1 and mark NOT called so nextval() returns 1
          -- if table non-empty: set sequence value to max(id) and mark called so nextval() returns max(id)+1
          PERFORM setval(
            pg_get_serial_sequence('"users"', 'id'),
            (SELECT COALESCE(MAX(id), 1) FROM "users"),
            (SELECT CASE WHEN MAX(id) IS NULL THEN false ELSE true END FROM "users")
          );
          RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS reset_users_id_seq_trg ON "users";
        CREATE TRIGGER reset_users_id_seq_trg
          AFTER DELETE ON "users"
          FOR EACH STATEMENT
          EXECUTE FUNCTION reset_users_id_seq();
        """

        try:
            with connection.cursor() as cur:
                # try to acquire an advisory lock so only one process runs this at a time
                cur.execute("SELECT pg_try_advisory_lock(%s);", [123456789])
                locked = cur.fetchone()[0]
                if not locked:
                    return
                cur.execute(sql)
                cur.execute("SELECT pg_advisory_unlock(%s);", [123456789])
        except (OperationalError, RuntimeError):
            # DB might not be available yet (startup/migration). Ignore failures.
            return
