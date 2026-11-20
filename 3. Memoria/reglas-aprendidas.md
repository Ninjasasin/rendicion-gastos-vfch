# Reglas aprendidas (cada una viene de un error real)

_Formato: la regla en negrita y, después, qué pasó. Se agregan con fecha._

- **No abrir "Crear gasto" (Simple o Múltiples) hasta tener todo listo.** El gasto se crea en borrador apenas se aprieta "Continuar"; si se abandona, queda un gasto vacío de 0,00. (19-nov-2026: así quedó un borrador vacío en la primera prueba; antes había 8 borradores USD vacíos del 13-nov con el mismo origen probable.)
- **La fecha en Rindegastos no se escribe: solo calendario.** Escribirla no hace nada o deja otra fecha (19-nov-2026: quedó 11/10 en vez de 09/10). Usar `scripts/js/fechas_multiples.js`.
- **Rindegastos borra el "&" del proveedor.** "B & A" quedó "B A" (19-nov-2026). Escribir "and".
- **Una línea de la cartola puede llevar dos papeles.** Pro forma 45,00 + voucher de pago 49,50 (otra empresa en la terminal) = cargo de 49,50 en la cartola (19-nov-2026). Se resuelve con una decisión `adjuntar_a`; nunca se crean dos gastos.
- **Monto de la boleta = monto cobrado, con propina.** La boleta decía 28,70 y la tarjeta cobró 31,70 (19-nov-2026).
- **"Cash" en la boleta no siempre es efectivo.** Una boleta decía Cash y el cargo estaba en la tarjeta (19-nov-2026). Si calza con la cartola, se rinde y se avisa.
- **Chrome solo sube archivos traídos con device_stage_files** (carpeta `/mnt/user-data/uploads/…`). La ruta del PC y las copias en otras carpetas del espacio de trabajo se rechazan (19-nov-2026).
- **En la cartola CLP la fecha viene pegada al detalle** ("02/10/267019 JV AERO") y "PAGAR HASTA 10/11/2026 $ 55.044" parece una línea: `leer_cartola.py` lo maneja (19-nov-2026).
- **En PowerShell una lista de un solo par se "aplana"** (`@( @('a','b') )` queda como `'a','b'`): en `ordenar.ps1` cada movimiento se agrega con `$movs += ,@(origen, destino)` (20-nov-2026, revisión del script antes de usarlo).
- **Si la sesión no tiene terminal en el PC, Claude no puede mover ni renombrar archivos** (solo leer y crear nuevos). Por eso existen `ordenar.bat` (lo corre el ejecutivo) y `ordenar_si.bat` (lo corre Claude con doble clic desde el Explorador, si tiene control del computador; el Explorador queda en modo solo clic). En Cowork sí hay terminal (20-nov-2026).
- **Cuando hay otra persona usando la misma sesión de Rindegastos, la pestaña puede cambiar sola.** Si la pantalla no es la esperada, parar y preguntar antes de seguir (19-nov-2026).
