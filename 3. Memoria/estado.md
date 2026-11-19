# Estado (al 19-nov-2026)

## Último trabajo
- Agente creado y verificado con un caso real (cartola USD oct-2026: 80 líneas, cuadra; 13 con boleta, 2 boletas personales, 1 decisión manual pro forma + voucher). Informe creado en Rindegastos en borrador y carpetas ordenadas en el PC del ejecutivo.
- Cartola CLP del mismo mes: 3 líneas, sin boletas → no se creó informe.

## Probado y no probado
- Probado: leer cartola USD y CLP, cruce, marcar PDF, armar carpetas, crear informe con cartola adjunta, crear gastos con Múltiples (proveedor/total/categoría/nota escribiendo, fechas con el JS, boletas con file_upload), agregar gastos al informe.
- Fondo por rendir: `fondo.py`, `grilla.py --cruce/--offsets` y `preparar_archivo.py --cruce` probados con datos de prueba. **No probado en Rindegastos** (columnas de la grilla REEM y si acepta otra moneda).
- No probado todavía: `grilla.py` generando las acciones de punta a punta en una corrida nueva; la parte de categoría de `verificar_grilla.js`; cartola CLP con gastos con boleta; agregar gastos a un informe que ya fue enviado.

## Pendientes (decide Ignacio o se consulta)
1. Categoría para gastos con tarjeta personal.
2. Si en el futuro se crean también las líneas sin boleta (hoy no; `crear_lineas_sin_boleta` en parametros.json, no programado).
4. Si hay casos en que conviene "Simple" en vez de "Múltiples".
3. Qué hacer si aparece una boleta faltante cuando el informe ya fue enviado.
