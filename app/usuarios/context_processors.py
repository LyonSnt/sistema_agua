from tenants.modules import tenant_tiene_modulo


def roles_usuario(request):
    if not request.user.is_authenticated:
        return {}

    grupos = set(
        request.user.groups.values_list("name", flat=True)
    )

    es_admin = request.user.is_superuser or "Administrador" in grupos
    es_cajero = "Cajero" in grupos
    es_lecturista = "Lecturista" in grupos
    es_supervisor = "Supervisor" in grupos
    es_consulta = "Consulta" in grupos
    puede_entrar_admin_django = (
        request.user.is_active
        and request.user.is_staff
        and es_admin
    )
    tenant = getattr(request, "tenant", None)

    modulo_panel = tenant_tiene_modulo(tenant, "panel")
    modulo_abonados = tenant_tiene_modulo(tenant, "abonados")
    modulo_medidores = tenant_tiene_modulo(tenant, "medidores")
    modulo_lecturas = tenant_tiene_modulo(tenant, "lecturas")
    modulo_facturacion = tenant_tiene_modulo(tenant, "facturacion")
    modulo_pagos = tenant_tiene_modulo(tenant, "pagos")
    modulo_reportes = tenant_tiene_modulo(tenant, "reportes")
    modulo_servicios = tenant_tiene_modulo(tenant, "servicios")
    modulo_multas = tenant_tiene_modulo(tenant, "multas")
    modulo_admin = tenant_tiene_modulo(tenant, "admin")
    modulo_auditoria = tenant_tiene_modulo(tenant, "auditoria")

    return {
        "es_admin": es_admin,
        "es_cajero": es_cajero,
        "es_lecturista": es_lecturista,
        "es_supervisor": es_supervisor,
        "es_consulta": es_consulta,
        "modulo_panel": modulo_panel,
        "modulo_abonados": modulo_abonados,
        "modulo_medidores": modulo_medidores,
        "modulo_lecturas": modulo_lecturas,
        "modulo_facturacion": modulo_facturacion,
        "modulo_pagos": modulo_pagos,
        "modulo_reportes": modulo_reportes,
        "modulo_servicios": modulo_servicios,
        "modulo_multas": modulo_multas,
        "modulo_admin": modulo_admin,
        "modulo_auditoria": modulo_auditoria,

        # Panel
        "puede_ver_panel": modulo_panel and (
            es_admin or es_supervisor or es_cajero or es_lecturista or es_consulta
        ),

        # Abonados y medidores
        "puede_ver_abonados": modulo_abonados and (
            es_admin or es_supervisor or es_cajero or es_lecturista or es_consulta
        ),
        "puede_gestionar_abonados": modulo_abonados and (es_admin or es_supervisor),
        "puede_ver_medidores": modulo_medidores and (
            es_admin or es_supervisor or es_cajero or es_lecturista or es_consulta
        ),
        "puede_gestionar_medidores": modulo_medidores and (es_admin or es_supervisor),

        # Lecturas
        "puede_generar_lecturas": modulo_lecturas and (es_admin or es_supervisor),
        "puede_registrar_lecturas": modulo_lecturas and (
            es_admin or es_supervisor or es_lecturista
        ),
        "puede_importar_lecturas": modulo_lecturas and (
            es_admin or es_supervisor or es_lecturista
        ),

        # Facturacion
        "puede_generar_facturacion": modulo_facturacion and (es_admin or es_supervisor),
        "puede_ver_facturas": modulo_facturacion and (
            es_admin or es_supervisor or es_cajero or es_consulta
        ),
        "puede_agregar_rubro_factura": modulo_facturacion and (
            es_admin or es_supervisor
        ),
        "puede_anular_factura": modulo_facturacion and es_admin,

        # Pagos
        "puede_cobrar": modulo_pagos and (es_admin or es_supervisor or es_cajero),
        "puede_ver_comprobante": modulo_pagos and (
            es_admin or es_supervisor or es_cajero or es_consulta
        ),
        "puede_anular_pago": modulo_pagos and es_admin,

        # Reportes
        "puede_ver_reportes": modulo_reportes and (
            es_admin or es_supervisor or es_cajero or es_consulta
        ),
        "puede_exportar_reportes": modulo_reportes and (es_admin or es_supervisor),
        "puede_ver_cartera": modulo_reportes and (
            es_admin or es_supervisor or es_cajero or es_consulta
        ),

        # Servicios
        "puede_ver_suspensiones": modulo_servicios and (
            es_admin or es_supervisor or es_consulta
        ),
        "puede_suspender": modulo_servicios and (es_admin or es_supervisor),
        "puede_reconectar": modulo_servicios and (es_admin or es_supervisor),

        # Multas
        "puede_ver_multas": modulo_multas and (
            es_admin or es_supervisor or es_cajero or es_consulta
        ),
        "puede_gestionar_multas": modulo_multas and (
            es_admin or es_supervisor or es_cajero
        ),
        "puede_anular_multa": modulo_multas and es_admin,
        "puede_cobrar_multa": modulo_multas and (
            es_admin or es_supervisor or es_cajero
        ),
        "puede_ver_reporte_multas": modulo_multas and (
            es_admin or es_supervisor or es_cajero or es_consulta
        ),
        "puede_exportar_multas": modulo_multas and (es_admin or es_supervisor),

        # Sistema
        "puede_administrar_sistema": (
            modulo_admin or modulo_auditoria
        ) and (es_admin or puede_entrar_admin_django),
        "puede_entrar_admin_django": modulo_admin and puede_entrar_admin_django,
        "puede_ver_auditoria": modulo_auditoria and es_admin,
    }
