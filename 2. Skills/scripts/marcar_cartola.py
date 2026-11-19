"""Marca la cartola en PDF según el cruce: verde = tiene boleta, amarillo = falta boleta.

Uso:
    python -X utf8 marcar_cartola.py <carpeta_trabajo> <cartola.pdf> [<salida.pdf>]

Lee cartola_USD.json o cartola_CLP.json (según el PDF) y cruce_AAAA-MM.json de <carpeta_trabajo>.
Por defecto escribe "<nombre de la cartola> - revisión boletas.pdf" en <carpeta_trabajo>/salida/.
Cada marca lleva una nota (al pasar el mouse) con la boleta o "Falta boleta".
Las líneas que no se rinden (pago de la cartola anterior, cargos del banco) no se marcan.
"""
import json, os, sys
import pymupdf
import rutas as R
from leer_cartola import leer

VERDE, AMARILLO = (0.75, 0.95, 0.75), (1.0, 0.93, 0.3)


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    carpeta, pdf = sys.argv[1], sys.argv[2]
    cart = leer(pdf)                                   # se vuelve a leer para tener las posiciones exactas
    cruces = [f for f in os.listdir(carpeta) if f.startswith('cruce_2') and f.endswith('.json')]
    if not cruces:
        raise SystemExit('ERROR: no hay cruce_AAAA-MM.json en %s (corre antes cruzar.py)' % carpeta)
    cruce = json.load(open(os.path.join(carpeta, sorted(cruces)[-1]), encoding='utf-8'))
    bol = {l['id']: l['boletas'] for l in cruce['lineas'] if l.get('cartola') == cart['tipo']}

    salida = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
        carpeta, R.SALIDA, os.path.splitext(os.path.basename(pdf))[0] + ' - revisión boletas.pdf')
    os.makedirs(os.path.dirname(salida), exist_ok=True)

    doc = pymupdf.open(pdf)
    n_con = n_sin = 0
    for l in cart['lineas']:
        if l['tipo'] != 'gasto':
            continue
        page = doc[l['pagina']]
        x0, y0, x1, y1 = l['bbox']
        rect = pymupdf.Rect(x0 - 2, y0 - 1.5, page.rect.width - 25, y1 + 1.5)
        b = bol.get(l['id'], [])
        h = page.add_highlight_annot(rect)
        h.set_colors(stroke=VERDE if b else AMARILLO)
        h.set_info(content=('Boleta: ' + ', '.join(b)) if b else 'Falta boleta')
        h.update()
        n_con += 1 if b else 0
        n_sin += 0 if b else 1
    doc[0].insert_text((300, 40), 'Verde: con boleta   |   Amarillo: falta boleta', fontsize=8, color=(0, 0, 0))
    doc.save(salida)
    print('Marcadas %d líneas con boleta (verde) y %d sin boleta (amarillo)' % (n_con, n_sin))
    print('Escrito:', salida)


if __name__ == '__main__':
    main()
