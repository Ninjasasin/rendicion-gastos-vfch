# Mapa de categorías de Rindegastos

Las 12 categorías que tiene VFCH en Rindegastos, qué significa cada una para el agente, cuándo se usa y en qué estado está su definición. Se va completando con el uso: **cada vez que Ignacio define o corrige una, se actualiza aquí** (y la fecha va a `3. Memoria/decisiones.md`).

**Criterio de Ignacio (19-nov-2026):** lo importante es que el informe quede creado con todos los gastos, sus boletas y sus datos. La clasificación la revisa el ejecutivo y la corrige en Rindegastos si hace falta. Por eso **el agente no pregunta por categorías**: usa Gastos De Viajes (lo más común) salvo que la boleta calce claramente con una categoría **Definida**.

Estado:
- **Definida**: el agente la aplica cuando la boleta calza claramente.
- **Por definir**: hay uso histórico pero falta la regla; el agente **usa Gastos De Viajes** y, si cree que podría ser esta, lo menciona en el resumen para que el ejecutivo revise.
- **Sin uso**: nunca se ha usado; el agente usa Gastos De Viajes (y lo menciona en el resumen si le parece que podría ir aquí).

## Uso histórico (base del mapa)
Revisión de los **36 informes anteriores** de un ejecutivo en Rindegastos (de 2024 a nov-2026, **281 gastos**), el 19-nov-2026:

| Categoría | Gastos | % | Dónde aparece |
|---|---|---|---|
| Gastos De Viajes | 252 | 90% | Casi todos los informes TC Internacional y los de viajes al extranjero (TC y reembolso) |
| Gastos Visitas | 18 | 6% | Informes "Visita <cliente>" (reembolso CLP) y algunos de TC Nacional |
| Gastos De Oficina | 7 | 2% | 1 compra de supermercado (reembolso) y 6 gastos sueltos dentro de informes TC Internacional |
| Gtos Representacion | 3 | 1% | Almuerzos en un restaurante de Santiago (TC Nacional y reembolso) |
| Desarrollo Y Promocion | 1 | 0,4% | Un servicio de diseño gráfico (TC Nacional) |
| Las otras 7 | 0 | 0% | — |

## Las 12 categorías

| # | Categoría | Qué es (propuesta) | Cuándo la usa el agente | Ejemplos | Estado |
|---|---|---|---|---|---|
| 1 | **Gastos De Viajes** | Todo gasto hecho **durante un viaje de trabajo** fuera de la ciudad base: alojamiento, transporte, comidas propias, supermercado, propinas | **Por defecto en tarjeta corporativa** y en fondos por rendir de viajes | Hoteles, Booking, Uber, trenes, aeropuerto, restaurantes y cafés en el viaje | **Definida** (Ignacio, 19-nov-2026) |
| 2 | **Gastos Visitas** | Gastos de una **visita a un cliente o a las plantas/viñas** (normalmente dentro de Chile): traslado, peajes, comidas de la visita | Informes de visita (p. ej. Panquehue / plantas: sin boletas, solo comprobantes). En TC: si la boleta es de una visita | Tag y peajes, Uber de la visita, almuerzo con el cliente durante la visita | **Definida para visitas a plantas** (Ignacio, 19-nov-2026); **por definir** el resto |
| 3 | **Gtos Representacion** | **Atenciones a terceros** (clientes, socios) que no son parte de una visita ni de un viaje: almuerzos, cenas, regalos | Solo si el ejecutivo lo indica | Almuerzo de negocios en Santiago | **Por definir** |
| 4 | **Gastos De Oficina** | Compras para la oficina: útiles, insumos, cafetería de la oficina | Solo compras para la oficina, no consumo personal en viaje | Supermercado para la oficina, librería | **Por definir** (hay 6 cafés/kioscos de viaje clasificados aquí en un informe TC Internacional: parece inconsistente) |
| 5 | **Desarrollo Y Promocion** | Gastos para promover las marcas o desarrollar mercado | Solo si el ejecutivo lo indica | Diseño gráfico, material de una feria | **Por definir** |
| 6 | **Gastos Marketing (Corporativo)** | Marketing de la compañía (no de una marca en particular) | Solo si el ejecutivo lo indica | — | **Sin uso** |
| 7 | **Gastos Marketing A&P** | Advertising & Promotion de marcas (actividades con clientes/consumidores) | Solo si el ejecutivo lo indica | — | **Sin uso** |
| 8 | **Gastos Equipos Computacion** | Compra de equipos o accesorios computacionales | Si la boleta es de un equipo o accesorio (cargador, mouse, adaptador) | — | **Sin uso** |
| 9 | **Servicios Y Equipos Comunicación Ti** | Telefonía, internet, roaming, servicios TI | Si la boleta es de roaming, chip, internet de viaje o similar | — | **Sin uso** |
| 10 | **Suscripciones Y Membresías** | Suscripciones y membresías (software, revistas, asociaciones, salones VIP) | Si la boleta es una suscripción o membresía | — | **Sin uso** |
| 11 | **Petroleo/Bencina** | Combustible | Si la boleta es de bencina/diésel (auto de la empresa o arriendo) | — | **Sin uso** |
| 12 | **Suministros** | Insumos y suministros (no de oficina) | Solo si el ejecutivo lo indica | — | **Sin uso** |

## Cómo decide el agente la categoría de un gasto
1. Usa la **categoría por defecto** del tipo de rendición (`reglas-de-negocio.md` §5): **Gastos De Viajes** en tarjeta corporativa y en fondos por rendir de viaje. Un restaurante, un café o un taxi van a Gastos De Viajes.
2. Si el **ejecutivo indica** otra categoría para un gasto o un grupo de gastos, se usa la que indica (campo `categoria` en `boletas.json`).
3. Si la boleta calza claramente con otra categoría **Definida**, la usa.
4. Si podría ser una categoría **Por definir** o **Sin uso**, **no pregunta**: deja Gastos De Viajes y lo menciona en el resumen ("revisa la categoría de estos gastos").
5. Nunca usa una categoría que no esté en la lista de 12.
6. Cuando el ejecutivo o Ignacio corrigen una categoría y dicen que es regla, se actualiza este mapa (y pasa a **Definida**).

## Preguntas abiertas para Ignacio (no frenan al agente: mientras tanto, Gastos De Viajes)
1. **Visitas vs. Representación:** el mismo restaurante de Santiago aparece una vez como Gastos Visitas y tres veces como Gtos Representacion. ¿Cuál es la regla? (propuesta: Visitas si es parte de una visita a cliente/planta; Representación si es una atención a terceros sin visita).
2. **Gastos De Oficina en viajes:** en el informe TC Internacional de abril 2026 hay cafés, un kiosco y un tren clasificados como Gastos De Oficina. ¿Fue un error o hay un criterio? (propuesta: en viajes todo va a Gastos De Viajes).
3. **Gastos Visitas en TC Nacional:** un bar/club social y Uber en Santiago se rindieron como Gastos Visitas. ¿Un gasto local con tarjeta corporativa va a Visitas o a Representación?
4. **Tarjeta personal:** ¿qué categoría lleva?
5. **Desarrollo Y Promocion / Marketing:** ¿quién usa estas categorías y para qué gastos?
