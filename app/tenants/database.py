from copy import deepcopy

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError


def alias_para_tenant(slug):
    return f"tenant_{slug.replace('-', '_')}"


def configurar_base_tenant(tenant):
    alias = alias_para_tenant(tenant.slug)
    config = deepcopy(settings.DATABASES["default"])
    config["NAME"] = tenant.db_name
    settings.DATABASES[alias] = config
    connections.databases[alias] = config
    return alias


def configurar_base_admin_tenants():
    alias = "tenant_admin"
    config = deepcopy(settings.DATABASES["default"])
    config["NAME"] = settings.TENANT_ADMIN_DB_NAME
    settings.DATABASES[alias] = config
    connections.databases[alias] = config
    return alias


def crear_base_datos_tenant(db_name):
    alias = configurar_base_admin_tenants()
    connection = connections[alias]
    connection.ensure_connection()
    connection.inc_thread_sharing()

    try:
        connection.connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [db_name])

            if cursor.fetchone():
                return False

            db_name_sql = connection.ops.quote_name(db_name)
            cursor.execute(f"CREATE DATABASE {db_name_sql}")
            return True
    except (OperationalError, ProgrammingError):
        raise
    finally:
        connection.dec_thread_sharing()
        connection.close()
