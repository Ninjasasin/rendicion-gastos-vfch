# Rindegastos (VFCH)

Plataforma: **https://app.rindegastos.com** — perfil **Rendidor**, empresa **Viñedos Familia Chadwick SpA**, plan Business.
El agente trabaja en el Chrome del ejecutivo (Claude in Chrome), con su sesión ya iniciada. Si no hay sesión, se le pide que inicie sesión él: el agente nunca escribe contraseñas.

> Las **reglas** (qué política, qué nombre de informe, qué categoría y nota, múltiple o individual) están en `reglas-de-negocio.md`. Este archivo describe solo **cómo es la plataforma**.

## Políticas que existen
| Política | Para qué |
|---|---|
| `USD - TC - VFCH - ECA` | Tarjeta corporativa, cartola internacional (USD) |
| `CLP - TC - VFCH - ECA` | Tarjeta corporativa, cartola nacional (CLP) |
| `CLP - REEM - VFCH - ECA` | Reembolsos en pesos (gastos pagados por el ejecutivo) |
| `USD - REEM - VFCH - ECA` | Reembolsos en dólares |

La política de un gasto **no se puede cambiar** después de creado.

Los informes anteriores en la plataforma se llaman "TC Internacional - Abril 2026", "TC Nacional - Abril 2026", etc.

## Categorías que existen en la plataforma
Desarrollo Y Promocion, Gastos De Oficina, Gastos De Viajes, Gastos Equipos Computacion, Gastos Marketing (Corporativo), Gastos Marketing A&P, Gastos Visitas, Gtos Representacion, Petroleo/Bencina, Servicios Y Equipos Comunicación Ti, Suministros, Suscripciones Y Membresías.

**Cuenta contable**: la pone Rindegastos según la categoría (Gastos De Viajes = 50370). No se toca.
**Tipo de documento** en las políticas TC: `Comprobante` (queda como "Comprobante - CTE"). Viene puesto por defecto en la grilla de Múltiples.
**Nota**: campo de texto libre en la plataforma; los valores que usamos están en `reglas-de-negocio.md` §5.

## Pantallas (como están al 19-nov-2026)

### Menú lateral (Rendidor)
Gastos · Informes · Agentes (solo plan Corporate, no disponible) · Fondos · Viáticos · Galería.

### Informes > "+ Crear informe"
Diálogo "Nuevo informe": **Política** (lista) y **Título**. "Crear informe" lo crea **en borrador** y abre la edición:
- **Archivos del informe**: aquí va la cartola original (máx. 5 archivos). El campo es un `file-input` oculto: se sube con `file_upload` sobre su ref.
- Empresa y Tipo De Rendicion se llenan solos según la política (p. ej. "USD - Tarjeta Corporativa").
- "Guardar cambios" guarda. El informe queda con los botones **Editar** y **Enviar informe** (este último **no se toca**).

### Gastos > "+ Crear gasto" > pestaña **Múltiples** (la que se usa; ver `reglas-de-negocio.md` §6)
- Diálogo: **Política** y **Número de gastos** (ambas listas; se escribe y Enter). "Continuar" abre la grilla "Crear gastos múltiples".
- **Ojo:** con "Simple" o "Múltiples", el gasto se crea en borrador apenas se aprieta "Continuar". Si se abandona la pantalla, quedan gastos vacíos (0,00). No abrir la grilla hasta tener todo listo.
- Grilla, una fila por gasto: Proveedor · Total · Moneda (viene la de la política) · Fecha · Tipo De Documento (viene "Comprobante") · Centro De Costo Distinto Al Propio (se deja vacío) · Categoría · Nota · Archivo ("Cargar archivos").
- **Fecha: no se puede escribir**, solo con el calendario. Se usa `scripts/js/fechas_multiples.js`.
- **Archivo**: cada fila tiene un `file-input` oculto; se sube con `file_upload` sobre su ref (se pueden subir 2 imágenes juntas a una fila). Al hacer clic en una fila, el panel derecho muestra sus archivos ("1/2" si son dos).
- "Guardar cambios" crea todos los gastos y vuelve a la lista de Gastos.
- Rindegastos **borra el "&"** del proveedor ("B & A" → "B A"): se escribe "and".

### Políticas REEM (fondo por rendir / reembolso)
Los gastos REEM tienen campos que no están en TC (visto en un gasto aprobado de "USD - REEM - VFCH - ECA"): **RUT Proveedor** (en comercios extranjeros se usa `11111111-1`), **Tipo De Documento** (`Bol y otros Gastos VFCH - 144`), **Número De Documento** y Centro de costo. El informe queda con "Tipo De Rendicion: Reembolso". **Todavía no se ha abierto la grilla de Múltiples con política REEM**: en la primera corrida hay que mirar sus columnas y si la columna Moneda acepta otra moneda (EUR, etc.), y anotarlo aquí.

### Informe > "+ Agregar gasto" / "+ Agregar más gastos"
Diálogo con los gastos de **la misma política que no están en un informe**, cada uno con un checkbox. "Agregar gastos" los mete al informe. Después el informe muestra "Gastos del informe (N)" y el total.

### Gasto (detalle)
Muestra fecha, proveedor, total, nota, categoría, cuenta contable, tipo de documento y las imágenes. "Editar gasto" abre el formulario (Proveedor, Fecha, Total + moneda, Categoría, Tipo De Documento, Centro de costo, Nota, archivos).

### Galería
Bandeja de imágenes subidas que aún no se usan en un gasto. El agente no la usa.
