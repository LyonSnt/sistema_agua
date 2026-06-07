# Arquitectura del sistema

## Vision general

Sistema web de facturacion de agua potable construido con Django. La aplicacion se organiza como un monolito modular: cada dominio funcional vive en una app Django independiente, comparte la misma base de datos PostgreSQL y expone vistas renderizadas con plantillas HTML.

## Componentes principales

- `configuracion`: proyecto Django principal. Contiene `settings.py`, `urls.py`, ASGI y WSGI.
- `usuarios`: usuario personalizado, autenticacion, roles, decoradores de acceso y contexto de permisos para plantillas.
- `panel`: panel principal con indicadores operativos y atencion requerida.
- `abonados`: gestion de abonados, sectores, rutas y ficha integral.
- `medidores`: gestion de medidores e historial de cambios.
- `tarifas`: tarifas de agua, rangos y rubros.
- `lecturas`: periodos de facturacion, lecturas, generacion masiva, registro e importacion/exportacion Excel.
- `facturacion`: generacion, detalle, anulacion y PDF de facturas.
- `pagos`: cobro, comprobantes, tickets, PDF y anulacion de pagos.
- `multas`: creacion, cobro, anulacion, comprobantes y reportes de multas.
- `servicios`: suspension y reconexion del servicio.
- `reportes`: reportes de recaudacion, cartera, cierre diario y exportaciones PDF/Excel.
- `auditoria`: registro y consulta de acciones criticas.
- `configuracion_institucional`: datos institucionales usados en comprobantes y reportes.
- `nucleo`: app de soporte para comandos y estructura base.
- `tenants`: registro maestro de juntas de agua para preparacion multi-tenant por base de datos.

## Flujo de ejecucion

1. El usuario ingresa por `/login/`.
2. Django autentica con el modelo `usuarios.Usuario`.
3. Los roles se asignan mediante grupos de Django: Administrador, Supervisor, Cajero, Lecturista y Consulta.
4. Las vistas usan `rol_requerido` para restringir acceso directo por URL.
5. El menu y las acciones visibles se controlan con `usuarios.context_processors.roles_usuario`.
6. Las operaciones criticas registran auditoria cuando corresponde.
7. Las respuestas son plantillas HTML, archivos PDF o exportaciones Excel, segun el caso.

## Datos y persistencia

- Base de datos principal: PostgreSQL.
- Configuracion de conexion mediante variables de entorno: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
- Volumen Docker persistente: `postgres_data`.
- Backups locales mediante scripts:
  - `scripts/backup_db.sh`
  - `scripts/restore_db.sh`
- Los backups se guardan en `backups/`, directorio ignorado por git.

## Multi-tenant por base de datos

La fase actual agrega una base `master` para registrar juntas de agua y activa seleccion dinamica de base para las apps operativas cuando la request viene con prefijo tenant. Las rutas legacy sin prefijo siguen trabajando contra `default`, que se conserva como base legacy/de pruebas. El objetivo es mantener un solo contenedor Django y un solo PostgreSQL, con una base master y una base por junta de agua.

Convencion propuesta:

- Base master: `sistema_agua_master`.
- Base por tenant:
  - `sistema_agua_carabuela`
  - `sistema_agua_esperanza`
  - `sistema_agua_pesillo`
  - `sistema_agua_rumipamba`
- Deteccion inicial por ruta:
  - `/carabuela/`
  - `/esperanza/`
  - `/pesillo/`

Variables preparadas en `.env.example`:

- `MASTER_DB_NAME`
- `TENANT_DEFAULT`
- `TENANT_SLUGS`
- `TENANT_DB_PREFIX`
- `TENANT_ADMIN_DB_NAME`
- `TENANT_ROUTE_MODE`

Implementado actualmente:

- App `tenants` con modelo `Tenant`.
- Router `TenantMasterRouter` para enviar `tenants` a la base `master`.
- Contexto local de request para registrar el alias de base tenant activo.
- Router `TenantOperationalRouter` para enviar apps operativas al alias tenant activo.
- Middleware `TenantPathMiddleware` para detectar tenant por prefijo de ruta, activar contexto tenant y reescribir `request.path_info`.
- Prefijo automatico de redirects relativos durante requests tenant.
- Tag builtin `tenant_url` para que las plantillas generen enlaces internos conservando el prefijo tenant.
- Comandos `crear_tenant`, `crear_base_tenant`, `listar_tenants`, `migrate_tenant` y `migrate_tenants`.
- Comando `provisionar_tenant` para crear una junta en un solo flujo: registro en master, base fisica, migraciones, roles y administrador inicial.
- Cookies con nombres propios para evitar choque con otros proyectos locales:
  - `sistema_agua_sessionid`
  - `sistema_agua_csrftoken`
- Ocultamiento de la app `tenants` dentro del admin de cada junta, para que un tenant no vea ni edite el registro global de otros tenants.

Tenants validados actualmente:

- `carabuela`
- `rumipamba`

El administrador inicial de cada tenant se crea como superusuario dentro de su propia base operativa para permitir la configuracion inicial desde Django Admin.

## Despliegue

El despliegue esta definido con Docker Compose por capas:

- `docker-compose.yml`: base comun.
- `docker-compose.dev.yml`: desarrollo local.
- `docker-compose.prod.yml`: VPS/produccion.

- Servicio `web`:
  - Construye la imagen desde `Dockerfile`.
  - En desarrollo ejecuta `migrate` y `runserver`.
  - En produccion ejecuta `collectstatic`, `migrate` y `gunicorn`.
  - Expone el puerto configurado con `APP_PORT`.
  - Lee variables desde `.env`.
  - Corre como usuario no privilegiado `appuser`.
- Servicio `db`:
  - Usa imagen `postgres:16`.
  - En desarrollo puede exponer `DB_PUBLIC_PORT`.
  - En produccion no expone puerto al host por defecto.
  - Usa volumen persistente `postgres_data`.

Comando de desarrollo:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Comando de produccion:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Archivos estaticos y plantillas

- Plantillas: `app/templates/`.
- Estaticos: `app/static/`.
- Recoleccion de estaticos: `STATIC_ROOT = app/staticfiles`.
- WhiteNoise esta configurado en middleware para servir archivos estaticos desde la aplicacion.

## Pruebas

Las pruebas estan distribuidas por app en archivos `tests.py`. La validacion reciente se ejecuta principalmente dentro del contenedor web, porque el host local no tiene las dependencias Django instaladas.

Ejemplo:

```bash
docker exec sistema_agua_web python manage.py test usuarios
```
