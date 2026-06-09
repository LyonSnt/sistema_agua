# Seguridad

## Estado actual

El proyecto fue endurecido para separar configuracion sensible del codigo, restringir accesos por rol, auditar acciones criticas y preparar el despliegue para un entorno productivo con HTTPS.

## Correcciones realizadas

### Configuracion sensible

- `SECRET_KEY` se lee desde variables de entorno.
- `DEBUG` se controla por entorno y no queda fijo en codigo.
- `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` se parametrizan por entorno.
- Las credenciales de PostgreSQL se leen desde `.env`.
- `.env` no debe versionarse; `.env.example` funciona como contrato de configuracion.
- Se elimino una clave secreta antigua comentada en `settings.py`.

### Flags de seguridad HTTP

Se agregaron variables para activar seguridad de transporte cuando exista HTTPS real:

- `SECURE_SSL_REDIRECT`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- `SECURE_HSTS_SECONDS`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `SECURE_HSTS_PRELOAD`
- `USE_X_FORWARDED_HOST`
- `SECURE_PROXY_SSL_HEADER_ENABLED`

Estos valores estan apagados por defecto para evitar romper entornos sin TLS.

### Autenticacion y fuerza bruta

- Se usa el modelo personalizado `usuarios.Usuario`.
- Se mantiene autenticacion basada en sesiones de Django.
- `django-axes` esta configurado para limitar intentos fallidos.
- El bloqueo se calcula por usuario e IP.
- El contador se reinicia al iniciar sesion correctamente.

### Autorizacion por roles

- Los roles se gestionan con grupos de Django:
  - Administrador
  - Supervisor
  - Cajero
  - Lecturista
  - Consulta
- Las vistas criticas usan `rol_requerido`.
- La matriz de permisos vive en `docs/matriz_permisos_roles.md`.
- El menu usa permisos calculados por `usuarios.context_processors.roles_usuario`.
- El acceso a la administracion Django requiere rol Administrador y usuario `is_staff`, salvo superusuario.

### Auditoria

Se agrego auditoria para acciones y descargas sensibles:

- Anulacion de facturas.
- Anulacion de pagos.
- Anulacion de multas.
- Cambio de medidor.
- Exportaciones de reportes.
- Descargas PDF/Excel sensibles:
  - Fichas de abonado y medidor.
  - Facturas.
  - Comprobantes de pago y multa.
  - Plantilla Excel de lecturas.
  - Reportes PDF/Excel.
  - Exportacion Excel de auditoria.

La vista de auditoria esta restringida al rol Administrador.

### Despliegue

- `runserver` fue reemplazado por `gunicorn`.
- PostgreSQL no expone puerto al host por defecto.
- El contenedor web corre con usuario no privilegiado.
- `django_extensions` solo se habilita por entorno.
- Dependencias de produccion y desarrollo estan separadas.

### Backups

- Se agregaron scripts de backup y restauracion de PostgreSQL.
- `backup_all.sh` respalda `master`, `default` y todos los tenants activos.
- Los backups locales se guardan fuera de git.
- La restauracion pide confirmacion explicita antes de reemplazar datos.
- Para automatizar en VPS se recomienda cron, por ejemplo:

```bash
0 2 * * * cd /ruta/sistema_agua && bash scripts/backup_all.sh
```

## Riesgos residuales

- Activar HTTPS real y flags seguros en produccion.
- Definir politica formal de rotacion y retencion de backups.
- Probar restauracion sobre una base temporal.
- Revisar periodicamente permisos del menu y permisos por URL cuando se agreguen vistas.
- Evaluar si los roles Consulta y Cajero necesitan permisos mas finos para descargas, multas y comprobantes.
- Revisar rendimiento de vistas con consultas amplias antes de crecer en volumen.
