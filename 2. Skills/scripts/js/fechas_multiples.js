// Rindegastos > Crear gastos múltiples: pone la fecha de cada fila.
// La fecha NO se puede escribir en el campo (solo calendario), por eso se hace así.
// Uso: reemplazar FECHAS por las fechas de cada fila, en el MISMO orden de la grilla (dd/mm/aaaa),
// y pegar todo el archivo en javascript_tool sobre la pestaña de "Múltiples Gastos".
// Devuelve las fechas que quedaron en cada fila: hay que compararlas con FECHAS.
const FECHAS = ['09/10/2026', '09/10/2026'];   // <- reemplazar

const MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const sleep = ms => new Promise(r => setTimeout(r, ms));
document.querySelector('button[aria-label="Close calendar"]')?.click();
await sleep(300);
const res = [];
for (let i = 0; i < FECHAS.length; i++) {
  const [d, m, a] = FECHAS[i].split('/').map(Number);
  const label = `${d} de ${MESES[m - 1]} de ${a}`;
  const abrir = [...document.querySelectorAll('button[aria-label="Open calendar"]')];
  abrir[i].click(); await sleep(400);
  let dia = document.querySelector(`button[aria-label="${label}"]`);
  for (let k = 0; !dia && k < 12; k++) {            // retrocede mes a mes hasta encontrar el día (máx. 12 meses)
    document.querySelector('button[aria-label="Previous month"]')?.click(); await sleep(350);
    dia = document.querySelector(`button[aria-label="${label}"]`);
  }
  if (dia) { dia.click(); await sleep(400); res.push('fila ' + (i + 1) + ': ok'); }
  else { document.querySelector('button[aria-label="Close calendar"]')?.click(); res.push('fila ' + (i + 1) + ': NO ENCONTRÉ ' + label); }
}
const quedaron = [...document.querySelectorAll('input[placeholder="Fecha"]')].map(e => e.value);
JSON.stringify({ res, quedaron, cuadra: FECHAS.every((f, i) => quedaron[i] === f) });
