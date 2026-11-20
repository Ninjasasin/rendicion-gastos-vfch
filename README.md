# Rendición de Gastos — VFCH

Agente para **Claude** que arma en **Rindegastos** la rendición de la **tarjeta de crédito corporativa** (a partir del estado de cuenta y las fotos de las boletas) y de los **fondos por rendir** en efectivo (con las boletas que indique el ejecutivo). Deja el informe **en borrador**, con las boletas adjuntas: el ejecutivo solo revisa y envía.

Hecho para los ejecutivos de Viñedos Familia Chadwick (VFCH). Mantenido por Ignacio Zúñiga.

## Qué hace
1. Lee la cartola del banco (PDF, USD y/o CLP) y verifica que cuadre con su total.
2. Lee las fotos de las boletas (monto, fecha, comercio, cómo se pagó).
3. Cruza cada boleta con su línea de la cartola. Las boletas que no están en la cartola quedan como **gasto personal**.
4. Marca la cartola: **verde** = tiene boleta, **amarillo** = falta boleta.
5. En Rindegastos crea el informe `TC Internacional - <Mes> <AAAA>` (o `TC Nacional`), le adjunta la cartola, crea los gastos con su boleta y los agrega al informe. **No lo envía.**
6. Ordena tu carpeta: renombra y mueve tus boletas (sin copias) a una carpeta con el nombre del informe (boletas rendidas + cartola) y a una carpeta `AAAA-MM` con lo no rendido del mes.

## Cómo se usa (ejecutivo)
1. Crea en tu PC la carpeta **`Documentos\Rinde gastos\`** y deja ahí, sueltos:
   - el estado de cuenta en PDF (el que llega del banco), y
   - las fotos de tus boletas (como lleguen, por ejemplo de WhatsApp).
2. Abre **Rindegastos** en Chrome con tu sesión iniciada, y ten activa la extensión **Claude in Chrome**.
3. En la **app de escritorio de Claude**, abre un chat en **Cowork** y conecta tu carpeta `Rinde gastos` con **"Add folder"**. (En Cowork Claude puede ordenar tu carpeta directamente; en otro tipo de chat te pedirá un doble clic en `ordenar.bat`.)
4. Escríbele a Claude:
   > Usa el agente https://github.com/Ninjasasin/rendicion-gastos-vfch y rinde mi cartola.
5. Claude te muestra lo que va a cargar y te pide el OK. Al final te deja la cartola marcada, el informe en borrador y un resumen de lo que falta.
6. Revisa el informe en Rindegastos y **envíalo tú**.

**Solo ordenar boletas:** "Usa el agente … y ordena mis boletas" → las renombra por monto y las deja en la carpeta de su mes, sin crear informes.

**Fondo por rendir (efectivo):** deja las boletas en la misma carpeta y dile a Claude, por ejemplo:
> Usa el agente https://github.com/Ninjasasin/rendicion-gastos-vfch. Las boletas de la carpeta 2026-10 son personales; con las que quedan crea mi informe de fondos por rendir del viaje a Rusia (fueron 1.500 dólares).

## Qué necesita
- App de escritorio de Claude con acceso a tu carpeta.
- Claude in Chrome, con Rindegastos abierto y sesión iniciada (Claude nunca escribe contraseñas).
- Python 3 con `pdfplumber` y `pymupdf` (Claude los instala si faltan).

## Privacidad
Este repositorio **no contiene datos de nadie**: ni cartolas, ni boletas, ni montos. Tus archivos se quedan en tu PC; Claude trabaja con una copia temporal y te devuelve las carpetas ordenadas.

## Para Claude
Todas las reglas (qué informe, categoría, nota, cruce, gasto personal) están en [`1. Contexto/reglas-de-negocio.md`](1.%20Contexto/reglas-de-negocio.md), y el mapa de las 12 categorías en [`1. Contexto/categorias.md`](1.%20Contexto/categorias.md). Las instrucciones están en [`Rendición de Gastos.md`](Rendición%20de%20Gastos.md) (puntero en `CLAUDE.md`). El trabajo paso a paso está en [`2. Skills/rendir-cartola/SKILL.md`](2.%20Skills/rendir-cartola/SKILL.md).

## Estructura
```
Rendición de Gastos.md   instrucciones principales
CLAUDE.md                puntero
1. Contexto/             reglas-de-negocio.md + parametros.json (todas las decisiones), fuentes y pantallas de Rindegastos
2. Skills/               rendir-cartola (paso a paso) y scripts/ (Python + JavaScript)
3. Memoria/              preferencias, reglas aprendidas, decisiones, estado
4. Proyectos/            vacío: los datos viven en el PC de cada ejecutivo
```
