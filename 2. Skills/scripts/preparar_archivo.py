"""Deja listas, en <carpeta_trabajo>/salida/, las carpetas que se copian a la carpeta del ejecutivo.

Uso:
    python -X utf8 preparar_archivo.py <carpeta_trabajo> <carpeta_fotos_y_cartolas> [--cruce <archivo>]

--cruce: archivo de cruce a usar (por defecto el cruce_AAAA-MM.json más reciente de cartola; para un fondo por
         rendir: --cruce cruce_fondo_AAAA-MM.json).

<carpeta_fotos_y_cartolas> = copia de trabajo de lo que el ejecutivo dejó en su carpeta (fotos con su nombre
original y los PDF de las cartolas).

Arma:
  salida/<Nombre del informe>/   por cada cartola que tiene al menos una línea con boleta:
        - las boletas rendidas, renombradas por su monto ("49,50.jpeg"; repetidos "49,50 (2).jpeg")
        - la cartola original
        - la cartola marcada ("... - revisión boletas.pdf", si ya se corrió marcar_cartola.py)
  salida/AAAA-MM/                por cada mes (fecha de la boleta) con boletas NO rendidas:
        - personales: "49,50 - personal.jpeg"
        - sin cartola (pendientes para la próxima): "49,50.jpeg"
  salida/cruce_AAAA-MM.json      copia del cruce con las decisiones (para repetir la corrida igual)
  salida/copias.json             lista de archivos (ruta relativa dentro de la carpeta del ejecutivo)
  salida/borrar.txt              lo que el ejecutivo puede borrar después (Claude no borra en el PC)
"""
import json, os, shutil, sys
from collections import Counter
import rutas as R


def monto_txt(m):
    return ('%.2f' % float(m)).replace('.', ',')


def nombre_libre(carpeta, base, ext, usados):
    n, nombre = 1, base + ext
    while nombre.lower() in usados:
        n += 1
        nombre = '%s (%d)%s' % (base, n, ext)
    usados.add(nombre.lower())
    return nombre


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
    cruce = json.load(open(os.path.join(trabajo, cruces[-1]), encoding='utf-8'))
    if cruce.get('dudas'):
        raise SystemExit('ERROR: el cruce tiene dudas sin decidir. Resuélvelas antes de archivar.')

    salida = os.path.join(trabajo, R.SALIDA)
    os.makedirs(salida, exist_ok=True)
    copias, faltan = [], []
    usados = {}

    def copiar(origen, carpeta_dest, nombre):
        os.makedirs(os.path.join(salida, carpeta_dest), exist_ok=True)
        shutil.copy2(origen, os.path.join(salida, carpeta_dest, nombre))
        copias.append(carpeta_dest + '/' + nombre)

    # 1. carpeta del informe por cartola
    lineas_con = {}
    for l in cruce['lineas']:
        if l['boletas']:
            lineas_con.setdefault(l['cartola'], []).append(l)
    bol = {b['archivo']: b for b in cruce['boletas']}
    for c in cruce['cartolas']:
        if c['tipo'] not in lineas_con:
            continue
        dest = c['nombre_informe']
        usados.setdefault(dest, set())
        for l in sorted(lineas_con[c['tipo']], key=lambda x: x['id']):
            for a in sorted(l['boletas']):
                src = os.path.join(fotos, a)
                if not os.path.exists(src):
                    faltan.append(a); continue
                ext = os.path.splitext(a)[1].lower()
                nom = nombre_libre(dest, monto_txt(bol[a]['monto']), ext, usados[dest])
                copiar(src, dest, nom)
                bol[a]['archivado_como'] = dest + '/' + nom
        if not c.get('archivo'):          # fondo por rendir: no hay cartola
            continue
        src = os.path.join(fotos, c['archivo'])
        if os.path.exists(src):
            copiar(src, dest, c['archivo'])
        else:
            faltan.append(c['archivo'])
        marcada = os.path.join(salida, os.path.splitext(c['archivo'])[0] + ' - revisión boletas.pdf')
        if os.path.exists(marcada):
            shutil.move(marcada, os.path.join(salida, dest, os.path.basename(marcada)))
            copias.append(dest + '/' + os.path.basename(marcada))

    # 2. carpeta del mes con lo no rendido
    for b in sorted(cruce['boletas'], key=lambda x: x['archivo']):
        if b['estado'] not in ('personal', 'sin_cartola'):
            continue
        dest = b['fecha'][:7]
        usados.setdefault(dest, set())
        src = os.path.join(fotos, b['archivo'])
        if not os.path.exists(src):
            faltan.append(b['archivo']); continue
        base = monto_txt(b['monto']) + (R.parametros()['sufijo_boleta_personal'] if b['estado'] == 'personal' else '')
        nom = nombre_libre(dest, base, os.path.splitext(b['archivo'])[1].lower(), usados[dest])
        copiar(src, dest, nom)
        b['archivado_como'] = dest + '/' + nom

    # 3. cruce y listas
    json.dump(cruce, open(os.path.join(trabajo, cruces[-1]), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    shutil.copy2(os.path.join(trabajo, cruces[-1]), os.path.join(salida, cruces[-1]))
    copias.append(cruces[-1])
    json.dump(copias, open(os.path.join(salida, 'copias.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    archivadas = [b['archivo'] for b in cruce['boletas'] if b.get('archivado_como')]
    cartolas = [c['archivo'] for c in cruce['cartolas'] if c['tipo'] in lineas_con and c.get('archivo')]
    with open(os.path.join(salida, 'borrar.txt'), 'w', encoding='utf-8') as fh:
        fh.write('Archivos sueltos que ya quedaron copiados en las carpetas nuevas (se pueden borrar):\n')
        for a in archivadas + cartolas:
            fh.write('  ' + a + '\n')

    print('Carpetas listas en', salida)
    for k, v in sorted(Counter(c.split('/')[0] for c in copias if '/' in c).items()):
        print('  %-40s %d archivos' % (k, v))
    print('  + %s' % cruces[-1])
    print('Se pueden borrar después: %d fotos y %d cartolas sueltas (ver borrar.txt)' % (len(archivadas), len(cartolas)))
    if faltan:
        print('ERROR: no encontré estos archivos en %s: %s' % (fotos, ', '.join(faltan)))
        sys.exit(1)


if __name__ == '__main__':
    main()
