# Encargo y fuentes

## Qué es y para quién
- Rendición mensual de la **tarjeta de crédito corporativa** (Santander WorldMember Business, a nombre de Viñedos Familia Chadwick SpA) de cada ejecutivo de VFCH, en **Rindegastos**.
- Hoy cada ejecutivo arma sus gastos a mano en Rindegastos. El agente lo deja armado; el ejecutivo solo revisa y envía.
- Se corre por pedido, cuando llega el estado de cuenta (mensual).

Además de la tarjeta corporativa, el agente rinde **fondos por rendir**: efectivo que la empresa entregó al ejecutivo (por ejemplo para un viaje). Ahí no hay cartola: el ejecutivo indica qué boletas van (ver `reglas-de-negocio.md` §9).

## Qué se entrega
1. **Informe en Rindegastos, en borrador** (uno por cartola que tenga al menos un gasto con boleta):
   - `TC Internacional - <Mes> <AAAA>` con la cartola USD, o `TC Nacional - <Mes> <AAAA>` con la cartola CLP.
   - Con la cartola original adjunta en "Archivos del informe".
   - Con un gasto por cada línea de la cartola que tiene boleta, con la boleta adjunta.
2. **Cartola marcada** (PDF): verde = tiene boleta, amarillo = falta boleta. Es la lista de pendientes del ejecutivo.
3. **Carpetas ordenadas en el PC del ejecutivo** (ver `Rendición de Gastos.md`): carpeta del informe, carpeta `AAAA-MM` con lo no rendido, y `cruce_AAAA-MM.json`.
4. **Resumen en el chat**: totales, pendientes, personales, avisos y qué puede borrar.

## Fuentes

| Fuente | Cómo llega | Estructura | Datos que usamos |
|---|---|---|---|
| Cartola USD | PDF del banco, "ESTADO DE CUENTA INTERNACIONAL DE TARJETA DE CRÉDITO". El nombre del archivo puede ser cualquiera. | 3–4 páginas. Cabecera con titular, tarjeta (`XXXX XXXX XXXX 1234`), fecha del estado de cuenta, período facturado y total. Luego una línea por movimiento. | Por línea: fecha (dd/mm/aa), descripción del comercio, ciudad, país (2 letras), **monto en moneda de origen** y **monto en USD**. |
| Cartola CLP | PDF del banco, "ESTADO DE CUENTA EN MONEDA NACIONAL DE TARJETA DE CRÉDITO". | 3 páginas. Igual que la USD, pero el lugar (p. ej. SANTIAGO) va a la izquierda de la fecha y hay un solo monto en pesos. | Por línea: fecha, descripción, monto en CLP. |
| Boletas | Fotos (JPEG/PNG, muchas veces de WhatsApp con nombres "WhatsApp Image …"). También pueden ser PDF de boletas electrónicas. | Una foto por papel. Puede haber dos papeles para un mismo gasto. | Lo lee Claude mirando cada imagen y lo anota en `boletas.json` (formato en la skill). |

`leer_cartola.py` reconoce la cartola **por su contenido**, no por el nombre del archivo.

## Trampas conocidas de las cartolas
- **"MONTO CANCELADO"** (USD) es el pago de la cartola anterior, con monto negativo. No es gasto. El script la marca `pago`.
- **"COMISION DE MANTENCION"** y todo lo de la sección "3. CARGOS, COMISIONES, IMPUESTOS Y ABONOS" son cargos del banco. No se rinden. El script los marca `cargo_banco`.
- **Montos** con punto de miles y coma decimal (`7.000,00`, `$18.868`).
- En la CLP la **fecha viene pegada al detalle** (`02/10/267019 JV AERO`): el script lo maneja.
- **Montos repetidos** en días distintos (Albert Heijn 2,59 dos días seguidos): el cruce usa la fecha más cercana.
- Una línea puede estar en **otra moneda de origen** que la boleta (RSD, TRY, CHF, GBP): el cruce compara la boleta con el **monto de origen** de la línea, no con el USD.
- Control obligatorio: suma de las líneas `gasto` = "TOTAL DE COMPRAS Y CARGOS" (USD) o "1. TOTAL OPERACIONES" (CLP). Si no cuadra, se para.

## Trampas conocidas de las boletas
- **Propina**: la boleta dice un total y el cobro en la tarjeta es mayor (boleta 28,70 + propina 3,00 = 31,70). En `boletas.json` el **monto es el cobrado** (31,70) y la diferencia va en "observacion".
- **Pro forma** ("PRO FORMA", "dit is geen geldig BTW kasticket"): no es boleta tributaria. Se adjunta igual, pero se avisa.
- **Dos papeles para un gasto**: pro forma + voucher de pago (pro forma 45,00 y voucher 49,50 = cargo de 49,50). Va una sola línea con las dos imágenes. El voucher puede tener otro nombre de comercio que la cartola (la terminal de pago está a nombre de otra empresa).
- **Voucher sin nombre de comercio** (solo "Customer's receipt"): se cruza por monto y fecha; el proveedor se toma de la cartola.
- **Pagada con otra tarjeta**: si la boleta muestra otros 4 últimos dígitos (p. ej. Visa …5678), es personal.
- **Pagada en efectivo** ("Kontant", "Cash", "Efectivo"): si no está en la cartola, es personal. Si sí está en la cartola, se rinde igual y se avisa (pasó con una boleta que decía Cash y estaba cobrada en la tarjeta).
- **Fecha de la boleta vs. cartola**: pueden diferir en 1–2 días (pagos cerca de medianoche, días de proceso). Tolerancia del cruce: ±2 días.
- **Moneda**: la boleta está en la moneda del país (EUR, CHF, GBP…). Nunca se convierte a mano: el monto a rendir es el de la cartola.
