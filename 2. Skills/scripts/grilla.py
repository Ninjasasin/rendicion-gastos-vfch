"""Prepara lo necesario para llenar la grilla de Rindegastos > Crear gasto > Múltiples con los gastos de una cartola.

Uso:
    python -X utf8 grilla.py <carpeta_trabajo> <USD|CLP|FONDO> [<n_ref_primer_proveedor> <tab_id>] [--cruce <archivo>] [--offsets <lista>]

Sin <n_ref_primer_proveedor>: imprime la tabla de filas (en el orden en que van en la grilla), la lista de FECHAS
para js/fechas_multiples.js y qué boleta(s) va(n) en cada fila.

Con <n_ref_primer_proveedor> (número del ref del campo "Indica el proveedor" de la fila 1, p. ej. 366 si read_page
muestra ref_366) y <tab_id>: además escribe <carpeta_trabajo>/grilla_<tipo>.json con las acciones para browser_batch.

--cruce: archivo de cruce a usar (por defecto, el cruce_AAAA-MM.json más reciente de cartola). Para un fondo por
         rendir: --cruce cruce_fondo_AAAA-MM.json (lo deja fondo.py).
--offsets: posición de cada campo dentro de la fila, relativa al ref del proveedor, y el paso entre filas.
         Por defecto (grilla de políticas TC, verificada el 19-nov-2026): prov=0,total=1,cat=9,nota=10,paso=12
         Las políticas REEM (fondo por rendir) tienen más columnas (RUT, tipo de documento, número): leer los refs
         de la fila 1 y 2 con read_page y pasar los offsets, p. ej.
         --offsets prov=0,total=1,moneda=2,tipodoc=6,rut=8,cat=11,nota=12,paso=14
         Campos posibles: prov, total, moneda, tipodoc, rut, cat, nota, paso. Si un campo no está, no se llena.
         VERIFICAR SIEMPRE el patrón antes de usar las acciones.

Reglas de los datos ('1. Contexto/reglas-de-negocio.md' §5; valores en parametros.json):
  - Proveedor sin "&" (Rindegastos lo borra): se reemplaza por "and".
  - Total = monto de la cartola en la moneda de la cartola (USD en la internacional, CLP en la nacional),
    con coma decimal. NO el monto de la boleta en moneda local.
  - Categoría: categoria_por_tipo_de_rendicion['tc_corporativa'] (hoy Gastos De Viajes).
"""
import json, os, sys
import rutas as R

P = R.parametros()
CATEGORIA_TC = P['categoria_por_tipo_de_rendicion']['tc_corporativa']
OFFSETS_TC = {'prov': 0, 'total': 1, 'cat': 9, 'nota': 10, 'paso': 12}


def cargar_cruce(carpeta, nombre=None):
    if not nombre:
        nombre = sorted(f for f in os.listdir(carpeta) if f.startswith('cruce_2') and f.endswith('.json'))[-1]
    return json.load(open(os.path.join(carpeta, nombre), encoding='utf-8'))


def filas(carpeta, tipo, cruce):
    bol = {b['archivo']: b for b in cruce['boletas']}
    out = []
    for l in sorted((x for x in cruce['lineas'] if x['cartola'] == tipo and x['boletas']), key=lambda x: x['id']):
        a, m, d = l['fecha'].split('-')
        mon = l.get('moneda_gasto') or tipo
        total = '%d' % round(l['monto']) if mon == 'CLP' else ('%.2f' % l['monto']).replace('.', ',')
        out.append({'linea': l['id'], 'proveedor': l['proveedor'].replace('&', 'and').strip(), 'moneda': mon,
                    'total': total, 'fecha': '%s/%s/%s' % (d, m, a), 'categoria': l.get('categoria') or CATEGORIA_TC,
                    'nota': l['nota'], 'boletas': l['boletas'],
                    'archivos': [bol[x].get('archivado_como', x) for x in l['boletas']]})
    return out


def acciones(fs, base, tab, off, moneda_politica, extra):
    acc = []
    for i, f in enumerate(fs):
        b = base + off['paso'] * i
        s = lambda a, **k: acc.append({'name': 'computer', 'input': dict(k, action=a, tabId=tab)})
        def combo(campo, valor, nombre):
            s('left_click', ref='ref_%d' % (b + off[campo]), action_summary='Opens %s row %d' % (nombre, i + 1))
            s('type', text=valor, action_summary='Filters %s %s' % (nombre, valor))
            s('key', text='Enter', action_summary='Selects %s %s' % (nombre, valor))
        def texto(campo, valor, nombre, reemplazar=False):
            s('triple_click' if reemplazar else 'left_click', ref='ref_%d' % (b + off[campo]),
              action_summary='Focuses %s row %d' % (nombre, i + 1))
            s('type', text=valor, action_summary='Types %s %s' % (nombre, valor))
        texto('prov', f['proveedor'], 'proveedor')
        texto('total', f['total'], 'total', reemplazar=True)
        if 'moneda' in off and f['moneda'] != moneda_politica:
            combo('moneda', f['moneda'], 'moneda')
        if 'tipodoc' in off and extra.get('tipo_documento'):
            combo('tipodoc', extra['tipo_documento'], 'tipo de documento')
        if 'rut' in off and extra.get('rut_proveedor_extranjero'):
            texto('rut', extra['rut_proveedor_extranjero'], 'RUT proveedor', reemplazar=True)
        if 'cat' in off:
            combo('cat', f['categoria'], 'categoría')
        if 'nota' in off:
            texto('nota', f['nota'], 'nota')
    return acc


def main():
    args = sys.argv[1:]
    opts = {}
    for k in ('--cruce', '--offsets'):
        if k in args:
            i = args.index(k); opts[k] = args[i + 1]; del args[i:i + 2]
    if len(args) < 2:
        print(__doc__); sys.exit(1)
    carpeta, tipo = args[0], args[1].upper()
    cruce = cargar_cruce(carpeta, opts.get('--cruce'))
    off = dict(OFFSETS_TC)
    if '--offsets' in opts:
        off = {k: int(v) for k, v in (x.split('=') for x in opts['--offsets'].split(','))}
        if 'paso' not in off or 'prov' not in off or 'total' not in off:
            raise SystemExit('ERROR: --offsets necesita al menos prov, total y paso')
    if P['modo_creacion_gastos'] != 'multiples':
        raise SystemExit('ERROR: modo_creacion_gastos = %s; este script solo sirve para "multiples".' % P['modo_creacion_gastos'])
    if P['crear_lineas_sin_boleta']:
        raise SystemExit('ERROR: crear_lineas_sin_boleta = true no está programado. Ver reglas-de-negocio.md §2.')
    fs = filas(carpeta, tipo, cruce)
    if not fs:
        print('No hay líneas con boleta en la cartola %s: no se crean gastos.' % tipo); return
    print('%d filas para la grilla (cartola %s):' % (len(fs), tipo))
    for i, f in enumerate(fs, 1):
        print('%2d | %-28s | %10s %s | %s | %-16s | %-12s | %s' % (
            i, f['proveedor'], f['total'], f['moneda'], f['fecha'], f['categoria'], f['nota'], ' + '.join(f['boletas'])))
    print('\nFECHAS para js/fechas_multiples.js:')
    print(json.dumps([f['fecha'] for f in fs]))
    if len(args) >= 4:
        base, tab = int(args[2]), int(args[3])
        moneda_pol = cruce.get('moneda') or tipo
        acc = acciones(fs, base, tab, off, moneda_pol, cruce.get('campos_reembolso', {}))
        out = os.path.join(carpeta, 'grilla_%s.json' % tipo)
        json.dump({'filas': fs, 'offsets': off, 'acciones': acc}, open(out, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('\nAcciones para browser_batch escritas en', out, '(%d acciones; offsets %s)' % (len(acc), off))


if __name__ == '__main__':
    main()
