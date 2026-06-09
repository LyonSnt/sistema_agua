TENANT_MODULES = (
    ("panel", "Panel principal"),
    ("abonados", "Abonados"),
    ("medidores", "Medidores"),
    ("lecturas", "Lecturas"),
    ("facturacion", "Facturacion"),
    ("pagos", "Pagos"),
    ("reportes", "Reportes"),
    ("multas", "Multas"),
    ("servicios", "Servicios"),
    ("auditoria", "Auditoria"),
    ("admin", "Administracion"),
)

TENANT_MODULE_KEYS = tuple(key for key, _label in TENANT_MODULES)


def modulos_por_defecto():
    return list(TENANT_MODULE_KEYS)


def normalizar_modulos(modulos):
    if not modulos:
        return modulos_por_defecto()

    validos = set(TENANT_MODULE_KEYS)
    return [modulo for modulo in modulos if modulo in validos]


def tenant_tiene_modulo(tenant, modulo):
    if not tenant:
        return True

    if modulo not in TENANT_MODULE_KEYS:
        return True

    return modulo in normalizar_modulos(getattr(tenant, "modulos_habilitados", []))


def parsear_modulos(valor):
    if not valor:
        return modulos_por_defecto()

    modulos = [
        modulo.strip()
        for modulo in valor.split(",")
        if modulo.strip()
    ]
    desconocidos = [
        modulo
        for modulo in modulos
        if modulo not in TENANT_MODULE_KEYS
    ]

    if desconocidos:
        disponibles = ", ".join(TENANT_MODULE_KEYS)
        raise ValueError(
            "Modulos desconocidos: "
            f"{', '.join(desconocidos)}. Disponibles: {disponibles}"
        )

    return normalizar_modulos(modulos)
