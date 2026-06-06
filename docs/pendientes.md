# Pendientes priorizados

## Alta prioridad

- [ ] Reconstruir o redeplegar la imagen Docker para incorporar los cambios locales de codigo al contenedor definitivo.
- [ ] Revisar en navegador el CRUD de abonados: listado, creacion, edicion, ficha y permisos visibles.
- [ ] Definir si `estado_servicio` puede editarse manualmente desde el formulario de abonado o solo mediante suspension/reconexion.
- [ ] Implementar desactivar/reactivar abonado sin borrado fisico.
- [ ] Activar flags de produccion cuando exista HTTPS real:
  - `SECURE_SSL_REDIRECT=True`
  - `SESSION_COOKIE_SECURE=True`
  - `CSRF_COOKIE_SECURE=True`
  - `SECURE_HSTS_SECONDS` con un valor definido para produccion.
- [ ] Probar restauracion de backups en una base temporal, no sobre la base viva.
- [ ] Definir politica de rotacion y retencion de backups.
- [ ] Auditar usuarios existentes con `is_staff=True` y confirmar que solo Administradores o superusuarios puedan entrar a `/admin/`.
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
