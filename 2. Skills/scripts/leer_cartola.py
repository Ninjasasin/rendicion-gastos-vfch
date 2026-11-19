"""Lee un estado de cuenta de la tarjeta corporativa (Santander WorldMember Business) en PDF y lo deja en JSON.

Uso:
    python -X utf8 leer_cartola.py <cartola.pdf> [<carpeta_salida>]

Detecta solo si es la cartola internacional (USD) o nacional (CLP) por su contenido, no por el nombre del archivo.
Escribe <carpeta_salida>/cartola_USD.json o cartola_CLP.json (por defecto, junto al PDF) e imprime un resumen.

Cada línea queda con:
  id, pagina, fecha (AAAA-MM-DD), detalle (texto del comercio tal como viene), pais, monto_origen, monto,
  tipo  = 'gasto'        -> se rinde
          'pago'         -> "MONTO CANCELADO" (pago de la cartola anterior): no se rinde
          'cargo_banco'  -> comisiones, impuestos o cargos del banco (sección 3): no se rinde
  bbox  = posición en la página (para marcar el PDF)

Control: la suma de las líneas 'gasto' tiene que ser igual al total de operaciones de la cartola. Si no cuadra,
el script lo avisa con 'ERROR' y sale con código 1. No se sigue con la rendición si no cuadra.
"""
import json, os, re, sys
import pdfplumber
import rutas as R

FECHA = r'(\d{2}/\d{2}/\d{2})(?!\d{2}\b)'  # dd/mm/aa; no toma dd/mm/aaaa, pero sí '02/10/267019 JV AERO' (fecha pegada al detalle)
MONTO_USD = r'(-?[\d.]+,\d{2})'


def num(s):
    """'7.000,00' -> 7000.0 ; '$18.868' -> 18868.0"""
    s = s.replace('US$', '').replace('$', '').strip()
    return float(s.replace('.', '').replace(',', '.'))


def fecha_iso(ddmmaa):
    d, m, a = ddmmaa.split('/')
    a = int(a)
    a = a + 2000 if a < 100 else a
    return '%04d-%s-%s' % (a, m, d)


NO_SE_RINDE = R.parametros()['cartola_no_se_rinde_si_contiene']   # ver reglas-de-negocio.md §2


def lineas_pdf(path):
    """Agrupa las palabras de cada página en líneas (por posición vertical). Devuelve dicts con texto y bbox."""
    out = []
    with pdfplumber.open(path) as pdf:
        for pi, page in enumerate(pdf.pages):
            grupos = {}
            for w in page.extract_words():
                grupos.setdefault(round(w['top'] / 3), []).append(w)
            for k in sorted(grupos):
                ws = sorted(grupos[k], key=lambda w: w['x0'])
                out.append({'pagina': pi, 'texto': ' '.join(w['text'] for w in ws),
                            'bbox': [min(w['x0'] for w in ws), min(w['top'] for w in ws),
                                     max(w['x1'] for w in ws), max(w['bottom'] for w in ws)],
                            'ancho_pagina': float(page.width)})
    return out


def buscar(patron, texto, grupo=1):
    m = re.search(patron, texto)
    return m.group(grupo) if m else None


def leer(path):
    lns = lineas_pdf(path)
    todo = '\n'.join(l['texto'] for l in lns)
    if 'ESTADO DE CUENTA INTERNACIONAL' in todo:
        tipo = 'USD'
    elif 'ESTADO DE CUENTA EN MONEDA NACIONAL' in todo:
        tipo = 'CLP'
    else:
        raise SystemExit('ERROR: no reconozco el PDF como estado de cuenta Santander (ni internacional ni nacional): %s' % path)

    cab = {
        'tipo': tipo,
        'archivo': os.path.basename(path),
        'tarjeta_ult4': buscar(r'XXXX XXXX XXXX (\d{4})', todo),
        'fecha_estado': fecha_iso(buscar(r'FECHA ESTADO DE CUENTA (\d{2}/\d{2}/\d{4})', todo)),
        'pagar_hasta': None,
    }
    d = buscar(r'PER[IÍ]ODO FACTURADO (?:DESDE )?(\d{2}/\d{2}/\d{4})', todo)
    h = buscar(r'PER[IÍ]ODO FACTURADO (?:DESDE )?\d{2}/\d{2}/\d{4}\s+(\d{2}/\d{2}/\d{4})', todo) or \
        buscar(r'PER[IÍ]ODO FACTURADO HASTA (\d{2}/\d{2}/\d{4})', todo)
    cab['periodo_desde'] = fecha_iso(d) if d else None
    cab['periodo_hasta'] = fecha_iso(h) if h else cab['fecha_estado']  # en la USD el "hasta" es la fecha del estado
    # titular de la tarjeta: la línea en mayúsculas que va antes del correo, en la primera página
    for i, l in enumerate(lns):
        if '@' in l['texto'] and i > 0 and l['pagina'] == 0:
            cab['titular'] = lns[i - 1]['texto'].strip()
            break

    lineas, seccion = [], 1
    for l in lns:
        t = l['texto']
        if re.search(r'^\s*1\.\s*TOTAL OPERACIONES', t):
            seccion = 1
        elif re.search(r'^\s*2\.\s*PRODUCTOS', t):
            seccion = 2
        elif re.search(r'^\s*3\.\s*CARGOS', t):
            seccion = 3
        elif re.search(r'^\s*4\.\s*INFORMACION', t):
            seccion = 4

        if tipo == 'USD':
            m = re.match(r'^' + FECHA + r'\s+(.+?)\s+' + MONTO_USD + r'\s+' + MONTO_USD + r'$', t)
            if not m:
                continue
            f, det, mo, mu = m.groups()
            pais = buscar(r'\s([A-Z]{2})$', det)
            detalle = det[:-3].strip() if pais else det
            monto_origen, monto = num(mo), num(mu)
        else:
            m = re.match(r'^(?:(.+?)\s+)?' + FECHA + r'\s*(.+?)\s+\$\s?([\d.]+)$', t)  # en la CLP la fecha viene pegada al detalle
            if not m:
                continue
            lugar, f, detalle, mc = m.groups()
            pais = 'CL'
            monto_origen = monto = num(mc)
            detalle = detalle.strip()
            if lugar:
                detalle = '%s (%s)' % (detalle, lugar.strip())  # el lugar (p. ej. SANTIAGO) va a la izquierda de la fecha
        if 'MONTO CANCELADO' in detalle.upper() or monto < 0:
            tp = 'pago'
        elif seccion == 3 or any(k.upper() in detalle.upper() for k in NO_SE_RINDE):
            tp = 'cargo_banco'
        else:
            tp = 'gasto'
        lineas.append({'pagina': l['pagina'], 'fecha': fecha_iso(f), 'detalle': detalle, 'pais': pais,
                       'monto_origen': monto_origen, 'monto': monto, 'tipo': tp,
                       'bbox': l['bbox'], 'ancho_pagina': l['ancho_pagina']})
    for i, x in enumerate(lineas, 1):
        x['id'] = '%s-%03d' % (tipo, i)

    gastos = round(sum(x['monto'] for x in lineas if x['tipo'] == 'gasto'), 2)
    if tipo == 'USD':
        total = buscar(r'TOTAL DE COMPRAS Y CARGOS\s+US\$\s*([\d.]+,\d{2})', todo)
    else:
        total = buscar(r'1\.\s*TOTAL OPERACIONES\s+\$\s*([\d.]+)', todo)
    cab['total_operaciones'] = num(total) if total else None
    cab['total_gastos_leidos'] = gastos
    cab['cuadra'] = cab['total_operaciones'] is not None and abs(gastos - cab['total_operaciones']) < 0.005
    a, m_, _ = cab['fecha_estado'].split('-')
    cab['periodo'] = '%s-%s' % (a, m_)
    cab['nombre_informe'] = R.nombre_informe(tipo, int(a), int(m_))
    cab['lineas'] = lineas
    return cab


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    pdf = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(pdf))
    c = leer(pdf)
    out = os.path.join(dest, R.CARTOLA_JSON.format(tipo=c['tipo']))
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(c, fh, ensure_ascii=False, indent=1)
    n = {t: sum(1 for x in c['lineas'] if x['tipo'] == t) for t in ('gasto', 'pago', 'cargo_banco')}
    print('Cartola %s  tarjeta ...%s  titular: %s' % (c['tipo'], c['tarjeta_ult4'], c.get('titular')))
    print('Estado de cuenta %s  (período %s a %s)  -> informe "%s"' % (
        c['fecha_estado'], c['periodo_desde'], c['periodo_hasta'], c['nombre_informe']))
    print('Líneas: %d gastos, %d pagos, %d cargos del banco' % (n['gasto'], n['pago'], n['cargo_banco']))
    print('Total gastos leídos %.2f  vs total operaciones cartola %s  -> %s' % (
        c['total_gastos_leidos'], c['total_operaciones'], 'CUADRA' if c['cuadra'] else 'ERROR: NO CUADRA'))
    print('Escrito:', out)
    if not c['cuadra']:
        sys.exit(1)


if __name__ == '__main__':
    main()
