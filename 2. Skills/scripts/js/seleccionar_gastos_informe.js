// Rindegastos > informe > "+ Agregar gasto": marca todos los gastos que muestra el diálogo.
// El diálogo solo muestra gastos de la misma política que todavía no están en un informe.
// ANTES de usarlo, revisar con get_page_text que la lista sea exactamente la de los gastos creados en esta corrida.
const dlg = document.querySelector('mat-dialog-container, [role=dialog]') || document;
const cbs = [...dlg.querySelectorAll('input[type=checkbox]')];
for (const c of cbs) { if (!c.checked) { c.click(); await new Promise(r => setTimeout(r, 150)); } }
JSON.stringify({ en_lista: cbs.length, marcados: cbs.filter(c => c.checked).length });
