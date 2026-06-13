# nucleo/menu.py

MENU_SIDEBAR = [
    {
        "titulo": "Inicio",
        "items": [
            {
                "texto": "Panel principal",
                "url_name": "panel:inicio",
                "permiso": "puede_ver_panel",
                "rutas_activas": ["/panel/"],
            },
        ],
    },

    {
        "titulo": "Gestión comercial",
        "items": [
            {
                "texto": "Abonados",
                "icono": "pi pi-users",
                "url_name": "abonados:lista",
                "permiso": "puede_ver_abonados",
                "rutas_activas": ["/abonados/"],
            },
            {
                "texto": "Medidores",
                "url_name": "medidores:lista",
                "icono": "pi pi-bolt",         # Medidores
                "permiso": "puede_ver_medidores",
                "rutas_activas": ["/medidores/"],
            },
        ],
    },

    {
        "titulo": "Lecturas y facturación",
        "items": [
            {
                "texto": "Generar lecturas",
                "url_name": "lecturas:generar",
                "icono": "pi pi-file-edit",
                "permiso": "puede_generar_lecturas",
                "rutas_activas": ["/lecturas/generar/"],
            },
            {
                "texto": "Importar lecturas",
                "url_name": "lecturas:importar_excel",
                "permiso": "puede_importar_lecturas",
                "rutas_activas": ["/lecturas/importar-excel/"],
            },
            {
                "texto": "Registro de lecturas",
                "url_name": "lecturas:registro_masivo",
                "permiso": "puede_registrar_lecturas",
                "rutas_activas": ["/lecturas/registro-masivo/"],
            },
            {
                "texto": "Generar facturación",
                "url_name": "facturacion:generar",
                "icono": "pi pi-receipt",
                "permiso": "puede_generar_facturacion",
                "rutas_activas": ["/facturacion/generar/"],
            },
            {
                "texto": "Facturas pendientes",
                "url_name": "facturacion:pendientes",
                "permiso": "puede_ver_facturas",
                "rutas_activas": [
                    "/facturacion/pendientes/",
                    "/pagos/",
                ],
            },
            {
                "texto": "Facturas pagadas",
                "url_name": "reportes:facturas_pagadas",
                "permiso": "puede_ver_reportes",
                "permiso_extra": "puede_ver_facturas",
                "rutas_activas": ["/reportes/facturas-pagadas/"],
            },
            {
                "texto": "Facturas anuladas",
                "url_name": "reportes:facturas_anuladas",
                "permiso": "puede_ver_reportes",
                "permiso_extra": "puede_ver_facturas",
                "rutas_activas": ["/reportes/facturas-anuladas/"],
            },
        ],
    },

    {
        "titulo": "Recaudación",
        "items": [
            {
                "texto": "Cierre diario",
                "url_name": "reportes:cierre_diario",
                "permiso": "puede_ver_reportes",
                "rutas_activas": ["/reportes/cierre-diario/"],
            },
            {
                "texto": "Recaudación diaria",
                "url_name": "reportes:recaudacion_diaria",
                "permiso": "puede_ver_reportes",
                "rutas_activas": ["/reportes/recaudacion-diaria/"],
            },
            {
                "texto": "Recaudación mensual",
                "url_name": "reportes:recaudacion_mensual",
                "permiso": "puede_ver_reportes",
                "rutas_activas": ["/reportes/recaudacion-mensual/"],
            },
        ],
    },

    {
        "titulo": "Cartera y control",
        "items": [
            {
                "texto": "Cartera pendiente",
                "url_name": "reportes:cartera",
                "permiso": "puede_ver_cartera",
                "rutas_activas": ["/reportes/cartera/"],
            },
            {
                "texto": "Cartera vencida",
                "url_name": "reportes:cartera_vencida",
                "permiso": "puede_ver_cartera",
                "rutas_activas": ["/reportes/cartera-vencida/"],
            },
            {
                "texto": "Suspensiones",
                "url_name": "servicios:lista",
                "permiso": "puede_ver_suspensiones",
                "rutas_activas": ["/servicios/"],
            },
            {
                "texto": "Multas",
                "url_name": "multas:lista",
                "icono": "pi pi-exclamation-circle",
                "permiso": "puede_ver_multas",
                "rutas_activas": ["/multas/"],
                "rutas_excluidas": ["/multas/reporte/"],
            },
            {
                "texto": "Reporte de multas",
                "url_name": "multas:reporte",
                "permiso": "puede_ver_reporte_multas",
                "rutas_activas": ["/multas/reporte/"],
            },
        ],
    },

    {
        "titulo": "Sistema",
        "items": [
            {
                "texto": "Administración",
                "url_name": "admin:index",
                "permiso": "puede_entrar_admin_django",
                "rutas_activas": ["/admin/"],
                "rutas_excluidas": ["/admin/medidores/"],
            },
            {
                "texto": "Auditoría",
                "url_name": "auditoria:lista",
                "icono": "pi pi-shield",
                "permiso": "puede_ver_auditoria",
                "rutas_activas": ["/auditoria/"],
            },
        ],
    },
]
