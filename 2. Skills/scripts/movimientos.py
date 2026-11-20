"""Arma el plan para RENOMBRAR y MOVER los archivos originales de la carpeta del ejecutivo (sin copias) y escribe
el script de Windows que lo ejecuta.

No se corre solo: lo usan preparar_archivo.py y ordenar_boletas.py.

Escribe en <carpeta_trabajo>/salida/:
  movimientos.json   lista de {"origen": ruta relativa, "destino": ruta relativa} dentro de la carpeta del ejecutivo

Cómo se ejecuta (ver la skill):
  - Cowork (siempre): Claude corre ejecutar_movimientos.py con movimientos.json en su terminal, en segundo plano.
    NO se genera ni se entrega ningún .bat.
  - Respaldo, SOLO si la sesión de verdad no puede mover archivos (se intentó y falló, o no es Cowork):
      python -X utf8 movimientos.py --respaldo <carpeta_trabajo>/salida
    genera ordenar.ps1 (PowerShell que hace los movimientos) y ordenar.bat (doble clic del ejecutivo).

Reglas del script:
  - Solo MUEVE (renombrar = mover con otro nombre). Nunca borra boletas ni cartolas.
  - Si el destino ya existe, agrega " (2)", " (3)"… (no pisa nada).
  - Si un origen ya no está (lo movió el ejecutivo), lo avisa y sigue.
  - Deja un registro "ordenar_<fecha>.log" y, al terminar bien, se borra a sí mismo (ordenar.ps1 y ordenar.bat).
"""
import json, os


def _ps(s):
    """Texto entre comillas simples de PowerShell."""
    return "'" + s.replace("'", "''") + "'"


def nombre_libre(base, ext, usados):
    n, nombre = 1, base + ext
    while nombre.lower() in usados:
        n += 1
        nombre = '%s (%d)%s' % (base, n, ext)
    usados.add(nombre.lower())
    return nombre


def escribir(salida, movs, titulo='Ordenar boletas y cartolas'):
    """movs: lista de (origen_relativo, destino_relativo) con '/' como separador."""
    os.makedirs(salida, exist_ok=True)
    movs = [(o, d) for o, d in movs if o.replace('\\', '/') != d.replace('\\', '/')]
    json.dump([{'origen': o, 'destino': d} for o, d in movs],
              open(os.path.join(salida, 'movimientos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # ordenar.ps1/.bat NO se generan por defecto: en Cowork Claude mueve con ejecutar_movimientos.py.
    # Solo si mover falló de verdad: python movimientos.py --respaldo <salida>
    for viejo in ('ordenar.ps1', 'ordenar.bat'):
        p = os.path.join(salida, viejo)
        if os.path.exists(p):
            os.remove(p)
    return movs


def escribir_respaldo(salida, titulo='Ordenar boletas y cartolas'):
    """Genera ordenar.ps1 y ordenar.bat desde salida/movimientos.json (respaldo fuera de Cowork)."""
    movs = [(m['origen'], m['destino']) for m in json.load(open(os.path.join(salida, 'movimientos.json'), encoding='utf-8'))]

    # una línea "$movs += ,@(origen, destino)" por archivo: así la lista no se "aplana" aunque haya un solo archivo
    filas = '\n'.join('$movs += ,@(%s, %s)' % (_ps(o.replace('/', '\\')), _ps(d.replace('/', '\\'))) for o, d in movs)
    ps1 = r'''# %(titulo)s — generado por el agente Rendición de Gastos (VFCH)
# Mueve y renombra los archivos de esta carpeta. No borra boletas ni cartolas. No pisa archivos.
param([switch]$Si)
$ErrorActionPreference = 'Stop'
$base = $PSScriptRoot
$movs = @()
%(filas)s
Write-Host ''
Write-Host '%(titulo)s: se van a mover %(n)d archivos'
foreach ($m in $movs) { Write-Host ('  ' + $m[0] + '  ->  ' + $m[1]) }
if (-not $Si) {
  $r = Read-Host '¿Continuar? (S/N)'
  if ($r -notmatch '^[sS]') { Write-Host 'Cancelado. No se movió nada.'; exit 1 }
}
$log = Join-Path $base ('ordenar_' + (Get-Date -Format 'yyyy-MM-dd_HHmm') + '.log')
$ok = 0; $faltan = 0
foreach ($m in $movs) {
  $src = Join-Path $base $m[0]
  $dst = Join-Path $base $m[1]
  if (-not (Test-Path -LiteralPath $src)) {
    Add-Content -LiteralPath $log -Value ('NO ESTA: ' + $m[0]) -Encoding UTF8
    Write-Host ('  No encontré ' + $m[0] + ' (sigo)'); $faltan++; continue
  }
  $dir = Split-Path -Parent $dst
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  if (Test-Path -LiteralPath $dst) {
    $sin = [System.IO.Path]::GetFileNameWithoutExtension($dst); $ext = [System.IO.Path]::GetExtension($dst); $n = 2
    do { $dst = Join-Path $dir ($sin + ' (' + $n + ')' + $ext); $n++ } while (Test-Path -LiteralPath $dst)
  }
  Move-Item -LiteralPath $src -Destination $dst
  Add-Content -LiteralPath $log -Value ($m[0] + ' -> ' + $dst.Substring($base.Length + 1)) -Encoding UTF8
  $ok++
}
Write-Host ('Listo: ' + $ok + ' movidos, ' + $faltan + ' no encontrados. Registro: ' + (Split-Path -Leaf $log))
if ($faltan -eq 0) {
  Remove-Item -LiteralPath (Join-Path $base 'ordenar.bat') -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $PSCommandPath -ErrorAction SilentlyContinue
}
''' % {'titulo': titulo.replace("'", "''"), 'filas': filas, 'n': len(movs)}
    # UTF-8 con BOM: así PowerShell 5.1 de Windows lee bien la "ñ" y los tildes
    with open(os.path.join(salida, 'ordenar.ps1'), 'w', encoding='utf-8-sig', newline='\r\n') as fh:
        fh.write(ps1)
    bat = ('@echo off\r\nchcp 65001 >nul\r\n'
           'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ordenar.ps1"\r\npause\r\n')
    with open(os.path.join(salida, 'ordenar.bat'), 'w', encoding='ascii', newline='') as fh:
        fh.write(bat)
    return movs


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == '--respaldo':
        n = len(escribir_respaldo(sys.argv[2]))
        print('Respaldo generado: ordenar.ps1 y ordenar.bat (%d movimientos) en %s' % (n, sys.argv[2]))
    else:
        sys.exit('Uso: python -X utf8 movimientos.py --respaldo <carpeta_trabajo>/salida')
