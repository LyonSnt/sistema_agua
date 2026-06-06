# Matriz de permisos por rol

## Roles

- Administrador
- Supervisor
- Cajero
- Lecturista
- Consulta

## Resumen por modulo

| Modulo / accion | Administrador | Supervisor | Cajero | Lecturista | Consulta |
| --- | --- | --- | --- | --- | --- |
| Panel principal | Si | Si | Si | Si | Si |
| Ver abonados | Si | Si | Si | Si | Si |
| Ver ficha PDF de abonado | Si | Si | Si | Si | Si |
| Ver medidores | Si | Si | Si | Si | Si |
| Crear / editar medidores | Si | Si | No | No | No |
| Cambiar medidor | Si | Si | No | No | No |
| Ver ficha PDF de medidor | Si | Si | Si | Si | Si |
| Generar lecturas | Si | Si | No | No | No |
| Registrar lecturas | Si | Si | No | Si | No |
| Importar lecturas | Si | Si | No | Si | No |
| Descargar plantilla de lecturas | Si | Si | No | Si | No |
| Ver facturas pendientes | Si | Si | Si | No | Si |
| Ver detalle/PDF de factura | Si | Si | Si | No | Si |
| Generar facturacion | Si | Si | No | No | No |
| Agregar rubro a factura | Si | Si | No | No | No |
| Anular factura | Si | No | No | No | No |
| Cobrar factura | Si | Si | Si | No | No |
| Ver comprobantes de pago | Si | Si | Si | No | No |
| Anular pago | Si | No | No | No | No |
| Ver reportes generales | Si | Si | Si | No | Si |
| Exportar reportes Excel/PDF restringidos | Si | Si | No | No | No |
| Ver suspensiones | Si | Si | No | No | No |
| Suspender servicio | Si | Si | No | No | No |
| Reconectar servicio | Si | Si | No | No | No |
| Ver multas | Si | Si | Si | No | No |
| Crear / cobrar multas | Si | Si | Si | No | No |
| Anular multa | Si | No | No | No | No |
| Ver reporte de multas | Si | Si | Si | No | Si |
| Exportar multas | Si | Si | No | No | No |
| Ver auditoria | Si | No | No | No | No |
| Exportar auditoria | Si | No | No | No | No |
| Administracion Django | Si | No | No | No | No |

## Rutas criticas cubiertas por tests

- `facturacion:anular`
- `pagos:anular`
- `multas:anular`
- `medidores:cambiar`
- `servicios:suspender`
- `servicios:reconectar`
- `auditoria:lista`
- `auditoria:exportar_excel`
- `reportes:recaudacion_diaria_excel`
- `reportes:cartera_vencida_excel`
- `pagos:cobrar`
- `facturacion:generar`
- `lecturas:registro_masivo`

## Decisiones

- El rol Administrador conserva acceso completo a rutas criticas.
- Supervisor puede operar procesos de gestion y exportaciones, pero no anular pagos, facturas o multas.
- Cajero puede cobrar y consultar operaciones de caja, pero no exportar reportes restringidos ni anular.
- Lecturista queda limitado a lecturas, abonados/medidores y panel.
- Consulta puede ver informacion general y reportes, pero no ejecutar acciones operativas.

## Pendientes recomendados

- Revisar acceso a `/admin/` con usuarios reales de cada rol.
- Evaluar si `Consulta` debe poder descargar PDFs de abonado, medidor y factura.
- Evaluar si `Cajero` debe poder ver multas pero no crearlas.
- Separar permisos finos de multas si se requiere: crear, cobrar, anular y consultar.
- Revisar permisos del menu y permisos por URL cada vez que se agregue una vista nueva.
