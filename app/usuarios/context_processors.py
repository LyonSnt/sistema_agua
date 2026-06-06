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

    return {
        "es_admin": es_admin,
        "es_cajero": es_cajero,
        "es_lecturista": es_lecturista,
        "es_supervisor": es_supervisor,
        "es_consulta": es_consulta,

        # Panel
        "puede_ver_panel": es_admin or es_supervisor or es_cajero or es_lecturista or es_consulta,

        # Abonados y medidores
        "puede_ver_abonados": es_admin or es_supervisor or es_cajero or es_lecturista or es_consulta,
        "puede_gestionar_abonados": es_admin or es_supervisor,
        "puede_ver_medidores": es_admin or es_supervisor or es_cajero or es_lecturista or es_consulta,
        "puede_gestionar_medidores": es_admin or es_supervisor,

        # Lecturas
        "puede_generar_lecturas": es_admin or es_supervisor,
        "puede_registrar_lecturas": es_admin or es_supervisor or es_lecturista,
        "puede_importar_lecturas": es_admin or es_supervisor or es_lecturista,

        # Facturación
        "puede_generar_facturacion": es_admin or es_supervisor,
        "puede_ver_facturas": es_admin or es_supervisor or es_cajero or es_consulta,
        "puede_agregar_rubro_factura": es_admin or es_supervisor,
        "puede_anular_factura": es_admin,

        # Pagos
        "puede_cobrar": es_admin or es_supervisor or es_cajero,
        "puede_ver_comprobante": es_admin or es_supervisor or es_cajero or es_consulta,
        "puede_anular_pago": es_admin,

        # Reportes
        "puede_ver_reportes": es_admin or es_supervisor or es_cajero or es_consulta,
        "puede_exportar_reportes": es_admin or es_supervisor,
        "puede_ver_cartera": es_admin or es_supervisor or es_cajero or es_consulta,

        # Servicios
        "puede_ver_suspensiones": es_admin or es_supervisor or es_consulta,
        "puede_suspender": es_admin or es_supervisor,
        "puede_reconectar": es_admin or es_supervisor,

        # Multas
        "puede_ver_multas": es_admin or es_supervisor or es_cajero or es_consulta,
        "puede_gestionar_multas": es_admin or es_supervisor or es_cajero,
        "puede_anular_multa": es_admin,
        "puede_cobrar_multa": es_admin or es_supervisor or es_cajero,
        "puede_ver_reporte_multas": es_admin or es_supervisor or es_cajero or es_consulta,
        "puede_exportar_multas": es_admin or es_supervisor,

        # Sistema
        "puede_administrar_sistema": es_admin,
        "puede_ver_auditoria": es_admin,
    }
