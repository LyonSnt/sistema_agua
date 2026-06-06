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

## Despliegue

El despliegue actual esta definido con Docker Compose:

- Servicio `web`:
  - Construye la imagen desde `Dockerfile`.
  - Ejecuta `collectstatic`, `migrate` y luego `gunicorn`.
  - Expone el puerto `8015`.
  - Lee variables desde `.env`.
  - Corre como usuario no privilegiado `appuser`.
- Servicio `db`:
  - Usa imagen `postgres:16`.
  - No expone puerto al host por defecto.
  - Usa volumen persistente `postgres_data`.

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
