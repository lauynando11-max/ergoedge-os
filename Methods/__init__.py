"""
Methods package - Módulos de análisis ergonómico OWAS, RULA y REBA
"""

from .reports import crear_pdf_senior
from .reports import generar_reporte_reba

# Exportadores eliminados de la nueva versión de reports.py
# Si necesitas compatibilidad, descomenta las líneas inferiores
# from .reports import exportar_json, exportar_csv_estadisticas, exportar_resumen_txt

# Importar owas desde la subcarpeta metodologias
from .metodologias.owas import analizar_owas_completo

__all__ = [
    'crear_pdf_senior',
    'generar_reporte_reba',
    'analizar_owas_completo',
    # 'exportar_json',
    # 'exportar_csv_estadisticas',
    # 'exportar_resumen_txt',
]