from tenants.context import obtener_tenant_db_alias


class TenantMasterRouter:
    app_label = "tenants"

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return "master"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return "master"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        labels = {obj1._meta.app_label, obj2._meta.app_label}

        if self.app_label in labels:
            return labels == {self.app_label}

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            return db == "master"

        if db == "master":
            return False

        return None


class TenantOperationalRouter:
    app_label_master = "tenants"

    def db_for_read(self, model, **hints):
        return self._db_operativa(model)

    def db_for_write(self, model, **hints):
        return self._db_operativa(model)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label_master:
            return None

        if self._es_base_tenant(db):
            return True

        return None

    def _db_operativa(self, model):
        if model._meta.app_label == self.app_label_master:
            return None

        return obtener_tenant_db_alias() or None

    def _es_base_tenant(self, db):
        return db.startswith("tenant_")
