r"""Solo ORDENA boletas: las renombra por su monto y las mueve a la carpeta de su mes (AAAA-MM). No cruza con
cartolas, no crea informes, no toca Rindegastos.

Uso:
    python -X utf8 ordenar_boletas.py <carpeta_trabajo> <carpeta_fotos>

Lee <carpeta_trabajo>/boletas.json (mismo formato que en rendir-cartola; para ordenar bastan archivo, fecha, monto
y, si el ejecutivo lo dijo, "personal": true). Cada boleta va a:
    <AAAA-MM de su fecha>\<monto>.<ext>             p. ej. 2026-10\49,50.jpeg
    <AAAA-MM de su fecha>\<monto> - personal.<ext>  si el ejecutivo dijo que es personal
Repetidos: "49,50 (2).jpeg". Las que ya están en su carpeta y con su nombre no se mueven.

Deja en <carpeta_trabajo>/salida/ movimientos.json (ver movimientos.py; se ejecuta con ejecutar_movimientos.py).
"""
import json, os, sys
import rutas as R
import movimientos as M


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    trabajo, fotos = sys.argv[1], sys.argv[2]
    boletas = json.load(open(os.path.join(trabajo, R.BOLETAS_JSON), encoding='utf-8'))
    sufijo = R.parametros()['sufijo_boleta_personal']
    usados, movs, faltan, resumen = {}, [], [], {}
    for b in sorted(boletas, key=lambda x: (x['fecha'], x['archivo'])):
        a = b['archivo']
        if not os.path.exists(os.path.join(fotos, a)):
            faltan.append(a); continue
        mes = b['fecha'][:7]
        base = ('%.2f' % float(b['monto'])).replace('.', ',') + (sufijo if b.get('personal') else '')
        usados.setdefault(mes, set())
        ext = os.path.splitext(a)[1].lower()
        actual = a.replace('\\', '/')
        # si ya está en su carpeta con el nombre correcto, no se mueve (y su nombre queda reservado)
        if actual.lower() == (mes + '/' + base + ext).lower():
            usados[mes].add((base + ext).lower()); continue
        d = mes + '/' + M.nombre_libre(base, ext, usados[mes])
        movs.append((a, d))
        resumen[mes] = resumen.get(mes, 0) + 1
    movs = M.escribir(os.path.join(trabajo, R.SALIDA), movs, 'Ordenar boletas por mes')
    print('%d boletas a renombrar y mover:' % len(movs))
    for o, d in movs:
        print('  %-50s -> %s' % (o, d))
    print('Por mes: ' + ', '.join('%s: %d' % kv for kv in sorted(resumen.items())))
    if faltan:
        print('ERROR: no encontré: ' + ', '.join(faltan)); sys.exit(1)


if __name__ == '__main__':
    main()
