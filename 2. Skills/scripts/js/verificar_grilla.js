// Rindegastos > Crear gastos múltiples: lee lo que quedó en cada fila antes de "Guardar cambios".
// Pegar en javascript_tool. Comparar fila por fila con el cruce (proveedor, total, fecha, categoría, nota, archivos).
const g = s => [...document.querySelectorAll(s)].map(e => e.value);
const prov = g('input[placeholder="Indica el proveedor"]'), tot = g('input[placeholder="Total"]'),
      fec = g('input[placeholder="Fecha"]'), nota = g('input[placeholder="Escribe una nota o comentario"]');
const cat = [...document.querySelectorAll('button[aria-label^="Remove "]')]
  .map(b => b.getAttribute('aria-label').replace('Remove ', ''))
  .filter(t => !t.startsWith('USD') && !t.startsWith('CLP') && t !== 'Comprobante');
prov.map((p, i) => [i + 1, p, tot[i], fec[i], cat[i] || 'SIN CATEGORÍA', nota[i]].join(' | ')).join('\n');
