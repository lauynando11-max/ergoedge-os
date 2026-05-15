"""
Utilidades para Gemini - IA Generativa
"""

from google import genai

API_KEY_GEMINI = "AIzaSyBkZ47zhVjrYrDdmZBxFs3GGdAY6ZY198o"
GEMINI_MODEL = "gemini-2.5-flash"

cliente_gemini = None

def validar_api_gemini():
    global cliente_gemini
    try:
        cliente = genai.Client(api_key=API_KEY_GEMINI)
        print("✅ API Key de Gemini validada correctamente")
        cliente_gemini = cliente
        return cliente
    except Exception as e:
        print(f"⚠️ Advertencia: Error con API Key de Gemini: {e}")
        return None

def generar_dictamen_gemini_unificado(metodo, resultados, datos_operario, datos_adicionales=None):
    """Genera dictamen experto usando Gemini"""
    global cliente_gemini
    
    if cliente_gemini is None:
        validar_api_gemini()
    
    if cliente_gemini is None:
        return generar_dictamen_fallback_unificado(metodo, resultados, datos_operario, datos_adicionales)
    
    nombre = datos_operario.get('nombre', 'Operario')
    edad = datos_operario.get('edad', 'N/A')
    antiguedad = datos_operario.get('antiguedad', 'N/A')
    patologias = datos_operario.get('patologias', 'Ninguna')
    
    if metodo == 'OWAS':
        system_instruction = """
Actuás como un Ingeniero Senior en Ergonomía especializado en análisis OWAS.
Tu redacción debe ser técnica y precisa.

REGLAS DE ORO:
- Usar terminología técnica biomecánica
- Si el operario tiene patologías, el dictamen debe ser crítico y protector
- Proponer cambios de ingeniería, no solo cambios de conducta
- El dictamen debe ser detallado pero conciso (máximo 400 palabras)
- Usar viñetas (•) para las recomendaciones
"""
        user_prompt = f"""
Generá un Dictamen Técnico-Ergonómico basado en resultados OWAS:

DATOS DEL OPERARIO:
- Nombre: {nombre}
- Edad: {edad} años
- Antigüedad: {antiguedad} años
- Patologías: {patologias}

RESULTADOS OWAS:
- Código OWAS: {resultados.get('codigo_owas', 'N/A')}
- Riesgo máximo: {resultados.get('riesgo_max', 0)}/4
- Nivel de Acción: {resultados.get('nivel_accion', 0)}/4

Por favor, emití un dictamen profesional con:
1. Conclusión del riesgo
2. Recomendaciones de ingeniería
3. Nota sobre seguimiento médico
"""
    elif metodo == 'RULA':
        system_instruction = """
Actuás como un Especialista en Ergonomía de Miembros Superiores.
"""
        user_prompt = f"""
Generá un Dictamen Técnico-Ergonómico basado en resultados RULA:

DATOS DEL OPERARIO:
- Nombre: {nombre}
- Edad: {edad} años
- Patologías: {patologias}

RESULTADOS RULA:
- Puntuación máxima: {resultados.get('puntuacion_max', 0)}/7
- Nivel de riesgo: {resultados.get('nivel_riesgo', 'N/A')}

Por favor, emití un dictamen profesional.
"""
    elif metodo == 'REBA':
        system_instruction = """
Actuás como un Ingeniero Biomecánico especializado en REBA.
"""
        user_prompt = f"""
Generá un Dictamen Técnico-Ergonómico basado en resultados REBA:

DATOS DEL OPERARIO:
- Nombre: {nombre}
- Edad: {edad} años
- Patologías: {patologias}

RESULTADOS REBA:
- Puntuación máxima: {resultados.get('puntuacion_max', 0)}/15
- Nivel de riesgo: {resultados.get('nivel_riesgo', 'N/A')}

Por favor, emití un dictamen profesional.
"""
    elif metodo == 'ROSA':
        system_instruction = """
Actuás como un Especialista en Ergonomía de Oficina.
"""
        user_prompt = f"""
Generá un Dictamen Técnico-Ergonómico basado en resultados ROSA:

DATOS DEL OPERARIO:
- Nombre: {nombre}
- Edad: {edad} años
- Patologías: {patologias}

RESULTADOS ROSA:
- Puntuación final: {resultados.get('puntuacion_final', 0)}/10
- Nivel de riesgo: {resultados.get('nivel_riesgo', 'N/A')}

Por favor, emití un dictamen profesional.
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
            return generar_dictamen_fallback_unificado(metodo, resultados, datos_operario, datos_adicionales)
    except Exception as e:
        print(f"❌ Error generando dictamen con Gemini: {e}")
        return generar_dictamen_fallback_unificado(metodo, resultados, datos_operario, datos_adicionales)


def generar_dictamen_fallback_unificado(metodo, resultados, datos_operario, datos_adicionales):
    """Dictamen de respaldo si Gemini no está disponible"""
    nombre = datos_operario.get('nombre', 'Operario')
    patologias = datos_operario.get('patologias', '')
    
    if metodo == 'OWAS':
        nivel = resultados.get('riesgo_max', resultados.get('puntuacion', 1))
        codigo = resultados.get('codigo_owas', 'N/A')
        
        if nivel >= 4:
            return f"""🤖 DICTAMEN IA - RIESGO CRÍTICO

El operario {nombre} {'con patologías previas' if patologias else 'sin patologías previas'} presenta una exposición MUY DAÑINA según el método OWAS (Código: {codigo}, Nivel: {nivel}/4).

RECOMENDACIONES URGENTES:
• Suspender la tarea hasta rediseño ergonómico inmediato
• Instalar ayudas mecánicas obligatorias (polipastos, mesas elevadoras)
• Implementar rotación de personal cada 30 minutos
• Evaluación médica por medicina laboral en un plazo NO MAYOR a 7 días

Este dictamen es prioritario. Se requiere intervención gerencial inmediata."""
        
        elif nivel >= 3:
            return f"""🤖 DICTAMEN IA - RIESGO ALTO

El trabajador {nombre} requiere intervención en el corto plazo (30 días).

Recomendaciones:
• Rediseñar el puesto para mantener espalda <20° de flexión
• Instalar apoyabrazos ergonómicos ajustables
• Implementar pausas activas cada 45 minutos
• Seguimiento médico semestral"""
        
        elif nivel >= 2:
            return f"""🤖 DICTAMEN IA - RIESGO MODERADO

El puesto evaluado requiere ajustes programados.

Recomendaciones:
• Reorganizar elementos de trabajo al alcance frontal
• Capacitar al operario en técnicas de auto-corrección postural
• Monitoreo ergonómico trimestral"""
        
        else:
            return f"""🤖 DICTAMEN IA - RIESGO BAJO

Las condiciones posturales del operario {nombre} son aceptables.

Recomendaciones preventivas:
• Mantener programa de pausas activas diarias
• Auditorías ergonómicas anuales"""
    
    elif metodo == 'RULA':
        punt = resultados.get('puntuacion_max', resultados.get('puntuacion', 1))
        if punt >= 6:
            return f"""🤖 DICTAMEN IA - RIESGO MUY ALTO

El operario {nombre} presenta riesgo crítico en miembros superiores (puntuación RULA: {punt}/7).

Recomendaciones URGENTES:
• Rediseñar inmediatamente la tarea
• Instalar apoyabrazos y soporte ergonómico
• Evaluación médica urgente"""
        elif punt >= 4:
            return f"""🤖 DICTAMEN IA - RIESGO MEDIO

Recomendaciones: Ajustar altura del plano de trabajo y reducir alcances."""
        else:
            return f"""🤖 DICTAMEN IA - RIESGO BAJO

Mantener buenas prácticas posturales."""
    
    elif metodo == 'REBA':
        punt = resultados.get('puntuacion_max', resultados.get('puntuacion', 1))
        if punt >= 11:
            return f"""🤖 DICTAMEN IA - RIESGO MUY ALTO

¡INTERVENCIÓN INMEDIATA REQUERIDA!
Puntuación REBA: {punt}/15. Suspender tarea hasta rediseño completo."""
        elif punt >= 8:
            return f"""🤖 DICTAMEN IA - RIESGO ALTO

Rediseñar el puesto en 30 días. Mejorar agarre y reducir carga."""
        else:
            return f"""🤖 DICTAMEN IA - RIESGO BAJO

Mantener buenas prácticas."""
    
    elif metodo == 'ROSA':
        punt = resultados.get('puntuacion_final', 1)
        if punt >= 8:
            return f"""🤖 DICTAMEN IA - RIESGO MUY ALTO

Intervención inmediata en el puesto de oficina (puntuación ROSA: {punt}/10)."""
        else:
            return f"""🤖 DICTAMEN IA - RIESGO {resultados.get('nivel_riesgo', 'MEDIO')}

Revisar ajustes de silla, monitor y teclado."""
    
    return "No se pudo generar dictamen. Consulte a un especialista."


# ============================================================
# IMPORTANTE: No ejecutar validación automática al importar
# ============================================================
# La siguiente línea está comentada para evitar que se ejecute
# automáticamente cuando se importa este módulo.
# validar_api_gemini()