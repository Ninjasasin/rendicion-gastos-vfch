"""Cruza las boletas con las líneas de la(s) cartola(s) y deja el resultado en cruce_AAAA-MM.json.

Uso:
    python -X utf8 cruzar.py <carpeta_trabajo>

Lee de <carpeta_trabajo>:
  cartola_USD.json / cartola_CLP.json   (salida de leer_cartola.py; puede haber una o las dos)
  boletas.json                          (lo que Claude leyó de cada foto; formato en la skill rendir-cartola)
  cruce_AAAA-MM.json                    (si ya existe: se respetan sus "decisiones" para que la corrida se repita igual)

Las reglas de negocio están en '1. Contexto/reglas-de-negocio.md' (§3 y §4); los valores, en parametros.json.

Reglas del cruce (en este orden):
  1. Una boleta solo puede ir con líneas de su misma moneda de origen y de tipo 'gasto'.
  2. Si la boleta muestra los últimos 4 dígitos de OTRA tarjeta, es personal (no se cruza).
  3. Candidatas: líneas con el MISMO monto en moneda de origen y fecha a ± cruce_tolerancia_dias de la boleta.
  4. Se asignan primero los pares únicos (la boleta tiene una sola candidata y la línea una sola boleta).
  5. Si hay empate: gana la boleta que muestra los 4 últimos dígitos de la tarjeta de la cartola; después, la
     pagada con tarjeta sobre la de efectivo/desconocido; después, la de menor diferencia de días. Si sigue el
     empate, queda como 'duda' para que decida el ejecutivo.
  6. Boletas sin línea:
       - pagadas con un medio de medios_de_pago_personales (efectivo, otra tarjeta) -> 'personal'
       - con los 4 dígitos de la tarjeta corporativa -> 'sin_cartola' marcada como corporativa (sale en la
         próxima cartola; NUNCA personal)
       - el resto                                -> 'sin_cartola' (pendiente: puede salir en la próxima cartola)
  7. Las "decisiones" del archivo de cruce mandan sobre todo lo anterior:
       {"boleta": "<archivo>", "accion": "adjuntar_a", "linea": "USD-045", "motivo": "..."}
       {"boleta": "<archivo>", "accion": "personal",   "motivo": "..."}
       {"boleta": "<archivo>", "accion": "pendiente",  "motivo": "..."}

Imprime un resumen y la lista de dudas. Sale con código 2 si quedan dudas sin decidir.
"""
import json, os, sys
from datetime import date
import rutas as R

P = R.parametros()
TOL_DIAS = P['cruce_tolerancia_dias']
PERSONALES = P['medios_de_pago_personales']
NOTAS = P['notas_validas']
CAT_DEFECTO = P['categoria_por_tipo_de_rendicion']['tc_corporativa']
CAT_VALIDAS = P['categorias_validas']
CAT_DEFINIDAS = P['categorias_definidas']


def d(s):
    a, m, dd = s.split('-')
    return date(int(a), int(m), int(dd))


def titulo(s):
    return ' '.join(w.capitalize() if w.isupper() else w for w in s.split())


def cargar(carpeta):
    cartolas = []
    for tipo in ('USD', 'CLP'):
        p = os.path.join(carpeta, R.CARTOLA_JSON.format(tipo=tipo))
        if os.path.exists(p):
            cartolas.append(json.load(open(p, encoding='utf-8')))
    if not cartolas:
        raise SystemExit('ERROR: no hay cartola_USD.json ni cartola_CLP.json en %s (corre antes leer_cartola.py)' % carpeta)
    pb = os.path.join(carpeta, R.BOLETAS_JSON)
    boletas = json.load(open(pb, encoding='utf-8')) if os.path.exists(pb) else []
    periodo = max(c['periodo'] for c in cartolas)
    pc = os.path.join(carpeta, R.CRUCE_JSON.format(periodo=periodo))
    previo = json.load(open(pc, encoding='utf-8')) if os.path.exists(pc) else {}
    return cartolas, boletas, periodo, pc, previo.get('decisiones', [])


def moneda_origen(cartola, linea):
    """En la USD la moneda de origen no viene en la cartola: la tomamos de la boleta. En la CLP es CLP."""
    return 'CLP' if cartola['tipo'] == 'CLP' else None


def cruzar(cartolas, boletas, decisiones):
    lineas = []
    for c in cartolas:
        for l in c['lineas']:
            if l['tipo'] == 'gasto':
                l = dict(l, tarjeta_ult4=c['tarjeta_ult4'], cartola=c['tipo'], boletas=[])
                lineas.append(l)
    por_id = {l['id']: l for l in lineas}
    tarjetas = {c['tarjeta_ult4'] for c in cartolas}
    estado = {}                      # archivo -> (estado, linea_id o None, motivo)
    dec = {x['boleta']: x for x in decisiones}

    # 7. decisiones primero
    for b in boletas:
        x = dec.get(b['archivo'])
        if not x:
            continue
        if x['accion'] == 'adjuntar_a':
            if x['linea'] not in por_id:
                raise SystemExit('ERROR: la decisión para %s apunta a %s, que no existe' % (b['archivo'], x['linea']))
            estado[b['archivo']] = ('rendida', x['linea'], 'decisión: ' + x.get('motivo', ''))
        else:
            estado[b['archivo']] = (x['accion'] if x['accion'] != 'pendiente' else 'sin_cartola', None,
                                    'decisión: ' + x.get('motivo', ''))

    # 2. otra tarjeta
    for b in boletas:
        if b['archivo'] in estado:
            continue
        u4 = (b.get('tarjeta_ult4') or '').strip()
        if u4 and u4 not in tarjetas:
            estado[b['archivo']] = ('personal', None, 'pagada con otra tarjeta (...%s)' % u4)

    # 3. candidatas
    # Una línea puede llevar varias boletas (p. ej. pro forma + voucher del mismo gasto): las decisiones
    # 'adjuntar_a' NO bloquean la línea para el cruce automático.
    usadas = set()
    cand = {}
    for b in boletas:
        if b['archivo'] in estado:
            continue
        cs = []
        for l in lineas:
            if l['id'] in usadas:
                continue
            if l['cartola'] == 'CLP' and b['moneda'] != 'CLP':
                continue
            if l['cartola'] == 'USD' and b['moneda'] == 'CLP':
                continue
            if abs(l['monto_origen'] - float(b['monto'])) > 0.005:
                continue
            dif = abs((d(l['fecha']) - d(b['fecha'])).days)
            if dif <= TOL_DIAS:
                cs.append((l['id'], dif))
        cand[b['archivo']] = cs

    # 4 y 5. asignación
    bol = {b['archivo']: b for b in boletas}
    dudas = []
    cambio = True
    while cambio:
        cambio = False
        # pares únicos
        for a, cs in list(cand.items()):
            libres = [(lid, dif) for lid, dif in cs if lid not in usadas]
            if not libres:
                continue
            otros = lambda lid: [o for o, ocs in cand.items() if o != a and o not in estado and lid in [x for x, _ in ocs]]
            if len(libres) == 1 and not otros(libres[0][0]):
                estado[a] = ('rendida', libres[0][0], 'monto y fecha')
                usadas.add(libres[0][0]); del cand[a]; cambio = True
        if cambio:
            continue
        # desempate por día más cercano dentro de la misma boleta
        for a, cs in list(cand.items()):
            libres = sorted([(dif, lid) for lid, dif in cs if lid not in usadas])
            if len(libres) > 1 and libres[0][0] < libres[1][0]:
                lid = libres[0][1]
                rivales = [o for o, ocs in cand.items() if o != a and lid in [x for x, _ in ocs]]
                if not rivales:
                    estado[a] = ('rendida', lid, 'monto y fecha más cercana')
                    usadas.add(lid); del cand[a]; cambio = True
        if cambio:
            continue
        # desempate entre boletas que compiten por la misma línea
        por_linea = {}
        for a, cs in cand.items():
            for lid, dif in cs:
                if lid not in usadas:
                    por_linea.setdefault(lid, []).append((a, dif))
        for lid, rs in por_linea.items():
            if len(rs) < 2:
                continue
            u4 = por_id[lid]['tarjeta_ult4']
            clave = lambda r: (0 if (bol[r[0]].get('tarjeta_ult4') or '') == u4 else 1,
                               0 if bol[r[0]].get('medio_pago') == 'tarjeta' else 1, r[1])
            rs = sorted(rs, key=clave)
            if clave(rs[0]) < clave(rs[1]):
                a = rs[0][0]
                estado[a] = ('rendida', lid, 'monto y fecha; ganó a %s' % ', '.join(r[0] for r in rs[1:]))
                usadas.add(lid); del cand[a]; cambio = True
                break

    for a, cs in cand.items():
        libres = [lid for lid, _ in cs if lid not in usadas]
        if len(libres) > 1:
            dudas.append({'boleta': a, 'lineas_posibles': libres})
            estado[a] = ('duda', None, 'más de una línea posible: %s' % ', '.join(libres))

    # 6. sin línea
    for b in boletas:
        if b['archivo'] in estado:
            continue
        if (b.get('tarjeta_ult4') or '') in tarjetas:
            estado[b['archivo']] = ('sin_cartola', None, 'tarjeta corporativa ...%s, no está en esta cartola: '
                                    'pendiente para la próxima' % b['tarjeta_ult4'])
        elif b.get('medio_pago') in PERSONALES:
            estado[b['archivo']] = ('personal', None, 'no está en la cartola y se pagó en %s' % b['medio_pago'])
        else:
            estado[b['archivo']] = ('sin_cartola', None, 'no está en esta cartola')

    for a, (e, lid, mot) in estado.items():
        if e == 'rendida':
            por_id[lid]['boletas'].append(a)

    # datos para Rindegastos de cada línea con boleta
    for l in lineas:
        if not l['boletas']:
            continue
        bs = [bol[a] for a in l['boletas']]
        principal = next((b for b in bs if b.get('documento') != 'proforma'), bs[0])
        l['proveedor'] = principal.get('proveedor') or principal.get('comercio') or titulo(l['detalle'])
        l['nota'] = principal.get('nota') or P['nota_por_defecto']
        avisos = []
        if l['nota'] not in NOTAS:
            avisos.append('nota "%s" no es una de %s' % (l['nota'], ', '.join(NOTAS)))
        # categoría: por defecto la de tarjeta corporativa; la boleta puede proponer otra (ver 1. Contexto/categorias.md)
        cat = principal.get('categoria') or CAT_DEFECTO
        if cat not in CAT_VALIDAS:
            avisos.append('categoría "%s" no existe en Rindegastos; queda %s' % (cat, CAT_DEFECTO))
            cat = CAT_DEFECTO
        elif cat != CAT_DEFECTO:
            avisos.append('categoría "%s" (no es la por defecto)%s' % (
                cat, '' if cat in CAT_DEFINIDAS else '; está "Por definir" en categorias.md: se usa porque la indicó el ejecutivo'))
        l['categoria'] = cat
        for b in bs:
            if b.get('documento') == 'proforma':
                avisos.append('%s es pro forma (no es boleta tributaria)' % b['archivo'])
            if b.get('medio_pago') == 'efectivo':
                avisos.append('%s dice efectivo, pero el cargo está en la tarjeta' % b['archivo'])
            if b.get('observacion'):
                avisos.append('%s: %s' % (b['archivo'], b['observacion']))
        l['avisos'] = avisos

    boletas_out = []
    for b in boletas:
        e, lid, mot = estado[b['archivo']]
        boletas_out.append(dict(b, estado=e, linea=lid, motivo=mot))
    return lineas, boletas_out, dudas


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    carpeta = sys.argv[1]
    cartolas, boletas, periodo, pc, decisiones = cargar(carpeta)
    lineas, bs, dudas = cruzar(cartolas, boletas, decisiones)
    out = {
        'periodo': periodo,
        'cartolas': [{k: c[k] for k in ('tipo', 'archivo', 'tarjeta_ult4', 'titular', 'fecha_estado',
                                        'periodo_desde', 'periodo_hasta', 'total_operaciones', 'nombre_informe')}
                     for c in cartolas],
        'lineas': lineas,
        'boletas': bs,
        'dudas': dudas,
        'decisiones': decisiones,
        'rindegastos': {},   # lo llena Claude: id del informe y de cada gasto creado
    }
    json.dump(out, open(pc, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    for c in cartolas:
        ls = [l for l in lineas if l['cartola'] == c['tipo']]
        con = [l for l in ls if l['boletas']]
        f = (lambda v: '%.2f' % v) if c['tipo'] == 'USD' else (lambda v: '%.0f' % v)
        print('%s  "%s": %d líneas %s | con boleta %d = %s | sin boleta %d = %s' % (
            c['tipo'], c['nombre_informe'], len(ls), f(sum(l['monto'] for l in ls)),
            len(con), f(sum(l['monto'] for l in con)), len(ls) - len(con),
            f(sum(l['monto'] for l in ls if not l['boletas']))))
    for e in ('rendida', 'personal', 'sin_cartola', 'duda'):
        xs = [b for b in bs if b['estado'] == e]
        if xs:
            print('\nBoletas %s (%d):' % (e, len(xs)))
            for b in xs:
                print('  %-45s %s %s %8.2f %s  -> %s  [%s]' % (b['archivo'], b['fecha'], b['moneda'], float(b['monto']),
                                                           b.get('comercio', ''), b['linea'] or '-', b['motivo']))
    avisos = [(l['id'], a) for l in lineas for a in l.get('avisos', [])]
    if avisos:
        print('\nAvisos para revisar:')
        for lid, a in avisos:
            print('  %s  %s' % (lid, a))
    print('\nEscrito:', pc)
    if dudas:
        print('HAY %d DUDAS: agrega una decisión por cada una en "decisiones" y vuelve a correr.' % len(dudas))
        sys.exit(2)


if __name__ == '__main__':
    main()
