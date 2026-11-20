---
name: ordenar-boletas
description: Solo ordena las boletas de la carpeta del ejecutivo: las renombra por su monto y las mueve a la carpeta de su mes (AAAA-MM), sin crear informes ni tocar Rindegastos. Se usa cuando el ejecutivo dice "ordena mis boletas", "renombra las boletas" o "ordena la carpeta".
---

# Ordenar boletas

**Reglas:** `1. Contexto/reglas-de-negocio.md` §7 y §10. Scripts en `2. Skills/scripts/`, con `python -X utf8`.
**Esta skill no crea informes, no lee cartolas y no abre Rindegastos.** Si el ejecutivo pide además rendir, eso es `rendir-cartola` o `rendir-fondo`.

## Paso 1 · Traer las boletas
1. `device_list_dir` de la carpeta del ejecutivo (`Documentos\Rinde gastos\`) y de sus carpetas `AAAA-MM`.
2. Boletas a ordenar: las imágenes (y PDF que no sean cartolas) **sueltas** en la carpeta. Si el ejecutivo lo pide, también las de las carpetas `AAAA-MM` que estén mal nombradas. **No se tocan** las carpetas de informes (`TC Internacional - …`, `TC Nacional - …`, `Fondo por rendir - …`) ni las cartolas.
3. `device_stage_files` de esas boletas (máx. 50 por llamada).

## Paso 2 · Leer cada boleta → `boletas.json`
Para ordenar basta con `archivo`, `fecha` y `monto` (mismo formato que `rendir-cartola` paso 3; si es fácil, llena también comercio, moneda, medio de pago y últimos 4 dígitos, porque sirven después para rendir).
- Si el ejecutivo dijo que alguna es personal, agrega `"personal": true` (queda `<monto> - personal`).
- Si una boleta no se lee (fecha o monto), no la inventes: déjala fuera y pregúntale.

## Paso 3 · Preparar
```bash
python -X utf8 ordenar_boletas.py <carpeta_trabajo> "<carpeta de fotos>"
```
Muestra qué boleta va a qué carpeta y con qué nombre (`2026-10\49,50.jpeg`; repetidos `49,50 (2).jpeg`). Muéstraselo al ejecutivo en una tabla simple (o un resumen por mes si son muchas) y pide el OK.

## Paso 4 · Ordenar (renombrar y mover, sin copias)
Igual que `rendir-cartola` paso 8 ("Ejecutar el orden"):
- **Vía normal (Cowork):** lo haces tú en segundo plano, sin clics del ejecutivo y sin tomar el control de la pantalla: `python -X utf8 ejecutar_movimientos.py "<carpeta del ejecutivo>" <trabajo>/salida/movimientos.json` (o `ordenar.ps1 -Si` si la terminal es Windows sin Python).
- **Solo si la sesión no puede mover archivos:** recomienda Cowork; si igual sigue aquí, copia `ordenar.ps1` y `ordenar.bat` a la raíz y pídele doble clic en `ordenar.bat`.
- **Control:** `device_list_dir` recursivo: cada boleta está en su carpeta con su nombre, no quedan boletas sueltas y no queda ningún `ordenar.*` (el script se borra solo al terminar bien; si quedó, revisa el `ordenar_<fecha>.log`).

## Paso 5 · Cerrar
Resumen: cuántas boletas por mes, cuáles quedaron como personales y cuáles no se pudieron leer.
