r"""Prepara el orden final de la carpeta del ejecutivo después de una rendición: RENOMBRA y MUEVE los originales
(sin copias) y deja los archivos nuevos que generó el agente.

Uso:
    python -X utf8 preparar_archivo.py <carpeta_trabajo> <carpeta_fotos_y_cartolas> [--cruce <archivo>]

<carpeta_fotos_y_cartolas> = copia de trabajo (device_stage_files) de la carpeta del ejecutivo: los nombres de los
archivos, relativos a ella, son los mismos que en el PC.
--cruce: archivo de cruce (por defecto el cruce_AAAA-MM.json más reciente de cartola; fondo: cruce_fondo_AAAA-MM.json).

Orden final (reglas-de-negocio.md §7):
  <Nombre del informe>\   por cada cartola: las boletas rendidas renombradas por monto ("49,50.jpeg"), la cartola
                          original y la cartola marcada. Si la cartola no tuvo boletas (no se creó informe), la
                          carpeta igual se crea con la cartola (y la marcada), para que no quede suelta.
  AAAA-MM\                (mes de la fecha de la boleta) las boletas NO rendidas: "49,50 - personal.jpeg" y las
                          pendientes "49,50.jpeg".
  cruce_AAAA-MM.json      en la raíz de la carpeta del ejecutivo.

Deja en <carpeta_trabajo>/salida/:
  nuevos/...              archivos NUEVOS para copiar a la carpeta del ejecutivo con device_commit_files
                          (cartolas marcadas y cruce), ya en su carpeta de destino
  nuevos.json             lista de esos archivos (ruta relativa dentro de la carpeta del ejecutivo)
  movimientos.json        qué original va a dónde y con qué nombre
  (se ejecuta con ejecutar_movimientos.py; ver la skill)
"""
import json, os, shutil, sys
import rutas as R
import movimientos as M


def monto_txt(m):
    return ('%.2f' % float(m)).replace('.', ',')


def main():
    args = sys.argv[1:]
    elegido = None
    if '--cruce' in args:
        i = args.index('--cruce'); elegido = args[i + 1]; del args[i:i + 2]
    if len(args) < 2:
        print(__doc__); sys.exit(1)
    trabajo, fotos = args[0], args[1]
    cruces = [elegido] if elegido else sorted(f for f in os.listdir(trabajo) if f.startswith('cruce_2') and f.endswith('.json'))
    if not cruces or not os.path.exists(os.path.join(trabajo, cruces[-1])):
        raise SystemExit('ERROR: no encontré el archivo de cruce en %s' % trabajo)
    nombre_cruce = cruces[-1]
    cruce = json.load(open(os.path.join(trabajo, nombre_cruce), encoding='utf-8'))
    if cruce.get('dudas'):
        raise SystemExit('ERROR: el cruce tiene dudas sin decidir. Resuélvelas antes de ordenar.')

    salida = os.path.join(trabajo, R.SALIDA)
    nuevos_dir = os.path.join(salida, 'nuevos')
    if os.path.exists(nuevos_dir):
        shutil.rmtree(nuevos_dir)
    os.makedirs(nuevos_dir)
    nuevos, movs, faltan, usados = [], [], [], {}
    sufijo = R.parametros()['sufijo_boleta_personal']

    def existe(rel):
        if os.path.exists(os.path.join(fotos, rel)):
            return True
        faltan.append(rel)
        return False

    def destino(carpeta, base, ext):
        usados.setdefault(carpeta, set())
        return carpeta + '/' + M.nombre_libre(base, ext, usados[carpeta])

    def nuevo(origen_abs, rel):
        os.makedirs(os.path.dirname(os.path.join(nuevos_dir, rel)), exist_ok=True)
        shutil.copy2(origen_abs, os.path.join(nuevos_dir, rel))
        nuevos.append(rel)

    bol = {b['archivo']: b for b in cruce['boletas']}
    lineas_con = {}
    for l in cruce['lineas']:
        if l['boletas']:
            lineas_con.setdefault(l['cartola'], []).append(l)

    # 1. carpeta de cada informe (o de cada cartola, aunque no haya tenido boletas)
    for c in cruce['cartolas']:
        dest = c['nombre_informe']
        if c['tipo'] not in lineas_con and not c.get('archivo'):
            continue                                   # fondo sin gastos: nada que hacer
        for l in sorted(lineas_con.get(c['tipo'], []), key=lambda x: x['id']):
            for a in sorted(l['boletas']):
                if existe(a):
                    d = destino(dest, monto_txt(bol[a]['monto']), os.path.splitext(a)[1].lower())
                    movs.append((a, d)); bol[a]['archivado_como'] = d
        if c.get('archivo') and existe(c['archivo']):
            movs.append((c['archivo'], dest + '/' + c['archivo']))
            marcada = os.path.join(salida, os.path.splitext(c['archivo'])[0] + ' - revisión boletas.pdf')
            if os.path.exists(marcada):
                nuevo(marcada, dest + '/' + os.path.basename(marcada))

    # 2. carpeta del mes con lo no rendido
    for b in sorted(cruce['boletas'], key=lambda x: x['archivo']):
        if b['estado'] not in ('personal', 'sin_cartola'):
            continue
        if existe(b['archivo']):
            base = monto_txt(b['monto']) + (sufijo if b['estado'] == 'personal' else '')
            d = destino(b['fecha'][:7], base, os.path.splitext(b['archivo'])[1].lower())
            movs.append((b['archivo'], d)); b['archivado_como'] = d

    # 3. cruce (con dónde quedó cada boleta) y plan de movimientos
    json.dump(cruce, open(os.path.join(trabajo, nombre_cruce), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    nuevo(os.path.join(trabajo, nombre_cruce), nombre_cruce)
    json.dump(nuevos, open(os.path.join(salida, 'nuevos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    movs = M.escribir(salida, movs, 'Ordenar rendición ' + cruce.get('periodo', ''))

    print('Orden preparado en', salida)
    print('  %d archivos a mover/renombrar (movimientos.json)' % len(movs))
    carpetas = {}
    for o, d in movs:
        carpetas[d.split('/')[0]] = carpetas.get(d.split('/')[0], 0) + 1
    for k, v in sorted(carpetas.items()):
        print('    %-40s %d' % (k, v))
    print('  %d archivos nuevos para copiar (nuevos.json): %s' % (len(nuevos), ', '.join(nuevos)))
    fuera = [b['archivo'] for b in cruce['boletas'] if b['estado'] == 'fuera']
    if fuera:
        print('  Quedan donde están (fuera): %s' % ', '.join(fuera))
    if faltan:
        print('ERROR: no encontré estos archivos en %s: %s' % (fotos, ', '.join(faltan)))
        sys.exit(1)


if __name__ == '__main__':
    main()
