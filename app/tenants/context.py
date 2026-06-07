from contextvars import ContextVar


_tenant_db_alias = ContextVar("tenant_db_alias", default="")


def activar_tenant_db(alias):
    return _tenant_db_alias.set(alias or "")


def limpiar_tenant_db(token=None):
    if token is None:
        _tenant_db_alias.set("")
        return

    _tenant_db_alias.reset(token)


def obtener_tenant_db_alias():
    return _tenant_db_alias.get()
