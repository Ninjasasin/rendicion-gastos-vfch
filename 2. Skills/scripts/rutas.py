"""Rutas del agente Rendición de Gastos.

Todo se resuelve desde la ubicación de este archivo, así que funciona igual en el PC de cualquier ejecutivo,
en el repositorio de GitHub o en una copia en el espacio de trabajo de Claude.
Los demás scripts importan de aquí: `import rutas as R`.

Los datos del ejecutivo (cartolas y boletas) NO viven en la carpeta del agente: viven en la carpeta del ejecutivo
(`Documentos\\Rinde gastos\\` en su PC). Los scripts reciben esa carpeta (o la copia de trabajo) como argumento.

python rutas.py  -> muestra las rutas y si existen.
"""
import json, os

SCRIPTS = os.path.dirname(os.path.abspath(__file__))           # 2. Skills/scripts
AGENTE = os.path.dirname(os.path.dirname(SCRIPTS))             # carpeta del agente
CONTEXTO = os.path.join(AGENTE, '1. Contexto')
MEMORIA = os.path.join(AGENTE, '3. Memoria')
PROYECTOS = os.path.join(AGENTE, '4. Proyectos')
JS = os.path.join(SCRIPTS, 'js')
PARAMETROS = os.path.join(CONTEXTO, 'parametros.json')   # reglas de negocio con valor (ver reglas-de-negocio.md)

# Nombres fijos de archivos de trabajo (dentro de la carpeta de trabajo de cada corrida)
CARTOLA_JSON = 'cartola_{tipo}.json'          # salida de leer_cartola.py (tipo = USD o CLP)
BOLETAS_JSON = 'boletas.json'                 # lo que Claude leyó de cada foto
CRUCE_JSON = 'cruce_{periodo}.json'           # resultado del cruce + decisiones de la corrida
SALIDA = 'salida'                             # carpetas listas para copiar al PC del ejecutivo

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto',
         'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


def parametros():
    """Lee 1. Contexto/parametros.json. Todas las reglas con valor salen de aquí, no del código."""
    with open(PARAMETROS, encoding='utf-8') as fh:
        return json.load(fh)


def nombre_informe(tipo, anio, mes):
    """'TC Internacional - Octubre 2026' (USD) o 'TC Nacional - Octubre 2026' (CLP). Mes = mes del estado de cuenta."""
    base = parametros()['nombre_informe_por_cartola'][tipo]
    return '%s - %s %d' % (base, MESES[mes - 1], anio)


if __name__ == '__main__':
    for n in ['AGENTE', 'CONTEXTO', 'MEMORIA', 'PROYECTOS', 'JS', 'PARAMETROS']:
        p = globals()[n]
        print('%-10s %s  %s' % (n, 'OK ' if os.path.exists(p) else 'NO ', p))
