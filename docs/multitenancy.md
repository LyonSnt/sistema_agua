# Multi-tenancy por base de datos

## Objetivo

Preparar el sistema para operar varias juntas de agua desde una sola instancia de Django y un solo servidor PostgreSQL, manteniendo aislamiento de datos por base de datos.

## Estrategia

- Un contenedor Django.
- Un contenedor PostgreSQL.
- Una base master.
- Una base por junta de agua.
- Deteccion inicial de tenant por prefijo de ruta:
  - `/carabuela/`
  - `/esperanza/`
  - `/pesillo/`

## Estado actual

La fase actual ya incorpora seleccion dinamica de base por request para las apps operativas. La app `tenants` sigue aislada en la base `master`; cuando una ruta prefijada resuelve un tenant activo, el middleware registra el alias de base tenant en un contexto local de request y el router operativo envia lecturas y escrituras de las apps no globales a esa base.

Las rutas sin prefijo tenant siguen funcionando sobre `default` para mantener compatibilidad durante la transicion.

La navegacion tenant-prefijada tambien queda cubierta para redirects y plantillas. Los redirects relativos generados durante una request tenant se devuelven con el prefijo correspondiente, y las plantillas usan el tag `tenant_url` para generar enlaces internos conservando el prefijo.

Tambien se valido el flujo contra bases fisicas reales. Actualmente `carabuela`
queda como tenant principal de prueba/validacion mientras se estabiliza el
sistema. Luego se iran agregando nuevos tenants operativos segun necesidad. La
base `default` se conserva como base legacy/de pruebas y no se migrara por
ahora.

Para evitar choque de sesiones con otros proyectos locales sobre `localhost`, la configuracion usa nombres propios de cookies:

- `SESSION_COOKIE_NAME=sistema_agua_sessionid`
- `CSRF_COOKIE_NAME=sistema_agua_csrftoken`

## Base master

La base master debe guardar solo informacion global necesaria para resolver tenants.

Modelo inicial:

- `slug`: identificador usado en URL.
- `nombre`: nombre corto visible de la junta, por ejemplo `Carabuela`.
- `db_name`: nombre de la base de datos del tenant.
- `activo`: permite habilitar o bloquear una junta.
- `modulos_habilitados`: lista de modulos/pestanas activas para esa junta.

Ejemplo:

| slug | nombre | db_name |
| --- | --- | --- |
| `carabuela` | Carabuela | `sistema_agua_carabuela` |
| `esperanza` | Esperanza | `sistema_agua_esperanza` |
| `pesillo` | Pesillo | `sistema_agua_pesillo` |

## Bases tenant

Cada base tenant contendra los datos operativos actuales:

- abonados
- medidores
- lecturas
- tarifas
- facturacion
- pagos
- multas
- servicios
- reportes derivados
- auditoria
- usuarios y roles de esa junta, inicialmente

## Variables de entorno

Contrato preparado en `.env.example`:

- `MASTER_DB_NAME`
- `TENANT_DEFAULT`
- `TENANT_SLUGS`
- `TENANT_DB_PREFIX`
- `TENANT_ADMIN_DB_NAME`
- `TENANT_ROUTE_MODE`

## Router de base de datos

`tenants.db_router.TenantMasterRouter` aplica estas reglas:

- Lecturas y escrituras de `tenants` van a `master`.
- Migraciones de `tenants` solo se permiten en `master`.
- Migraciones de apps operativas no se permiten en `master`.

`tenants.db_router.TenantOperationalRouter` aplica estas reglas:

- Si hay tenant activo en el contexto de request, las apps operativas usan el alias tenant.
- Si no hay tenant activo, Django mantiene el routing normal hacia `default`.
- Las migraciones de apps no globales se permiten en aliases tenant como `tenant_carabuela`.

## URLs tenant-aware

`TenantPathMiddleware` prefija automaticamente encabezados `Location` relativos cuando la request tiene tenant activo. Esto mantiene dentro del tenant flujos como login, logout, permisos y redirects manuales de vistas.

Las plantillas usan el tag builtin `tenant_url`, registrado en `settings.py`, como reemplazo de `{% url %}`. El tag genera la URL normal cuando no hay tenant y antepone `request.tenant_path_prefix` cuando la navegacion viene desde una ruta tenant.

El menu lateral se construye desde `nucleo/menu.py` mediante
`nucleo.context_processors.menu_sidebar`. El builder genera URLs con el prefijo
tenant activo, calcula el item activo usando la ruta sin prefijo y filtra items
segun los permisos ya cruzados con modulos habilitados.

## Modulos por tenant

La base `master` define que modulos tiene habilitados cada junta mediante
`Tenant.modulos_habilitados`. Esto permite que una junta use todo el sistema y
otra use solo algunas pestanas sin duplicar codigo ni mezclar datos.

Modulos actuales:

- `panel`
- `abonados`
- `medidores`
- `lecturas`
- `facturacion`
- `pagos`
- `reportes`
- `multas`
- `servicios`
- `auditoria`
- `admin`

Reglas:

- Si no se define una lista, el tenant queda con todos los modulos habilitados.
- El menu y el panel ocultan accesos a modulos deshabilitados.
- El menu se define una sola vez en `nucleo/menu.py`; para ocultar una opcion
  por tenant se usa el permiso asociado, calculado desde los modulos activos.
- El middleware bloquea el acceso directo por URL a modulos deshabilitados con HTTP 403.
- Los permisos por rol siguen aplicando dentro de cada modulo habilitado.
- Las rutas sin tenant siguen funcionando con todos los modulos para mantener el modo legacy/de pruebas.

## Rutas con y sin tenant

El sistema conserva dos modos de entrada:

| URL | Base usada | Uso recomendado |
| --- | --- | --- |
| `/login/` | `default` / `sistema_agua` | Pruebas, datos legacy o validaciones generales. |
| `/admin/` | `default` y `master` para `tenants` | Administracion legacy/global. Usar con cuidado. |
| `/carabuela/login/` | `sistema_agua_carabuela` | Tenant de prueba/validacion. |
| `/carabuela/admin/` | `sistema_agua_carabuela` | Configuracion del tenant de prueba. |

Reglas practicas:

- Para pruebas tenant, usar `carabuela` con URLs prefijadas.
- Para trabajo real de una junta futura, usar siempre URLs con su prefijo tenant.
- `/login/` sin prefijo trabaja sobre `default`; no representa a una junta real.
- Los datos creados en `default` no aparecen en Carabuela ni en otros tenants.
- Los datos creados en Carabuela no aparecen en `default` ni en tenants futuros.
- La app `tenants` no se muestra dentro del admin tenant; una junta no debe ver ni editar el registro global de otras juntas.
- Desde el admin global `/admin/`, la ficha de cada tenant permite resetear la
  clave de un usuario administrador dentro de la base de esa junta. Esta accion
  no esta disponible desde `/{junta}/admin/`.
- En el login tenant se muestra `Tenant.nombre` como nombre corto. El nombre
  legal/base se mantiene en `ConfiguracionInstitucional.nombre` dentro de cada
  base tenant. `ConfiguracionInstitucional.nombre_corto` permite mostrar el
  nombre propio de la junta sin repetirlo en la linea institucional.
- Convencion recomendada para cada tenant:
  - `Tenant.nombre`: nombre corto de respaldo, por ejemplo `Carabuela`.
  - `ConfiguracionInstitucional.nombre`: nombre institucional base, por ejemplo
    `Junta Administradora de Agua Potable`.
  - `ConfiguracionInstitucional.nombre_corto`: nombre propio de la junta, por
    ejemplo `Carabuela`.
  - Login izquierdo: `Sistema de Facturacion` + `nombre nombre_corto`.
  - Login derecho: `nombre` + `nombre_corto` en lineas separadas.

## Comandos iniciales

Registrar una junta en master:

```bash
python manage.py crear_tenant carabuela "Junta Carabuela"
```

Registrar una junta con nombre de base explicito:

```bash
python manage.py crear_tenant esperanza "Junta Esperanza" --db-name sistema_agua_esperanza
```

Crear la base fisica PostgreSQL del tenant:

```bash
python manage.py crear_base_tenant carabuela
```

Listar juntas registradas:

```bash
python manage.py listar_tenants
```

Ejecutar migraciones para un tenant:

```bash
python manage.py migrate_tenant carabuela
```

Ejecutar migraciones para todos los tenants activos:

```bash
python manage.py migrate_tenants
```

Crear y preparar una junta nueva con un solo comando:

```bash
python manage.py provisionar_tenant san-pablo "Junta San Pablo" \
  --admin-user admin_san_pablo \
  --admin-password "ClaveSegura123" \
  --admin-email admin@sanpablo.local
```

Crear una junta con solo algunos modulos:

```bash
python manage.py provisionar_tenant carabuela "Carabuela" \
  --admin-user admin_carabuela \
  --admin-password "ClaveSegura123" \
  --modules panel,abonados,medidores,lecturas,facturacion,pagos,reportes,admin
```

Este comando realiza los pasos tecnicos principales:

- registra el tenant en `master`;
- crea la base fisica PostgreSQL;
- ejecuta migraciones en la base tenant;
- crea roles base;
- crea o actualiza el usuario Administrador inicial con acceso completo al admin de su junta.
- guarda los modulos habilitados si se usa `--modules`; si se omite, habilita todos.

Si el slug no esta en `TENANT_SLUGS`, el comando termina pero muestra una
advertencia. Para acceder por URL se debe agregar el slug en `.env` y recrear
el contenedor web.

Ejemplo con Docker:

```bash
docker exec -it sistema_agua_web python manage.py provisionar_tenant carabuela "Carabuela" \
  --admin-user admin_carabuela \
  --admin-password "ClaveSegura123" \
  --admin-email admin@carabuela.local
```

`crear_base_tenant` se conecta a la base administrativa definida por `TENANT_ADMIN_DB_NAME`, por defecto `postgres`. El usuario PostgreSQL configurado en `DB_USER` debe tener permisos para crear bases.

## Resolucion por ruta

La fase actual incorpora un middleware por ruta. Detecta el prefijo tenant, carga el registro desde `master`, registra el alias tenant en un contexto local de request y reescribe internamente `request.path_info` para reutilizar las URLs actuales.

El middleware corre antes de `SessionMiddleware`, de modo que sesiones, autenticacion, usuarios y permisos tambien usen la base tenant cuando la ruta viene prefijada.

Flujo actual:

1. El usuario entra a `/carabuela/panel/`.
2. Un middleware lee el primer segmento: `carabuela`.
3. Se busca el tenant activo en master.
4. Se asigna `request.tenant`.
5. Se registra `request.tenant_db_alias`.
6. Se activa el alias tenant en contexto local de request.
7. La URL interna se resuelve contra las rutas actuales.
8. Las apps operativas leen y escriben en la base tenant mientras dura la request.
9. Los redirects y enlaces internos conservan el prefijo tenant.
10. Al terminar la request, el contexto tenant se limpia.

## Decisiones iniciales

- Usuarios por tenant al inicio.
  - Justificacion: simplifica permisos y aislamiento operativo.
- El administrador inicial de cada tenant se crea como superusuario dentro de su base tenant para poder configurar su junta desde Django Admin.
- La app `tenants` se oculta y bloquea dentro del admin tenant. La lista global de tenants solo debe gestionarse fuera de una ruta tenant.
- No se mezclan datos de juntas en una misma base.
- `default` se conserva como base legacy/de pruebas; no se migrara por ahora.

## Fases pendientes

1. Usar `carabuela` como tenant de prueba hasta estabilizar el sistema.
2. Definir modulos activos de Carabuela en el admin global de tenants.
3. Reconstruir o redeplegar la imagen Docker con los cambios confirmados.
4. Definir politica de retencion/rotacion para backups multi-tenant.
