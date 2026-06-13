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

1. El usuario puede ingresar sin prefijo por `/login/` o con prefijo tenant por `/{junta}/login/`.
2. Sin prefijo, el sistema trabaja sobre `default`, que se conserva como base legacy/de pruebas.
3. Con prefijo tenant, `TenantPathMiddleware` resuelve la junta y las apps operativas trabajan sobre la base de esa junta.
4. El middleware valida que el modulo solicitado este habilitado para la junta.
5. El login muestra la identidad institucional de la base activa: combina `ConfiguracionInstitucional.nombre` y `nombre_corto`; si aun no existe, usa el tenant como respaldo.
6. Django autentica con el modelo `usuarios.Usuario` en la base correspondiente.
7. Los roles se asignan mediante grupos de Django: Administrador, Supervisor, Cajero, Lecturista y Consulta.
8. Las vistas usan `rol_requerido` para restringir acceso directo por URL.
9. El menu y las acciones visibles se controlan con `usuarios.context_processors.roles_usuario`.
   El menu lateral se construye desde `nucleo/menu.py` mediante
   `nucleo.context_processors.menu_sidebar`, por lo que `base.html` solo
   renderiza secciones e items ya filtrados.
10. Las operaciones criticas registran auditoria cuando corresponde.
11. Las respuestas son plantillas HTML, archivos PDF o exportaciones Excel, segun el caso.

## Navegacion y menu lateral

El menu lateral principal se define en `nucleo/menu.py` como configuracion
Python. Cada item declara:

- `texto`: etiqueta visible.
- `url_name`: nombre de ruta Django, por ejemplo `abonados:lista`.
- `permiso`: bandera calculada por `usuarios.context_processors.roles_usuario`.
- `permiso_extra`: bandera adicional opcional para casos combinados.
- `rutas_activas`: rutas internas usadas para resaltar el item activo.
- `rutas_excluidas`: rutas que no deben activar ese item.

`nucleo.context_processors.menu_sidebar` toma esa configuracion, cruza permisos
con los modulos habilitados del tenant activo, genera URLs con
`request.tenant_path_prefix` cuando corresponde y elimina secciones vacias.

`base.html` usa el tag `obtener_menu_sidebar` y ya no contiene el menu escrito
a mano. Para agregar una opcion nueva al menu se debe agregar el item en
`nucleo/menu.py` y asegurar que exista el permiso/contexto correspondiente.

En listados con muchas acciones, el patron recomendado es dejar visibles las
acciones principales y mover acciones secundarias o delicadas al menu `...`
controlado por `.menu-acciones`. Las acciones que modifican datos deben seguir
usando `POST` y CSRF.

## Layout y tablas

El layout base usa un menu lateral fijo en escritorio y un area principal
flexible. Para evitar que las tablas anchas achiquen el menu lateral,
`base.html` mantiene el `aside` con `md:shrink-0` y el contenedor principal con
`min-w-0`.

Las tablas operativas deben vivir dentro de un contenedor con
`tabla-scroll overflow-x-auto`. La clase `tabla-scroll`, definida en
`app/static/css/app.css`, permite que una tabla conserve su ancho natural cuando
crecen las columnas y que el desplazamiento horizontal ocurra dentro del area de
contenido, sin deformar el menu ni el resto del layout.

Patron recomendado para tablas nuevas:

```html
<div class="tabla-scroll overflow-x-auto">
    <table class="w-full text-sm">
        ...
    </table>
</div>
```

## Datos y persistencia

- Base de datos principal: PostgreSQL.
- Configuracion de conexion mediante variables de entorno: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
- Volumen Docker persistente para PostgreSQL: `postgres_data`.
- Volumen Docker persistente para archivos subidos: `media_data`, montado en
  `/app/media`.
- Los logos institucionales se guardan como archivos en `/app/media/logos/`.
  La base de datos guarda solo la ruta, por ejemplo `logos/a.png`.
- Backups locales mediante scripts:
  - `scripts/backup_db.sh`
  - `scripts/backup_all.sh`
  - `scripts/restore_db.sh`
- `scripts/backup_all.sh` respalda bases y archivos subidos. El respaldo de
  media se genera como `media_YYYYMMDD_HHMMSS.tar.gz`.
- Los backups se guardan en `backups/YYYYMMDD/`, directorio ignorado por git.

## Multi-tenant por base de datos

La fase actual agrega una base `master` para registrar juntas de agua y activa seleccion dinamica de base para las apps operativas cuando la request viene con prefijo tenant. Las rutas legacy sin prefijo siguen trabajando contra `default`, que se conserva como base legacy/de pruebas. El objetivo es mantener un solo contenedor Django y un solo PostgreSQL, con una base master y una base por junta de agua.

Convencion propuesta:

- Base master: `sistema_agua_master`.
- Base por tenant:
  - `sistema_agua_carabuela`
  - `sistema_agua_esperanza`
  - `sistema_agua_pesillo`
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
- Configuracion de modulos por tenant en `master` mediante `Tenant.modulos_habilitados`.
- Router `TenantMasterRouter` para enviar `tenants` a la base `master`.
- Contexto local de request para registrar el alias de base tenant activo.
- Router `TenantOperationalRouter` para enviar apps operativas al alias tenant activo.
- Middleware `TenantPathMiddleware` para detectar tenant por prefijo de ruta, activar contexto tenant y reescribir `request.path_info`.
- Prefijo automatico de redirects relativos durante requests tenant.
- Tag builtin `tenant_url` para que las plantillas generen enlaces internos conservando el prefijo tenant.
- Bloqueo HTTP 403 para URLs de modulos deshabilitados en una junta.
- Comandos `crear_tenant`, `crear_base_tenant`, `listar_tenants`, `migrate_tenant` y `migrate_tenants`.
- Comando `provisionar_tenant` para crear una junta en un solo flujo: registro en master, base fisica, migraciones, roles y administrador inicial.
- Cookies con nombres propios para evitar choque con otros proyectos locales:
  - `sistema_agua_sessionid`
  - `sistema_agua_csrftoken`
- Ocultamiento de la app `tenants` dentro del admin de cada junta, para que un tenant no vea ni edite el registro global de otros tenants.
- Menu lateral centralizado en `nucleo/menu.py`, tenant-aware y filtrado por
  permisos/modulos.

Tenant de prueba/validacion actual:

- `carabuela`

Cuando el sistema quede estable se agregaran nuevos tenants operativos usando
la misma estructura por base de datos.

El administrador inicial de cada tenant se crea como superusuario dentro de su propia base operativa para permitir la configuracion inicial desde Django Admin.

Los modulos actuales configurables por junta son `panel`, `abonados`,
`medidores`, `lecturas`, `facturacion`, `pagos`, `reportes`, `multas`,
`servicios`, `auditoria` y `admin`. Si una junta no define lista de modulos,
queda con todos habilitados.

Uso de rutas:

- `/login/` y `/admin/`: base `default`, con `tenants` aislado en `master`; se usan para pruebas/legacy o administracion global controlada.
- `/{junta}/login/` y `/{junta}/admin/`: base propia de la junta; se usan para operacion y configuracion real de esa junta.

## Despliegue

El despliegue esta definido con Docker Compose por capas:

- `docker-compose.yml`: base comun.
- `docker-compose.dev.yml`: desarrollo local.
- `docker-compose.prod.yml`: VPS/produccion.

- Servicio `web`:
  - Construye la imagen desde `Dockerfile`.
  - En desarrollo ejecuta `migrate` y `runserver`.
  - En produccion ejecuta `collectstatic`, `migrate` y `gunicorn`.
  - En produccion expone el puerto configurado con `APP_PORT` solo en `127.0.0.1`.
  - Lee variables desde `.env`.
  - Corre como usuario no privilegiado `appuser`.
  - Usa el volumen persistente `media_data` en `/app/media` para conservar
    logos institucionales y otros archivos subidos entre reconstrucciones.
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

En VPS, el servicio Django/Gunicorn no se publica directamente a internet.
`docker-compose.prod.yml` mantiene la app escuchando solo en el host local del
servidor:

```yaml
ports:
  - "127.0.0.1:${APP_PORT:-8015}:8015"
```

La entrada publica recomendada es Nginx en la misma VPS, escuchando en el
puerto `80` y reenviando internamente hacia `127.0.0.1:8015`:

```nginx
server {
    listen 80;
    server_name 178.105.190.153;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8015;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Con esta configuracion:

- `http://127.0.0.1:8015/login/` valida Django/Gunicorn desde la VPS.
- `http://178.105.190.153/login/` valida el flujo publico por Nginx.
- El puerto `8015` no necesita abrirse publicamente.

El `.env` de produccion debe permitir la IP publica o dominio usado por Nginx:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,178.105.190.153
CSRF_TRUSTED_ORIGINS=http://178.105.190.153
```

Cuando exista dominio, se debe reemplazar la IP en `server_name`,
`ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` por el dominio real.

## Archivos estaticos y plantillas

- Plantillas: `app/templates/`.
- Estaticos: `app/static/`.
- Recoleccion de estaticos: `STATIC_ROOT = app/staticfiles`.
- WhiteNoise esta configurado en middleware para servir archivos estaticos desde la aplicacion.
- Archivos subidos: `MEDIA_ROOT = app/media`, con `MEDIA_URL = /media/`.
- Los logos institucionales se sirven por `/media/logos/...`. En produccion se
  recomienda que Nginx sirva esa ruta directamente cuando se estabilice el
  dominio/certificado.

## Pruebas

Las pruebas estan distribuidas por app en archivos `tests.py`. La validacion reciente se ejecuta principalmente dentro del contenedor web, porque el host local no tiene las dependencias Django instaladas.

Ejemplo:

```bash
docker exec sistema_agua_web python manage.py test usuarios
```
