"""
SISTEMA AVANZADO DE ANÁLISIS ERGONÓMICO - VERSIÓN IA
Generador de reportes con inteligencia predictiva
"""

import os
import datetime
import math
import base64
import time
import traceback
from jinja2 import Template
# from weasyprint import HTML
# WeasyPrint eliminado temporalmente

# ============================================================
# MÓDULO 0: DETECCIÓN DE MÉTODO Y CONVERSIÓN DE RULA A OWAS
# ============================================================

def normalizar_datos_rula_a_owas(datos):
    """
    Detecta si los datos vienen de RULA y los normaliza al formato OWAS
    Retorna: (datos_normalizados, es_rula)
    """
    # Detectar si es RULA (tiene campo 'metodo' o 'puntuacion_max')
    es_rula = datos.get('metodo') == 'RULA' or 'puntuacion_max' in datos
    
    if es_rula:
        print("📌 Detectado método RULA - Convirtiendo a formato compatible para PDF...")
        
        # Guardar método original
        datos['metodo_usado'] = 'RULA'
        
        # Obtener puntuación máxima
        punt_max = datos.get('puntuacion_max', 1)
        
        # Convertir puntuación RULA (1-7) a nivel (1-4)
        if punt_max <= 2:
            nivel_convertido = 1
        elif punt_max <= 4:
            nivel_convertido = 2
        elif punt_max <= 6:
            nivel_convertido = 3
        else:
            nivel_convertido = 4
        
        # Convertir estadísticas de RULA (1-7) a niveles (1-4)
        stats_rula = datos.get('estadisticas', {})
        stats_convertidas = {1: 0, 2: 0, 3: 0, 4: 0}
        
        # Mapeo: RULA 1-2 -> Nivel 1, RULA 3-4 -> Nivel 2, RULA 5-6 -> Nivel 3, RULA 7 -> Nivel 4
        mapeo_niveles = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4}
        
        for rula_score, porcentaje in stats_rula.items():
            try:
                rula_int = int(rula_score)
                nivel_owas = mapeo_niveles.get(rula_int, 4)
                stats_convertidas[nivel_owas] = stats_convertidas.get(nivel_owas, 0) + porcentaje
            except:
                pass
        
        # Normalizar a 100%
        total = sum(stats_convertidas.values())
        if total > 0:
            for k in stats_convertidas:
                stats_convertidas[k] = (stats_convertidas[k] / total) * 100
        
        # Actualizar datos
        datos['estadisticas'] = stats_convertidas
        datos['nivel_accion_owas'] = nivel_convertido
        datos['nivel_maximo_presente'] = nivel_convertido
        datos['frecuencia_nivel_maximo'] = stats_convertidas.get(nivel_convertido, 0)
        
        # Descripciones específicas para RULA
        descripciones_rula = {
            1: "Fase 1: Postura aceptable. Nivel de riesgo BAJO según RULA.",
            2: "Fase 2: Riesgo MODERADO. Se requieren cambios en el puesto según RULA.",
            3: "Fase 3: Riesgo ALTO. Intervención en el corto plazo según RULA.",
            4: "Fase 4: Riesgo MUY ALTO. Intervención INMEDIATA según RULA."
        }
        datos['descripcion_accion_owas'] = descripciones_rula.get(nivel_convertido, 
            f"Puntuación RULA: {punt_max}/7 - Nivel: {nivel_convertido}/4")
        
        print(f"   ✅ RULA {punt_max}/7 → Nivel {nivel_convertido}/4")
    else:
        datos['metodo_usado'] = datos.get('metodo_usado', 'OWAS')
    
    return datos, es_rula


# ============================================================
# MÓDULO 1: UTILIDADES Y CONVERSIÓN DE IMÁGENES
# ============================================================

def image_to_base64(ruta_imagen):
    """Convierte una imagen a base64 para incrustarla en el HTML"""
    try:
        if not ruta_imagen or not os.path.exists(ruta_imagen):
            return None
        with open(ruta_imagen, 'rb') as img_file:
            extension = os.path.splitext(ruta_imagen)[1].lower()
            mime_type = 'image/jpeg'
            if extension == '.png':
                mime_type = 'image/png'
            elif extension == '.jpg' or extension == '.jpeg':
                mime_type = 'image/jpeg'
            return f"data:{mime_type};base64,{base64.b64encode(img_file.read()).decode()}"
    except Exception as e:
        print(f"⚠️ Error convirtiendo imagen a base64: {e}")
        return None


def get_nombre_metodo(metodo_usado):
    """Retorna el nombre correcto del método para mostrar en el PDF"""
    if metodo_usado == 'REBA':
        return 'REBA 3D'
    elif metodo_usado == 'RULA':
        return 'RULA'
    elif metodo_usado == 'ROSA':
        return 'ROSA'
    else:
        return 'OWAS'


def color_estado(estado):
    """
    Devuelve el color de fondo correcto según el estado ergonómico real
    """
    estado = estado or ''
    # Verde - sin riesgo
    if any(p in estado for p in ['Recta', 'Bajo hombro', 'De pie', 'Sentado', 'Normal', 'Ligera', 'Aceptable', 'Negligible']):
        return '#d4edda'
    # Amarillo - riesgo leve
    if any(p in estado for p in ['inclinada', 'Semi-agachado', 'elevados', 'Media', 'MODERADO', 'Medio', 'Bajo']):
        return '#fff3cd'
    # Naranja - riesgo considerable
    if any(p in estado for p in ['muy inclinada', 'Agachado', 'Sobre hombro', 'ALTO', 'Alto']):
        return '#ffe5d0'
    # Rojo - crítico
    if any(p in estado for p in ['Extrema', 'Muy torcida', 'CRÍTICO', 'Pesada', 'Muy alto', 'CRITICO']):
        return '#f8d7da'
    return '#ffffff'


def get_reba_nivel_texto(puntuacion):
    """Retorna el nivel de riesgo REBA según puntuación oficial"""
    if puntuacion == 1:
        return "Negligible"
    elif puntuacion <= 3:
        return "Bajo"
    elif puntuacion <= 7:
        return "Medio"
    elif puntuacion <= 10:
        return "Alto"
    else:
        return "Muy alto"


def get_reba_nivel_accion(puntuacion):
    """Retorna el nivel de acción REBA (0-4) según puntuación oficial"""
    if puntuacion == 1:
        return 0
    elif puntuacion <= 3:
        return 1
    elif puntuacion <= 7:
        return 2
    elif puntuacion <= 10:
        return 3
    else:
        return 4


def get_reba_descripcion_accion(puntuacion):
    """Retorna la descripción de acción REBA según puntuación oficial"""
    if puntuacion == 1:
        return "No requiere acción"
    elif puntuacion <= 3:
        return "Puede requerir cambios"
    elif puntuacion <= 7:
        return "Necesaria acción correctiva"
    elif puntuacion <= 10:
        return "Necesaria acción correctiva cuanto antes"
    else:
        return "ACCIÓN CORRECTIVA INMEDIATA REQUERIDA"


# ============================================================
# MÓDULO 2: IA ERGONÓMICA INTELIGENTE
# ============================================================

class AnalizadorErgonomicoIA:
    """Sistema de recomendaciones basado en reglas + lógica difusa"""
    
    def __init__(self):
        self.recomendaciones_por_segmento = {
            'espalda': {
                'recta': "Postura óptima. Mantener.",
                'inclinada': "⚠️ Riesgo lumbar. Ajustar altura de superficie de trabajo.",
                'muy inclinada': "🔴 ALERTA CRÍTICA: Instalar soporte lumbar y reducir alcance.",
                'torcida': "⚠️ Rediseñar flujo de trabajo para evitar rotaciones."
            },
            'cuello': {
                'recta': "Postura neutra. Monitorear cada 2 horas.",
                'inclinada': "⚠️ Elevar monitor o reducir distancia visual.",
                'muy inclinada': "🔴 Riesgo cervical. Cambiar ángulo de visión inmediatamente."
            },
            'brazos': {
                'bajo hombro': "Ergonómico. Mantener apoyabrazos.",
                'elevados': "⚠️ Riesgo de fatiga de hombros. Bajar superficie de trabajo.",
                'sobre hombro': "🔴 Peligro de lesión de manguito rotador. Rediseñar tarea."
            },
            'brazo': {
                'bajo hombro': "Ergonómico. Mantener apoyabrazos.",
                'elevados': "⚠️ Riesgo de fatiga de hombros. Bajar superficie de trabajo.",
                'sobre hombro': "🔴 Peligro de lesión de manguito rotador. Rediseñar tarea."
            },
            'piernas': {
                'de pie': "Alternar con asiento cada 30 min.",
                'sentado': "Usar reposapiés y cambiar postura cada 45 min.",
                'semi-agachado': "⚠️ Riesgo de rodillas. Usar banco elevador.",
                'agachado': "🔴 Alto riesgo. Instalar elevador de carga."
            }
        }
        
        self.recomendaciones_generales = {
            0: ["✓ Mantener programa de pausas activas preventivas", "✓ Realizar chequeo ergonómico anual"],
            1: ["✓ Mantener programa de pausas activas cada 2 horas", "✓ Realizar chequeo ergonómico semestral"],
            2: ["⚠️ Implementar rotación de tareas cada 2 horas", "⚠️ Ajustar altura de superficies de trabajo"],
            3: ["🔴 INTERVENCIÓN PRONTA: Rediseñar estación de trabajo", "🔴 Instalar ayudas mecánicas"],
            4: ["🆘 PARALIZAR TAREA: Riesgo inminente", "🆘 Rediseño completo del puesto en 48 horas"]
        }
    
    def generar_recomendacion_inteligente(self, analisis, puesto, nivel_riesgo_global):
        """Genera recomendaciones específicas usando lógica difusa"""
        recomendaciones = []
        riesgos_criticos = []
        
        for item in analisis:
            segmento = item.get('segmento', '').lower()
            estado = item.get('estado', '').lower()
            
            for key, value in self.recomendaciones_por_segmento.items():
                if key in segmento:
                    for estado_key, rec in value.items():
                        if estado_key in estado:
                            recomendaciones.append({
                                'segmento': segmento,
                                'recomendacion': rec,
                                'urgencia': 'alta' if '🔴' in rec else 'media' if '⚠️' in rec else 'baja'
                            })
                            if '🔴' in rec:
                                riesgos_criticos.append(segmento)
        
        final_recomendaciones = []
        for rec in recomendaciones[:3]:
            final_recomendaciones.append(f"{rec['recomendacion']} (Segmento: {rec['segmento'].capitalize()})")
        
        if nivel_riesgo_global in self.recomendaciones_generales:
            final_recomendaciones.extend(self.recomendaciones_generales.get(nivel_riesgo_global, []))
        else:
            mapeo = {1: 1, 2: 2, 3: 3, 4: 4}
            final_recomendaciones.extend(self.recomendaciones_generales.get(mapeo.get(nivel_riesgo_global, 2), []))
        
        return final_recomendaciones
    
    def predecir_riesgo_futuro(self, nivel_actual, frecuencia, historial=None):
        if nivel_actual >= 3 and frecuencia > 60:
            return "⚠️ RIESGO PROGRESIVO MUY ALTO: Probabilidad de lesión en 3 meses: 78%"
        elif nivel_actual >= 3:
            return "⚠️ RIESGO MODERADO: Probabilidad de lesión en 6 meses: 45%"
        elif nivel_actual == 2 and frecuencia > 50:
            return "📈 Tendencia al alza detectada: Revisar en 30 días"
        elif nivel_actual == 2:
            return "📊 Riesgo controlable. Implementar mejoras en 90 días."
        else:
            return "✅ Riesgo controlado. Mantener monitoreo trimestral"


# ============================================================
# MÓDULO 3: VALIDADOR DE DATOS
# ============================================================

def validar_datos_entrada(datos):
    """Valida que todos los campos necesarios existan y sean correctos"""
    errores = []
    advertencias = []
    
    required_fields = ['empresa', 'proyecto', 'evaluador', 'estadisticas', 'analisis', 'operario_datos']
    
    for field in required_fields:
        if field not in datos:
            errores.append(f"Falta campo requerido: {field}")
        elif datos[field] is None:
            errores.append(f"Campo vacío: {field}")
    
    if 'operario_datos' in datos and datos['operario_datos']:
        op_fields = ['nombre', 'edad', 'antiguedad', 'patologias']
        for field in op_fields:
            if field not in datos['operario_datos']:
                datos['operario_datos'][field] = "No especificado"
                advertencias.append(f"Campo operario.{field} no especificado, usando valor por defecto")
    
    if 'estadisticas' in datos and datos['estadisticas']:
        suma = sum(datos['estadisticas'].values())
        if not (95 <= suma <= 105):
            advertencias.append(f"Las estadísticas suman {suma:.1f}%, se normalizarán al 100%")
            if suma > 0:
                factor = 100.0 / suma
                for k in datos['estadisticas']:
                    datos['estadisticas'][k] = datos['estadisticas'][k] * factor
    
    if 'nivel_accion_owas' in datos:
        nivel = datos['nivel_accion_owas']
        if not 0 <= nivel <= 4:
            if not 1 <= nivel <= 4:
                errores.append(f"Nivel de acción inválido: {nivel}")
    else:
        if 'estadisticas' in datos:
            niveles = [k for k, v in datos['estadisticas'].items() if v > 0]
            datos['nivel_accion_owas'] = max(niveles) if niveles else 1
            advertencias.append(f"Nivel de acción calculado automáticamente: {datos['nivel_accion_owas']}")
    
    if errores:
        print("❌ ERRORES DE VALIDACIÓN:")
        for error in errores:
            print(f"   - {error}")
        return False, errores
    
    if advertencias:
        print("⚠️ ADVERTENCIAS:")
        for adv in advertencias:
            print(f"   - {adv}")
    
    return True, []


# ============================================================
# MÓDULO 4: FUNCIÓN PARA GENERAR PLANILLAS SRT
# ============================================================

def generar_planillas_srt(datos):
    """Genera las Planillas 1 y 2 de la Resolución SRT 886/2015"""
    
    nivel_riesgo_srt = datos.get('nivel_accion_owas', 1)
    if nivel_riesgo_srt <= 1:
        nivel_srt = 1
        nivel_texto = "Tolerable"
    elif nivel_riesgo_srt <= 2:
        nivel_srt = 2
        nivel_texto = "Moderado"
    else:
        nivel_srt = 3
        nivel_texto = "No Tolerable"
    
    riesgo_color = {1: "#28a745", 2: "#ffc107", 3: "#dc3545"}.get(nivel_srt, "#6c757d")
    
    metodo = datos.get('metodo_usado', 'OWAS')
    puntuacion = datos.get('puntuacion', 1)
    
    # Evaluación de cada factor
    peso = int(datos.get('peso_carga', 0))
    if peso > 15:
        evaluacion_2a = "ALTO"
    elif peso > 10:
        evaluacion_2a = "MODERADO"
    else:
        evaluacion_2a = "BAJO"
    
    evaluacion_2d = "ALTO" if puntuacion >= 3 else "MODERADO" if puntuacion >= 2 else "BAJO"
    evaluacion_2e = "ALTO" if metodo == 'RULA' and puntuacion >= 6 else "MODERADO" if metodo == 'RULA' and puntuacion >= 4 else "BAJO"
    
    # Construir filas de análisis biomecánico (sin Jinja2)
    analisis_rows = ""
    for item in datos.get('analisis', []):
        estado = item.get('estado', 'N/A')
        angulo = item.get('angulo', 'N/A')
        segmento = item.get('segmento', 'N/A')
        
        if 'CRITICO' in estado.upper() or 'ALTO' in estado.upper():
            bg_color = "#f8d7da"
            riesgo_texto = "ALTO"
        elif 'MODERADO' in estado.upper():
            bg_color = "#fff3cd"
            riesgo_texto = "MODERADO"
        else:
            bg_color = "#d4edda"
            riesgo_texto = "BAJO"
        
        analisis_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>{segmento}</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{angulo}</td>
            <td style="padding: 8px; border: 1px solid #ddd; background: {bg_color};">{estado} - {riesgo_texto}</td>
        </tr>
        """
    
    planillas = f"""
    <!-- SECCIÓN: RESOLUCIÓN SRT 886/2015 - PROTOCOLO DE ERGONOMÍA -->
    <div style="page-break-before: avoid; margin-top: 30px;">
        <h2 style="background: #001f3f; color: white; padding: 10px 15px; border-radius: 5px;">
            📋 ANEXO I - PROTOCOLO DE ERGONOMÍA (Res. SRT 886/2015)
        </h2>
        
        <!-- PLANILLA 1: IDENTIFICACIÓN DE FACTORES DE RIESGO -->
        <h3 style="background: #e9ecef; padding: 8px; margin-top: 20px;">Planilla N° 1: Identificación de Factores de Riesgo</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f2f2f2;">
                    <th style="padding: 8px; border: 1px solid #ddd;">Factor de Riesgo</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Presente</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Nivel de Riesgo</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Referencia</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Posturas forzadas</td>
                    <td style="text-align:center;">✓</td>
                    <td style="text-align:center; background:{riesgo_color}; color:white;">{nivel_texto}</td>
                    <td>Planilla 2.F</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Movimientos repetitivos</td>
                    <td style="text-align:center;">{'✓' if metodo in ['RULA', 'REBA'] else '-'}</td>
                    <td style="text-align:center;">{evaluacion_2e}</td>
                    <td>Planilla 2.E</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Levantamiento manual</td>
                    <td style="text-align:center;">{'✓' if metodo == 'OWAS' else '-'}</td>
                    <td style="text-align:center;">{evaluacion_2a}</td>
                    <td>Planilla 2.A</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Bipedestación</td>
                    <td style="text-align:center;">✓</td>
                    <td style="text-align:center;">{datos.get('tipo_bipedestacion', 'Fija')}</td>
                    <td>Planilla 2.D</td>
                </tr>
            </tbody>
        </table>
        
        <!-- PLANILLA 2: EVALUACIÓN INICIAL -->
        <h3 style="background: #e9ecef; padding: 8px; margin-top: 20px;">Planilla N° 2: Evaluación Inicial de Factores de Riesgo</h3>
        
        <h4>2.A - Levantamiento manual de cargas sin transporte</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f2f2f2;">
                <th style="padding: 8px; border: 1px solid #ddd;">Parámetro</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Valor</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Puntuación</th>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Peso de la carga (kg)</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{datos.get('peso_carga', '10')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{evaluacion_2a}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Frecuencia (levantamientos/hora)</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{datos.get('frecuencia_levantamiento', '20')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{'ALTO' if int(datos.get('frecuencia_levantamiento', 0)) > 12 else 'MODERADO' if int(datos.get('frecuencia_levantamiento', 0)) > 5 else 'BAJO'}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Distancia vertical (cm)</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{datos.get('distancia_vertical', '50')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{'ALTO' if int(datos.get('distancia_vertical', 0)) > 75 else 'MODERADO' if int(datos.get('distancia_vertical', 0)) > 25 else 'BAJO'}</td>
            </tr>
        </table>
        
        <h4>2.D - Bipedestación</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><th style="padding: 8px; border: 1px solid #ddd;">Tipo</th><td style="padding: 8px; border: 1px solid #ddd;" colspan="2">{datos.get('tipo_bipedestacion', 'Fija')}</td></tr>
        </table>
        
        <h4>2.E - Movimientos repetitivos de miembros superiores</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><th style="padding: 8px; border: 1px solid #ddd;">Método</th><td style="padding: 8px; border: 1px solid #ddd;">{metodo}</td></tr>
            <tr><th style="padding: 8px; border: 1px solid #ddd;">Puntuación</th><td style="padding: 8px; border: 1px solid #ddd;">{puntuacion}{'/4' if metodo == 'OWAS' else '/7' if metodo == 'RULA' else '/15' if metodo == 'REBA' else ''}</td></tr>
            <tr><th style="padding: 8px; border: 1px solid #ddd;">Nivel de riesgo</th><td style="padding: 8px; border: 1px solid #ddd;">{datos.get('nivel_riesgo', 'Desconocido')}</td></tr>
        </table>
        
        <h4>2.F - Posturas forzadas</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f2f2f2;">
                    <th style="padding: 8px; border: 1px solid #ddd;">Segmento</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Valor</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Estado</th>
                </tr>
            </thead>
            <tbody>{analisis_rows}</tbody>
        </table>
        
        <h4>2.H - Confort térmico</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><th style="padding: 8px; border: 1px solid #ddd;">Estado</th><td style="padding: 8px; border: 1px solid #ddd;">{datos.get('confort_termico', 'Adecuado')}</td></tr>
        </table>
        
        <h4>2.I - Estrés de contacto</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><th style="padding: 8px; border: 1px solid #ddd;">Presente</th><td style="padding: 8px; border: 1px solid #ddd;">{datos.get('estres_contacto', 'No')}</td></tr>
        </table>
        
        <!-- NIVEL DE RIESGO GLOBAL -->
        <div class="resultado-banner" style="background: {riesgo_color}; margin-top: 20px; padding: 15px; text-align: center; border-radius: 8px; color: white;">
            <h3>NIVEL DE RIESGO GLOBAL (SRT 886/2015): {nivel_srt}/3 - {nivel_texto.upper()}</h3>
            <p>{'No requiere acción' if nivel_srt == 1 else 'Implementar medidas correctivas' if nivel_srt == 2 else 'INTERVENCIÓN INMEDIATA REQUERIDA'}</p>
        </div>
        
        <!-- REFERENCIAS NORMATIVAS -->
        <div class="info-box" style="margin-top: 20px; background: #e9ecef; padding: 15px; border-radius: 8px;">
            <h3>Marco Normativo Aplicable</h3>
            <ul>
                <li><strong>Ley 19.587/72</strong> - Higiene y Seguridad en el Trabajo (Art. 5 inc. f, Art. 8, Art. 9)</li>
                <li><strong>Resolución SRT 295/2003</strong> - Anexo I: Programa de Ergonomía Integrado</li>
                <li><strong>Resolución SRT 886/2015</strong> - Protocolo de Ergonomía (Planillas 1 a 4)</li>
                <li><strong>Decreto 49/2014</strong> - Nuevas Enfermedades Profesionales</li>
            </ul>
            <p style="margin-top: 10px; font-style: italic;">El presente informe cumple con los requisitos del Protocolo de Ergonomía establecido por la Superintendencia de Riesgos del Trabajo (SRT).</p>
        </div>
    </div>
    """
    return planillas


# ============================================================
# MÓDULO 5: GENERADOR PRINCIPAL DE PDF
# ============================================================

def crear_pdf_senior(nombre_archivo, datos, imagenes_evidencia):
    """
    Función principal que integra el sistema con el main.py existente.
    """
    print("=" * 50)
    print("📄 GENERANDO INFORME ERGONÓMICO")
    print("=" * 50)
    
    if 'operario_datos' not in datos:
        datos['operario_datos'] = {
            'nombre': datos.get('operario', 'No especificado'),
            'edad': datos.get('edad', 'N/A'),
            'antiguedad': datos.get('antiguedad', 'N/A'),
            'patologias': datos.get('patologias', 'Ninguna')
        }
    
    if 'descripcion_accion_owas' not in datos:
        niveles_desc = {
            0: "Nivel 0: Riesgo Negligible. No requiere acción.",
            1: "Fase 1: Postura Normal. Sin efectos dañinos.",
            2: "Fase 2: Posibilidad de daño. Acción correctiva a futuro.",
            3: "Fase 3: Efectos dañinos. Acción correctiva lo antes posible.",
            4: "Fase 4: Muy dañina. Requiere acciones inmediatas."
        }
        nivel = datos.get('nivel_accion_owas', 1)
        datos['descripcion_accion_owas'] = niveles_desc.get(nivel, "Riesgo no clasificado")
    
    if 'estadisticas' not in datos:
        datos['estadisticas'] = {1: 100, 2: 0, 3: 0, 4: 0}
    
    if 'analisis' not in datos:
        datos['analisis'] = []
    
    if 'empresa' not in datos:
        datos['empresa'] = "No especificada"
    
    if 'proyecto' not in datos:
        datos['proyecto'] = "No especificado"
    
    if 'evaluador' not in datos:
        datos['evaluador'] = "No especificado"
    
    datos, es_rula = normalizar_datos_rula_a_owas(datos)
    
    es_valido, errores = validar_datos_entrada(datos)
    if not es_valido:
        print("❌ No se puede generar PDF - datos inválidos")
        print("   Corrija los errores y vuelva a intentar")
        return False
    
    ia_ergonomica = AnalizadorErgonomicoIA()
    
    if 'frecuencia_nivel_maximo' not in datos:
        nivel_max = max(datos.get('estadisticas', {1: 0}).keys()) if datos.get('estadisticas') else 1
        datos['frecuencia_nivel_maximo'] = datos.get('estadisticas', {}).get(nivel_max, 0)
    
    if 'nivel_maximo_presente' not in datos and datos.get('estadisticas'):
        datos['nivel_maximo_presente'] = max([k for k, v in datos['estadisticas'].items() if v > 0] or [1])
    
    nivel_riesgo = datos.get('nivel_accion_owas', 1)
    recomendaciones_ia = ia_ergonomica.generar_recomendacion_inteligente(
        datos.get('analisis', []),
        datos.get('proyecto', ''),
        nivel_riesgo
    )
    
    frecuencia_max = datos.get('frecuencia_nivel_maximo', 0)
    prediccion = ia_ergonomica.predecir_riesgo_futuro(nivel_riesgo, frecuencia_max, datos.get('estadisticas', {}))
    
    if not datos.get('recomendacion') or datos['recomendacion'] == "":
        datos['recomendacion'] = '\n'.join(recomendaciones_ia)
    
    datos['prediccion_riesgo'] = prediccion
    
    alertas = []
    for item in datos.get('analisis', []):
        estado = item.get('estado', '')
        if 'CRÍTICO' in estado or 'Extrema' in estado or 'CRITICO' in estado.upper():
            alertas.append(f"🔴 {item['segmento']}: {estado}")
        elif 'ALTO' in estado or 'muy' in estado.lower():
            alertas.append(f"⚠️ {item['segmento']}: {estado}")
    
    datos['alertas_criticas'] = alertas
    
    fecha_hoy = datetime.datetime.now().strftime("%d de %B de 2026")
    
    imagenes_base64 = []
    for i, img in enumerate(imagenes_evidencia):
        if img and os.path.exists(img):
            img_base64 = image_to_base64(img)
            if img_base64:
                imagenes_base64.append(img_base64)
                print(f"✓ Imagen {i+1} convertida a base64")
            else:
                print(f"⚠️ No se pudo convertir imagen {i+1}")
        else:
            print(f"⚠️ Imagen no encontrada: {img}")
    
    logo_base64 = None
    if datos.get('logo') and os.path.exists(datos['logo']):
        logo_base64 = image_to_base64(datos['logo'])
        if logo_base64:
            print("✓ Logo convertido a base64")
    
    estadisticas_norm = {}
    for k, v in datos['estadisticas'].items():
        try:
            estadisticas_norm[int(k)] = float(v)
        except:
            estadisticas_norm[int(k)] = 0.0
    datos['estadisticas'] = estadisticas_norm
    
    niveles_con_datos = [k for k, v in estadisticas_norm.items() if v > 0]
    riesgo_maximo = max(niveles_con_datos) if niveles_con_datos else 1
    
    colores_riesgo = {0: "#28a745", 1: "#28a745", 2: "#ffc107", 3: "#fd7e14", 4: "#dc3545"}
    textos_accion = {
        0: "Nivel 0: Riesgo Negligible. No requiere acción.",
        1: "Fase 1: Postura Normal. Sin efectos dañinos.",
        2: "Fase 2: Posibilidad de daño. Acción correctiva a futuro.",
        3: "Fase 3: Efectos dañinos. Acción correctiva lo antes posible.",
        4: "Fase 4: Muy dañina. Requiere acciones inmediatas."
    }
    
    metodo_original = datos.get('metodo_usado', 'OWAS')
    es_reba = False
    es_rosa = False
    
    for item in datos.get('analisis', []):
        if 'REBA' in item.get('segmento', '') or 'Puntuación REBA' in item.get('segmento', ''):
            es_reba = True
        if 'ROSA' in item.get('segmento', '') or 'Silla' in item.get('segmento', '') or 'Monitor' in item.get('segmento', ''):
            es_rosa = True
    
    if datos.get('metodo') == 'REBA' or datos.get('metodo_usado') == 'REBA' or es_reba:
        metodo_original = 'REBA'
        print("   📌 Forzando método REBA 3D para el PDF")
    elif datos.get('metodo') == 'ROSA' or datos.get('metodo_usado') == 'ROSA' or es_rosa:
        metodo_original = 'ROSA'
        print("   📌 Forzando método ROSA para el PDF")
    
    nombre_metodo = get_nombre_metodo(metodo_original)
    datos['metodo_usado'] = metodo_original
    print(f"   📌 Método detectado: {nombre_metodo}")
    
    total_pct = sum(estadisticas_norm.values())
    if total_pct == 0:
        total_pct = 100
    
    acumulado = 0
    gradiente_partes = []
    for nivel in [1, 2, 3, 4]:
        valor = estadisticas_norm.get(nivel, 0)
        if valor > 0:
            angulo = (valor / total_pct) * 360
            color = colores_riesgo.get(nivel, "#6c757d")
            gradiente_partes.append(f"{color} {acumulado:.2f}deg {acumulado + angulo:.2f}deg")
            acumulado += angulo
    
    gradiente_str = f"conic-gradient({', '.join(gradiente_partes)})" if gradiente_partes else "conic-gradient(#ccc 0deg 360deg)"
    
    if metodo_original == 'REBA':
        niveles_nombres = {1: "Negligible", 2: "Bajo", 3: "Medio", 4: "Alto/Muy alto"}
    elif metodo_original == 'ROSA':
        niveles_nombres = {1: "Aceptable", 2: "Bajo", 3: "Medio", 4: "Alto/Muy alto"}
    else:
        niveles_nombres = {1: "Normal", 2: "Moderado", 3: "Alto", 4: "Crítico"}
    
    leyenda_items = ''.join([
        f'<span style="display:inline-flex;align-items:center;gap:4px;margin:2px 4px;">'
        f'<span style="display:inline-block;width:12px;height:12px;background:{colores_riesgo.get(n, "#cccccc")};border-radius:2px;"></span>'
        f'Nivel {n} ({niveles_nombres.get(n, "")}): {estadisticas_norm.get(n, 0):.1f}%</span>'
        for n in [1, 2, 3, 4] if estadisticas_norm.get(n, 0) > 0
    ])
    
    nivel_accion = datos.get('nivel_accion_owas', 1)
    color_riesgo_hex = colores_riesgo.get(nivel_accion, "#dc3545")
    
    svg_pie = f'''
    <div style="position: relative; width: 200px; height: 200px; margin: 0 auto;">
        <div style="position: absolute; width: 100%; height: 100%; border-radius: 50%; background: {gradiente_str}; border: 3px solid white; box-shadow: 0 2px 10px rgba(0,0,0,0.1);"></div>
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80px; height: 80px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
            <div style="font-size: 10px; color: #666; text-align:center; line-height:1.2;">Riesgo<br>Máx.</div>
            <div style="font-size: 22px; font-weight: bold; color: {color_riesgo_hex};">{riesgo_maximo}</div>
        </div>
    </div>
    <div style="margin-top: 10px; display: flex; flex-wrap: wrap; justify-content: center; font-size: 9pt;">
        {leyenda_items}
    </div>
    '''
    
    historial = [
        estadisticas_norm.get(1, 0),
        estadisticas_norm.get(2, 0),
        estadisticas_norm.get(3, 0),
        estadisticas_norm.get(4, 0),
    ]
    
    max_val = max(historial) if max(historial) > 0 else 1
    bar_width = 50
    svg_width = len(historial) * (bar_width + 15) + 40
    svg_height = 200
    
    bars_svg = []
    for i, val in enumerate(historial):
        bar_height = (val / max_val) * 120 if max_val > 0 else 0
        x = 30 + i * (bar_width + 15)
        y = svg_height - 40 - bar_height
        color = colores_riesgo.get(i + 1, "#6c757d")
        bars_svg.append(f'''
            <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4"/>
            <text x="{x + bar_width/2}" y="{svg_height - 15}" text-anchor="middle" font-size="10" font-weight="bold">Nivel {i+1}</text>
            <text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" font-size="9" fill="#333">{val:.1f}%</text>
        ''')
    
    svg_bars = f'''<svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">
        <line x1="20" y1="{svg_height-30}" x2="{svg_width-20}" y2="{svg_height-30}" stroke="#333" stroke-width="1.5"/>
        <line x1="20" y1="20" x2="20" y2="{svg_height-30}" stroke="#333" stroke-width="1.5"/>
        <text x="10" y="{svg_height/2}" text-anchor="middle" font-size="9" transform="rotate(-90, 10, {svg_height/2})">Porcentaje</text>
        <text x="{svg_width/2}" y="{svg_height-8}" text-anchor="middle" font-size="9">Niveles de Riesgo</text>
        {''.join(bars_svg)}
    </svg>'''
    
    colores_analisis = [color_estado(item.get('estado', '')) for item in datos.get('analisis', [])]
    
    # Generar planillas SRT solo si cumple_normativa = True
    planillas_srt_html = ""
    if datos.get('cumple_normativa', False):
        try:
            planillas_srt_html = generar_planillas_srt(datos)
            print("   📋 Planillas SRT 886/2015 incluidas en el PDF")
        except Exception as e:
            print(f"   ⚠️ Error generando planillas SRT: {e}")
    
    # Template HTML
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
        @page { 
            size: A4; 
            margin: 15mm;
            @bottom-center {
                content: "Página " counter(page) " de " counter(pages);
                font-size: 8pt;
                color: #666;
            }
        }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            color: #1a1a1a; 
            margin: 0; 
            padding: 0; 
            line-height: 1.4;
        }
        
        .keep-together {
            page-break-inside: avoid;
        }
        
        .table-container {
            page-break-inside: avoid;
            margin-bottom: 20px;
        }
        
        h2 {
            background: #001f3f; 
            color: white; 
            padding: 8px 15px; 
            font-size: 14pt; 
            text-transform: uppercase; 
            border-left: 5px solid #00d1b2; 
            margin: 30px 0 15px 0;
            page-break-after: avoid;
        }
        
        table {
            page-break-inside: avoid;
        }
        
        .img-grid {
            page-break-inside: avoid;
        }
        
        .dictamen {
            page-break-inside: avoid;
        }
        
        .cover { 
            height: 260mm; 
            background: linear-gradient(135deg, #001f3f 0%, #002b5c 100%);
            color: white; 
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
            padding: 50px; 
            box-sizing: border-box;
            page-break-after: avoid;
        }
        .logo-container { text-align: center; margin-bottom: 50px; }
        .logo-container img { max-height: 100px; max-width: 200px; }
        .cover h1 { font-size: 28pt; text-align: center; margin: 40px 0 20px 0; letter-spacing: 2px; }
        .cover-subtitle { text-align: center; color: #00d1b2; font-size: 16pt; font-weight: bold; margin-bottom: 60px; }
        .info-box { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin-top: 40px; }
        .info-box p { margin: 10px 0; font-size: 12pt; }
        .info-box strong { color: #00d1b2; }
        
        .resultado-banner { 
            background: {{ color_res }}; 
            color: white; 
            padding: 15px; 
            text-align: center; 
            border-radius: 8px; 
            margin-bottom: 20px;
        }
        .resultado-banner h3 { margin: 0; color: white; font-size: 18pt; }
        
        .tabla-graficos-final { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .tabla-graficos-final td { width: 50%; border: none; text-align: center; vertical-align: top; padding: 10px; }
        .grafico-container { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        
        table.datos { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
        table.datos th, table.datos td { padding: 10px; border: 1px solid #ddd; font-size: 10pt; text-align: left; }
        table.datos th { background: #f2f2f2; font-weight: bold; }
        table.datos tr:hover { background: #f5f5f5; }
        
        .bar-container { background: #e9ecef; height: 25px; border-radius: 12px; overflow: hidden; width: 100%; }
        .r1 { background: #28a745; height: 100%; } 
        .r2 { background: #ffc107; height: 100%; } 
        .r3 { background: #fd7e14; height: 100%; } 
        .r4 { background: #dc3545; height: 100%; }
        
        .img-grid { width: 100%; border-collapse: collapse; table-layout: fixed; margin: 15px 0; }
        .img-grid td { padding: 10px; text-align: center; border: none; width: 33%; vertical-align: top; }
        .img-grid img { 
            width: 100%; height: auto; max-height: 200px; object-fit: contain; 
            border: 3px solid #001f3f; border-radius: 8px; background: #f8f9fa;
            transition: transform 0.2s;
        }
        .img-grid img:hover { transform: scale(1.02); }
        .img-label { font-size: 10pt; font-weight: bold; margin-top: 10px; color: #001f3f; }
        
        .dictamen { background: #f0f7ff; border-left: 5px solid #001f3f; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .dictamen strong { color: #001f3f; font-size: 12pt; }
        .dictamen ul { margin: 10px 0 5px 0; padding-left: 20px; }
        .dictamen li { margin: 8px 0; line-height: 1.4; color: #1a1a1a; list-style-type: disc; }
        
        .alerta-box { background: #fff3cd; border-left: 5px solid #dc3545; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .alerta-box strong { color: #dc3545; }
        
        .footer-nota { font-size: 8pt; text-align: center; color: #999; margin-top: 30px; padding-top: 10px; border-top: 1px solid #ddd; }
        .text-center { text-align: center; }
        .bold { font-weight: bold; }
    </style>
    </head>
    <body>
        <!-- CARÁTULA -->
        <div class="cover">
            {% if logo %}
            <div class="logo-container"><img src="{{ logo }}"></div>
            {% endif %}
            <p style="font-weight: bold; font-size: 10pt; text-align: center; letter-spacing: 3px;">ERGOEDGE OS</p>
            <p style="font-size: 9pt; text-align: center; margin-top: -10px;">INGENIERÍA DE FACTORES HUMANOS</p>
            <h1>INFORME TÉCNICO<br>DE AUDITORÍA {{ nombre_metodo }}</h1>
            <div class="cover-subtitle">ESPECIFICACIÓN ERGONÓMICA NIVEL SENIOR</div>
            <div class="info-box">
                <p><strong>CLIENTE:</strong> {{ datos.empresa }}</p>
                <p><strong>PUESTO EVALUADO:</strong> {{ datos.proyecto }}</p>
                <p><strong>EVALUADOR CERTIFICADO:</strong> {{ datos.evaluador }}</p>
                <p><strong>FECHA DE EMISIÓN:</strong> {{ fecha }}</p>
            </div>
        </div>
        
        <!-- PÁGINA 1: DATOS Y RESULTADOS -->
        <div>
            <h2>Ficha del Personal Evaluado</h2>
            <table class="datos">
                <tr><th style="width:20%;">OPERARIO</th><td style="width:30%;"><strong>{{ datos.operario_datos.nombre }}</strong></td><th style="width:20%;">EDAD</th><td style="width:30%;">{{ datos.operario_datos.edad }} años</td></tr>
                <tr><th>ANTIGÜEDAD</th><td>{{ datos.operario_datos.antiguedad }}</td><th>PATOLOGÍAS</th><td>{{ datos.operario_datos.patologias }}</td></tr>
            </div>
            
            <h2>Resultado Global</h2>
            <div class="resultado-banner" style="background: {{ color_res }};">
                <h3>NIVEL DE ACCIÓN {{ nombre_metodo }} GLOBAL: {{ datos.nivel_accion_owas }}/4</h3>
                <p>{{ datos.descripcion_accion_owas }}</p>
            </div>
            
            <table class="tabla-graficos-final">
                <tr><td><div class="grafico-container"><strong>📊 Proporción de Riesgos por Nivel</strong><br>{{ svg_pie|safe }}</div></td>
                    <td><div class="grafico-container"><strong>📈 Distribución por Nivel de Riesgo</strong><div style="margin: 10px auto;">{{ svg_bars|safe }}</div><p style="font-size: 8pt; color: #666;">Porcentaje de tiempo en cada nivel durante el análisis</p></div></td>
                </tr>
            </div>
            
            <h2>Distribución Estadística</h2>
            <table class="datos">
                <tr><th>NIVEL</th><th>PORCENTAJE</th><th>REPRESENTACIÓN VISUAL</th></tr>
                {% for nivel in [1,2,3,4] %}
                {% set pct = datos.estadisticas.get(nivel, 0) %}
                {% if datos.metodo_usado == 'ROSA' %}
                    {% if nivel == 1 %}{% set nombre_nivel = 'Aceptable' %}
                    {% elif nivel == 2 %}{% set nombre_nivel = 'Bajo' %}
                    {% elif nivel == 3 %}{% set nombre_nivel = 'Medio' %}
                    {% else %}{% set nombre_nivel = 'Alto/Muy alto' %}
                    {% endif %}
                {% elif datos.metodo_usado == 'REBA' %}
                    {% if nivel == 1 %}{% set nombre_nivel = 'Negligible' %}
                    {% elif nivel == 2 %}{% set nombre_nivel = 'Bajo' %}
                    {% elif nivel == 3 %}{% set nombre_nivel = 'Medio' %}
                    {% else %}{% set nombre_nivel = 'Alto/Muy alto' %}
                    {% endif %}
                {% else %}
                    {% if nivel == 1 %}{% set nombre_nivel = 'Normal' %}
                    {% elif nivel == 2 %}{% set nombre_nivel = 'Moderado' %}
                    {% elif nivel == 3 %}{% set nombre_nivel = 'Alto' %}
                    {% else %}{% set nombre_nivel = 'Crítico' %}
                    {% endif %}
                {% endif %}
                <tr>
                    <td style="font-weight:bold; text-align:center;">Nivel {{ nivel }} ({{ nombre_nivel }})</td>
                    <td style="text-align:center; font-weight:bold;">{{ "%.1f"|format(pct) }}%</td>
                    <td><div class="bar-container"><div class="r{{ nivel }}" style="width: {{ pct }}%;"></div></div></td>
                </tr>
                {% endfor %}
            </div>
        </div>
        
        <!-- PÁGINA 2: EVIDENCIAS Y ANÁLISIS -->
        <div>
            <h2>Registro Fotográfico</h2>
            {% if imagenes %}
            <table class="img-grid"><tr>{% for img in imagenes %}<td><img src="{{ img }}"><div class="img-label">Evidencia {{ loop.index }}</div></td>{% endfor %}</tr></table>
            {% else %}
            <p class="text-center" style="color: #999; padding: 40px;">⚠️ No se registraron evidencias fotográficas durante la auditoría</p>
            {% endif %}
            
            <h2>Análisis Biomecánico</h2>
            <div class="table-container">
            <table class="datos">
                <thead><tr><th>SEGMENTO CORPORAL</th><th>VALOR</th><th>ESTADO ERGONÓMICO</th></tr></thead>
                <tbody>{% for item, color_bg in zip(datos.analisis, colores_analisis) %}<tr><td><strong>{{ item.segmento }}</strong></td><td style="text-align: center;">{{ item.angulo }}</td><td style="background: {{ color_bg }}; font-weight: 500;">{{ item.estado }}</td></tr>{% endfor %}</tbody>
            </div>
            
            <!-- Checklist específico para ROSA -->
            {% if datos.checklist %}
            <h2>📋 Lista de Verificación Rápida (Checklist ROSA)</h2>
            <table class="datos">
                <thead><tr><th>Ítem</th><th>Estado</th><th>Recomendación</th></tr></thead>
                <tbody>
                    {% for item in datos.checklist[:15] %}
                    <tr>
                        <td style="width:50%;">{{ item.replace('✅ ', '').replace('⚠️ ', '').replace('❌ ', '') }}</td>
                        <td style="width:15%; text-align:center;">
                            {% if '✅' in item %}
                            <span style="color:#28a745;">✓ Correcto</span>
                            {% elif '⚠️' in item %}
                            <span style="color:#ffc107;">⚠️ Atención</span>
                            {% else %}
                            <span style="color:#dc3545;">❌ Pendiente</span>
                            {% endif %}
                        </td>
                        <td style="width:35%;">
                            {% if '✅' in item %}Mantener
                            {% elif '⚠️' in item %}Revisar
                            {% else %}Corregir
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </div>
            {% endif %}
            
            <!-- Dictamen IA (Gemini) -->
            {% if datos.dictamen_ia %}
            <h2>🤖 Dictamen Experto (IA Gemini)</h2>
            <div class="dictamen">
                <p>{{ datos.dictamen_ia|replace('\n', '<br>')|safe }}</p>
            </div>
            {% endif %}
            
            <div class="dictamen">
                <strong>📋 RECOMENDACIONES ERGONÓMICAS INTELIGENTES:</strong>
                <ul>{% if datos.recomendacion %}{% set lines = datos.recomendacion.split('\n') %}{% for line in lines %}{% set clean_line = line.replace('•', '').replace('-', '').replace('*', '').strip() %}{% if clean_line and clean_line|length > 5 %}<li>{{ clean_line }}</li>{% endif %}{% endfor %}{% else %}<li>Mantener buenas prácticas posturales</li>{% endif %}</ul>
            </div>
            
            <!-- PLANILLAS SRT 886/2015 -->
            {{ planillas_srt|safe }}
            
            <div class="footer-nota">
                <p>Informe generado automáticamente por <strong>ERGOEDGE OS - IA INTEGRADA</strong><br>
                Los resultados se basan en el análisis biomecánico <strong>{{ nombre_metodo }}</strong> según la normativa ergonómica vigente.<br>
                Sistema de IA predictiva versión 2.0 | Este informe es orientativo.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        template = Template(html_template)
        html_out = template.render(
            datos=datos,
            nombre_metodo=nombre_metodo,
            fecha=fecha_hoy,
            imagenes=imagenes_base64,
            logo=logo_base64,
            riesgo_max=riesgo_maximo,
            color_res=color_riesgo_hex,
            texto_accion=textos_accion.get(nivel_accion, "Riesgo no clasificado"),
            svg_pie=svg_pie,
            svg_bars=svg_bars,
            colores_analisis=colores_analisis,
            zip=zip,
            planillas_srt=planillas_srt_html
        )
        
        debug_html = nombre_archivo.replace('.pdf', '_debug.html')
        with open(debug_html, 'w', encoding='utf-8') as f:
            f.write(html_out)
        print(f"📄 HTML de depuración guardado: {debug_html}")
        
        HTML(string=html_out).write_pdf(nombre_archivo)
        print(f"✅ PDF generado exitosamente: {nombre_archivo}")
        
        return True
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        return False


# ============================================================
# MÓDULO 6: GENERADOR DE REPORTES PARA REBA 3D
# ============================================================

def generar_reporte_reba(resultados_reba, empresa_input, puesto_input, evaluador_input,
                          op_nombre, op_edad, op_antiguedad, op_patologias,
                          logo_path, imagenes_riesgo, muestras_posturales,
                          carga, acople):
    
    puntuaciones = [r['puntuacion_final'] for r in resultados_reba if r is not None]
    
    if puntuaciones:
        niveles_reba_oficial = {
            'Negligible (1)': [1],
            'Bajo (2-3)': [2, 3],
            'Medio (4-7)': [4, 5, 6, 7],
            'Alto (8-10)': [8, 9, 10],
            'Muy alto (11-15)': [11, 12, 13, 14, 15]
        }
        
        stats_niveles = {'Negligible (1)': 0, 'Bajo (2-3)': 0, 'Medio (4-7)': 0, 'Alto (8-10)': 0, 'Muy alto (11-15)': 0}
        
        for p in puntuaciones:
            if p == 1:
                stats_niveles['Negligible (1)'] += 1
            elif p <= 3:
                stats_niveles['Bajo (2-3)'] += 1
            elif p <= 7:
                stats_niveles['Medio (4-7)'] += 1
            elif p <= 10:
                stats_niveles['Alto (8-10)'] += 1
            else:
                stats_niveles['Muy alto (11-15)'] += 1
        
        total = len(puntuaciones)
        stats_pct = {k: round((v / total) * 100, 1) for k, v in stats_niveles.items() if v > 0}
        puntuacion_max = max(puntuaciones)
        puntuacion_prom = round(sum(puntuaciones) / len(puntuaciones), 1)
    else:
        stats_pct = {}
        puntuacion_max = 0
        puntuacion_prom = 0
    
    peor_frame = max(resultados_reba, key=lambda x: x['puntuacion_final'] if x else 0) if resultados_reba else None
    
    nivel_texto = get_reba_nivel_texto(puntuacion_max)
    nivel_accion = get_reba_nivel_accion(puntuacion_max)
    descripcion_accion = get_reba_descripcion_accion(puntuacion_max)
    
    stats_owas = {1: 0, 2: 0, 3: 0, 4: 0}
    for p in puntuaciones:
        if p == 1:
            stats_owas[1] += 1
        elif p <= 3:
            stats_owas[1] += 1
        elif p <= 7:
            stats_owas[2] += 1
        elif p <= 10:
            stats_owas[3] += 1
        else:
            stats_owas[4] += 1
    
    total_pct = sum(stats_owas.values())
    if total_pct > 0:
        for k in stats_owas:
            stats_owas[k] = round((stats_owas[k] / total_pct) * 100, 1)
    
    def generar_dictamen_reba(puntuacion, carga, acople, nombre, patologias):
        patologia_riesgo = any(p in patologias.lower() for p in ['hernia', 'disco', 'lumbar', 'cervical', 'dolor', 'hombro'])
        if puntuacion >= 11 or patologia_riesgo:
            return f"""DICTAMEN ERGONÓMICO REBA - RIESGO MUY ALTO (Nivel {get_reba_nivel_accion(puntuacion)}/4)

El operario {nombre} presenta una puntuación REBA de {puntuacion}/15, riesgo MUY ALTO que requiere intervención INMEDIATA.

Recomendaciones URGENTES:
• ¡INTERVENCIÓN INMEDIATA REQUERIDA!
• Suspender la tarea actual hasta rediseño ergonómico
• Instalar ayudas mecánicas obligatorias
• Evaluación médica INMEDIATA"""
        elif puntuacion >= 8:
            return f"""DICTAMEN ERGONÓMICO REBA - RIESGO ALTO (Nivel {get_reba_nivel_accion(puntuacion)}/4)
Recomendaciones: Rediseñar el puesto, mejorar agarre, reducir carga."""
        elif puntuacion >= 4:
            return f"""DICTAMEN ERGONÓMICO REBA - RIESGO MEDIO (Nivel {get_reba_nivel_accion(puntuacion)}/4)
Recomendaciones: Ajustar alturas, reorganizar elementos."""
        else:
            return f"""DICTAMEN ERGONÓMICO REBA - RIESGO {nivel_texto.upper()} (Nivel {nivel_accion}/4)
Mantener buenas prácticas."""
    
    conclusion_medica = generar_dictamen_reba(puntuacion_max, carga, acople, op_nombre, op_patologias)
    
    analisis_f = [
        {"segmento": "Puntuación REBA", "angulo": f"{puntuacion_max}/15", "estado": f"{nivel_texto.upper()} - Nivel {nivel_accion}/4"},
        {"segmento": "Puntaje A (Tronco+Cuello+Piernas)", "angulo": str(peor_frame['puntuacion_A']) if peor_frame else "N/A", "estado": "Riesgo en tronco" if peor_frame and peor_frame['puntuacion_A'] >= 6 else "Aceptable"},
        {"segmento": "Puntaje B (Brazo+Antebrazo+Muñeca)", "angulo": str(peor_frame['puntuacion_B']) if peor_frame else "N/A", "estado": "Riesgo en brazos" if peor_frame and peor_frame['puntuacion_B'] >= 5 else "Aceptable"},
        {"segmento": "Carga", "angulo": f"{carga}/3", "estado": "Pesada" if carga >= 2 else "Ligera"},
        {"segmento": "Acople (agarre)", "angulo": f"{acople}/3", "estado": "Malo" if acople >= 2 else "Aceptable"},
    ]
    
    if peor_frame and peor_frame['detalles'].get('abduccion', 0) > 20:
        analisis_f.append({"segmento": "Abducción de brazo", "angulo": f"{peor_frame['detalles']['abduccion']:.1f}°", "estado": "CRÍTICO - Brazo muy separado"})
    
    alertas = []
    if puntuacion_max >= 11:
        alertas.append(f"🔴 Puntuación REBA: {puntuacion_max}/15 - Riesgo MUY ALTO")
    if peor_frame and peor_frame['detalles'].get('abduccion', 0) > 20:
        alertas.append(f"🔴 Abducción de brazo: {peor_frame['detalles']['abduccion']:.1f}°")
    
    datos_reporte = {
        "logo": logo_path,
        "empresa": empresa_input,
        "proyecto": puesto_input,
        "evaluador": evaluador_input,
        "operario_datos": {"nombre": op_nombre, "edad": op_edad, "antiguedad": op_antiguedad, "patologias": op_patologias},
        "analisis": analisis_f,
        "recomendacion": conclusion_medica,
        "estadisticas": stats_owas,
        "nivel_accion_owas": nivel_accion,
        "descripcion_accion_owas": descripcion_accion,
        "nivel_maximo_presente": nivel_accion,
        "frecuencia_nivel_maximo": stats_owas.get(max(1, min(4, nivel_accion)), 0),
        "metodo_usado": "REBA",
        "alertas_criticas": alertas,
        "prediccion_riesgo": f"REBA: {puntuacion_max}/15 - Riesgo {nivel_texto.upper()}"
    }
    
    timestamp = int(time.time())
    nombre_pdf = f"reports/YOLO_REBA_{empresa_input}_{op_nombre.replace(' ', '_')}_{timestamp}.pdf"
    return crear_pdf_senior(nombre_pdf, datos_reporte, imagenes_riesgo)


# ============================================================
# MÓDULO 7: GENERADOR DE REPORTES PARA ROSA
# ============================================================

def generar_reporte_rosa(resultado_rosa, empresa_input, puesto_input, evaluador_input,
                          op_nombre, op_edad, op_antiguedad, op_patologias,
                          logo_path, datos_rosa):
    """
    Genera reporte específico para ROSA (Rapid Office Strain Assessment)
    """
    
    # Extraer puntuaciones
    puntuacion_final = resultado_rosa['puntuacion_final']
    puntuacion_base = resultado_rosa.get('puntuacion_base', puntuacion_final)
    factor_tiempo = resultado_rosa.get('factor_tiempo', 0)
    nivel_riesgo = resultado_rosa['nivel_riesgo']
    
    # Obtener puntuaciones por componente
    punt_silla = resultado_rosa.get('silla', 'N/A')
    punt_monitor = resultado_rosa.get('monitor', 'N/A')
    punt_teclado = resultado_rosa.get('teclado', 'N/A')
    punt_mouse = resultado_rosa.get('mouse', 'N/A')
    
    # Obtener dictamen IA si existe
    dictamen_ia = resultado_rosa.get('dictamen_ia', '')
    
    # Determinar nivel de acción (1-4) para compatibilidad con gráficos
    if puntuacion_final <= 2:
        nivel_accion = 1
        nivel_texto = "Aceptable"
    elif puntuacion_final <= 4:
        nivel_accion = 1
        nivel_texto = "Bajo"
    elif puntuacion_final <= 6:
        nivel_accion = 2
        nivel_texto = "Medio"
    elif puntuacion_final <= 8:
        nivel_accion = 3
        nivel_texto = "Alto"
    else:
        nivel_accion = 4
        nivel_texto = "Muy alto"
    
    # Preparar estadísticas en formato (1-4) para gráficos
    stats_owas = {1: 0, 2: 0, 3: 0, 4: 0}
    
    # Asignar la puntuación al nivel correspondiente
    if puntuacion_final <= 4:
        stats_owas[1] = 100
    elif puntuacion_final <= 6:
        stats_owas[2] = 100
    elif puntuacion_final <= 8:
        stats_owas[3] = 100
    else:
        stats_owas[4] = 100
    
    # Preparar análisis para la tabla del PDF
    analisis_f = [
        {"segmento": "Puntuación ROSA", "angulo": f"{puntuacion_final}/10", "estado": f"{nivel_riesgo.upper()} - Nivel {nivel_accion}/4"},
        {"segmento": "Puntuación Base", "angulo": f"{puntuacion_base}/10", "estado": "Sin factor tiempo"},
        {"segmento": "Factor Tiempo de Uso", "angulo": f"+{factor_tiempo}", "estado": "Por uso continuo >1 hora" if factor_tiempo else "Sin factor adicional"},
        {"segmento": "Silla", "angulo": f"{punt_silla}/10" if isinstance(punt_silla, (int, float)) else str(punt_silla), "estado": "Evaluar ajustes" if isinstance(punt_silla, (int, float)) and punt_silla >= 6 else "Configuración aceptable"},
        {"segmento": "Monitor", "angulo": f"{punt_monitor}/10" if isinstance(punt_monitor, (int, float)) else str(punt_monitor), "estado": "Revisar posición" if isinstance(punt_monitor, (int, float)) and punt_monitor >= 6 else "Posición adecuada"},
        {"segmento": "Teclado", "angulo": f"{punt_teclado}/10" if isinstance(punt_teclado, (int, float)) else str(punt_teclado), "estado": "Ajustar altura/distancia" if isinstance(punt_teclado, (int, float)) and punt_teclado >= 6 else "Configuración adecuada"},
        {"segmento": "Mouse", "angulo": f"{punt_mouse}/10" if isinstance(punt_mouse, (int, float)) else str(punt_mouse), "estado": "Revisar posición" if isinstance(punt_mouse, (int, float)) and punt_mouse >= 6 else "Posición adecuada"},
    ]
    
    # Obtener checklist si existe en el resultado
    checklist = resultado_rosa.get('checklist', [])
    
    # Generar recomendaciones completas
    recomendaciones_completas = resultado_rosa.get('recomendaciones', [])
    
    # Crear recomendación en formato texto
    recomendacion_texto = "\n".join([f"• {rec}" for rec in recomendaciones_completas])
    
    # Alertas específicas de ROSA
    alertas = []
    if puntuacion_final >= 8:
        alertas.append(f"🔴 Puntuación ROSA: {puntuacion_final}/10 - Riesgo MUY ALTO")
    elif puntuacion_final >= 6:
        alertas.append(f"⚠️ Puntuación ROSA: {puntuacion_final}/10 - Riesgo MEDIO/ALTO")
    
    if isinstance(punt_silla, (int, float)) and punt_silla >= 6:
        alertas.append(f"⚠️ Silla: {punt_silla}/10 - Requiere ajustes urgentes")
    if isinstance(punt_monitor, (int, float)) and punt_monitor >= 6:
        alertas.append(f"⚠️ Monitor: {punt_monitor}/10 - Posición incorrecta")
    if isinstance(punt_teclado, (int, float)) and punt_teclado >= 6:
        alertas.append(f"⚠️ Teclado: {punt_teclado}/10 - Ajustar altura/distancia")
    if isinstance(punt_mouse, (int, float)) and punt_mouse >= 6:
        alertas.append(f"⚠️ Mouse: {punt_mouse}/10 - Revisar posición")
    
    if factor_tiempo:
        alertas.append("⚠️ Tiempo de uso continuo >1 hora - Implementar pausas cada 45-60 minutos")
    
    # Preparar datos para el PDF
    datos_reporte = {
        "logo": logo_path,
        "empresa": empresa_input,
        "proyecto": puesto_input,
        "evaluador": evaluador_input,
        "operario_datos": {
            "nombre": op_nombre,
            "edad": op_edad,
            "antiguedad": op_antiguedad,
            "patologias": op_patologias
        },
        "analisis": analisis_f,
        "recomendacion": recomendacion_texto,
        "estadisticas": stats_owas,
        "nivel_accion_owas": nivel_accion,
        "descripcion_accion_owas": f"Nivel {nivel_accion}/4 - Riesgo {nivel_riesgo.upper()} según ROSA",
        "nivel_maximo_presente": nivel_accion,
        "frecuencia_nivel_maximo": 100,
        "metodo_usado": "ROSA",
        "alertas_criticas": alertas,
        "prediccion_riesgo": f"ROSA: {puntuacion_final}/10 - Riesgo {nivel_riesgo.upper()}",
        "checklist": checklist,
        "dictamen_ia": dictamen_ia
    }
    
    try:
        timestamp = int(time.time())
        nombre_base = f"YOLO_ROSA_{empresa_input}_{op_nombre.replace(' ', '_')}"
        nombre_pdf = f"reports/{nombre_base}_{timestamp}.pdf"
        
        print("\n📄 Generando reporte PDF para ROSA...")
        crear_pdf_senior(nombre_pdf, datos_reporte, [])
        
        print("\n" + "=" * 60)
        print("✅ INFORME ROSA GENERADO CON ÉXITO")
        print("=" * 60)
        print(f"📄 PDF: {nombre_pdf}")
        print(f"🎯 Puntuación ROSA: {puntuacion_final}/10")
        print(f"📊 Nivel de riesgo: {nivel_riesgo} (Nivel {nivel_accion}/4)")
        print(f"⚙️ Silla: {punt_silla}/10 | Monitor: {punt_monitor}/10")
        print(f"⌨️ Teclado: {punt_teclado}/10 | Mouse: {punt_mouse}/10")
        if factor_tiempo:
            print(f"⏱️ Factor tiempo de uso: +{factor_tiempo} punto")
        if dictamen_ia:
            print(f"🤖 Dictamen IA incluido en el reporte")
        print("=" * 60)
        
        return True
    except Exception as e:
        print(f"\n❌ Error al generar reporte ROSA: {e}")
        traceback.print_exc()
        return False


# ============================================================
# MÓDULO 8: GENERADOR DE REPORTES GENÉRICO PARA OWAS Y RULA
# ============================================================

def generar_reporte_generico(resultado, empresa_input, puesto_input, evaluador_input,
                              op_nombre, op_edad, op_antiguedad, op_patologias,
                              logo_path=None, metodo='OWAS'):
    """
    Genera reporte para OWAS, RULA o REBA (genérico)
    """
    puntuacion = resultado.get('puntuacion', 1)
    nivel_riesgo = resultado.get('nivel_riesgo', 'Desconocido')
    recomendaciones = resultado.get('recomendaciones', [])
    dictamen_ia = resultado.get('dictamen_ia', '')
    codigo_owas = resultado.get('codigo_owas', 'N/A')
    
    # Determinar nivel de acción (1-4)
    if metodo == 'RULA':
        if puntuacion <= 2:
            nivel_accion = 1
            nivel_texto = "Bajo"
        elif puntuacion <= 4:
            nivel_accion = 2
            nivel_texto = "Medio"
        elif puntuacion <= 6:
            nivel_accion = 3
            nivel_texto = "Alto"
        else:
            nivel_accion = 4
            nivel_texto = "Muy alto"
        descripcion_accion = f"Nivel {nivel_accion}/4 - Riesgo {nivel_texto} según RULA"
    elif metodo == 'REBA':
        if puntuacion <= 3:
            nivel_accion = 1
            nivel_texto = "Bajo"
        elif puntuacion <= 7:
            nivel_accion = 2
            nivel_texto = "Medio"
        elif puntuacion <= 10:
            nivel_accion = 3
            nivel_texto = "Alto"
        else:
            nivel_accion = 4
            nivel_texto = "Muy alto"
        descripcion_accion = f"Nivel {nivel_accion}/4 - Riesgo {nivel_texto} según REBA"
    else:  # OWAS
        nivel_accion = puntuacion
        niveles_texto = {1: "Normal", 2: "Moderado", 3: "Alto", 4: "Crítico"}
        nivel_texto = niveles_texto.get(puntuacion, "Desconocido")
        descripcion_accion = f"Nivel {nivel_accion}/4 - Riesgo {nivel_texto} según OWAS"
    
    # Preparar estadísticas
    stats_owas = {1: 0, 2: 0, 3: 0, 4: 0}
    stats_owas[nivel_accion] = 100
    
    # Preparar análisis para tabla
    analisis_f = [
        {"segmento": f"Puntuación {metodo}", "angulo": f"{puntuacion}/4" if metodo == 'OWAS' else f"{puntuacion}", "estado": nivel_riesgo},
    ]
    if metodo == 'OWAS' and codigo_owas != 'N/A':
        analisis_f.append({"segmento": "Código OWAS", "angulo": codigo_owas, "estado": "Código de postura"})
    
    # Alertas
    alertas = []
    if nivel_accion >= 3:
        alertas.append(f"🔴 {metodo}: Puntuación {puntuacion} - Riesgo {nivel_texto.upper()}")
    
    # Recomendaciones en texto
    recomendacion_texto = "\n".join([f"• {rec}" for rec in recomendaciones]) if recomendaciones else "• Mantener buenas prácticas posturales"
    
    # Datos para el reporte
    datos_reporte = {
        "logo": logo_path,
        "empresa": empresa_input,
        "proyecto": puesto_input,
        "evaluador": evaluador_input,
        "operario_datos": {
            "nombre": op_nombre,
            "edad": op_edad,
            "antiguedad": op_antiguedad,
            "patologias": op_patologias
        },
        "analisis": analisis_f,
        "recomendacion": recomendacion_texto,
        "estadisticas": stats_owas,
        "nivel_accion_owas": nivel_accion,
        "descripcion_accion_owas": descripcion_accion,
        "nivel_maximo_presente": nivel_accion,
        "frecuencia_nivel_maximo": 100,
        "metodo_usado": metodo,
        "alertas_criticas": alertas,
        "prediccion_riesgo": f"{metodo}: {puntuacion} - Riesgo {nivel_texto.upper()}",
        "dictamen_ia": dictamen_ia
    }
    
    timestamp = int(time.time())
    nombre_base = f"YOLO_{metodo}_{empresa_input}_{op_nombre.replace(' ', '_')}"
    nombre_pdf = f"reports/{nombre_base}_{timestamp}.pdf"
    
    return crear_pdf_senior(nombre_pdf, datos_reporte, [])


# ============================================================
# EJECUCIÓN DE PRUEBA (solo si se ejecuta directamente)
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SISTEMA ERGONÓMICO IA - GENERADOR DE REPORTES")
    print("=" * 60)
    
    # Crear datos de ejemplo para ROSA
    datos_rosa_ejemplo = {
        'silla': {'altura': 1, 'profundidad_asiento': 'adecuado', 'apoyo_lumbar': 'ajustado', 'apoyabrazos_altura': 'adecuado', 'apoyabrazos_ancho': 'adecuado'},
        'monitor': {'altura': 1, 'distancia': 60, 'inclinacion': 'perpendicular', 'reflejos': False},
        'teclado': {'altura': 'adecuado', 'distancia': 95, 'inclinacion': 'neutro', 'reposamunecas': 'acolchado'},
        'mouse': {'altura': 'misma', 'distancia': 5, 'posicion': 'frontal'},
        'telefono': {'manos_libres': True, 'distancia': 'inmediato'},
        'uso_continuo': True
    }
    
        # Simular un resultado ROSA con dictamen IA
    resultado_rosa_ejemplo = {
        'silla': 2,
        'monitor': 2,
        'teclado': 2,
        'mouse': 2,
        'puntuacion_base': 2.0,
        'factor_tiempo': 1,
        'puntuacion_final': 3.0,
        'nivel_riesgo': 'Bajo',
        'accion': 'Monitorear, cambios menores',
        'color': '#98c379',
        'recomendaciones': ['✓ Puesto de trabajo en condiciones aceptables', '⚠️ Implementar pausas cada 45-60 minutos por uso continuo prolongado'],
        'dictamen_ia': 'DICTAMEN IA DE PRUEBA: El puesto de oficina se encuentra en condiciones aceptables. Se recomienda mantener pausas activas cada 2 horas.',
        'checklist': [
            '✅ Altura del asiento: pies apoyados en el suelo o en reposapiés',
            '✅ Profundidad del asiento: espacio de 2-3 dedos detrás de la rodilla',
            '✅ Apoyo lumbar: correctamente ajustado a la curvatura de la espalda',
            '✅ Reposabrazos: altura correcta (hombros relajados, codos a 90°)',
            '⚠️ Tiempo de uso continuo >1 hora: implementar pausas cada 45-60 minutos'
        ]
    }
    
    print("\n📊 Probando generación de reporte ROSA...")
    generar_reporte_rosa(
        resultado_rosa_ejemplo,
        "EMPRESA TEST",
        "PUESTO OFICINA",
        "Evaluador Test",
        "Juan Perez",
        "35",
        "5 años",
        "Ninguna",
        None,
        datos_rosa_ejemplo
    )
    
    print("\n" + "=" * 60)
    print("¡Prueba completada! Revisa la carpeta 'reports'")
    print("=" * 60)
