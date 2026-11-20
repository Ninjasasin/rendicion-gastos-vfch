# Reglas de negocio (todas las decisiones del agente en un solo lugar)

Este es el **único lugar** donde están las reglas. El resto de los archivos apunta aquí.
- Lo que tiene un **parámetro** se cambia en `1. Contexto/parametros.json` (lo leen los scripts; no hay que tocar código).
- Lo que no tiene parámetro es criterio de Claude al leer boletas o al usar Rindegastos.
- Quien decide las reglas es **Ignacio** (dueño del agente). Todo cambio se anota con fecha en `3. Memoria/decisiones.md`.

---

## 1. Qué informe se crea

| Regla | Valor hoy | Parámetro |
|---|---|---|
| Un informe por cartola | Cartola USD → un informe; cartola CLP → otro informe | — |
| Nombre del informe | `<nombre> - <Mes> <AAAA>` → "TC Internacional - Octubre 2026" / "TC Nacional - Octubre 2026" | `nombre_informe_por_cartola` |
| Mes del nombre | Mes de la **fecha del estado de cuenta** (26/10/2026 → Octubre 2026) | — |
| Política del informe | USD → `USD - TC - VFCH - ECA`; CLP → `CLP - TC - VFCH - ECA` | `politica_por_cartola` |
| Cartola sin ninguna boleta | **No se crea informe** (la cartola queda suelta en la carpeta y se dice en el resumen) | — |
| Ya existe un informe con ese nombre | No se crea otro: se pregunta si se agregan los gastos a ese | — |
| Archivo adjunto al informe | La **cartola original** en "Archivos del informe" | — |
| Envío | **Nunca.** El informe queda en borrador; lo envía el ejecutivo | — |

## 2. Qué líneas de la cartola se rinden

| Regla | Valor hoy | Parámetro |
|---|---|---|
| No se rinden | Pago de la cartola anterior ("MONTO CANCELADO", monto negativo) y cargos del banco (sección 3: comisiones, impuestos, intereses) | `cartola_no_se_rinde_si_contiene` |
| Línea con boleta | Se crea un gasto | — |
| Línea sin boleta | **No se crea** por ahora; queda en amarillo en la cartola marcada | `crear_lineas_sin_boleta` (hoy `false`; **`true` no está programado**) |
| Control | Suma de líneas que se rinden = total de operaciones de la cartola. Si no cuadra, se para | — |

## 3. Cómo se cruza una boleta con la cartola

| Regla | Valor hoy | Parámetro |
|---|---|---|
| Qué se compara | El **monto de la boleta** (cobrado, con propina) contra el **monto en moneda de origen** de la línea | — |
| Tolerancia de fecha | ± días entre la boleta y la línea | `cruce_tolerancia_dias` (hoy 2) |
| Cruce válido | Solo si es **único** (la boleta tiene una sola línea posible y la línea una sola boleta) | — |
| Empate entre boletas por una línea | Gana la que muestra los 4 dígitos de la tarjeta de la cartola; después, la pagada con tarjeta; después, la de fecha más cercana | — |
| Empate entre líneas para una boleta | Gana la de fecha más cercana | — |
| Si sigue el empate | **Duda**: se le pregunta al ejecutivo; su respuesta queda en "decisiones" del `cruce_AAAA-MM.json` | — |
| Dos papeles para un mismo gasto (pro forma + voucher) | Un solo gasto con las dos imágenes, por decisión `adjuntar_a` | — |

## 4. Cuándo una boleta es gasto personal

| Regla | Valor hoy | Parámetro |
|---|---|---|
| Otra tarjeta | La boleta muestra otros 4 últimos dígitos que la tarjeta de la cartola → **personal** | — |
| Tarjeta corporativa | La boleta muestra los 4 últimos dígitos de la tarjeta corporativa → es corporativa: si no está en esta cartola, queda **pendiente para la próxima** (nunca personal) | — |
| Sin dígitos en la boleta | Muchas boletas corporativas no los muestran: se cruza por monto y fecha | — |
| No está en la cartola y se pagó en efectivo u otra tarjeta | → **personal** | `medios_de_pago_personales` |
| No está en la cartola y no se sabe cómo se pagó | → **pendiente** (puede salir en la próxima cartola); se revisa con el ejecutivo | — |
| Dice "Cash"/efectivo pero sí está en la cartola | Se rinde igual y se avisa | — |
| Qué se hace con la personal | No va al informe. Se archiva como `<monto> - personal` en la carpeta del mes | `sufijo_boleta_personal` |

## 5. Cómo se llena cada gasto

| Campo | Regla | Parámetro |
|---|---|---|
| Proveedor | Nombre legible del comercio. Si la boleta no lo dice o el voucher está a nombre de otra empresa, el de la cartola. Sin "&" (se escribe "and") | — |
| Total | **Monto de la cartola** en la moneda de la cartola (USD o CLP). Nunca el de la boleta ni uno calculado | — |
| Fecha | Fecha de la línea de la cartola | — |
| Tipo de documento | `Comprobante` (queda "Comprobante - CTE"; viene por defecto) | — |
| Centro de costo distinto al propio | Vacío | — |
| **Categoría** | Por defecto según el tipo de rendición; otra solo según `categorias.md` | `categoria_por_tipo_de_rendicion`, `categorias_validas`, `categorias_definidas` |
| **Nota** | Una de cuatro (tabla de abajo) | `notas_validas`, `nota_por_defecto` |
| Archivo | La(s) boleta(s) de esa línea | — |

### Categoría
**El mapa completo de las 12 categorías (qué es cada una, cuándo se usa, estado de la definición y uso histórico) está en `1. Contexto/categorias.md`.** Resumen:

- Cada gasto parte con la **categoría por defecto de su tipo de rendición** (tabla de abajo).
- Otra categoría solo si el **ejecutivo la indica** o si la boleta calza claramente con una categoría **Definida**. **No se pregunta por categorías**: el ejecutivo corrige en Rindegastos al revisar (criterio de Ignacio, 19-nov-2026). Lo dudoso se menciona en el resumen.
- Parámetros: `categorias_validas` (las 12), `categorias_definidas` (las que el agente aplica por su cuenta).

#### Categoría por defecto según el tipo de rendición
| Tipo de rendición | Categoría | Estado en el agente |
|---|---|---|
| Tarjeta corporativa (boleta, CLP y USD) | **Gastos De Viajes** | **Es lo que hace el agente hoy** |
| Fondo por rendir (p. ej. viaje con efectivo) | Gastos De Viajes | Regla definida; el agente aún no lo hace |
| Visita a Panquehue / plantas productivas (sin boletas, solo comprobantes) | Gastos Visitas | Regla definida; el agente aún no lo hace |
| Tarjeta personal (boleta, CLP o USD) | **Por definir** | Pendiente de Ignacio |

La cuenta contable la pone Rindegastos según la categoría (Gastos De Viajes = 50370).

### Nota según el gasto
| Nota | Qué va |
|---|---|
| Alimentación | Restaurantes, cafés, bares, supermercado, comida en aeropuertos |
| Alojamiento | Hoteles, Booking, tasas municipales del hotel (city tax) |
| Movilización | Uber, taxi, trenes, metro, buses, bicicletas, vuelos, peajes |
| Otros | Lo que no calza en las anteriores o no se sabe qué es (se avisa en el resumen) |

## 6. Cómo se crean los gastos en Rindegastos

| Regla | Valor hoy | Parámetro |
|---|---|---|
| Múltiple o individual | **Siempre "Crear gasto > Múltiples"**, aunque sea un solo gasto. "Simple" no se usa | `modo_creacion_gastos` (hoy `multiples`) |
| Cuándo abrir la grilla | Solo cuando el cruce está cerrado y el ejecutivo dio el OK (al apretar "Continuar" los gastos ya quedan creados) | — |
| Cuándo pedir OK | Antes de cargar: se muestra la tabla de gastos, el informe y el total | — |
| Gastos en borrador que ya existían | No se tocan ni se borran; se avisa al ejecutivo | — |

## 7. Carpetas y nombres de archivo (PC del ejecutivo)

| Regla | Valor hoy | Parámetro |
|---|---|---|
| Carpeta del ejecutivo | `Documentos\Rinde gastos\` (o una subcarpeta por ejecutivo si una persona rinde por varios) | — |
| Carpeta del informe | Mismo nombre del informe; lleva boletas rendidas, cartola original y cartola marcada | — |
| Cartola sin boletas | Igual va a una carpeta con el nombre que habría tenido su informe (aunque no se cree informe), para que no quede suelta | — |
| Cómo se ordena | Los **originales se renombran y se mueven** (no se hacen copias). Con terminal en el PC (Cowork) lo hace Claude; sin terminal, el ejecutivo hace doble clic en `ordenar.bat` | — |
| Carpeta del mes | `AAAA-MM` = **mes de la fecha de la boleta**; lleva lo no rendido (personales y pendientes) | — |
| Nombre de cada boleta | Su monto con coma: `49,50.jpeg`; repetidos `49,50 (2).jpeg`; personales `49,50 - personal.jpeg` | `sufijo_boleta_personal` |
| Decisiones de la corrida | `cruce_AAAA-MM.json` en la carpeta del ejecutivo (AAAA-MM = mes del estado de cuenta) | — |
| Borrar | Nunca se borran boletas ni cartolas: solo se mueven. Si un nombre ya existe, se agrega " (2)" | — |

## 8. Lo que el agente nunca hace
- Enviar un informe.
- Borrar gastos, informes o borradores en Rindegastos sin que el ejecutivo lo pida para ese caso.
- Escribir contraseñas.
- Inventar un monto, una fecha o un cruce.
- Guardar datos de ejecutivos en la carpeta del agente (es pública).

## 9. Fondo por rendir (efectivo entregado por la empresa)

Se usa cuando el ejecutivo pide "crea mi informe de fondos por rendir" o similar. Skill: `2. Skills/rendir-fondo/SKILL.md`.

| Regla | Valor hoy | Parámetro |
|---|---|---|
| Cartola | **No hay.** Qué boletas van al informe lo indica el ejecutivo (por carpeta, por fechas, por nombre o "todas menos…"). El agente le repite la lista y espera el OK | — |
| Boletas que el ejecutivo dice que son personales | No van al informe; se archivan como `<monto> - personal` en la carpeta del mes (p. ej. "las de octubre son personales porque la TC ya se rindió") | `sufijo_boleta_personal` |
| Política | Según la moneda en que se entregó el efectivo: USD → `USD - REEM - VFCH - ECA`; CLP → `CLP - REEM - VFCH - ECA` | `fondo_politica_por_moneda` |
| Nombre del informe | `Fondo por rendir - <motivo> - <Mes> <AAAA>` (p. ej. "Fondo por rendir - Viaje Rusia - Noviembre 2026"); el motivo lo da el ejecutivo | `fondo_nombre_informe` |
| Monto de cada gasto | El de la boleta (cobrado, con propina). Si la boleta está en otra moneda que el fondo: (1) se prueba si Rindegastos acepta la moneda de la boleta; (2) si no, se usa el **tipo de cambio que entrega el ejecutivo**. Nunca se inventa | `fondo_conversion` |
| Categoría | Gastos De Viajes (mismo criterio de §5: no se pregunta) | `categoria_por_tipo_de_rendicion.fondo_por_rendir` |
| Tipo de documento | `Bol y otros Gastos VFCH - 144` | `fondo_tipo_documento` |
| RUT proveedor | Extranjero: `11111111-1`. Chileno: el de la boleta si se ve | `fondo_rut_proveedor_extranjero` |
| Número de documento | Solo si la boleta lo trae | — |
| Control | Si el ejecutivo dice el monto del fondo, se compara con el total y se avisa si lo pasa | — |
| Carpetas | Igual que §7: carpeta con el nombre del informe (boletas rendidas) y `AAAA-MM` (personales). Las que quedan "fuera" no se mueven | — |

## 10. Solo ordenar boletas

Si el ejecutivo pide "ordena mis boletas" (sin pedir rendir): skill `2. Skills/ordenar-boletas/SKILL.md`.

| Regla | Valor hoy | Parámetro |
|---|---|---|
| Qué hace | Renombra cada boleta suelta por su monto y la mueve a la carpeta de su mes (`AAAA-MM` de la fecha de la boleta) | — |
| Qué no hace | No lee cartolas, no crea informes, no toca Rindegastos, no mueve carpetas de informes | — |
| Personales | Solo si el ejecutivo lo dice: `<monto> - personal` | `sufijo_boleta_personal` |

## Pendientes de definir (Ignacio)
1. Categoría para tarjeta personal y las preguntas abiertas de `categorias.md` (Visitas vs. Representación, Oficina en viajes, etc.).
2. Si alguna vez se crean las líneas sin boleta (`crear_lineas_sin_boleta`).
3. Si hay casos en que conviene "Simple" en vez de "Múltiples".
4. Qué hacer si aparece una boleta faltante cuando el informe ya fue enviado.
5. Fondo por rendir: confirmar en la primera corrida si Rindegastos acepta gastos en otra moneda en las políticas REEM y cuáles son las columnas de su grilla.
