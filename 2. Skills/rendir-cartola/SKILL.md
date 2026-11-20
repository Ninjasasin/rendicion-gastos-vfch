---
name: rendir-cartola
description: Arma en Rindegastos la rendición de la tarjeta corporativa de un ejecutivo de VFCH a partir de su cartola (PDF) y las fotos de sus boletas, la deja en borrador y ordena las boletas en carpetas. Se usa cuando el ejecutivo dice "rinde mi cartola", "me llegó el estado de cuenta" o "arma la rendición".
---

# Rendir cartola

**Todas las reglas (qué informe, política, categoría, nota, cruce, personal, carpetas) están en `1. Contexto/reglas-de-negocio.md`.** Esta skill dice cómo se ejecuta; ante una duda de regla, manda ese archivo.

Todos los scripts están en `2. Skills/scripts/` y se corren con `python -X utf8 <script> ...` desde esa carpeta.
**Carpeta de trabajo** = una carpeta nueva en el espacio de trabajo de Claude, por ejemplo `~/rendicion/` (no en el PC del ejecutivo).
**Carpeta del ejecutivo** = `Documentos\Rinde gastos\` en su PC (o su subcarpeta, si se rinde por otro).

No te saltes pasos. Cada paso tiene un control; si el control falla, para y avisa.

---

## Paso 0 · Confirmar en una línea
1. De quién es la rendición y cuál es su carpeta. Si la carpeta no está conectada a la sesión, pídele que la conecte con **"Add folder"** en la app de escritorio de Claude (las rutas con "ñ" no se pueden pedir desde el chat).
2. Que tenga **Rindegastos abierto con su sesión iniciada** en Chrome (Claude in Chrome). El agente nunca escribe contraseñas.
3. Dile en una línea lo que vas a hacer: leer cartola y boletas, cruzar, marcar la cartola, cargar en Rindegastos **sin enviar** y ordenar carpetas.

## Paso 1 · Traer los archivos
1. `device_list_dir` de la carpeta del ejecutivo (no recursivo) y de cada subcarpeta `AAAA-MM` que exista.
2. Separa:
   - **Cartolas**: PDF sueltos en la carpeta (no los "… - revisión boletas.pdf").
   - **Boletas nuevas**: imágenes (y PDF que no sean cartolas) sueltas en la carpeta.
   - **Boletas pendientes de meses anteriores**: imágenes en las carpetas `AAAA-MM` **que no digan "personal"**. Pueden calzar con la cartola nueva.
   - Las carpetas de informes anteriores (`TC Internacional - …`, `TC Nacional - …`) **no se tocan**.
3. `device_stage_files` de todo lo anterior (máx. 50 por llamada). Quedan en `/mnt/user-data/uploads/<carpeta>/…`. Esa ruta es la **carpeta de fotos** para los scripts y la única desde la que Chrome puede subir archivos.
4. Si no hay cartola, para y pídela. Si no hay boletas, sigue igual (solo se marcará la cartola).

## Paso 2 · Leer las cartolas
```bash
python -X utf8 leer_cartola.py "<carpeta de fotos>/<cartola>.pdf" <carpeta_trabajo>
```
- Una vez por cada PDF de cartola. Deja `cartola_USD.json` y/o `cartola_CLP.json`.
- Imprime titular, tarjeta, fecha del estado de cuenta, nombre del informe que corresponde y el control de totales.
- **Control:** tiene que decir `CUADRA`. Si dice `ERROR: NO CUADRA`, para: el PDF tiene un formato que el script no conoce. Muestra al ejecutivo qué líneas leyó y avisa a Ignacio.
- Revisa que el titular y la tarjeta sean del ejecutivo. Si no, pregunta.

## Paso 3 · Leer las boletas → `boletas.json`
Mira **cada imagen** (Read) y anota una entrada por foto en `<carpeta_trabajo>/boletas.json`:

```json
[
 {"archivo": "WhatsApp Image 2026-11-19 at 11.39.25.jpeg",
  "fecha": "2026-10-14",
  "comercio": "WHSmith Brussels Airport",
  "proveedor": "WH Smith Brussels Airport",
  "monto": 12.58,
  "moneda": "EUR",
  "medio_pago": "tarjeta",
  "tarjeta_ult4": "1234",
  "documento": "boleta",
  "nota": "Alimentación",
  "categoria": "",
  "observacion": ""}
]
```

| Campo | Qué va | Reglas |
|---|---|---|
| `archivo` | Nombre del archivo, relativo a la carpeta de fotos | Para pendientes de otro mes: `"2026-09/12,00.jpeg"` |
| `fecha` | Fecha del pago (AAAA-MM-DD) | La del voucher de pago si hay; si no, la de la boleta |
| `comercio` | Nombre tal como aparece en la boleta | `""` si el voucher no lo dice |
| `proveedor` | Nombre para Rindegastos | Legible y sin "&" (usar "and"). Si la boleta no dice comercio, usa el de la cartola. Si el voucher está a nombre de otra empresa que la cartola (terminal de pago), usa el de la cartola |
| `monto` | **Monto cobrado** | Con propina si la hubo. Número con punto decimal |
| `moneda` | Moneda de la boleta | EUR, CHF, GBP, CLP, USD… |
| `medio_pago` | `tarjeta`, `efectivo`, `otra_tarjeta` o `desconocido` | "Kontant"/"Cash" = efectivo. Otros 4 dígitos = otra_tarjeta |
| `tarjeta_ult4` | Últimos 4 dígitos si se ven | `""` si no se ven |
| `documento` | `boleta`, `voucher`, `factura` o `proforma` | "PRO FORMA" / "geen geldig BTW kasticket" = proforma |
| `nota` | Alimentación, Alojamiento, Movilización u Otros | Ver `reglas-de-negocio.md` §5 |
| `categoria` | Vacío = la por defecto (Gastos De Viajes) | Llenar solo si el ejecutivo indicó otra o si la boleta calza claramente con una categoría **Definida** de `1. Contexto/categorias.md`. **No se pregunta por categorías** |
| `observacion` | Lo raro que vea el ejecutivo | Propina, efectivo, ilegible, no dice qué se compró… |

Si algo no se lee (monto o fecha), no lo inventes: deja la boleta fuera de `boletas.json` y pregúntale al ejecutivo.

## Paso 4 · Cruzar
```bash
python -X utf8 cruzar.py <carpeta_trabajo>
```
- Deja `cruce_AAAA-MM.json` (AAAA-MM = mes del estado de cuenta) y muestra: líneas con y sin boleta por cartola, boletas `rendida`, `personal`, `sin_cartola` y `duda`, y avisos.
- **Dudas** (exit 2): una boleta calza con más de una línea. Muestra las opciones al ejecutivo, anota su respuesta en `"decisiones"` del `cruce_AAAA-MM.json` y vuelve a correr.
- **Revisa con el ejecutivo las `sin_cartola`**: puede ser (a) un gasto que sale en la próxima cartola → se deja pendiente; (b) un segundo papel del mismo gasto (pro forma + voucher) → decisión `adjuntar_a` la línea; (c) un gasto personal → decisión `personal`.
- **Revisa los avisos** (pro forma, efectivo que sí está en la tarjeta, propina, "no dice qué se compró") y menciónalos en el resumen.
- Formato de las decisiones:
```json
"decisiones": [
 {"boleta": "<archivo>", "accion": "adjuntar_a", "linea": "USD-044", "motivo": "pro forma del mismo gasto"},
 {"boleta": "<archivo>", "accion": "personal", "motivo": "lo dijo el ejecutivo"},
 {"boleta": "<archivo>", "accion": "pendiente", "motivo": "sale en la próxima cartola"}
]
```
Las decisiones se guardan con el cruce: si se vuelve a correr, sale igual.

## Paso 5 · Marcar la cartola
```bash
python -X utf8 marcar_cartola.py <carpeta_trabajo> "<carpeta de fotos>/<cartola>.pdf"
```
- Una vez por cartola. Deja `salida/<cartola> - revisión boletas.pdf` (verde = con boleta, amarillo = falta).
- Mándaselo al ejecutivo (SendUserFile) para que vea lo que le falta.

## Paso 6 · Mostrar el plan y pedir el OK
Antes de tocar Rindegastos muestra, por cartola:
```bash
python -X utf8 grilla.py <carpeta_trabajo> USD
```
- La tabla de gastos a crear (proveedor, total, fecha, categoría, nota, boletas), el nombre del informe y el total.
- Las boletas personales y las pendientes.
- Los gastos con **categoría distinta a la por defecto** (aviso de `cruzar.py`), solo para que el ejecutivo los vea. No se pregunta por categorías.
Pregunta en una línea: "¿Cargo estos N gastos en Rindegastos en el informe '<nombre>'? Queda en borrador, sin enviar." Si una cartola no tiene ninguna línea con boleta, **no se crea informe** para esa cartola (se dice en el resumen).

## Paso 7 · Cargar en Rindegastos (Claude in Chrome)
Carga las herramientas de Chrome en una sola llamada a ToolSearch (tabs_context_mcp, tabs_create_mcp, navigate, computer, find, read_page, get_page_text, browser_batch, javascript_tool, file_upload, tabs_close_mcp). Trabaja en una **pestaña nueva** y ciérrala al final.

### 7.1 Revisar antes de crear
1. Abre `https://app.rindegastos.com/employee/expenseReports`. Revisa que el rendidor sea el ejecutivo (aparece en el detalle de los informes) y que la sesión esté iniciada.
2. Mira la lista de informes y la pestaña **"Informes en borrador"**: si ya existe un informe con el mismo nombre, **no crees otro**: pregunta si se agregan los gastos a ese.
3. Mira **Gastos > "Gastos en borrador"**: si hay gastos vacíos (0,00) o gastos que parecen de esta misma cartola, avísale al ejecutivo antes de seguir (puede ser una carga anterior a medias). No los borres.

### 7.2 Crear el informe
1. Informes > **"+ Crear informe"** → Política (`USD - TC - VFCH - ECA` o `CLP - TC - VFCH - ECA`) → Título (`nombre_informe` del cruce) → **"Crear informe"**.
2. En "Archivos del informe": busca el `file-input` con `find` y sube la **cartola original** con `file_upload` (ruta de la carpeta de fotos; origin `https://app.rindegastos.com`).
3. **"Guardar cambios"**. Anota el id del informe (está en la URL: `/report/<id>`) en `"rindegastos"` del cruce.

### 7.3 Crear los gastos con **Múltiples**
1. Gastos > **"+ Crear gasto"** → pestaña **Múltiples** → Política (escribe "USD - TC" o "CLP - TC" y Enter) → Número de gastos (escribe el número y Enter) → **"Continuar"**. Espera a que la grilla cargue (≈5 s; mientras carga, read_page solo muestra "progressbar").
2. `read_page` (filter interactive): toma el número del ref del primer "Indica el proveedor" (p. ej. `ref_366`). Comprueba que el de la fila 2 sea ese +12. Si no, el patrón cambió: llena a mano y anota en `3. Memoria/reglas-aprendidas.md`.
3. Genera las acciones:
   ```bash
   python -X utf8 grilla.py <carpeta_trabajo> USD <n_ref> <tabId>
   ```
   y ejecuta las `acciones` de `grilla_USD.json` con **browser_batch** (en bloques de ≤ 60 acciones). Llena proveedor, total, categoría y nota.
4. Fechas: copia `scripts/js/fechas_multiples.js`, reemplaza `FECHAS` por la lista que imprimió `grilla.py` y córrelo con `javascript_tool`. Tiene que devolver `"cuadra": true`.
5. Boletas: `read_page` (filter all) y toma, en orden, los `button … type="file"` que están dentro de la grilla (uno por fila, al lado de "Cargar archivos"; los dos últimos fuera de la grilla son del panel derecho y no se usan). Para cada fila, `file_upload` con la(s) ruta(s) de la carpeta de fotos de sus boletas (columna "boletas" de `grilla.py`). Dos boletas para un gasto van juntas en la misma llamada.
6. Verifica antes de guardar:
   - `scripts/js/verificar_grilla.js` con `javascript_tool`: compara fila por fila con la tabla de `grilla.py` (proveedor, total, fecha, categoría, nota).
   - Haz clic en 2–3 filas (las de dos boletas, al menos) y mira el panel derecho: tiene que mostrar la imagen correcta ("1/2" si son dos).
7. **"Guardar cambios"**. Vuelve a la lista de Gastos: tienen que aparecer los N gastos en "Borrador" con su imagen.

### 7.4 Agregar los gastos al informe
1. Abre el informe (`/employee/expenseReports/report/<id>`) → **"+ Agregar gasto"**.
2. `get_page_text`: la lista del diálogo tiene que ser **exactamente** los N gastos recién creados (proveedor, fecha, total). Si aparecen otros gastos de la misma política (de otra carga), marca solo los tuyos uno por uno; si son exactamente los tuyos, usa `scripts/js/seleccionar_gastos_informe.js`.
3. **"Agregar gastos"**.
4. **Control:** "Gastos del informe (N)" y el total del informe = total de líneas con boleta que dio `cruzar.py`. Si no cuadra, revisa gasto por gasto y no sigas hasta que cuadre.
5. Abre 1–2 gastos del informe y revisa: nota, categoría, cuenta contable (50370 en Gastos De Viajes), tipo de documento "Comprobante - CTE" e imagen.
6. **No aprietes "Enviar informe".** Cierra la pestaña.

## Paso 8 · Ordenar las carpetas del ejecutivo (renombrar y mover, sin copias)
```bash
python -X utf8 preparar_archivo.py <carpeta_trabajo> "<carpeta de fotos>"
```
- Arma el orden final (`reglas-de-negocio.md` §7): cada boleta rendida se **renombra por su monto y se mueve** a la carpeta del informe junto con su cartola; las no rendidas van a `AAAA-MM` (personales como `<monto> - personal`); la cartola que no tuvo boletas va igual a una carpeta con el nombre que habría tenido su informe. **No se hacen copias.**
- Deja en `salida/`: `movimientos.json` (qué original va a dónde), `ordenar.ps1`, `ordenar_si.bat` y `ordenar.bat` (los ejecutan) y `nuevos/` + `nuevos.json` (archivos que generó el agente: cartolas marcadas y `cruce_AAAA-MM.json`).

### Ejecutar el orden
1. Copia cada archivo de `nuevos.json` a la carpeta del ejecutivo con `device_commit_files` (`devicePath` = carpeta del ejecutivo + la ruta de `nuevos.json`).
2. **Si la sesión tiene terminal en el PC** (Cowork: existe la herramienta `device_bash`):
   - Copia `salida/ordenar.ps1` a la **raíz** de la carpeta del ejecutivo (`device_commit_files`).
   - Córrelo desde esa carpeta: `powershell -NoProfile -ExecutionPolicy Bypass -File ordenar.ps1 -Si`.
3. **Si no tiene terminal pero sí control del computador** (herramientas `computer_*`): copia `ordenar.ps1` y `ordenar_si.bat` a la raíz; pide acceso al **Explorador de archivos** (queda en modo solo clic: no se puede escribir en la barra de direcciones, así que se navega con clics por las carpetas); entra a la carpeta y haz doble clic en `ordenar_si.bat` (corre sin preguntas). Luego suelta el control (`computer_release_lock`).
4. **Si no tiene ninguna de las dos:** copia `ordenar.ps1` y `ordenar.bat` a la raíz de la carpeta y pídele al ejecutivo: "haz doble clic en **ordenar.bat**: te muestra la lista y te pide confirmar". Espera a que diga que lo hizo.
5. **Control:** `device_list_dir` (recursivo): cada archivo de `movimientos.json` está en su destino, no quedan boletas ni cartolas sueltas de esta rendición, y `ordenar.ps1` y los `.bat` ya no están (se borran solos al terminar bien). Si algo no calza, lee el `ordenar_<fecha>.log` que deja el script.
- El script **solo mueve**: nunca borra boletas ni cartolas, y si un nombre ya existe agrega " (2)".
- Si una boleta pendiente de un `AAAA-MM` anterior se rindió ahora, el script la mueve desde esa carpeta a la del informe.

## Paso 9 · Cerrar
Resumen para el ejecutivo (corto, con tablas simples):
1. Informe(s) creado(s): nombre, N gastos, total, **en borrador: revísalo y envíalo tú**.
2. Líneas de la cartola **sin boleta** (cuántas y total) → ver el PDF marcado. Si consigue esas boletas, las deja en su carpeta y se corre de nuevo (se agregan al mismo informe mientras esté en borrador).
3. Boletas personales y pendientes (dónde quedaron).
4. Avisos a revisar (pro forma, propinas, efectivo, nota "Otros") y gastos cuya **categoría conviene revisar** (podrían ir en una categoría "Por definir"; quedaron en Gastos De Viajes).
5. Cómo quedó ordenada su carpeta (y el `ordenar_<fecha>.log`, que puede borrar cuando quiera).
6. Actualiza `3. Memoria/estado.md` (sin datos sensibles) y, si hubo algo nuevo, `reglas-aprendidas.md` / `decisiones.md`.

## Checklist
- [ ] Cartola(s) leída(s) y **CUADRA**.
- [ ] Todas las fotos están en `boletas.json` o se preguntó por ellas.
- [ ] Cruce sin dudas; `sin_cartola` revisadas con el ejecutivo.
- [ ] Cartola marcada enviada al ejecutivo.
- [ ] OK del ejecutivo antes de cargar.
- [ ] Informe con la cartola adjunta, N gastos y total = cruce.
- [ ] Informe **en borrador** (no enviado).
- [ ] Carpeta ordenada: originales renombrados y movidos (sin copias), cartola marcada y cruce copiados.
