r"""Ejecuta movimientos.json directamente sobre la carpeta del ejecutivo: renombra y mueve los originales (sin copias).

Es la vía normal en Cowork: Claude lo corre en su terminal, en segundo plano, sin clics del ejecutivo y sin tomar
el control de la pantalla. Funciona igual si la terminal es Windows o Linux (carpeta conectada/montada).

Uso:
  python -X utf8 ejecutar_movimientos.py "<carpeta del ejecutivo>" <carpeta_trabajo>/salida/movimientos.json

Reglas (las mismas que ordenar.ps1):
  - Solo MUEVE. Nunca borra boletas ni cartolas.
  - Si el destino ya existe, agrega " (2)", " (3)"… (no pisa nada).
  - Si un origen ya no está, lo avisa y sigue.
  - Deja "ordenar_<fecha>.log" en la carpeta del ejecutivo.
"""
import datetime, json, os, shutil, sys


def destino_libre(ruta):
    if not os.path.exists(ruta):
        return ruta
    base, ext = os.path.splitext(ruta)
    n = 2
    while os.path.exists('%s (%d)%s' % (base, n, ext)):
        n += 1
    return '%s (%d)%s' % (base, n, ext)


def main(carpeta, archivo_movs):
    movs = json.load(open(archivo_movs, encoding='utf-8'))
    log = os.path.join(carpeta, 'ordenar_%s.log' % datetime.datetime.now().strftime('%Y-%m-%d_%H%M'))
    ok, faltan, lineas = 0, 0, []
    for m in movs:
        src = os.path.join(carpeta, *m['origen'].replace('\\', '/').split('/'))
        dst = os.path.join(carpeta, *m['destino'].replace('\\', '/').split('/'))
        if not os.path.isfile(src):
            faltan += 1
            lineas.append('NO ENCONTRADO: ' + m['origen'])
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        dst = destino_libre(dst)
        shutil.move(src, dst)
        lineas.append('%s -> %s' % (m['origen'], os.path.relpath(dst, carpeta)))
        ok += 1
    with open(log, 'w', encoding='utf-8-sig') as fh:
        fh.write('\n'.join(lineas) + '\n')
    print('Listo: %d movidos, %d no encontrados. Registro: %s' % (ok, faltan, os.path.basename(log)))
    return 0 if faltan == 0 else 1


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
