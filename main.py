import cv2
import os
import numpy as np
from ultralytics import YOLO
import datetime
import time
import traceback

# ==== Variables de entorno ====
from dotenv import load_dotenv
load_dotenv()

# --- IMPORTACIONES ---
from clasificador import detectar_metodo_adecuado
from Methods import analizar_owas_completo as analizar_owas
from Methods import crear_pdf_senior as crear_pdf

# --- IMPORTACIÓN RULA ---
from Methods.metodologias.rula import evaluar_rula

# --- IMPORTACIÓN REBA 3D ---
from Methods.metodologias.reba_3d.reba_calculator import RebaCalculator

# --- IMPORTACIÓN ROSA ---
from Methods.metodologias.rosa import evaluar_rosa, recopilar_datos_rosa_interactivo

# ==================== FUNCIONES COMUNES (importadas) ====================
from Methods.comunes import obtener_punto, calcular_angulo_2d, clasificar_riesgo_owas, calcular_torsion_avanzada, detectar_carga_dinamica

# ==================== CONFIGURACIÓN DE GEMINI ====================
import google.generativeai as genai

API_KEY_GEMINI = os.getenv('GEMINI_API_KEY', "AIzaSyBkZ47zhVjrYrDdmZBxFs3GGdAY6ZY198o")
GEMINI_MODEL = "gemini-2.5-flash"


def validar_api_gemini():
    """Valida que la API key de Gemini funcione correctamente"""
    try:
        cliente = genai.Client(api_key=API_KEY_GEMINI)
        print("✅ API Key de Gemini validada correctamente")
        return cliente
    except Exception as e:
        print(f"⚠️ Advertencia: Error con API Key de Gemini: {e}")
        print("   El sistema usará dictamen de respaldo")
        return None


cliente_gemini = validar_api_gemini()


def generar_dictamen_con_gemini(datos_owas, operario):
    """Genera dictamen experto usando Gemini (para OWAS)"""
    if cliente_gemini is None:
        print("⚠️ Gemini no disponible, usando dictamen de respaldo")
        return generar_dictamen_fallback(datos_owas, operario)

    system_instruction = """
Actuás como un Ingeniero Senior en Ergonomía para Mercedes Benz. 
Tu redacción debe fusionar tres corrientes de pensamiento:
1. Alan Hedge (Cornell): Ergonomía predictiva y soluciones tecnológicas.
2. Waldemar Karwowski: Visión de ingeniería de sistemas y diseño industrial.
3. Sebastian Astorino: Marco legal, cumplimiento y salud del trabajador.

REGLAS DE ORO:
- Usar terminología técnica biomecánica (ej: 'momento de fuerza L5-S1', 'abducción acromioclavicular').
- Si el operario tiene patologías (como Hernia de Disco), el dictamen debe ser crítico y protector.
- Proponer cambios de ingeniería, no solo cambios de conducta.
- El dictamen debe ser detallado pero conciso (máximo 400 palabras).
- Usar viñetas (•) para las recomendaciones.
- No usar markdown, solo texto plano.
"""

    user_prompt = f"""
Generá un Dictamen Técnico-Ergonómico basado en estos resultados de evaluación OWAS:

DATOS GENERALES:
- Cliente: {datos_owas['cliente']}
- Puesto evaluado: {datos_owas['proyecto']}
- Fecha: {datos_owas['fecha']}

DATOS DEL OPERARIO:
- Nombre: {operario['nombre']}
- Edad: {operario['edad']} años
- Antigüedad: {operario['antiguedad']} años
- Patologías previas: {operario['patologias'] if operario['patologias'] else 'Ninguna informada'}

RESULTADOS OWAS:
- Código OWAS del peor momento: {datos_owas['codigo_owas']}
- Riesgo máximo: {datos_owas['riesgo_max']}/4
- Distribución de riesgos:
  • Nivel 1 (Normal): {datos_owas['estadisticas'].get(1, 0)}%
  • Nivel 2 (Moderado): {datos_owas['estadisticas'].get(2, 0)}%
  • Nivel 3 (Alto): {datos_owas['estadisticas'].get(3, 0)}%
  • Nivel 4 (Crítico): {datos_owas['estadisticas'].get(4, 0)}%
- Nivel de Acción Global OWAS: {datos_owas['nivel_accion']}/4
- Recomendación global: {datos_owas['descripcion_accion']}

ANÁLISIS BIOMECÁNICO DEL PEOR MOMENTO:
- Flexión de espalda: {datos_owas['angulo_espalda']}°
- Elevación de brazo: {datos_owas['angulo_brazo']}°

Por favor, emití un dictamen profesional con:
1. Un párrafo inicial de conclusión del riesgo
2. Viñetas con recomendaciones de ingeniería específicas
3. Una nota final sobre seguimiento médico si corresponde
"""

    try:
        response = cliente_gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"{system_instruction}\n\n{user_prompt}",
        )
        if response and response.text:
            return response.text
        else:
            print("⚠️ Gemini no generó respuesta, usando dictamen de respaldo")
            return generar_dictamen_fallback(datos_owas, operario)
    except Exception as e:
        print(f"❌ Error al generar dictamen con Gemini: {e}")
        return generar_dictamen_fallback(datos_owas, operario)


def generar_dictamen_fallback(datos_owas, operario):
    """Dictamen de respaldo si Gemini no está disponible"""
    nivel = datos_owas['nivel_accion']
    patologia_riesgo = any(p in operario['patologias'].lower() for p in ['hernia', 'disco', 'lumbar', 'cervical', 'dolor'])

    if nivel == 4 or patologia_riesgo:
        return f"""DICTAMEN ERGONÓMICO - RIESGO CRÍTICO

El operario {operario['nombre']} ({operario['edad']} años, {operario['antiguedad']} años de antigüedad) presenta exposición MUY DAÑINA según el método OWAS. {'Adicionalmente, se reportan patologías que agravan el riesgo.' if patologia_riesgo else ''}

Recomendaciones prioritarias (ingeniería):
• Rediseñar el puesto con mesas de altura regulable (rango 70-110 cm)
• Instalar ayudas mecánicas (balancines, polipastos) para manipulación >10kg
• Rotar tareas cada 30 minutos para reducir exposición acumulada
• Evaluación por medicina laboral en un plazo NO MAYOR a 7 días

Recomendaciones conductuales:
• Capacitación en técnicas de levantamiento seguro
• Implementar recordatorios de cambio postural cada 15 minutos
• Realizar pausas activas obligatorias cada 30 minutos"""
    elif nivel == 3:
        return f"""DICTAMEN ERGONÓMICO - RIESGO ALTO

El trabajador {operario['nombre']} requiere intervención en el corto plazo (30 días).

Recomendaciones de ingeniería:
• Ajustar altura del plano de trabajo para mantener espalda <20° de flexión
• Implementar sistema de gestión de alcances (elementos entre 60-120 cm del suelo)
• Instalar apoyabrazos ergonómicos ajustables
• Evaluar posibles ayudas mecánicas para manipulación de cargas

Medidas organizacionales:
• Implementar pausas activas cada 45 minutos (5 minutos de duración)
• Establecer sistema de monitoreo postural semanal
• Seguimiento médico semestral"""
    elif nivel == 2:
        return f"""DICTAMEN ERGONÓMICO - RIESGO MODERADO

El puesto evaluado requiere ajustes programados en los próximos meses (90 días).

Medidas correctivas:
• Reorganizar elementos de trabajo al alcance frontal (<90° de elevación)
• Establecer recordatorios de cambios posturales (software o señalética)
• Capacitar al operario en técnicas de auto-corrección postural
• Monitoreo ergonómico trimestral"""
    else:
        return f"""DICTAMEN ERGONÓMICO - RIESGO BAJO

Las condiciones posturales del operario {operario['nombre']} son aceptables según OWAS.

Recomendaciones preventivas:
• Mantener programa de pausas activas diarias
• Realizar auditorías ergonómicas anuales
• Registrar y monitorear cualquier queja musculoesquelética"""


# ==================== NUEVA FUNCIÓN UNIFICADA PARA GEMINI ====================

def generar_dictamen_gemini_unificado(metodo, resultados, datos_operario, datos_adicionales=None):
    """
    Genera dictamen experto usando Gemini para cualquier método ergonómico
    
    Args:
        metodo: 'OWAS', 'RULA', 'REBA', 'ROSA'
        resultados: dict con resultados del método
        datos_operario: dict con nombre, edad, antiguedad, patologias
        datos_adicionales: dict con datos específicos del método
    
    Returns:
        dictamen en texto plano
    """
    if cliente_gemini is None:
        print(f"⚠️ Gemini no disponible, usando dictamen de respaldo para {metodo}")
        return generar_dictamen_fallback_unificado(metodo, resultados, datos_operario, datos_adicionales)
    
    nombre = datos_operario['nombre']
    edad = datos_operario['edad']
    antiguedad = datos_operario['antiguedad']
    patologias = datos_operario['patologias']
    
    # Construir prompt según el método
    if metodo == 'RULA':
        system_instruction = """
Actuás como un Especialista en Ergonomía de Miembros Superiores y Trastornos Musculoesqueléticos.
Tu enfoque es la prevención de lesiones en hombros, codos, muñecas y cuello.

REGLAS DE ORO:
- Analizar específicamente los ángulos de brazo, antebrazo, muñeca y cuello
- Priorizar soluciones de ingeniería (alturas, alcances, herramientas)
- Considerar la repetitividad y la fuerza
- Si el operario tiene patologías, el dictamen debe ser especialmente protector
- Dictamen conciso pero completo (máximo 350 palabras)
- Usar viñetas (•)
- No usar markdown
"""
        
        user_prompt = f"""
Generá un Dictamen Técnico-Ergonómico basado en resultados RULA:

DATOS DEL OPERARIO:
- Nombre: {nombre}
- Edad: {edad} años
- Antigüedad en el puesto: {antiguedad} años
- Patologías previas: {patologias if patologias else 'Ninguna informada'}

RESULTADOS RULA:
- Puntuación máxima: {resultados.get('puntuacion_max', 0)}/7
- Puntuación promedio: {resultados.get('puntuacion_prom', 0)}/7
- Nivel de riesgo: {resultados.get('nivel_riesgo', 'N/A')}
- Distribución de niveles: {resultados.get('estadisticas', {})}

Por favor, emití un dictamen profesional con:
1. Un párrafo inicial de conclusión del riesgo para miembros superiores
2. Viñetas con recomendaciones de ingeniería específicas (alturas, alcances, herramientas)
3. Recomendaciones de pausas activas y estiramientos específicos
4. Una nota final sobre seguimiento médico si corresponde
"""
    
    elif metodo == 'REBA':
        system_instruction = """
Actuás como un Ingeniero Biomecánico especializado en evaluación de carga postural global.
Tu análisis integra tronco, cuello, piernas y miembros superiores.

REGLAS DE ORO:
- Analizar la interacción entre carga, agarre y postura
- Considerar el peso manipulado y la calidad del agarre
- Proponer cambios de ingeniería específicos
- Si el operario tiene patologías, el dictamen debe ser crítico
- Dictamen conciso (máximo 350 palabras)
- Usar viñetas (•)
"""
        
        user_prompt = f"""
Generá un Dictamen Técnico-Ergonómico basado en resultados REBA:

DATOS DEL OPERARIO:
- Nombre: {nombre}
- Edad: {edad} años
- Antigüedad en el puesto: {antiguedad} años
- Patologías previas: {patologias if patologias else 'Ninguna informada'}

RESULTADOS REBA:
- Puntuación máxima: {resultados.get('puntuacion_max', 0)}/15
- Puntuación promedio: {resultados.get('puntuacion_prom', 0)}/15
- Nivel de riesgo: {resultados.get('nivel_riesgo', 'N/A')}
- Puntaje A (tronco+cuello+piernas): {resultados.get('puntaje_A', 0)}/12
- Puntaje B (brazo+antebrazo+muñeca): {resultados.get('puntaje_B', 0)}/12
- Distribución de niveles: {resultados.get('estadisticas', {})}

DATOS ADICIONALES:
- Carga manipulada: {datos_adicionales.get('carga', 0)}/3 (0=sin carga, 1=5-10kg, 2=>10kg, 3=carga brusca)
- Calidad del agarre: {datos_adicionales.get('acople', 0)}/3 (0=bueno, 1=regular, 2=malo, 3=inaceptable)

Por favor, emití un dictamen profesional con:
1. Un párrafo inicial de conclusión del riesgo global (cuerpo completo)
2. Viñetas con recomendaciones de ingeniería específicas (carga, agarre, posturas)
3. Recomendaciones organizacionales (rotación, pausas)
4. Una nota final sobre seguimiento médico si corresponde
"""
    
    elif metodo == 'ROSA':
        system_instruction = """
Actuás como un Especialista en Ergonomía de Oficina y Teletrabajo.
Tu enfoque es la prevención de trastornos musculoesqueléticos en entornos de oficina.

REGLAS DE ORO:
- Evaluar silla, monitor, teclado, mouse y teléfono
- Considerar el tiempo de uso continuo
- Proponer ajustes prácticos y económicos
- Dictamen conciso (máximo 350 palabras)
- Usar viñetas (•)
"""
        
        user_prompt = f"""
Generá un Dictamen Técnico-Ergonómico basado en resultados ROSA:

DATOS DEL OPERARIO:
- Nombre: {nombre}
- Edad: {edad} años
- Antigüedad en el puesto: {antiguedad} años
- Patologías previas: {patologias if patologias else 'Ninguna informada'}

RESULTADOS ROSA:
- Puntuación silla: {resultados.get('silla', 'N/A')}/10
- Puntuación monitor: {resultados.get('monitor', 'N/A')}/10
- Puntuación teclado: {resultados.get('teclado', 'N/A')}/10
- Puntuación mouse: {resultados.get('mouse', 'N/A')}/10
- PUNTUACIÓN FINAL: {resultados.get('puntuacion_final', 0)}/10
- NIVEL DE RIESGO: {resultados.get('nivel_riesgo', 'N/A')}
- USO CONTINUO >1h: {'Sí' if datos_adicionales.get('uso_continuo') else 'No'}

Por favor, emití un dictamen profesional con:
1. Un párrafo inicial de conclusión del riesgo del puesto de oficina
2. Viñetas con recomendaciones específicas por componente (silla, monitor, teclado, mouse)
3. Recomendaciones sobre pausas activas y organización del trabajo
4. Una nota final sobre ajustes inmediatos si corresponde
"""
    
    else:
        return generar_dictamen_fallback_unificado(metodo, resultados, datos_operario, datos_adicionales)
    
    try:
        response = cliente_gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"{system_instruction}\n\n{user_prompt}",
        )
        if response and response.text:
            return response.text
        else:
            print(f"⚠️ Gemini no generó respuesta para {metodo}, usando dictamen de respaldo")
            return generar_dictamen_fallback_unificado(metodo, resultados, datos_operario, datos_adicionales)
    except Exception as e:
        print(f"❌ Error al generar dictamen con Gemini para {metodo}: {e}")
        return generar_dictamen_fallback_unificado(metodo, resultados, datos_operario, datos_adicionales)


def generar_dictamen_fallback_unificado(metodo, resultados, datos_operario, datos_adicionales):
    """Dictamen de respaldo para cualquier método si Gemini no está disponible"""
    
    nombre = datos_operario['nombre']
    edad = datos_operario['edad']
    antiguedad = datos_operario['antiguedad']
    patologias = datos_operario['patologias']
    patologia_riesgo = any(p in patologias.lower() for p in ['hernia', 'disco', 'lumbar', 'cervical', 'dolor', 'hombro'])
    
    if metodo == 'RULA':
        punt = resultados.get('puntuacion_max', 1)
        if punt >= 7 or patologia_riesgo:
            return f"""DICTAMEN ERGONÓMICO RULA - RIESGO MUY ALTO

El operario {nombre} ({edad} años, {antiguedad} años de antigüedad) presenta una puntuación RULA de {punt}/7, lo que indica un nivel de riesgo MUY ALTO que requiere intervención INMEDIATA.

Recomendaciones URGENTES:
• ¡INTERVENCIÓN INMEDIATA REQUERIDA!
• Rediseñar completamente el puesto para miembros superiores
• Suspender tareas de alto riesgo hasta evaluación detallada
• Instalar ayudas mecánicas y apoyabrazos ergonómicos
• Evaluación médica INMEDIATA

Medidas preventivas:
• Pausas activas enfocadas en hombros y muñecas cada 30 minutos
• Capacitación en técnicas de alcance seguro
• Rotación de tareas cada 45 minutos"""
        elif punt >= 5:
            return f"""DICTAMEN ERGONÓMICO RULA - RIESGO ALTO

El operario {nombre} presenta una puntuación RULA de {punt}/7, indicando un nivel de riesgo ALTO.

Recomendaciones prioritarias:
• Rediseñar el puesto en 30 días
• Ajustar alturas de trabajo (mantener brazos relajados)
• Reducir alcances frontales y laterales
• Capacitación en técnicas posturales específicas

Medidas:
• Pausas activas cada 45 minutos
• Evaluación médica en 30 días
• Monitoreo postural semanal"""
        elif punt >= 3:
            return f"""DICTAMEN ERGONÓMICO RULA - RIESGO MEDIO

El puesto evaluado presenta una puntuación RULA de {punt}/7, con riesgo MEDIO.

Recomendaciones:
• Revisar posición de brazos y muñecas
• Ajustar altura de teclado y mouse
• Implementar pausas activas cada 2 horas
• Monitoreo trimestral"""
        else:
            return f"""DICTAMEN ERGONÓMICO RULA - RIESGO BAJO

Las condiciones posturales de miembros superiores del operario {nombre} son aceptables.

Recomendaciones preventivas:
• Mantener buenas prácticas posturales
• Pausas activas preventivas cada 2 horas
• Auditoría ergonómica anual"""
    
    elif metodo == 'REBA':
        punt = resultados.get('puntuacion_max', 1)
        if punt >= 11 or patologia_riesgo:
            return f"""DICTAMEN ERGONÓMICO REBA - RIESGO MUY ALTO

El operario {nombre} ({edad} años, {antiguedad} años de antigüedad) presenta una puntuación REBA de {punt}/15, riesgo MUY ALTO - INTERVENCIÓN INMEDIATA.

Recomendaciones URGENTES:
• ¡SUSPENDER TAREA hasta rediseño completo!
• Eliminar o reducir drásticamente la carga manipulada
• Instalar ayudas mecánicas OBLIGATORIAS (polipastos, balancines)
• Rediseñar el agarre de herramientas (actualmente crítico)
• Evaluación médica INMEDIATA

Medidas organizacionales:
• Reasignar temporalmente al operario
• Rotación cada 15 minutos si la tarea no puede suspenderse
• Capacitación urgente en técnicas de levantamiento"""
        elif punt >= 8:
            return f"""DICTAMEN ERGONÓMICO REBA - RIESGO ALTO

El trabajador {nombre} presenta una puntuación REBA de {punt}/15, riesgo ALTO.

Recomendaciones prioritarias (30 días):
• Rediseñar el puesto (tronco <20°, brazos relajados)
• Mejorar agarre de herramientas (superficies antideslizantes)
• Reducir carga manipulada mediante ayudas mecánicas
• Pausas activas cada 30 minutos

Seguimiento:
• Evaluación médica en 30 días
• Monitoreo postural semanal"""
        elif punt >= 4:
            return f"""DICTAMEN ERGONÓMICO REBA - RIESGO MEDIO

Puntuación REBA {punt}/15 - Riesgo MEDIO.

Recomendaciones:
• Ajustar alturas y alcances del puesto
• Capacitar en técnicas de levantamiento seguro
• Implementar pausas activas cada 2 horas
• Monitoreo ergonómico trimestral"""
        else:
            return f"""DICTAMEN ERGONÓMICO REBA - RIESGO BAJO

Condiciones posturales aceptables según REBA.

Recomendaciones preventivas:
• Mantener buenas prácticas
• Pausas activas preventivas
• Auditoría anual"""
    
    elif metodo == 'ROSA':
        punt = resultados.get('puntuacion_final', 1)
        if punt >= 8:
            return f"""DICTAMEN ERGONÓMICO ROSA - RIESGO MUY ALTO

El puesto del operario {nombre} presenta una puntuación ROSA de {punt}/10 - INTERVENCIÓN INMEDIATA.

Recomendaciones URGENTES:
• Reemplazar o ajustar silla ergonómicamente
• Reubicar monitor a la altura de los ojos
• Instalar reposamuñecas y ajustar teclado
• Evaluación médica

Medidas:
• Pausas activas cada 30 minutos
• Revisión en 7 días"""
        elif punt >= 6:
            return f"""DICTAMEN ERGONÓMICO ROSA - RIESGO MEDIO/ALTO

Puntuación ROSA {punt}/10 - Requiere mejoras programadas (30 días).

Recomendaciones:
• Ajustar silla, monitor y teclado
• Implementar pausas activas cada 45-60 minutos
• Capacitación en configuración ergonómica
• Monitoreo trimestral"""
        elif punt >= 4:
            return f"""DICTAMEN ERGONÓMICO ROSA - RIESGO BAJO

Puntuación ROSA {punt}/10 - Riesgo BAJO.

Recomendaciones:
• Ajustes menores en el puesto
• Pausas activas cada 2 horas
• Auditoría ergonómica semestral"""
        else:
            return f"""DICTAMEN ERGONÓMICO ROSA - RIESGO ACEPTABLE

Puesto de oficina en condiciones aceptables.

Recomendaciones preventivas:
• Mantener buenas prácticas
• Pausas activas cada 2 horas
• Auditoría anual"""
    
    return "No se pudo generar dictamen. Consulte a un especialista en ergonomía."


# ==================== FUNCIONES DE ÁNGULOS PARA YOLO POSE ====================

# NOTA: obtener_punto(), calcular_angulo_2d(), clasificar_riesgo_owas()
# ahora se importan desde Methods.comunes


def calcular_flexion_espalda_yolo(keypoints):
    """Calcula la flexión de espalda usando puntos YOLO"""
    hombro = obtener_punto(keypoints, 5)
    cadera = obtener_punto(keypoints, 11)
    rodilla = obtener_punto(keypoints, 13)
    if hombro is None or cadera is None or rodilla is None:
        hombro = obtener_punto(keypoints, 6)
        cadera = obtener_punto(keypoints, 12)
        rodilla = obtener_punto(keypoints, 14)
    if hombro is None or cadera is None or rodilla is None:
        return 0
    angulo = calcular_angulo_2d(hombro, cadera, rodilla)
    if angulo > 90:
        angulo = 180 - angulo
    return max(0, min(angulo, 90))


def calcular_elevacion_brazo_yolo(keypoints, lado="izquierdo"):
    """Calcula la elevación del brazo respecto al tronco"""
    if lado == "izquierdo":
        hombro = obtener_punto(keypoints, 5)
        muneca = obtener_punto(keypoints, 9)
    else:
        hombro = obtener_punto(keypoints, 6)
        muneca = obtener_punto(keypoints, 10)
    if hombro is None or muneca is None:
        return 0, 1
    brazo = np.array([muneca[0] - hombro[0], muneca[1] - hombro[1]])
    vertical = np.array([0, 1])
    if np.linalg.norm(brazo) < 0.001:
        return 0, 1
    brazo_unit = brazo / np.linalg.norm(brazo)
    cos_angulo = np.dot(brazo_unit, vertical)
    cos_angulo = np.clip(cos_angulo, -1, 1)
    angulo = np.degrees(np.arccos(cos_angulo))
    if muneca[1] < hombro[1]:
        angulo = 180 - angulo
    if angulo <= 90:
        codigo = 1
    else:
        codigo = 2
    return angulo, codigo


def detectar_postura_piernas_yolo(angulo_rodilla, cadera, rodilla, tobillo):
    """Detecta postura de piernas basado en ángulo de rodilla"""
    if cadera is None or rodilla is None:
        return 2, "De pie", "Parado piernas rectas", 1
    diferencia_cadera_rodilla = rodilla[1] - cadera[1]
    if diferencia_cadera_rodilla < 0.02:
        return 1, "Sentado", "Postura sentada", 1
    elif angulo_rodilla > 60:
        return 3, "Agachado", f"Rodilla muy flexionada ({angulo_rodilla:.0f}°)", 3
    elif angulo_rodilla > 30:
        return 2, "De pie", f"Leve flexión de rodilla ({angulo_rodilla:.0f}°)", 2
    else:
        return 2, "De pie", "Parado piernas rectas", 1


def calcular_nivel_accion_owas(stats):
    """Calcula el nivel de acción global según la tabla de frecuencia relativa OWAS"""
    nivel_maximo = 0
    for nivel in [4, 3, 2, 1]:
        if stats.get(nivel, 0) > 0:
            nivel_maximo = nivel
            break
    frecuencia = stats.get(nivel_maximo, 0)
    if nivel_maximo == 4:
        if frecuencia < 10:
            nivel_accion = 3
            descripcion = "CATEGORÍA 3 - Acción correctiva lo antes posible (postura crítica poco frecuente)"
        elif frecuencia < 30:
            nivel_accion = 3
            descripcion = "CATEGORÍA 3 - Acción correctiva lo antes posible"
        elif frecuencia < 50:
            nivel_accion = 4
            descripcion = "CATEGORÍA 4 - Acción inmediata requerida"
        else:
            nivel_accion = 4
            descripcion = "CATEGORÍA 4 - Acción inmediata requerida (exposición muy frecuente)"
    elif nivel_maximo == 3:
        if frecuencia < 20:
            nivel_accion = 2
            descripcion = "CATEGORÍA 2 - Acción correctiva a futuro"
        elif frecuencia < 50:
            nivel_accion = 3
            descripcion = "CATEGORÍA 3 - Acción correctiva lo antes posible"
        else:
            nivel_accion = 4
            descripcion = "CATEGORÍA 4 - Acción inmediata requerida"
    elif nivel_maximo == 2:
        if frecuencia < 20:
            nivel_accion = 1
            descripcion = "CATEGORÍA 1 - No requiere acción inmediata"
        elif frecuencia < 50:
            nivel_accion = 2
            descripcion = "CATEGORÍA 2 - Acción correctiva a futuro"
        else:
            nivel_accion = 3
            descripcion = "CATEGORÍA 3 - Acción correctiva lo antes posible"
    else:
        nivel_accion = 1
        descripcion = "CATEGORÍA 1 - No requiere acción inmediata (postura normal)"
    return nivel_accion, descripcion, nivel_maximo, frecuencia


# ==================== FUNCIONES PARA RULA ====================

def obtener_angulos_rula(keypoints):
    """Extrae los ángulos necesarios para RULA desde keypoints de YOLO"""
    # Puntos para brazo izquierdo (usamos izquierdo por defecto)
    hombro_izq = obtener_punto(keypoints, 5)
    codo_izq = obtener_punto(keypoints, 7)
    muneca_izq = obtener_punto(keypoints, 9)
    
    # Ángulo de brazo (hombro)
    angulo_brazo = 0
    if hombro_izq and codo_izq and muneca_izq:
        angulo_brazo = calcular_angulo_2d(hombro_izq, codo_izq, muneca_izq)
    
    # Ángulo de antebrazo (codo)
    angulo_antebrazo = 0
    if hombro_izq and codo_izq and muneca_izq:
        angulo_antebrazo = calcular_angulo_2d(hombro_izq, codo_izq, muneca_izq)
    
    # Ángulo de muñeca (simplificado)
    angulo_muneca = 0
    
    # Ángulo de cuello
    nariz = obtener_punto(keypoints, 0)
    hombro_izq = obtener_punto(keypoints, 5)
    hombro_der = obtener_punto(keypoints, 6)
    angulo_cuello = 0
    if nariz and hombro_izq and hombro_der:
        base_cuello = ((hombro_izq[0] + hombro_der[0]) / 2,
                       (hombro_izq[1] + hombro_der[1]) / 2)
        punto_arriba = (nariz[0], nariz[1] - 50)
        angulo_cuello = calcular_angulo_2d(punto_arriba, base_cuello, nariz)
    
    # Ángulo de tronco
    cadera_izq = obtener_punto(keypoints, 11)
    cadera_der = obtener_punto(keypoints, 12)
    angulo_tronco = 0
    if hombro_izq and hombro_der and cadera_izq and cadera_der:
        hombro_medio = ((hombro_izq[0] + hombro_der[0]) / 2,
                        (hombro_izq[1] + hombro_der[1]) / 2)
        cadera_medio = ((cadera_izq[0] + cadera_der[0]) / 2,
                        (cadera_izq[1] + cadera_der[1]) / 2)
        punto_arriba = (cadera_medio[0], cadera_medio[1] - 100)
        angulo_tronco = calcular_angulo_2d(punto_arriba, cadera_medio, hombro_medio)
    
    return {
        'angulo_brazo': angulo_brazo,
        'angulo_antebrazo': angulo_antebrazo,
        'angulo_muneca': angulo_muneca,
        'angulo_cuello': angulo_cuello,
        'angulo_tronco': angulo_tronco
    }


def procesar_frame_rula(keypoints, frame, contador_frames):
    """Procesa un frame con el método RULA"""
    from Methods.metodologias.rula import evaluar_rula
    
    # Evaluar RULA
    resultado_rula = evaluar_rula(keypoints)
    
    puntuacion = resultado_rula['puntuacion_final']
    nivel = resultado_rula['nivel_riesgo']
    accion = resultado_rula['accion']
    
    # Mostrar en consola si riesgo es medio/alto
    if puntuacion >= 5:
        print(f"\n⚠️ Frame {contador_frames} - RULA: {puntuacion}/7 - {nivel}")
        print(f"   {accion}")
    
    return resultado_rula


def generar_reporte_rula(resultados_rula, empresa_input, puesto_input, evaluador_input, 
                          op_nombre, op_edad, op_antiguedad, op_patologias,
                          logo_path, imagenes_riesgo, muestras_posturales):
    """Genera reporte específico para RULA con Gemini"""
    
    # Calcular estadísticas de puntuaciones RULA
    puntuaciones = [r['puntuacion_final'] for r in resultados_rula if r is not None]
    
    if puntuaciones:
        stats = {
            1: puntuaciones.count(1),
            2: puntuaciones.count(2),
            3: puntuaciones.count(3),
            4: puntuaciones.count(4),
            5: puntuaciones.count(5),
            6: puntuaciones.count(6),
            7: puntuaciones.count(7)
        }
        total = len(puntuaciones)
        stats_pct = {k: round((v / total) * 100, 1) for k, v in stats.items() if v > 0}
        
        puntuacion_max = max(puntuaciones)
        puntuacion_prom = round(sum(puntuaciones) / len(puntuaciones), 1)
    else:
        stats_pct = {}
        puntuacion_max = 0
        puntuacion_prom = 0
    
    # Buscar el frame con peor puntuación
    peor_frame = max(resultados_rula, key=lambda x: x['puntuacion_final'] if x else 0) if resultados_rula else None
    
    # Generar dictamen con Gemini para RULA
    print("\n🤖 Generando dictamen experto con IA para RULA...")
    operario_dictamen = {
        'nombre': op_nombre,
        'edad': op_edad,
        'antiguedad': op_antiguedad,
        'patologias': op_patologias
    }
    resultados_rula_dict = {
        'puntuacion_max': puntuacion_max,
        'puntuacion_prom': puntuacion_prom,
        'nivel_riesgo': peor_frame['nivel_riesgo'] if peor_frame else "DESCONOCIDO",
        'estadisticas': stats_pct
    }
    
    conclusion_medica = generar_dictamen_gemini_unificado(
        'RULA', 
        resultados_rula_dict, 
        operario_dictamen, 
        None
    )
    print("✅ Dictamen generado correctamente")
    
    # Preparar datos para el PDF
    analisis_f = [
        {"segmento": "Puntuación RULA", "angulo": f"{puntuacion_max}/7", "estado": peor_frame['nivel_riesgo'] if peor_frame else "N/A"},
        {"segmento": "Promedio", "angulo": f"{puntuacion_prom}", "estado": "RULA"},
        {"segmento": "Brazo", "angulo": "N/A", "estado": peor_frame['detalles']['brazo'].get('descripcion', peor_frame['detalles']['brazo'].get('error', 'N/A')) if peor_frame else "N/A"},
        {"segmento": "Cuello/Tronco", "angulo": "N/A", "estado": peor_frame['detalles']['cuello'].get('descripcion', peor_frame['detalles']['cuello'].get('error', 'N/A')) if peor_frame else "N/A"}
    ]
    
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
        "recomendacion": conclusion_medica,
        "resumen_40": muestras_posturales[:40],
        "estadisticas": stats_pct,
        "metodo": "RULA",
        "puntuacion_max": puntuacion_max,
        "puntuacion_prom": puntuacion_prom
    }
    
    try:
        timestamp = int(time.time())
        nombre_base = f"YOLO_RULA_{empresa_input}_{op_nombre.replace(' ', '_')}"
        nombre_pdf = f"reports/{nombre_base}_{timestamp}.pdf"
        
        print("\n📄 Generando reporte PDF...")
        crear_pdf(nombre_pdf, datos_reporte, imagenes_riesgo)
        
        print("\n" + "=" * 60)
        print("✅ INFORME RULA GENERADO CON ÉXITO")
        print("=" * 60)
        print(f"📄 PDF: {nombre_pdf}")
        print(f"🎯 Puntuación RULA máxima: {puntuacion_max}/7")
        print(f"📊 Puntuación promedio: {puntuacion_prom}/7")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error al generar reporte: {e}")
        traceback.print_exc()


# ==================== CONFIGURACIÓN INICIAL ====================

os.makedirs('reports', exist_ok=True)
os.makedirs('capturas_riesgo', exist_ok=True)


# ==================== CÓDIGO PRINCIPAL (solo se ejecuta si es script principal) ====================
if __name__ == "__main__":
    # ==================== SELECCIÓN DE TIPO DE ENTRADA (FOTO o VIDEO) ====================
    print("=" * 60)
    print("             ERGOEDGE OS - SISTEMA DE ANÁLISIS ERGONÓMICO")
    print("=" * 60)
    print("\n📋 TIPO DE ENTRADA:")
    print("   1. VIDEO - Analizar un video (recomendado para movimientos)")
    print("   2. FOTO - Analizar una sola imagen (para posturas estáticas)")
    print("-" * 40)

    while True:
        try:
            tipo_entrada = int(input("\n👉 Seleccione (1) Video o (2) Foto: "))
            if tipo_entrada in [1, 2]:
                break
            else:
                print("❌ Opción inválida. Elija 1 o 2.")
        except ValueError:
            print("❌ Ingrese un número válido (1 o 2).")

    # ==================== MENÚ DE SELECCIÓN DE MÉTODO ====================
    print("\n📋 MÉTODOS DISPONIBLES:")
    print("   1. OWAS - Ovako Working Posture Analysis (cuerpo completo)")
    print("   2. RULA - Rapid Upper Limb Assessment (miembros superiores)")
    print("   3. REBA - Rapid Entire Body Assessment (cuerpo completo + 3D)")
    print("   4. ROSA - Rapid Office Strain Assessment (puestos de oficina)")
    print("-" * 40)

    while True:
        try:
            metodo_elegido = int(input("\n👉 Seleccione el método (1, 2, 3 o 4): "))
            if metodo_elegido in [1, 2, 3, 4]:
                break
            else:
                print("❌ Opción inválida. Elija 1, 2, 3 o 4.")
        except ValueError:
            print("❌ Ingrese un número válido (1, 2, 3 o 4).")

    if metodo_elegido == 1:
        print("\n" + "=" * 60)
        print("             ERGOEDGE OS - YOLO11 POSE (OWAS)")
        print("=" * 60)
    elif metodo_elegido == 2:
        print("\n" + "=" * 60)
        print("             ERGOEDGE OS - YOLO11 POSE (RULA)")
        print("=" * 60)
    elif metodo_elegido == 3:
        print("\n" + "=" * 60)
        print("             ERGOEDGE OS - YOLO11 POSE (REBA 3D)")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("             ERGOEDGE OS - ROSA (Rapid Office Strain Assessment)")
        print("=" * 60)

    logo_path = None
    quiere_logo = input("\n¿Desea incluir un logo? (s/n): ").lower()
    if quiere_logo == 's':
        path_temp = input("Ruta del logo: ")
        if os.path.exists(path_temp):
            logo_path = os.path.abspath(path_temp).replace('\\', '/')

    empresa_input = input("Nombre de la Empresa: ").upper()
    puesto_input = input("Nombre del Puesto: ").upper()
    evaluador_input = input("Nombre del Evaluador: ")

    print("-" * 40)
    print("DATOS DEL OPERARIO:")
    op_nombre = input("Nombre y Apellido: ")
    op_edad = input("Edad: ")
    op_antiguedad = input("Antigüedad en el puesto: ")
    op_patologias = input("Patologías previas (vacío si no): ")
    if not op_patologias:
        op_patologias = "Ninguna informada"

    # ==================== CARGA DEL MODELO YOLO ====================
    print("\n📥 Cargando modelo YOLO11 Pose...")
    try:
        modelo_yolo = YOLO('yolo11x-pose.pt')  # 33 keypoints con nudillos para muñeca
        modelo_yolo.overrides['conf'] = 0.4
        modelo_yolo.overrides['iou'] = 0.6
        modelo_yolo.overrides['max_det'] = 1
        print("✅ Modelo YOLO11x-pose cargado correctamente")
    except Exception as e:
        print(f"⚠️ Error cargando modelo: {e}")
        try:
            modelo_yolo = YOLO('yolo11m-pose.pt')
            print("✅ Modelo YOLO11m-pose cargado correctamente")
        except Exception as e2:
            print(f"❌ Error cargando modelo: {e2}")
            exit()

    # ==================== CARGA DE ENTRADA (VIDEO o FOTO) ====================
    if tipo_entrada == 1:
        # Modo VIDEO
        video_path = input("\n📹 Ruta del video (test.mp4 por defecto): ").strip()
        if not video_path:
            video_path = "test.mp4"
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Error: No se pudo abrir {video_path}")
            exit()
        modo_video = True
        print(f"\n🎬 Procesando VIDEO: {video_path}")
    else:
        # Modo FOTO
        foto_path = input("\n📷 Ruta de la foto (jpg, png): ").strip()
        if not foto_path:
            foto_path = "test.jpg"
        
        frame = cv2.imread(foto_path)
        if frame is None:
            print(f"❌ Error: No se pudo cargar la foto {foto_path}")
            exit()
        modo_video = False
        print(f"\n🖼️ Procesando FOTO: {foto_path}")

    FRAME_SKIP = 4
    contador_frames = 0
    frames_con_persona = 0
    frame_counter = 0

    # Variables OWAS (solo se usan si metodo_elegido == 1)
    if metodo_elegido == 1:
        peor_riesgo_nivel = 0
        datos_peor_momento = None
        imagenes_riesgo = []
        angulo_espalda_peor = 0
        angulo_brazo_peor = 0
        muestras_posturales = []
        conteo_riesgos = {1: 0, 2: 0, 3: 0, 4: 0}
        historial_evolucion = []
        mejores_momentos = []
        ultimo_frame_procesado = -30
        keypoints_anterior = None  # <--- AGREGADO: variable para frame anterior

    # Variables RULA (solo se usan si metodo_elegido == 2)
    if metodo_elegido == 2:
        resultados_rula = []
        mejores_momentos_rula = []
        imagenes_riesgo = []
        muestras_posturales = []

    # Variables REBA (solo se usan si metodo_elegido == 3)
    if metodo_elegido == 3:
        resultados_reba = []
        mejores_momentos_reba = []
        imagenes_riesgo = []
        muestras_posturales = []
        carga = 0
        acople = 0
        reba_calc = None

    # Variables ROSA (solo se usan si metodo_elegido == 4)
    if metodo_elegido == 4:
        datos_rosa = None
        resultado_rosa = None

    print(f"\n🚀 Procesando...")
    if tipo_entrada == 1:
        print(f"   Frame skip: {FRAME_SKIP} (procesando {100/FRAME_SKIP:.0f}% de frames)")
    print("   Presione 'q' o 'ESC' para finalizar anticipadamente")

    if metodo_elegido == 1:
        print("📐 Aplicando método OWAS original")
    elif metodo_elegido == 2:
        print("📐 Aplicando método RULA (Rapid Upper Limb Assessment)")
    elif metodo_elegido == 3:
        print("📐 Aplicando método REBA 3D (Rapid Entire Body Assessment)")
    else:
        print("📐 Aplicando método ROSA (Rapid Office Strain Assessment)")

    # ==================== FUNCIÓN PARA PROCESAR UN FRAME ====================
    def procesar_frame(frame, frame_num, is_foto=False):
        def procesar_frame(frame, frame_num, is_foto=False):
            global frames_con_persona, peor_riesgo_nivel, angulo_espalda_peor, angulo_brazo_peor
            global datos_peor_momento, conteo_riesgos, historial_evolucion, mejores_momentos
            global muestras_posturales, resultados_rula, mejores_momentos_rula
            global resultados_reba, mejores_momentos_reba, reba_calc, carga, acople
            global keypoints_anterior, codigo_carga_constante
        
        results = modelo_yolo(frame, verbose=False)
        frame_display = frame.copy()
        
        if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
            frames_con_persona += 1
            keypoints = results[0].keypoints.data[0].cpu().numpy()

            if metodo_elegido == 1:  # OWAS
                hombro = obtener_punto(keypoints, 5)
                cadera = obtener_punto(keypoints, 11)
                rodilla = obtener_punto(keypoints, 13)
                tobillo = obtener_punto(keypoints, 15)

                angulo_espalda = calcular_flexion_espalda_yolo(keypoints)
                angulo_brazo, codigo_brazo = calcular_elevacion_brazo_yolo(keypoints, "izquierdo")
                angulo_rodilla = calcular_angulo_2d(cadera, rodilla, tobillo) if cadera and rodilla and tobillo else 0

                if angulo_espalda <= 20:
                    codigo_espalda = 1
                    estado_espalda = "Recta"
                elif angulo_espalda <= 60:
                    codigo_espalda = 2
                    estado_espalda = "Inclinada"
                elif angulo_espalda <= 90:
                    codigo_espalda = 3
                    estado_espalda = "Muy inclinada"
                else:
                    codigo_espalda = 4
                    estado_espalda = "Extrema"

                # ========== TORSIÓN AVANZADA ==========
                hombro_izq_punto = obtener_punto(keypoints, 5)
                hombro_der_punto = obtener_punto(keypoints, 6)
                cadera_izq_punto = obtener_punto(keypoints, 11)
                cadera_der_punto = obtener_punto(keypoints, 12)
                
                torsion_data = calcular_torsion_avanzada(hombro_izq_punto, hombro_der_punto, cadera_izq_punto, cadera_der_punto)
                torsion = 1 if torsion_data['detectada'] else 0
                
                if torsion_data['detectada']:
                    codigo_espalda = min(codigo_espalda + torsion_data['incremento'], 4)
                    print(f"   🔄 Torsión: {torsion_data['angulo']}° hacia {torsion_data['direccion']} (+{torsion_data['incremento']})")
                
                # ========== CARGA DINÁMICA ==========
                # Usar keypoints_anterior (puede ser None en primer frame)
                carga_data = detectar_carga_dinamica(keypoints, keypoints_anterior, codigo_carga_constante)
                codigo_carga = carga_data['codigo_carga']
                estado_carga = carga_data['descripcion']
                
                if carga_data['cargando']:
                    print(f"   📦 Carga: {carga_data['descripcion']} (código {codigo_carga})")

                codigo_piernas, estado_piernas, desc_piernas, riesgo_piernas = detectar_postura_piernas_yolo(
                    angulo_rodilla, cadera, rodilla, tobillo
                )

                nivel_riesgo, categoria_riesgo, accion_requerida = clasificar_riesgo_owas(
                    codigo_espalda, codigo_brazo, codigo_piernas, codigo_carga
                )

                codigo_owas = f"{codigo_espalda}{codigo_brazo}{codigo_piernas}{codigo_carga}"

                if nivel_riesgo >= 3:
                    print(f"\n⚠️ Frame {frame_num} - Nivel {nivel_riesgo}/4 - OWAS: {codigo_owas}")
                    print(f"   Espalda: {angulo_espalda:.1f}° (código {codigo_espalda})")
                    print(f"   Brazo: {angulo_brazo:.1f}° (código {codigo_brazo})")
                    print(f"   Piernas: {estado_piernas} (código {codigo_piernas})")

                conteo_riesgos[nivel_riesgo] += 1

                if len(historial_evolucion) < 40:
                    historial_evolucion.append(nivel_riesgo)

                if len(muestras_posturales) < 40:
                    muestras_posturales.append({
                        "posicion": len(muestras_posturales) + 1,
                        "espalda": estado_espalda,
                        "brazos": "Elevado" if codigo_brazo >= 2 else "Normal",
                        "piernas": estado_piernas,
                        "nivel": nivel_riesgo,
                        "angulo_espalda": angulo_espalda,
                        "angulo_brazo": angulo_brazo,
                        "codigo_owas": codigo_owas
                    })

                estado_brazo_str = "Elevado" if codigo_brazo >= 2 else "Normal"

                if nivel_riesgo >= peor_riesgo_nivel - 1:
                    mejores_momentos.append({
                        'frame': frame_num,
                        'nivel_riesgo': nivel_riesgo,
                        'codigo_owas': codigo_owas,
                        'angulo_espalda': angulo_espalda,
                        'angulo_brazo': angulo_brazo,
                        'angulo_rodilla': angulo_rodilla,
                        'estado_espalda': estado_espalda,
                        'estado_brazo': estado_brazo_str,
                        'estado_piernas': estado_piernas,
                        'frame_img': frame.copy() if nivel_riesgo >= 3 else None,
                        'results': results[0] if nivel_riesgo >= 3 else None,
                        'codigo_espalda': codigo_espalda,
                        'codigo_brazo': codigo_brazo,
                        'codigo_piernas': codigo_piernas,
                        'categoria_riesgo': categoria_riesgo,
                        'accion_requerida': accion_requerida,
                        'descripcion_espalda': f"{estado_espalda} ({angulo_espalda:.0f}°)",
                        'descripcion_brazo': f"Brazo {estado_brazo_str} ({angulo_brazo:.0f}°)",
                        'is_foto': is_foto
                    })

                es_peor_nivel = nivel_riesgo > peor_riesgo_nivel
                es_igual_nivel_pero_peor_espalda = (
                    nivel_riesgo == peor_riesgo_nivel and
                    angulo_espalda > angulo_espalda_peor
                )
                if es_peor_nivel or es_igual_nivel_pero_peor_espalda:
                    peor_riesgo_nivel = nivel_riesgo
                    angulo_espalda_peor = angulo_espalda
                    angulo_brazo_peor = angulo_brazo

                    recomendaciones = []
                    if codigo_espalda >= 2:
                        recomendaciones.append("• Ajustar la altura del plano de trabajo para mantener la espalda recta (<20°)")
                    if codigo_brazo >= 2:
                        recomendaciones.append("• Mantener los elementos de trabajo al alcance para evitar elevación de brazos (>90°)")
                    if codigo_piernas >= 3:
                        recomendaciones.append("• Evitar posturas en cuclillas prolongadas, usar ayudas mecánicas o plataformas")
                    if nivel_riesgo >= 3:
                        recomendaciones.append("• Realizar pausas activas cada 30 minutos")
                        recomendaciones.append("• Rotar tareas para evitar exposición prolongada")
                    if nivel_riesgo >= 2:
                        recomendaciones.append("• Monitorear periódicamente las posturas del trabajador")
                    if not recomendaciones:
                        recomendaciones.append("• Continuar con buenas prácticas ergonómicas")

                    texto_recomendaciones = "\n".join(recomendaciones)

                    datos_peor_momento = {
                        'estados': {
                            'espalda': f"{estado_espalda} ({categoria_riesgo})",
                            'brazos': estado_brazo_str,
                            'piernas': estado_piernas,
                            'carga': estado_carga
                        },
                        'detalles': {
                            'espalda': f"{estado_espalda} - Código OWAS {codigo_espalda}",
                            'brazos': f"Brazo {angulo_brazo:.0f}° - Código OWAS {codigo_brazo}",
                            'piernas': f"{desc_piernas} - Código OWAS {codigo_piernas}",
                            'carga': f"{estado_carga} - Código OWAS {codigo_carga}"
                        },
                        'codigo_owas': codigo_owas,
                        'nivel_riesgo': nivel_riesgo,
                        'categoria_riesgo': categoria_riesgo,
                        'accion_requerida': accion_requerida,
                        'recomendacion_ia': texto_recomendaciones,
                        'angulo_espalda': angulo_espalda,
                        'angulo_brazo': angulo_brazo
                    }

                frame_display = results[0].plot()
                color = (0, 0, 255) if nivel_riesgo >= 3 else (0, 255, 0) if nivel_riesgo == 1 else (0, 165, 255)
                cv2.putText(frame_display, f"OWAS: {codigo_owas} - Nivel {nivel_riesgo}/4", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.putText(frame_display, f"Espalda: {int(angulo_espalda)}° (Cod:{codigo_espalda})", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame_display, f"Brazo: {int(angulo_brazo)}° (Cod:{codigo_brazo})", (10, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame_display, f"Piernas: {estado_piernas} (Cod:{codigo_piernas})", (10, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame_display, f"Rodilla: {int(angulo_rodilla)}°", (10, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

                # Guardar keypoints para el próximo frame
                keypoints_anterior = keypoints.copy()

            elif metodo_elegido == 2:  # RULA
                resultado_rula = evaluar_rula(keypoints)
                resultados_rula.append(resultado_rula)
                
                puntuacion = resultado_rula['puntuacion_final']
                
                if puntuacion >= 5:
                    print(f"\n⚠️ Frame {frame_num} - RULA: {puntuacion}/7 - {resultado_rula['nivel_riesgo']}")
                    print(f"   {resultado_rula['accion']}")
                
                if len(muestras_posturales) < 40:
                    tronco_desc = resultado_rula['detalles']['tronco'].get('descripcion', 
                                  resultado_rula['detalles']['tronco'].get('error', 'N/A'))
                    brazo_desc = resultado_rula['detalles']['brazo'].get('descripcion', 
                                 resultado_rula['detalles']['brazo'].get('error', 'N/A'))
                    piernas_desc = resultado_rula['detalles']['piernas'].get('descripcion', 
                                   resultado_rula['detalles']['piernas'].get('error', 'N/A'))
                    
                    muestras_posturales.append({
                        "posicion": len(muestras_posturales) + 1,
                        "espalda": tronco_desc,
                        "brazos": brazo_desc,
                        "piernas": piernas_desc,
                        "nivel": puntuacion,
                        "codigo_owas": f"RULA:{puntuacion}",
                        "is_foto": is_foto
                    })
                
                if puntuacion >= 4:
                    mejores_momentos_rula.append({
                        'frame': frame_num,
                        'puntuacion': puntuacion,
                        'nivel_riesgo': resultado_rula['nivel_riesgo'],
                        'frame_img': frame.copy(),
                        'results': results[0],
                        'detalles': resultado_rula['detalles'],
                        'is_foto': is_foto
                    })
                
                frame_display = results[0].plot()
                color = (0, 0, 255) if puntuacion >= 6 else (0, 165, 255) if puntuacion >= 4 else (0, 255, 0)
                cv2.putText(frame_display, f"RULA: {puntuacion}/7 - {resultado_rula['nivel_riesgo']}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                brazo_score = resultado_rula['detalles']['brazo'].get('puntuacion', '?')
                cuello_score = resultado_rula['detalles']['cuello'].get('puntuacion', '?')
                tronco_score = resultado_rula['detalles']['tronco'].get('puntuacion', '?')
                
                cv2.putText(frame_display, f"Brazo: {brazo_score}/6", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
                cv2.putText(frame_display, f"Cuello: {cuello_score}/4", (10, 78),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
                cv2.putText(frame_display, f"Tronco: {tronco_score}/4", (10, 96),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

            elif metodo_elegido == 3:  # REBA
                if reba_calc is None:
                    reba_calc = RebaCalculator()
                    print("\n📋 DATOS MANUALES REQUERIDOS PARA REBA:")
                    carga = int(input("   Carga manipulado (0=sin carga, 1=5-10kg, 2=>10kg, 3=carga brusca): "))
                    acople = int(input("   Calidad de agarre (0=bueno, 1=regular, 2=malo, 3=inaceptable): "))
                
                resultado_reba = reba_calc.evaluar(keypoints, frame.shape[1], frame.shape[0], carga, acople)
                resultados_reba.append(resultado_reba)
                
                puntuacion = resultado_reba['puntuacion_final']
                nivel = resultado_reba['nivel_riesgo']
                accion = resultado_reba['accion']
                
                if puntuacion >= 4:
                    print(f"\n⚠️ Frame {frame_num} - REBA: {puntuacion}/15 - {nivel}")
                    print(f"   {accion}")
                    print(f"   Puntaje A: {resultado_reba['puntuacion_A']} | Puntaje B: {resultado_reba['puntuacion_B']}")
                    if resultado_reba['detalles']['abduccion'] > 20:
                        print(f"   ⚠️ Abducción de brazo: {resultado_reba['detalles']['abduccion']:.1f}° (>20°)")
                    if resultado_reba['detalles']['torsion']:
                        print(f"   ⚠️ Torsión de tronco detectada")
                
                if len(muestras_posturales) < 40:
                    muestras_posturales.append({
                        "posicion": len(muestras_posturales) + 1,
                        "espalda": f"Tronco: {resultado_reba['detalles']['tronco']}",
                        "brazos": f"Brazo: {resultado_reba['detalles']['brazo']}",
                        "piernas": f"Piernas: {resultado_reba['detalles']['piernas']}",
                        "nivel": puntuacion,
                        "codigo_owas": f"REBA:{puntuacion}",
                        "is_foto": is_foto
                    })
                
                if puntuacion >= 8:
                    mejores_momentos_reba.append({
                        'frame': frame_num,
                        'puntuacion': puntuacion,
                        'nivel_riesgo': nivel,
                        'frame_img': frame.copy(),
                        'results': results[0],
                        'detalles': resultado_reba['detalles'],
                        'is_foto': is_foto
                    })
                
                frame_display = results[0].plot()
                color = (0, 0, 255) if puntuacion >= 11 else (0, 165, 255) if puntuacion >= 8 else (0, 255, 0)
                cv2.putText(frame_display, f"REBA: {puntuacion}/15 - {nivel}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.putText(frame_display, f"Carga: {carga} | Acople: {acople}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
                cv2.putText(frame_display, f"Tronco A:{resultado_reba['detalles']['tronco']} Cuello:{resultado_reba['detalles']['cuello']}", (10, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                cv2.putText(frame_display, f"Brazo B:{resultado_reba['detalles']['brazo']} Antebrazo:{resultado_reba['detalles']['antebrazo']}", (10, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        else:
            cv2.putText(frame_display, "No se detectó persona en la imagen", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        return frame_display


    # ==================== BUCLE PRINCIPAL ====================

    # Para ROSA, es un caso especial (basado en cuestionario)
    if metodo_elegido == 4:
        print("\n📋 Recopilando datos para evaluación ROSA...")
        datos_rosa = recopilar_datos_rosa_interactivo()
        resultado_rosa = evaluar_rosa(datos_rosa)
        
        print("\n" + "=" * 60)
        print("📊 RESULTADOS ROSA")
        print("=" * 60)
        print(f"   Silla: {resultado_rosa['silla']}/10")
        print(f"   Monitor: {resultado_rosa['monitor']}/10")
        print(f"   Teclado: {resultado_rosa['teclado']}/10")
        print(f"   Mouse: {resultado_rosa['mouse']}/10")
        print(f"\n   PUNTUACIÓN FINAL: {resultado_rosa['puntuacion_final']}/10")
        print(f"   NIVEL DE RIESGO: {resultado_rosa['nivel_riesgo']}")
        print(f"   ACCIÓN: {resultado_rosa['accion']}")
        
        # Generar dictamen con Gemini para ROSA
        print("\n🤖 Generando dictamen experto con IA para ROSA...")
        operario_dictamen = {
            'nombre': op_nombre,
            'edad': op_edad,
            'antiguedad': op_antiguedad,
            'patologias': op_patologias
        }
        datos_adicionales_rosa = {
            'uso_continuo': datos_rosa.get('uso_continuo', False)
        }
        
        dictamen_rosa = generar_dictamen_gemini_unificado(
            'ROSA', 
            resultado_rosa, 
            operario_dictamen, 
            datos_adicionales_rosa
        )
        print(f"\n📋 DICTAMEN EXPERTO (IA Gemini):\n{dictamen_rosa}")
        
        # Guardar dictamen en resultado_rosa para el PDF
        resultado_rosa['dictamen_ia'] = dictamen_rosa
        
        # Mostrar recomendaciones originales también
        print("\n📋 RECOMENDACIONES (automáticas):")
        for rec in resultado_rosa['recomendaciones']:
            print(f"   {rec}")
        print("=" * 60)
        
        # Generar reporte PDF para ROSA
        print("\n📄 Generando reporte PDF para ROSA...")
        from Methods.reports import generar_reporte_rosa
        generar_reporte_rosa(
            resultado_rosa, empresa_input, puesto_input, evaluador_input,
            op_nombre, op_edad, op_antiguedad, op_patologias,
            logo_path, datos_rosa
        )
        
    else:
        # Procesamiento para OWAS, RULA, REBA
        if modo_video:
            # Modo VIDEO - bucle de frames
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("\n📹 Fin del video alcanzado")
                    break

                frame_counter += 1

                if frame_counter % 200 == 0:
                    print(f"   Procesando frame {frame_counter}... (personas detectadas: {frames_con_persona})")

                if frame_counter % FRAME_SKIP != 0:
                    frame_display = frame
                    cv2.putText(frame_display, f"Procesando frame {frame_counter}...", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.imshow("ERGOEDGE OS - YOLO11 POSE", frame_display)
                    if cv2.waitKey(1) & 0xFF in [ord('q'), 27]:
                        print("🔴 Procesamiento detenido por el usuario")
                        break
                    continue

                frame_display = procesar_frame(frame, frame_counter, is_foto=False)
                
                cv2.imshow("ERGOEDGE OS - YOLO11 POSE", frame_display)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    print("🔴 Procesamiento detenido por el usuario")
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            # Usar el último frame para casos donde no se detectaron personas
            if frames_con_persona == 0 and 'frame' in locals():
                print("\n⚠️ No se detectaron personas en el video. Verifique la calidad del video.")
        else:
            # Modo FOTO - procesar una sola imagen
            print("\n🖼️ Procesando foto...")
            frame_display = procesar_frame(frame, 1, is_foto=True)
            
            # Mostrar resultado en ventana
            cv2.imshow("ERGOEDGE OS - YOLO11 POSE (FOTO)", frame_display)
            print("\n📸 Presione cualquier tecla para continuar...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
            # Para foto, el contador de frames es 1
            contador_frames = 1
            # Si no se detectó persona, mostrar advertencia
            if frames_con_persona == 0:
                print("\n⚠️ No se detectó ninguna persona en la foto. Verifique la calidad de la imagen.")

    # ==================== POST-PROCESAMIENTO Y REPORTE ====================

    if metodo_elegido == 1:
        # ==================== POST-PROCESAMIENTO OWAS ====================
        print("\n📸 Capturando evidencias de los momentos de mayor riesgo...")

        if mejores_momentos:
            momentos_validos = [m for m in mejores_momentos if m['frame_img'] is not None]
            if not momentos_validos:
                momentos_validos = mejores_momentos
            
            momentos_validos.sort(key=lambda x: (x['nivel_riesgo'], x['angulo_espalda']), reverse=True)
            top_momentos = []
            frames_usados = []
            for momento in momentos_validos:
                demasiado_cerca = any(abs(momento['frame'] - f) < 30 for f in frames_usados)
                if not demasiado_cerca:
                    top_momentos.append(momento)
                    frames_usados.append(momento['frame'])
                if len(top_momentos) >= 3:
                    break

            for i, momento in enumerate(top_momentos):
                sufijo = "_foto" if momento.get('is_foto', False) else ""
                path_img = f"capturas_riesgo/riesgo_{i+1}_nivel{momento['nivel_riesgo']}_frame{momento['frame']}{sufijo}.jpg"
                
                if momento['frame_img'] is not None:
                    frame_evid = momento['frame_img'].copy()
                elif 'frame' in locals():
                    frame_evid = frame.copy()
                else:
                    continue
                
                if 'results' in momento and momento['results'] is not None and hasattr(momento['results'], 'plot'):
                    try:
                        frame_evid = momento['results'].plot()
                    except:
                        pass
                        
                cv2.rectangle(frame_evid, (5, 5), (350, 130), (0, 0, 0), -1)
                cv2.putText(frame_evid, f"RIESGO - Nivel {momento['nivel_riesgo']}/4", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(frame_evid, f"OWAS: {momento['codigo_owas']}", (10, 55),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                cv2.putText(frame_evid, f"Espalda: {int(momento['angulo_espalda'])}°", (10, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame_evid, f"Brazo: {int(momento['angulo_brazo'])}°", (10, 95),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame_evid, f"{'Foto' if momento.get('is_foto') else 'Frame'}: {momento['frame']}", (10, 115),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                cv2.imwrite(path_img, frame_evid)
                imagenes_riesgo.append(path_img)
                print(f"   ✅ Captura {i+1}: Nivel {momento['nivel_riesgo']}/4 - {'Foto' if momento.get('is_foto') else 'Frame'} {momento['frame']}")

        print("\n" + "=" * 60)
        print("📊 DIAGNÓSTICO FINAL - YOLO11 POSE (OWAS)")
        print("=" * 60)
        print(f"{'📸 Foto' if not modo_video else '📹 Frames'} totales procesados: {frame_counter if modo_video else 1}")
        print(f"✅ {'Personas' if modo_video else 'Persona'} detectada: {frames_con_persona}")
        print(f"⚠️ Riesgo máximo OWAS: {peor_riesgo_nivel}/4")

        if datos_peor_momento and frames_con_persona > 0:
            total = sum(conteo_riesgos.values())
            if total > 0:
                stats = {k: round((v / total) * 100, 1) for k, v in conteo_riesgos.items()}
            else:
                stats = {1: 100, 2: 0, 3: 0, 4: 0}

            print(f"\n📊 ESTADÍSTICAS DE RIESGO OWAS:")
            nombres = {1: "Normal", 2: "Moderado", 3: "Alto", 4: "Crítico"}
            for nivel in [1, 2, 3, 4]:
                pct = stats.get(nivel, 0)
                barra = "█" * int(pct / 2)
                print(f"   Nivel {nivel} ({nombres.get(nivel, '')}): {pct:5.1f}% {barra}")

            nivel_accion, descripcion_accion, nivel_maximo_presente, frecuencia_nivel_maximo = calcular_nivel_accion_owas(stats)

            print(f"\n📊 NIVEL DE ACCIÓN OWAS (por frecuencia relativa):")
            print(f"   Nivel de riesgo máximo presente: {nivel_maximo_presente}/4")
            print(f"   Frecuencia del nivel máximo: {frecuencia_nivel_maximo:.1f}%")
            print(f"   Nivel de Acción Global: {nivel_accion}/4")
            print(f"   {descripcion_accion}")

            print("\n🤖 Generando dictamen experto con IA...")
            datos_owas_para_ia = {
                'cliente': empresa_input,
                'proyecto': puesto_input,
                'fecha': datetime.datetime.now().strftime("%d/%m/%Y"),
                'codigo_owas': datos_peor_momento['codigo_owas'],
                'riesgo_max': peor_riesgo_nivel,
                'estadisticas': stats,
                'nivel_accion': nivel_accion,
                'descripcion_accion': descripcion_accion,
                'angulo_espalda': int(datos_peor_momento.get('angulo_espalda', angulo_espalda_peor)),
                'angulo_brazo': int(datos_peor_momento.get('angulo_brazo', angulo_brazo_peor))
            }

            operario_ia = {
                'nombre': op_nombre,
                'edad': op_edad,
                'antiguedad': op_antiguedad,
                'patologias': op_patologias
            }

            conclusion_medica = generar_dictamen_con_gemini(datos_owas_para_ia, operario_ia)
            print("✅ Dictamen generado correctamente")

            analisis_f = [
                {"segmento": "Espalda", "angulo": f"{int(datos_peor_momento.get('angulo_espalda', angulo_espalda_peor))}°", "estado": datos_peor_momento['estados'].get('espalda', 'N/A')},
                {"segmento": "Brazos", "angulo": f"{int(datos_peor_momento.get('angulo_brazo', angulo_brazo_peor))}°", "estado": datos_peor_momento['estados'].get('brazos', 'N/A')},
                {"segmento": "Piernas", "angulo": "N/A", "estado": datos_peor_momento['estados'].get('piernas', 'N/A')},
                {"segmento": "Carga", "angulo": "N/A", "estado": datos_peor_momento['estados'].get('carga', 'N/A')}
            ]

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
                "recomendacion": conclusion_medica,
                "resumen_40": muestras_posturales[:40],
                "estadisticas": stats,
                "historial_linea": [stats.get(1, 0), stats.get(2, 0), stats.get(3, 0), stats.get(4, 0)],
                "nivel_accion_owas": nivel_accion,
                "descripcion_accion_owas": descripcion_accion,
                "nivel_maximo_presente": nivel_maximo_presente,
                "frecuencia_nivel_maximo": frecuencia_nivel_maximo
            }

            try:
                timestamp = int(time.time())
                sufijo_tipo = "FOTO" if not modo_video else "VIDEO"
                nombre_base = f"YOLO_OWAS_{sufijo_tipo}_{empresa_input}_{op_nombre.replace(' ', '_')}"
                nombre_pdf = f"reports/{nombre_base}_{timestamp}.pdf"

                print("\n📄 Generando reporte PDF...")
                crear_pdf(nombre_pdf, datos_reporte, imagenes_riesgo)

                print("\n" + "=" * 60)
                print("✅ INFORME COMPLETO GENERADO CON ÉXITO")
                print("=" * 60)
                print(f"📄 PDF: {nombre_pdf}")
                print(f"📸 Imágenes capturadas: {len(imagenes_riesgo)}")
                print(f"🎯 Código OWAS peor momento: {datos_peor_momento['codigo_owas']}")
                print(f"⚠️ Nivel de riesgo máximo: {peor_riesgo_nivel}/4")
                print(f"📊 Nivel de Acción Global OWAS: {nivel_accion}/4")
                print("=" * 60)

            except Exception as e:
                print(f"\n❌ Error al generar reporte: {e}")
                traceback.print_exc()
        else:
            print("\n❌ No se detectó actividad suficiente para generar el informe")
            if frames_con_persona == 0:
                print("   No se detectó ninguna persona en la imagen/video.")
                print("   Verifique la calidad de la imagen/video.")

    elif metodo_elegido == 2:  # RULA
        # ==================== POST-PROCESAMIENTO RULA ====================
        print("\n📸 Capturando evidencias de los momentos de mayor riesgo RULA...")

        if mejores_momentos_rula:
            mejores_momentos_rula.sort(key=lambda x: x['puntuacion'], reverse=True)
            top_momentos = []
            frames_usados = []
            for momento in mejores_momentos_rula:
                demasiado_cerca = any(abs(momento['frame'] - f) < 30 for f in frames_usados)
                if not demasiado_cerca:
                    top_momentos.append(momento)
                    frames_usados.append(momento['frame'])
                if len(top_momentos) >= 3:
                    break

            for i, momento in enumerate(top_momentos):
                sufijo = "_foto" if momento.get('is_foto', False) else ""
                path_img = f"capturas_riesgo/riesgo_rula_{i+1}_punt{momento['puntuacion']}_frame{momento['frame']}{sufijo}.jpg"
                
                frame_evid = momento['frame_img'].copy()
                if 'results' in momento and momento['results'] is not None and hasattr(momento['results'], 'plot'):
                    try:
                        frame_evid = momento['results'].plot()
                    except:
                        pass
                        
                cv2.rectangle(frame_evid, (5, 5), (400, 160), (0, 0, 0), -1)
                cv2.putText(frame_evid, f"RULA - Riesgo {momento['nivel_riesgo']}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(frame_evid, f"Puntuación: {momento['puntuacion']}/7", (10, 55),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                
                brazo_texto = momento['detalles']['brazo'].get('descripcion', momento['detalles']['brazo'].get('error', f"Puntuación: {momento['detalles']['brazo'].get('puntuacion', '?')}"))
                cuello_texto = momento['detalles']['cuello'].get('descripcion', momento['detalles']['cuello'].get('error', f"Puntuación: {momento['detalles']['cuello'].get('puntuacion', '?')}"))
                tronco_texto = momento['detalles']['tronco'].get('descripcion', momento['detalles']['tronco'].get('error', f"Puntuación: {momento['detalles']['tronco'].get('puntuacion', '?')}"))
                
                cv2.putText(frame_evid, f"Brazo: {brazo_texto[:50]}", (10, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                cv2.putText(frame_evid, f"Cuello: {cuello_texto[:50]}", (10, 95),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                cv2.putText(frame_evid, f"Tronco: {tronco_texto[:50]}", (10, 115),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                cv2.putText(frame_evid, f"{'Foto' if momento.get('is_foto') else 'Frame'}: {momento['frame']}", (10, 140),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                cv2.imwrite(path_img, frame_evid)
                imagenes_riesgo.append(path_img)
                print(f"   ✅ Captura {i+1}: RULA {momento['puntuacion']}/7 - {'Foto' if momento.get('is_foto') else 'Frame'} {momento['frame']}")

        print("\n" + "=" * 60)
        print("📊 DIAGNÓSTICO FINAL - YOLO11 POSE (RULA)")
        print("=" * 60)
        print(f"{'📸 Foto' if not modo_video else '📹 Frames'} totales procesados: {frame_counter if modo_video else 1}")
        print(f"✅ {'Personas' if modo_video else 'Persona'} detectada: {frames_con_persona}")
        
        if resultados_rula:
            puntuaciones = [r['puntuacion_final'] for r in resultados_rula if r is not None]
            if puntuaciones:
                punt_max = max(puntuaciones)
                punt_prom = round(sum(puntuaciones) / len(puntuaciones), 1)
                print(f"🎯 Puntuación RULA máxima: {punt_max}/7")
                print(f"📊 Puntuación RULA promedio: {punt_prom}/7")
                
                # Estadísticas por nivel
                niveles = {}
                for r in resultados_rula:
                    nivel = r['nivel_riesgo']
                    niveles[nivel] = niveles.get(nivel, 0) + 1
                
                print(f"\n📊 DISTRIBUCIÓN DE RIESGO RULA:")
                for nivel, count in niveles.items():
                    pct = (count / len(resultados_rula)) * 100
                    barra = "█" * int(pct / 2)
                    print(f"   {nivel}: {pct:5.1f}% {barra}")
        
        # Generar reporte RULA
        if resultados_rula and frames_con_persona > 0:
            generar_reporte_rula(resultados_rula, empresa_input, puesto_input, evaluador_input,
                                  op_nombre, op_edad, op_antiguedad, op_patologias,
                                  logo_path, imagenes_riesgo, muestras_posturales)
        else:
            print("\n❌ No se detectó actividad suficiente para generar el informe")
            if frames_con_persona == 0:
                print("   No se detectó ninguna persona en la imagen/video.")

    elif metodo_elegido == 3:  # REBA
        # ==================== POST-PROCESAMIENTO REBA ====================
        print("\n📸 Capturando evidencias de los momentos de mayor riesgo REBA...")

        if mejores_momentos_reba:
            mejores_momentos_reba.sort(key=lambda x: x['puntuacion'], reverse=True)
            top_momentos = []
            frames_usados = []
            for momento in mejores_momentos_reba:
                demasiado_cerca = any(abs(momento['frame'] - f) < 30 for f in frames_usados)
                if not demasiado_cerca:
                    top_momentos.append(momento)
                    frames_usados.append(momento['frame'])
                if len(top_momentos) >= 3:
                    break

            for i, momento in enumerate(top_momentos):
                sufijo = "_foto" if momento.get('is_foto', False) else ""
                path_img = f"capturas_riesgo/riesgo_reba_{i+1}_punt{momento['puntuacion']}_frame{momento['frame']}{sufijo}.jpg"
                
                frame_evid = momento['frame_img'].copy()
                if 'results' in momento and momento['results'] is not None and hasattr(momento['results'], 'plot'):
                    try:
                        frame_evid = momento['results'].plot()
                    except:
                        pass
                        
                cv2.rectangle(frame_evid, (5, 5), (450, 170), (0, 0, 0), -1)
                cv2.putText(frame_evid, f"REBA - Riesgo {momento['nivel_riesgo']}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(frame_evid, f"Puntuación: {momento['puntuacion']}/15", (10, 55),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                cv2.putText(frame_evid, f"Tronco: {momento['detalles']['tronco']} | Cuello: {momento['detalles']['cuello']} | Piernas: {momento['detalles']['piernas']}", (10, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                cv2.putText(frame_evid, f"Brazo: {momento['detalles']['brazo']} | Antebrazo: {momento['detalles']['antebrazo']} | Muñeca: {momento['detalles']['muneca']}", (10, 95),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                if momento['detalles']['abduccion'] > 20:
                    cv2.putText(frame_evid, f"⚠️ Abducción: {momento['detalles']['abduccion']:.1f}°", (10, 115),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                if momento['detalles']['torsion']:
                    cv2.putText(frame_evid, f"⚠️ Torsión de tronco detectada", (10, 135),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                cv2.putText(frame_evid, f"{'Foto' if momento.get('is_foto') else 'Frame'}: {momento['frame']}", (10, 155),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                cv2.imwrite(path_img, frame_evid)
                imagenes_riesgo.append(path_img)
                print(f"   ✅ Captura {i+1}: REBA {momento['puntuacion']}/15 - {'Foto' if momento.get('is_foto') else 'Frame'} {momento['frame']}")

        print("\n" + "=" * 60)
        print("📊 DIAGNÓSTICO FINAL - YOLO11 POSE (REBA 3D)")
        print("=" * 60)
        print(f"{'📸 Foto' if not modo_video else '📹 Frames'} totales procesados: {frame_counter if modo_video else 1}")
        print(f"✅ {'Personas' if modo_video else 'Persona'} detectada: {frames_con_persona}")
        
        if resultados_reba:
            puntuaciones = [r['puntuacion_final'] for r in resultados_reba if r is not None]
            if puntuaciones:
                punt_max = max(puntuaciones)
                punt_prom = round(sum(puntuaciones) / len(puntuaciones), 1)
                print(f"🎯 Puntuación REBA máxima: {punt_max}/15")
                print(f"📊 Puntuación REBA promedio: {punt_prom}/15")
                
                # Estadísticas por nivel
                niveles = {}
                for r in resultados_reba:
                    nivel = r['nivel_riesgo']
                    niveles[nivel] = niveles.get(nivel, 0) + 1
                
                print(f"\n📊 DISTRIBUCIÓN DE RIESGO REBA:")
                for nivel, count in niveles.items():
                    pct = (count / len(resultados_reba)) * 100
                    barra = "█" * int(pct / 2)
                    print(f"   {nivel}: {pct:5.1f}% {barra}")
                
                # Mostrar detalles del peor momento
                peor = max(resultados_reba, key=lambda x: x['puntuacion_final'])
                print(f"\n📋 DETALLES DEL PEOR MOMENTO:")
                print(f"   Puntuación A (Tronco+Cuello+Piernas): {peor['puntuacion_A']}")
                print(f"   Puntuación B (Brazo+Antebrazo+Muñeca): {peor['puntuacion_B']}")
                print(f"   Carga: {peor['detalles']['carga']} | Acople: {peor['detalles']['acople']}")
                print(f"   Abducción máxima detectada: {peor['detalles']['abduccion']:.1f}°")
                print(f"   Torsión de tronco: {'Sí' if peor['detalles']['torsion'] else 'No'}")
        
        # Generar reporte REBA
        if resultados_reba and frames_con_persona > 0:
            from Methods.reports import generar_reporte_reba
            generar_reporte_reba(resultados_reba, empresa_input, puesto_input, evaluador_input,
                                  op_nombre, op_edad, op_antiguedad, op_patologias,
                                  logo_path, imagenes_riesgo, muestras_posturales,
                                  carga, acople)
        else:
            print("\n❌ No se detectó actividad suficiente para generar el informe")
            if frames_con_persona == 0:
                print("   No se detectó ninguna persona en la imagen/video.")

    else:  # metodo_elegido == 4 - ROSA
        # ==================== POST-PROCESAMIENTO ROSA ====================
        # ROSA ya mostró resultados y generó el reporte PDF durante el procesamiento
        print("\n✅ ROSA completado. El reporte PDF se ha generado con dictamen IA.")

    print("\n✨ Proceso completado")
