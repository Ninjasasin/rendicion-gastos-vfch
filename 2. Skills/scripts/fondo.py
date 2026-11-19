"""Prepara un informe de FONDO POR RENDIR (gastos pagados con efectivo entregado por la empresa). No hay cartola:
el ejecutivo dice qué boletas van al informe y cuáles son personales.

Uso:
    python -X utf8 fondo.py <carpeta_trabajo>

Lee de <carpeta_trabajo>:
  boletas.json   lo que Claude leyó de cada foto (mismo formato que en rendir-cartola)
  fondo.json     lo que indicó el ejecutivo (lo escribe Claude a partir de su instrucción):
    {
      "motivo": "Viaje Rusia",            -> va en el nombre del informe
      "moneda": "USD",                    -> moneda del fondo (USD o CLP): define la política REEM
      "mes": "2026-11",                   -> mes del nombre del informe (AAAA-MM)
      "instruccion": "texto tal como lo dijo el ejecutivo",
      "incluir":    ["<archivo>", ...],   -> boletas que van al informe
      "personales": ["<archivo>", ...],   -> boletas que el ejecutivo dijo que son personales
      "tipo_cambio": {"EUR": 1.08},       -> opcional: 1 unidad de la moneda de la boleta = X en la moneda del fondo.
                                             Solo si el ejecutivo lo entregó. NUNCA inventarlo.
      "decisiones": []                    -> notas de lo que se aclaró con el ejecutivo
    }

Escribe <carpeta_trabajo>/cruce_fondo_<AAAA-MM>.json con el mismo formato que el cruce de cartola (una "línea" por
boleta incluida), para que grilla.py y preparar_archivo.py funcionen igual (con --cruce).

Monto de cada gasto:
  - boleta en la moneda del fondo          -> su monto
  - otra moneda y hay tipo_cambio          -> monto x tipo de cambio (2 decimales en USD, entero en CLP)
  - otra moneda y NO hay tipo_cambio       -> se deja en la moneda de la boleta ("moneda_gasto"), para probar si
                                              Rindegastos la acepta y convierte. Si no la acepta, hay que pedir el
                                              tipo de cambio al ejecutivo y volver a correr.
Avisa (y sale con código 2) si una boleta de boletas.json no quedó ni en "incluir" ni en "personales"
(salvo que se quiera dejar fuera a propósito: ponla en "fuera").
"""
import json, os, re, sys
import rutas as R

P = R.parametros()


def slug(s):
    return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-').lower()


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    carpeta = sys.argv[1]
    bol = {b['archivo']: b for b in json.load(open(os.path.join(carpeta, R.BOLETAS_JSON), encoding='utf-8'))}
    f = json.load(open(os.path.join(carpeta, 'fondo.json'), encoding='utf-8'))
    moneda = f['moneda'].upper()
    if moneda not in P['fondo_politica_por_moneda']:
        raise SystemExit('ERROR: moneda del fondo "%s" no tiene política (ver fondo_politica_por_moneda)' % moneda)
    anio, mes = [int(x) for x in f['mes'].split('-')]
    nombre = P['fondo_nombre_informe'].format(motivo=f['motivo'].strip(), mes=R.MESES[mes - 1], anio=anio)
    tc = {k.upper(): float(v) for k, v in (f.get('tipo_cambio') or {}).items()}

    incluir, personales, fuera = f.get('incluir', []), f.get('personales', []), f.get('fuera', [])
    for a in incluir + personales + fuera:
        if a not in bol:
            raise SystemExit('ERROR: "%s" está en fondo.json pero no en boletas.json' % a)
    dobles = set(incluir) & set(personales)
    if dobles:
        raise SystemExit('ERROR: boletas a la vez en incluir y personales: %s' % ', '.join(dobles))
    sin_asignar = [a for a in bol if a not in incluir + personales + fuera]

    defecto_cat = P['categoria_por_tipo_de_rendicion']['fondo_por_rendir']
    lineas, avisos_gen = [], []
    for i, a in enumerate(sorted(incluir, key=lambda x: (bol[x]['fecha'], x)), 1):
        b = bol[a]
        mon_b = b['moneda'].upper()
        if mon_b == moneda:
            monto, moneda_gasto = float(b['monto']), moneda
        elif mon_b in tc:
            monto, moneda_gasto = float(b['monto']) * tc[mon_b], moneda
        else:
            monto, moneda_gasto = float(b['monto']), mon_b
        monto = round(monto, 0 if moneda_gasto == 'CLP' else 2)
        avisos = []
        if moneda_gasto != moneda:
            avisos.append('va en %s (sin tipo de cambio): probar si Rindegastos acepta esa moneda; si no, pedir tipo de cambio' % moneda_gasto)
        elif mon_b != moneda:
            avisos.append('convertido %s %.2f x %s = %s %.2f' % (mon_b, float(b['monto']), tc[mon_b], moneda, monto))
        if b.get('documento') == 'proforma':
            avisos.append('%s es pro forma (no es boleta tributaria)' % a)
        if b.get('observacion'):
            avisos.append('%s: %s' % (a, b['observacion']))
        cat = b.get('categoria') or defecto_cat
        if cat not in P['categorias_validas']:
            avisos.append('categoría "%s" no existe; queda %s' % (cat, defecto_cat)); cat = defecto_cat
        lineas.append({'id': 'FONDO-%03d' % i, 'cartola': 'FONDO', 'fecha': b['fecha'], 'detalle': b.get('comercio', ''),
                       'monto': monto, 'moneda_gasto': moneda_gasto, 'monto_origen': float(b['monto']),
                       'moneda_origen': mon_b, 'tipo': 'gasto', 'boletas': [a],
                       'proveedor': (b.get('proveedor') or b.get('comercio') or 'Sin nombre').replace('&', 'and'),
                       'nota': b.get('nota') or P['nota_por_defecto'], 'categoria': cat, 'avisos': avisos})

    boletas_out = []
    for a, b in bol.items():
        e = 'rendida' if a in incluir else 'personal' if a in personales else 'fuera'
        lid = next((l['id'] for l in lineas if a in l['boletas']), None)
        boletas_out.append(dict(b, estado=e, linea=lid, motivo='indicado por el ejecutivo'))

    out = {
        'tipo_rendicion': 'fondo_por_rendir',
        'periodo': f['mes'],
        'politica': P['fondo_politica_por_moneda'][moneda],
        'moneda': moneda,
        'instruccion': f.get('instruccion', ''),
        'cartolas': [{'tipo': 'FONDO', 'archivo': None, 'nombre_informe': nombre, 'tarjeta_ult4': None,
                      'titular': None, 'fecha_estado': None, 'periodo_desde': None, 'periodo_hasta': None,
                      'total_operaciones': None}],
        'lineas': lineas, 'boletas': boletas_out, 'dudas': [],
        'decisiones': f.get('decisiones', []), 'rindegastos': {},
        'campos_reembolso': {'tipo_documento': P['fondo_tipo_documento'],
                             'rut_proveedor_extranjero': P['fondo_rut_proveedor_extranjero']},
    }
    path = os.path.join(carpeta, 'cruce_fondo_%s.json' % f['mes'])
    json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print('Informe: "%s"  política %s' % (nombre, out['politica']))
    print('%d gastos al informe | %d personales | %d fuera' % (len(incluir), len(personales), len(fuera)))
    tot = {}
    for l in lineas:
        tot[l['moneda_gasto']] = tot.get(l['moneda_gasto'], 0) + l['monto']
        print('  %s %s %-28s %10.2f %s  %-12s %s' % (l['id'], l['fecha'], l['proveedor'], l['monto'], l['moneda_gasto'],
                                                  l['nota'], l['boletas'][0]))
    print('Total: ' + ' + '.join('%s %.2f' % (k, v) for k, v in tot.items()))
    for l in lineas:
        for a in l['avisos']:
            print('  aviso %s: %s' % (l['id'], a))
    if personales:
        print('Personales: ' + ', '.join(personales))
    print('Escrito:', path)
    if sin_asignar:
        print('SIN ASIGNAR (%d): %s  -> pregúntale al ejecutivo si van al informe, son personales o quedan fuera.'
              % (len(sin_asignar), ', '.join(sin_asignar)))
        sys.exit(2)


if __name__ == '__main__':
    main()
