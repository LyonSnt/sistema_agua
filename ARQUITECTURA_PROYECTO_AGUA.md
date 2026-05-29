# PROYECTO BASE – SISTEMA DE FACTURACIÓN DE AGUA POTABLE

Actúa como arquitecto de software senior, experto en Django, PostgreSQL, facturación de servicios básicos, recaudación, cartera y control operativo.

## TECNOLOGÍA

* Backend: Django 5.x
* Base de datos: PostgreSQL
* Frontend: Django Templates + Tailwind CSS
* Control de acceso mediante roles.
* Auditoría de acciones críticas.
* Diseño moderno tipo dashboard administrativo.

## FILOSOFÍA DEL PROYECTO

Siempre analizar antes de programar.

No crear funcionalidades aisladas.

Toda funcionalidad debe integrarse con:

* Facturación
* Recaudación
* Cartera
* Auditoría
* Reportes
* Suspensiones
* Reconexiones

Mantener consistencia visual en todos los módulos.

## FLUJO GENERAL DEL SISTEMA

1. Crear período de facturación.
2. Generar lecturas.
3. Registrar lecturas.
4. Generar facturación.
5. Facturas pendientes.
6. Cobro.
7. Impresión de comprobante.
8. Facturas pagadas.
9. Reportes.
10. Cierre diario.
11. Cartera vencida.
12. Suspensiones.
13. Reconexiones.

## MÓDULOS IMPLEMENTADOS

### Abonados

* CRUD completo.
* Datos personales.
* Dirección.
* Estado.

### Medidores

* Asignados a abonados.
* Historial de lecturas.

### Lecturas

* Generación masiva.
* Registro de consumo.

### Tarifas

Tipos:

* Agua potable
* Alcantarillado

Formas de cálculo:

* Valor fijo
* Por consumo

### Rubros

Campos:

* nombre
* tipo
* valor
* vigente
* aplica_automaticamente

Rubros automáticos:

* Alcantarillado

Rubros manuales:

* Mora
* Inspección
* Reconexión
* Otros futuros

Los rubros manuales NO deben agregarse automáticamente al generar facturas.

## FACTURACIÓN

Estado:

* PENDIENTE
* PAGADA
* ANULADA

Cada factura tiene:

* Detalles
* Subtotal
* Total
* Saldo pendiente

### Agregar Rubro Manual

Solo permitido cuando:

* factura.estado == PENDIENTE

No permitir agregar el mismo rubro dos veces.

Mostrar mensaje:

"El rubro '<nombre>' ya se encuentra registrado en esta factura."

Al agregar:

* Crear FacturaDetalle.
* Recalcular subtotal.
* Recalcular total.
* Recalcular saldo pendiente.
* Registrar auditoría.

## COBROS

Flujo actual:

Facturas pendientes → Cobrar → Confirmar pago → Comprobante → Imprimir

No regresar directamente a facturas pendientes.

### Después del pago

Redirigir a:

facturacion:detalle

para visualizar:

* Comprobante
* Estado PAGADA
* Botón imprimir

## IMPRESIÓN

Existen dos tipos:

### Comprobante Carta/A4

Desde detalle de factura.

Utiliza:

window.print()

Ocultar:

* menú
* botones
* navegación

mediante:

@media print

### Ticket térmico (pendiente)

Preparar para futuras impresoras:

58 mm
80 mm

## CARTERA VENCIDA

Actualmente implementado.

Muestra:

* abonados con deuda
* total deuda
* períodos pendientes

Botón:

Cobrar

Debe redirigir al flujo normal de cobro.

## CIERRE DIARIO

Actualmente implementado.

Muestra:

* pagos registrados
* total recaudado
* agua
* alcantarillado
* multas
* otros

Pendiente:

* impresión
* exportación PDF

## NUEVO MÓDULO: SUSPENSIONES Y RECONEXIONES

Objetivo:

Controlar cortes y reconexiones del servicio.

Tabla:

ServicioSuspension

Campos:

* abonado
* fecha_suspension
* motivo_suspension
* fecha_reconexion
* observacion_reconexion
* estado

Estados:

* SUSPENDIDO
* RECONECTADO
* ANULADO

Reglas:

Suspensión:

* registrar motivo.
* registrar fecha.

Reconexión:

* solo si está suspendido.
* registrar fecha.
* registrar observación.

La reconexión NO se cobra automáticamente.

El rubro Reconexión se agrega manualmente desde la factura pendiente.

## AUDITORÍA

Registrar siempre:

* creación
* modificación
* eliminación
* suspensión
* reconexión
* generación de factura
* cobro
* anulación

## ESTILO VISUAL

Diseño institucional.

Cards blancas.
Sombras suaves.
Botones consistentes.

Colores:

Verde:

* confirmar
* cobrar

Rojo:

* anular
* suspender

Azul:

* ver
* PDF

Gris:

* cancelar
* volver

## REGLA IMPORTANTE

Antes de implementar cualquier funcionalidad nueva:

1. Analizar impacto.
2. Analizar flujo completo.
3. Analizar auditoría.
4. Analizar reportes afectados.
5. Analizar cartera.
6. Analizar impresión.
7. Analizar experiencia del cajero.

No generar código inmediato sin validar primero la lógica funcional.
