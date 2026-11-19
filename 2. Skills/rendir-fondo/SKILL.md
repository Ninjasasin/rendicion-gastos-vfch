---
name: rendir-fondo
description: Arma en Rindegastos un informe de FONDO POR RENDIR (gastos pagados con efectivo que entregó la empresa) con las boletas que indica el ejecutivo, sin cartola. Se usa cuando el ejecutivo dice "crea mi informe de fondos por rendir", "rinde el efectivo del viaje" o similar.
---

# Rendir fondo por rendir

**Reglas:** `1. Contexto/reglas-de-negocio.md` §9 (y §5 para cómo se llena cada gasto). Scripts en `2. Skills/scripts/`, con `python -X utf8`.
Diferencia con `rendir-cartola`: **no hay cartola**. Qué boletas van al informe lo dice **el ejecutivo**; el agente interpreta su instrucción, se la repite como lista y espera su OK.

---

## Paso 0 · Entender la instrucción
El ejecutivo puede decirlo de muchas formas. Ejemplos y cómo se interpretan:

| Lo que dice el ejecutivo | Cómo se interpreta |
|---|---|
| "Crea mi informe de fondos por rendir con todas las boletas de la carpeta" | `incluir` = todas las boletas sueltas (no las de carpetas de informes ya hechos) |
| "Las boletas de la carpeta de octubre son gastos personales porque la TC ya fue rendida; con las que quedan crea el informe de fondos por rendir" | `personales` = las de `2026-10\`; `incluir` = las demás boletas sueltas |
| "Rinde el efectivo del viaje a Rusia: son las boletas del 5 al 12 de noviembre" | `incluir` = boletas con fecha en ese rango; el resto se pregunta |
| "Estas tres no van, son mías" (con nombres o montos) | esas tres a `personales` |
| "El fondo fue de 1.500 dólares" | `moneda` = USD (y sirve de control: el total no debería pasar de eso) |

Si falta algo, **pregunta en una sola tanda** (no de a uno):
1. **Motivo** del fondo (va en el nombre del informe): p. ej. "Viaje Rusia".
2. **Moneda** del fondo (en qué se entregó el efectivo): USD o CLP → define la política (USD - REEM o CLP - REEM).
3. **Mes** del informe (por defecto, el mes de la mayoría de las boletas).
4. Si hay boletas que no quedaron claras: ¿van al informe, son personales o quedan fuera?

## Paso 1 · Traer y leer las boletas
1. Conecta/lista la carpeta del ejecutivo y trae (`device_stage_files`) las boletas que corresponden según la instrucción (sueltas y/o de las carpetas `AAAA-MM` que nombró). No toques las carpetas de informes ya hechos.
2. Lee cada imagen y arma `boletas.json` **igual que en `rendir-cartola` paso 3** (archivo, fecha, comercio, proveedor, monto cobrado, moneda, medio_pago, documento, nota, categoria, observacion). Si una boleta no se lee, no la inventes: pregunta.

## Paso 2 · Escribir `fondo.json` con lo que dijo el ejecutivo
```json
{
 "motivo": "Viaje Rusia",
 "moneda": "USD",
 "mes": "2026-11",
 "instruccion": "texto tal como lo dijo el ejecutivo",
 "incluir": ["<archivo>", "..."],
 "personales": ["<archivo>", "..."],
 "fuera": [],
 "tipo_cambio": {},
 "decisiones": ["lo que se aclaró con el ejecutivo, con sus palabras"]
}
```
- `archivo` relativo a la carpeta de fotos (las de un `AAAA-MM` van como `"2026-10/12,00.jpeg"`).
- **Toda boleta traída tiene que quedar en una de las tres listas.**
- `tipo_cambio`: **solo si el ejecutivo lo dio** (1 unidad de la moneda de la boleta = X en la moneda del fondo, p. ej. `{"EUR": 1.08}`). Nunca inventarlo ni buscarlo por tu cuenta.

## Paso 3 · Preparar
```bash
python -X utf8 fondo.py <carpeta_trabajo>
```
- Muestra el nombre del informe (`Fondo por rendir - <motivo> - <Mes> <AAAA>`), la política, cada gasto con su monto y moneda, el total, avisos y personales. Escribe `cruce_fondo_AAAA-MM.json`.
- Si sale **SIN ASIGNAR** (exit 2): pregunta por esas boletas, ajusta `fondo.json` y vuelve a correr.
- **Moneda distinta a la del fondo y sin tipo de cambio:** el gasto queda en la moneda de la boleta (aviso). En el paso 5 se prueba si Rindegastos la acepta; si no, se le pide el tipo de cambio al ejecutivo y se vuelve a correr.
- Si el ejecutivo dio el monto del fondo, compáralo con el total y dilo (si el total pasa el fondo, avísale).

## Paso 4 · Mostrar la lista y pedir el OK
Muestra al ejecutivo, en tablas simples:
- **Van al informe**: cada boleta (fecha, comercio, monto, moneda, nota) y el total.
- **Personales**: cada boleta.
- **Quedan fuera** (si hay).
Y pregunta: "¿Creo el informe '<nombre>' con estos N gastos? Queda en borrador, sin enviar."

## Paso 5 · Cargar en Rindegastos
Igual que `rendir-cartola` paso 7, con estas diferencias:
1. **Informe**: política `USD - REEM - VFCH - ECA` o `CLP - REEM - VFCH - ECA` (la de `cruce_fondo_…json`), título = nombre del informe. **No hay cartola que adjuntar.**
2. **Gastos con Múltiples**, misma política REEM. Antes de llenar:
   - La grilla REEM tiene **más columnas** que la de TC (RUT Proveedor, Tipo De Documento, Número De Documento…). Con `read_page` toma los refs de la fila 1 y de la fila 2, calcula la posición de cada campo respecto del proveedor y el paso entre filas.
   - Si hay gastos en otra moneda, revisa si la columna **Moneda** deja elegir esa moneda (escribe "EUR" y mira si aparece). Si no aparece, **para**: pide el tipo de cambio, ponlo en `fondo.json`, vuelve al paso 3 y abre la grilla de nuevo (los gastos de la grilla anterior quedaron creados: avísale al ejecutivo; no los borres sin que lo pida).
   - Genera las acciones:
     ```bash
     python -X utf8 grilla.py <carpeta_trabajo> FONDO <n_ref> <tabId> --cruce cruce_fondo_AAAA-MM.json --offsets prov=..,total=..,moneda=..,tipodoc=..,rut=..,cat=..,nota=..,paso=..
     ```
     (sin `moneda=` si todo está en la moneda del fondo). Llena **Tipo De Documento** = `Bol y otros Gastos VFCH - 144` y **RUT Proveedor** = `11111111-1` para comercios extranjeros (para comercios chilenos, el RUT de la boleta si se ve; si no, se deja vacío y se avisa).
   - Fechas con `js/fechas_multiples.js`, boletas con `file_upload`, verificación con `js/verificar_grilla.js`, "Guardar cambios".
3. Agrega los gastos al informe ("+ Agregar gasto") y verifica N y total contra `fondo.py`.
4. **No envíes el informe.**

## Paso 6 · Ordenar las carpetas
```bash
python -X utf8 preparar_archivo.py <carpeta_trabajo> "<carpeta de fotos>" --cruce cruce_fondo_AAAA-MM.json
```
- `<Nombre del informe>\` con las boletas rendidas (renombradas por monto).
- `AAAA-MM\` con las personales (`<monto> - personal`).
- Las que quedaron "fuera" no se mueven.
- Copia con `device_commit_files`, verifica tamaños y di qué se puede borrar (`borrar.txt`). Si una boleta venía de una carpeta `AAAA-MM` y ahora quedó en el informe, también se puede borrar de ahí.

## Paso 7 · Cerrar
Resumen: informe (nombre, N gastos, total y moneda; en borrador), personales, fuera, conversiones hechas (tipo de cambio y quién lo dio), avisos (pro forma, propinas, categorías a revisar) y qué borrar. Si se aprendió algo de la grilla REEM (offsets reales, si acepta otra moneda), anótalo en `3. Memoria/reglas-aprendidas.md` y en `1. Contexto/rindegastos.md`.

## Checklist
- [ ] Instrucción del ejecutivo traducida a listas (`incluir`, `personales`, `fuera`) y confirmada.
- [ ] Todas las boletas asignadas (sin "SIN ASIGNAR").
- [ ] Tipo de cambio solo si lo dio el ejecutivo.
- [ ] OK del ejecutivo antes de cargar.
- [ ] Informe REEM en borrador con N gastos y total = `fondo.py`.
- [ ] Carpetas copiadas y tamaños verificados.
