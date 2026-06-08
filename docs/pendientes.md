# Pendientes priorizados

## Alta prioridad

- [ ] Configurar Rumipamba desde `/rumipamba/admin/`:
  - configuracion institucional
  - sectores
  - rutas
  - tarifa vigente
  - rubros necesarios
  - periodo inicial
- [ ] Probar ciclo operativo minimo en Rumipamba con 1 abonado y 1 medidor:
  - crear abonado
  - crear medidor
  - registrar lectura
  - generar factura
  - cobrar pago
  - revisar comprobante y reportes
- [ ] Reconstruir o redeplegar la imagen Docker para incorporar los cambios confirmados al contenedor definitivo.
- [ ] Implementar desactivar/reactivar abonado sin borrado fisico.
- [ ] Agregar reporte o comando de consistencia operativa:
  - facturas con pagos activos pero saldo desactualizado;
  - pagos activos sobre facturas anuladas;
  - facturas pagadas con saldo pendiente distinto de cero;
  - lecturas registradas sin factura en periodos ya facturados.
- [ ] Activar flags de produccion cuando exista HTTPS real:
  - `SECURE_SSL_REDIRECT=True`
  - `SESSION_COOKIE_SECURE=True`
  - `CSRF_COOKIE_SECURE=True`
  - `SECURE_HSTS_SECONDS` con un valor definido para produccion.
- [ ] Cuando exista dominio real, actualizar despliegue publico:
  - cambiar `server_name` de Nginx de IP publica a dominio;
  - actualizar `ALLOWED_HOSTS` con el dominio;
  - actualizar `CSRF_TRUSTED_ORIGINS` con `https://dominio`;
  - instalar certificado TLS con Certbot o proveedor equivalente;
  - activar flags HTTPS de produccion despues de validar el certificado.
- [ ] Probar restauracion de backups en una base temporal, no sobre la base viva.
- [ ] Definir politica de rotacion y retencion de backups.
- [ ] Revisar permisos del menu y permisos por URL cada vez que se agregue una vista nueva.

## Media prioridad

- [ ] Agregar filtro de activos/inactivos en listado de abonados.
- [ ] Agregar filtros de abonados por sector, ruta, estado de servicio y estado de cuenta.
- [ ] Optimizar `estado_cuenta` en listados para evitar consultas repetidas por fila.
- [ ] Filtrar rutas dinamicamente por sector en el formulario de abonado.
- [ ] Evaluar si `Consulta` debe poder descargar PDFs de abonado, medidor y factura.
- [ ] Evaluar si `Cajero` debe poder ver multas pero no crearlas.
- [ ] Separar permisos finos de multas si se requiere:
  - crear
  - cobrar
  - anular
  - consultar
- [ ] Mejorar auditoria relacionada por abonado con vinculos mas estructurados que `objeto_repr`.
- [ ] Revisar rendimiento del panel principal si crece el volumen de datos.
- [ ] Revisar rendimiento de la ficha integral del abonado si crece el historial.
- [ ] Validar en ambiente real que el menu Sistema se comporta correctamente para Administrador con y sin `is_staff`.
- [ ] Decidir si se unifica el color de accion `Editar` entre abonados y medidores.
- [ ] Adaptar scripts de backup/restore para base master y bases tenant.

## Baja prioridad

- [ ] Considerar exportacion Excel de ficha del abonado.
- [ ] Continuar alineando botones de otros modulos con el patron de cartera pendiente.
- [ ] Corregir detalles menores de texto y ortografia en interfaz cuando se detecten.
- [ ] Mantener documentadas las sesiones de trabajo en `docs/sesiones/`.
- [ ] Definir si la documentacion se mantendra en ASCII o si se normalizara con tildes.

## Completadas recientemente

- [x] Matriz de permisos por rol documentada.
- [x] Tests de acceso directo por URL para rutas criticas.
- [x] Revision de acceso a `/admin/` por rol.
- [x] Endurecimiento del acceso a Django Admin para exigir rol Administrador y usuario `is_staff`.
- [x] Ajuste del menu para mostrar Administracion solo a usuarios con acceso real al admin.
- [x] Organizacion de documentacion tecnica en `docs/`.
- [x] Creacion de `docs/arquitectura.md`.
- [x] Creacion de `docs/seguridad.md`.
- [x] Movimiento de la bitacora anterior a `docs/sesiones/2026_06_04.md`.
- [x] Creacion y actualizacion de la bitacora `docs/sesiones/2026_06_05.md`.
- [x] Revision del modulo Abonados antes de modificar codigo.
- [x] Identificacion del boton incorrecto "Nuevo medidor" en listado de abonados.
- [x] Reemplazo de "Nuevo medidor" por "Nuevo abonado".
- [x] Implementacion de creacion de abonados.
- [x] Implementacion de edicion de abonados.
- [x] Validacion de sector/ruta en formulario de abonados.
- [x] Auditoria de creacion y actualizacion de abonados.
- [x] Pruebas de CRUD inicial de abonados.
- [x] Actualizacion de matriz de permisos con "Crear / editar abonados".
- [x] Alineacion de acciones del listado de abonados con cartera pendiente.
- [x] Alineacion de acciones del listado de medidores con cartera pendiente.
- [x] Decision de no editar `estado_servicio` ni `activo` desde el formulario general de abonado.
- [x] Fase 1 Docker multi-entorno: `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.prod.yml` y contrato `.env.example`.
- [x] Documento `docs/multitenancy.md` con estrategia multi-tenant por base de datos.
- [x] Fase 2 inicial: `settings.py` preparado con base `master` y contrato de tenants sin activar routing dinamico.
- [x] App `tenants` con modelo master de juntas de agua, admin, migracion inicial y tests.
- [x] Router `TenantMasterRouter` para aislar la app `tenants` en la base `master`.
- [x] Comandos iniciales `crear_tenant` y `listar_tenants`.
- [x] Comando `crear_base_tenant` para crear la base fisica PostgreSQL de un tenant.
- [x] Comandos de migracion tenant `migrate_tenant` y `migrate_tenants`.
- [x] Middleware pasivo de deteccion por ruta: `/carabuela/`, `/esperanza/`, `/pesillo/`.
- [x] Seleccion dinamica de base para apps operativas segun contexto tenant por request.
- [x] Router operativo `TenantOperationalRouter` para usar alias tenant activo.
- [x] Middleware tenant reordenado antes de sesiones para login/autenticacion por tenant.
- [x] Redirects tenant-aware para conservar prefijo en login, logout, permisos y vistas.
- [x] Tag builtin `tenant_url` aplicado en plantillas para conservar prefijo tenant en enlaces internos.
- [x] Validacion con bases fisicas reales para Carabuela.
- [x] CRUD de abonados validado en `/carabuela/`: listado, creacion, ficha y edicion.
- [x] Decision de mantener `default` como base legacy/de pruebas sin migrar datos por ahora.
- [x] Cookies propias `sistema_agua_sessionid` y `sistema_agua_csrftoken` para evitar choques con otros proyectos en `localhost`.
- [x] Comando unico `provisionar_tenant` para crear una junta con base, migraciones, roles y admin inicial.
- [x] Tenant Rumipamba creado y validado con base `sistema_agua_rumipamba`.
- [x] Aislamiento de datos validado entre Rumipamba, Carabuela y `default`.
- [x] Admin inicial del tenant creado con permisos completos dentro de su junta.
- [x] App `tenants` oculta y bloqueada dentro del admin de cada junta.
- [x] Configuracion de Nginx en VPS para exponer la app por IP publica sin abrir Gunicorn directamente.
- [x] Endurecimiento transaccional de cobros y anulaciones criticas:
  - cobro de facturas;
  - anulacion de pagos;
  - anulacion de facturas;
  - cobro y anulacion de multas.
