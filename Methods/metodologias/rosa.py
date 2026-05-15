"""
ROSA - Rapid Office Strain Assessment
Método para evaluación ergonómica en puestos de oficina
Referencia: Sonne, Villalta, Andrews (2012) - University of Waterloo
"""

import numpy as np

# ============================================================
# FUNCIONES DE PUNTUACIÓN
# ============================================================

def puntuar_altura_asiento(altura_relativa, altura_usuario=None):
    """
    Puntúa altura del asiento
    1 = rodillas a 90°, pies apoyados
    2 = rodillas > 90° o < 90° (estándar)
    3 = significativamente incorrecta
    """
    if altura_relativa == 0:  # Datos no disponibles
        return 2
    return altura_relativa


def puntuar_apoyo_lumbar(apoyo):
    """
    Puntúa apoyo lumbar (versión mejorada)
    1 = apoyo lumbar ajustado y cómodo a la curvatura lordótica
    2 = apoyo lumbar presente pero no ajustado (estándar)
    3 = sin apoyo lumbar
    """
    mapeo = {
        'ajustado': 1,
        'presente': 2,
        'ausente': 3,
        'no_se': 2
    }
    return mapeo.get(apoyo, 2)


def puntuar_profundidad_asiento(profundidad):
    """
    Puntúa profundidad del asiento
    1 = espacio de 2-3 dedos detrás de la rodilla
    2 = espacio parcial
    3 = demasiado profundo o poco profundo
    """
    mapeo = {
        'adecuado': 1,
        'parcial': 2,
        'inadecuado': 3,
        'no_se': 2
    }
    return mapeo.get(profundidad, 2)


def puntuar_apoyabrazos_altura(altura):
    """
    Puntúa altura de apoyabrazos
    1 = hombros relajados, ángulo codo 90-110°
    2 = hombros ligeramente elevados (estándar)
    3 = hombros significativamente elevados (encogidos)
    """
    mapeo = {
        'adecuado': 1,
        'ligero': 2,
        'incorrecto': 3,
        'no_se': 2
    }
    return mapeo.get(altura, 2)


def puntuar_apoyabrazos_ancho(ancho):
    """
    Puntúa separación de apoyabrazos
    1 = separación adecuada para el cuerpo
    2 = separación parcial
    3 = demasiado separados o juntos
    """
    mapeo = {
        'adecuado': 1,
        'parcial': 2,
        'inadecuado': 3,
        'no_se': 2
    }
    return mapeo.get(ancho, 2)


def puntuar_altura_monitor(altura_ojos, altura_monitor):
    """
    Puntúa altura del monitor
    Regla: borde superior del monitor debe estar a la altura de los ojos o ligeramente más bajo
    """
    if altura_monitor is None:
        return 2
    
    diferencia = altura_ojos - altura_monitor
    if abs(diferencia) < 5:  # Diferencia < 5cm
        return 1
    elif abs(diferencia) < 10:
        return 2
    else:
        return 3


def puntuar_distancia_monitor(distancia):
    """
    Puntúa distancia del monitor
    1 = brazo extendido (45-70cm)
    2 = distancia moderada (30-45cm o 70-90cm)
    3 = demasiado cerca (<30cm) o demasiado lejos (>90cm)
    """
    if distancia < 30:
        return 3
    elif distancia < 45:
        return 2
    elif distancia <= 70:
        return 1
    elif distancia <= 90:
        return 2
    else:
        return 3


def puntuar_inclinacion_monitor(inclinacion):
    """
    Puntúa inclinación del monitor
    1 = perpendicular a la línea de visión
    2 = ligera inclinación
    3 = inclinación significativa
    """
    mapeo = {
        'perpendicular': 1,
        'ligera': 2,
        'significativa': 3,
        'no_se': 2
    }
    return mapeo.get(inclinacion, 2)


def puntuar_reflejos_monitor(tiene_reflejos):
    """
    Puntúa presencia de reflejos en monitor
    1 = sin reflejos
    2 = reflejos ocasionales
    3 = reflejos molestos constantes
    """
    if not tiene_reflejos:
        return 1
    return 2  # Asumimos reflejos ocasionales


def puntuar_altura_teclado(altura):
    """
    Puntúa altura del teclado
    1 = codos a 90-110°, muñecas rectas
    2 = codos ligeramente elevados o muñecas extendidas
    3 = codos significativamente elevados o muñecas flexionadas
    """
    mapeo = {
        'adecuado': 1,
        'ligero': 2,
        'incorrecto': 3,
        'no_se': 2
    }
    return mapeo.get(altura, 2)


def puntuar_distancia_teclado(distancia):
    """
    Puntúa distancia del teclado
    1 = antebrazo horizontal, codo a 90-110°
    2 = antebrazo extendido (>110°)
    3 = antebrazo flexionado (<90°)
    """
    if distancia is None:
        return 2
    if 90 <= distancia <= 110:
        return 1
    elif distancia < 90:
        return 3
    else:
        return 2


def puntuar_inclinacion_teclado(inclinacion):
    """
    Puntúa inclinación del teclado
    1 = neutro (0-5°)
    2 = inclinación positiva (5-15°)
    3 = inclinación negativa o >15°
    """
    mapeo = {
        'neutro': 1,
        'positiva': 2,
        'negativa': 3,
        'no_se': 2
    }
    return mapeo.get(inclinacion, 2)


def puntuar_reposamunecas(soporte):
    """
    Puntúa reposamuñecas
    1 = reposamuñecas acolchado ajustado
    2 = reposamuñecas básico
    3 = sin reposamuñecas
    """
    mapeo = {
        'acolchado': 1,
        'basico': 2,
        'ausente': 3,
        'no_se': 2
    }
    return mapeo.get(soporte, 2)


def puntuar_altura_mouse(altura):
    """
    Puntúa altura del mouse (misma superficie que teclado)
    1 = misma altura que teclado
    2 = altura ligeramente diferente
    3 = altura significativamente diferente
    """
    mapeo = {
        'misma': 1,
        'ligera': 2,
        'diferente': 3,
        'no_se': 2
    }
    return mapeo.get(altura, 2)


def puntuar_distancia_mouse(distancia):
    """
    Puntúa distancia del mouse
    1 = al alcance natural, codo a 90-110°
    2 = ligeramente alejado (<20cm extra)
    3 = significativamente alejado (>20cm extra)
    """
    if distancia is None:
        return 2
    if distancia < 10:
        return 1
    elif distancia < 20:
        return 2
    else:
        return 3


def puntuar_posicion_mouse(posicion):
    """
    Puntúa posición del mouse relativa al cuerpo
    1 = frente al hombro
    2 = ligeramente lateral
    3 = significativamente lateral (brazo abducido)
    """
    mapeo = {
        'frontal': 1,
        'ligera': 2,
        'lateral': 3,
        'no_se': 2
    }
    return mapeo.get(posicion, 2)


def puntuar_telefono_manos_libres(manos_libres):
    """
    Puntúa uso de manos libres en teléfono
    1 = usa manos libres
    2 = no usa manos libres
    """
    return 1 if manos_libres else 2


def puntuar_telefono_distancia(distancia):
    """
    Puntúa distancia del teléfono
    1 = alcance inmediato
    2 = alejado
    """
    mapeo = {
        'inmediato': 1,
        'alejado': 2
    }
    return mapeo.get(distancia, 1)


# ============================================================
# PUNTUACIÓN DE COMPONENTES (VERSIÓN MEJORADA)
# ============================================================

def puntuar_silla(datos_silla):
    """
    Calcula puntuación del componente SILLA (versión mejorada)
    
    Criterios ROSA oficiales:
    - Altura del asiento
    - Profundidad del asiento
    - Apoyo lumbar
    - Reposabrazos (altura y separación)
    """
    puntajes = []
    
    if 'altura' in datos_silla:
        puntajes.append(puntuar_altura_asiento(datos_silla['altura']))
    
    if 'profundidad_asiento' in datos_silla:
        puntajes.append(puntuar_profundidad_asiento(datos_silla['profundidad_asiento']))
    
    if 'apoyo_lumbar' in datos_silla:
        puntajes.append(puntuar_apoyo_lumbar(datos_silla['apoyo_lumbar']))
    
    if 'apoyabrazos_altura' in datos_silla:
        puntajes.append(puntuar_apoyabrazos_altura(datos_silla['apoyabrazos_altura']))
    
    if 'apoyabrazos_ancho' in datos_silla:
        puntajes.append(puntuar_apoyabrazos_ancho(datos_silla['apoyabrazos_ancho']))
    
    if not puntajes:
        return 5
    
    promedio = sum(puntajes) / len(puntajes)
    
    # Convertir a escala 1-10
    if promedio <= 1.5:
        return 2
    elif promedio <= 2.0:
        return 3
    elif promedio <= 2.5:
        return 4
    elif promedio <= 3.0:
        return 5
    else:
        return min(10, int(promedio * 2.5))


def puntuar_monitor(datos_monitor, altura_ojos=None):
    """
    Calcula puntuación del componente MONITOR (versión mejorada)
    
    Criterios:
    - Altura del monitor
    - Distancia
    - Inclinación
    - Reflejos
    """
    puntajes = []
    
    if 'altura' in datos_monitor and altura_ojos is not None:
        puntajes.append(puntuar_altura_monitor(altura_ojos, datos_monitor['altura']))
    elif 'altura' in datos_monitor:
        puntajes.append(datos_monitor['altura'])
    
    if 'distancia' in datos_monitor:
        puntajes.append(puntuar_distancia_monitor(datos_monitor['distancia']))
    
    if 'inclinacion' in datos_monitor:
        puntajes.append(puntuar_inclinacion_monitor(datos_monitor['inclinacion']))
    
    if 'reflejos' in datos_monitor and datos_monitor['reflejos']:
        puntajes.append(puntuar_reflejos_monitor(True))
    
    if not puntajes:
        return 5
    
    promedio = sum(puntajes) / len(puntajes)
    
    if promedio <= 1.5:
        return 2
    elif promedio <= 2.0:
        return 3
    elif promedio <= 2.5:
        return 4
    elif promedio <= 3.0:
        return 5
    else:
        return min(10, int(promedio * 2.5))


def puntuar_teclado(datos_teclado):
    """
    Calcula puntuación del componente TECLADO (versión mejorada)
    """
    puntajes = []
    
    if 'altura' in datos_teclado:
        puntajes.append(puntuar_altura_teclado(datos_teclado['altura']))
    if 'distancia' in datos_teclado:
        puntajes.append(puntuar_distancia_teclado(datos_teclado['distancia']))
    if 'inclinacion' in datos_teclado:
        puntajes.append(puntuar_inclinacion_teclado(datos_teclado['inclinacion']))
    if 'reposamunecas' in datos_teclado:
        puntajes.append(puntuar_reposamunecas(datos_teclado['reposamunecas']))
    
    if not puntajes:
        return 5
    
    promedio = sum(puntajes) / len(puntajes)
    
    if promedio <= 1.5:
        return 2
    elif promedio <= 2.0:
        return 3
    elif promedio <= 2.5:
        return 4
    elif promedio <= 3.0:
        return 5
    else:
        return min(10, int(promedio * 2.5))


def puntuar_mouse(datos_mouse):
    """
    Calcula puntuación del componente MOUSE (versión mejorada)
    """
    puntajes = []
    
    if 'altura' in datos_mouse:
        puntajes.append(puntuar_altura_mouse(datos_mouse['altura']))
    if 'distancia' in datos_mouse:
        puntajes.append(puntuar_distancia_mouse(datos_mouse['distancia']))
    if 'posicion' in datos_mouse:
        puntajes.append(puntuar_posicion_mouse(datos_mouse['posicion']))
    
    if not puntajes:
        return 5
    
    promedio = sum(puntajes) / len(puntajes)
    
    if promedio <= 1.5:
        return 2
    elif promedio <= 2.0:
        return 3
    elif promedio <= 2.5:
        return 4
    elif promedio <= 3.0:
        return 5
    else:
        return min(10, int(promedio * 2.5))


def puntuar_telefono(datos_telefono):
    """
    Calcula puntuación del componente TELÉFONO
    """
    if not datos_telefono:
        return 1
    
    puntajes = []
    
    if 'manos_libres' in datos_telefono:
        puntajes.append(puntuar_telefono_manos_libres(datos_telefono['manos_libres']))
    
    if 'distancia' in datos_telefono:
        puntajes.append(puntuar_telefono_distancia(datos_telefono['distancia']))
    
    if not puntajes:
        return 1
    
    return min(3, int(sum(puntajes) / len(puntajes)))


# ============================================================
# LISTA DE VERIFICACIÓN VISUAL (CHECKLIST)
# ============================================================

def generar_checklist_visual(datos_usuario):
    """
    Genera una lista de verificación visual basada en las respuestas del usuario
    Retorna lista de puntos verificados y recomendaciones
    """
    checklist = []
    recomendaciones_checklist = []
    
    # ===== SILLA =====
    if 'silla' in datos_usuario:
        silla = datos_usuario['silla']
        
        # Altura
        if silla.get('altura', 2) <= 2:
            checklist.append("✅ Altura del asiento: pies apoyados en el suelo o en reposapiés")
        else:
            checklist.append("❌ Altura del asiento: ajustar para que los pies queden planos")
            recomendaciones_checklist.append("Ajustar altura del asiento")
        
        # Profundidad
        if silla.get('profundidad_asiento', 'no_se') == 'adecuado':
            checklist.append("✅ Profundidad del asiento: espacio de 2-3 dedos detrás de la rodilla")
        else:
            checklist.append("❌ Profundidad del asiento: ajustar para evitar presión en la parte posterior de la rodilla")
            recomendaciones_checklist.append("Ajustar profundidad del asiento")
        
        # Apoyo lumbar
        apoyo = silla.get('apoyo_lumbar', 'no_se')
        if apoyo == 'ajustado':
            checklist.append("✅ Apoyo lumbar: correctamente ajustado a la curvatura de la espalda")
        elif apoyo == 'presente':
            checklist.append("⚠️ Apoyo lumbar presente pero no ajustado")
            recomendaciones_checklist.append("Ajustar apoyo lumbar a la curvatura de la espalda")
        else:
            checklist.append("❌ Apoyo lumbar: ausente o mal ajustado")
            recomendaciones_checklist.append("Instalar apoyo lumbar ajustable")
        
        # Reposabrazos altura
        altura_brazo = silla.get('apoyabrazos_altura', 'no_se')
        if altura_brazo == 'adecuado':
            checklist.append("✅ Reposabrazos: altura correcta (hombros relajados, codos a 90°)")
        else:
            checklist.append("⚠️ Reposabrazos: ajustar altura")
            recomendaciones_checklist.append("Ajustar altura de reposabrazos")
        
        # Reposabrazos ancho
        ancho_brazo = silla.get('apoyabrazos_ancho', 'no_se')
        if ancho_brazo == 'adecuado':
            checklist.append("✅ Reposabrazos: separación adecuada para el cuerpo")
        else:
            checklist.append("⚠️ Reposabrazos: ajustar separación")
            recomendaciones_checklist.append("Ajustar separación de reposabrazos")
    
    # ===== MONITOR =====
    if 'monitor' in datos_usuario:
        monitor = datos_usuario['monitor']
        
        if monitor.get('altura', 2) <= 2:
            checklist.append("✅ Altura del monitor: borde superior a la altura de los ojos")
        else:
            checklist.append("❌ Altura del monitor: ajustar para evitar flexión cervical")
            recomendaciones_checklist.append("Ajustar altura del monitor")
        
        distancia = monitor.get('distancia', 60)
        if 45 <= distancia <= 70:
            checklist.append("✅ Distancia del monitor: brazo extendido (45-70cm)")
        else:
            checklist.append("⚠️ Distancia del monitor: ajustar (ideal 45-70cm)")
            recomendaciones_checklist.append("Ajustar distancia del monitor")
        
        if not monitor.get('reflejos', False):
            checklist.append("✅ Monitor: sin reflejos molestos")
        else:
            checklist.append("❌ Monitor: eliminar reflejos (cambiar ángulo o posición)")
            recomendaciones_checklist.append("Eliminar reflejos en pantalla")
    
    # ===== TECLADO =====
    if 'teclado' in datos_usuario:
        teclado = datos_usuario['teclado']
        
        if teclado.get('altura', 'no_se') == 'adecuado':
            checklist.append("✅ Altura del teclado: muñecas rectas al teclear")
        else:
            checklist.append("⚠️ Altura del teclado: ajustar para mantener muñecas rectas")
            recomendaciones_checklist.append("Ajustar altura del teclado")
        
        distancia_tec = teclado.get('distancia', 95)
        if distancia_tec and 90 <= distancia_tec <= 110:
            checklist.append("✅ Distancia del teclado: codos en ángulo de 90-110°")
        else:
            checklist.append("⚠️ Distancia del teclado: ajustar para lograr ángulo de codo adecuado")
            recomendaciones_checklist.append("Ajustar distancia del teclado")
        
        if teclado.get('reposamunecas', 'no_se') in ['acolchado', 'basico']:
            checklist.append("✅ Reposamuñecas: presente")
        else:
            checklist.append("⚠️ Reposamuñecas: recomendado para apoyar muñecas en pausas")
            recomendaciones_checklist.append("Instalar reposamuñecas acolchado")
    
    # ===== MOUSE =====
    if 'mouse' in datos_usuario:
        mouse = datos_usuario['mouse']
        
        if mouse.get('altura', 'no_se') == 'misma':
            checklist.append("✅ Altura del mouse: misma que teclado")
        else:
            checklist.append("⚠️ Altura del mouse: debe estar a la misma altura que el teclado")
            recomendaciones_checklist.append("Ajustar altura del mouse")
        
        if mouse.get('posicion', 'no_se') == 'frontal':
            checklist.append("✅ Posición del mouse: alcance frontal sin abducción de hombro")
        else:
            checklist.append("⚠️ Posición del mouse: acercar para evitar abducción del hombro")
            recomendaciones_checklist.append("Acercar el mouse al teclado")
    
    # ===== TIEMPO DE USO =====
    if datos_usuario.get('uso_continuo', False):
        checklist.append("⚠️ Tiempo de uso continuo >1 hora: implementar pausas cada 45-60 minutos")
        recomendaciones_checklist.append("Implementar pausas activas cada 45-60 minutos")
    else:
        checklist.append("✅ Tiempo de uso: se recomienda pausa cada 2 horas")
    
    # ===== TELÉFONO =====
    if 'telefono' in datos_usuario and datos_usuario['telefono']:
        telefono = datos_usuario['telefono']
        if telefono.get('manos_libres', True):
            checklist.append("✅ Teléfono: uso de manos libres/auricular")
        else:
            checklist.append("⚠️ Teléfono: usar manos libres para evitar posturas forzadas de cuello")
            recomendaciones_checklist.append("Utilizar auricular o manos libres para llamadas")
    
    return checklist, recomendaciones_checklist


# ============================================================
# FUNCIÓN PRINCIPAL DE EVALUACIÓN ROSA (VERSIÓN MEJORADA)
# ============================================================

def evaluar_rosa(datos_usuario, keypoints=None, frame=None):
    """
    Evaluación completa ROSA con factor tiempo de uso
    
    Args:
        datos_usuario: dict con respuestas del usuario y mediciones
        keypoints: puntos clave de YOLO (opcional, para ayudar con estimaciones)
        frame: imagen (opcional)
    
    Returns:
        dict con resultados completos
    """
    
    # Inicializar secciones
    resultados = {
        'silla': None,
        'monitor': None,
        'teclado': None,
        'mouse': None,
        'telefono': None,
        'puntuacion_base': 0,
        'factor_tiempo': 0,
        'puntuacion_final': 0,
        'nivel_riesgo': '',
        'accion': '',
        'color': '',
        'recomendaciones': [],
        'checklist': [],
        'recomendaciones_checklist': []
    }
    
    # Evaluar cada componente
    if 'silla' in datos_usuario:
        resultados['silla'] = puntuar_silla(datos_usuario['silla'])
    
    # Para monitor, necesitamos altura de ojos (puede venir de keypoints)
    altura_ojos = None
    if keypoints is not None and len(keypoints) > 0:
        if frame is not None:
            altura_ojos = keypoints[0][1]
    
    if 'monitor' in datos_usuario:
        resultados['monitor'] = puntuar_monitor(datos_usuario['monitor'], altura_ojos)
    
    if 'teclado' in datos_usuario:
        resultados['teclado'] = puntuar_teclado(datos_usuario['teclado'])
    
    if 'mouse' in datos_usuario:
        resultados['mouse'] = puntuar_mouse(datos_usuario['mouse'])
    
    if 'telefono' in datos_usuario:
        resultados['telefono'] = puntuar_telefono(datos_usuario['telefono'])
    
    # Calcular puntuación base (promedio de componentes evaluados)
    puntuaciones = []
    for key in ['silla', 'monitor', 'teclado', 'mouse']:
        if resultados[key] is not None:
            puntuaciones.append(resultados[key])
    
    if puntuaciones:
        puntuacion_base = sum(puntuaciones) / len(puntuaciones)
    else:
        puntuacion_base = 5
    
    # ===== APLICAR FACTOR TIEMPO DE USO =====
    # Si usa equipo continuamente >1 hora, se añade 1 punto
    factor_tiempo = 1 if datos_usuario.get('uso_continuo', False) else 0
    puntuacion_final = puntuacion_base + factor_tiempo
    
    # Limitar a escala 1-10
    puntuacion_final = max(1, min(10, puntuacion_final))
    
    resultados['puntuacion_base'] = round(puntuacion_base, 1)
    resultados['factor_tiempo'] = factor_tiempo
    resultados['puntuacion_final'] = round(puntuacion_final, 1)
    
    # Determinar nivel de riesgo
    if resultados['puntuacion_final'] <= 2:
        resultados['nivel_riesgo'] = "Aceptable"
        resultados['accion'] = "No requiere acción"
        resultados['color'] = "#28a745"
    elif resultados['puntuacion_final'] <= 4:
        resultados['nivel_riesgo'] = "Bajo"
        resultados['accion'] = "Monitorear, cambios menores"
        resultados['color'] = "#98c379"
    elif resultados['puntuacion_final'] <= 6:
        resultados['nivel_riesgo'] = "Medio"
        resultados['accion'] = "Investigar cambios en el puesto"
        resultados['color'] = "#ffc107"
    elif resultados['puntuacion_final'] <= 8:
        resultados['nivel_riesgo'] = "Alto"
        resultados['accion'] = "Acción correctiva pronto"
        resultados['color'] = "#fd7e14"
    else:
        resultados['nivel_riesgo'] = "Muy alto"
        resultados['accion'] = "Intervención inmediata requerida"
        resultados['color'] = "#dc3545"
    
    # Generar recomendaciones específicas
    recomendaciones = []
    
    if resultados['silla'] and resultados['silla'] >= 6:
        recomendaciones.append("🔴 Ajustar la silla: altura, profundidad, apoyo lumbar o reposabrazos")
    elif resultados['silla'] and resultados['silla'] >= 4:
        recomendaciones.append("⚠️ Revisar configuración de la silla")
    
    if resultados['monitor'] and resultados['monitor'] >= 6:
        recomendaciones.append("🔴 Ajustar monitor: altura, distancia o inclinación")
        if datos_usuario.get('monitor', {}).get('reflejos', False):
            recomendaciones.append("🔴 Eliminar reflejos en pantalla (cambiar ángulo o agregar filtro)")
    elif resultados['monitor'] and resultados['monitor'] >= 4:
        recomendaciones.append("⚠️ Revisar posición del monitor")
    
    if resultados['teclado'] and resultados['teclado'] >= 6:
        recomendaciones.append("🔴 Ajustar teclado: altura, distancia o inclinación")
    elif resultados['teclado'] and resultados['teclado'] >= 4:
        recomendaciones.append("⚠️ Revisar posición del teclado")
    
    if resultados['mouse'] and resultados['mouse'] >= 6:
        recomendaciones.append("🔴 Ajustar posición del mouse")
    elif resultados['mouse'] and resultados['mouse'] >= 4:
        recomendaciones.append("⚠️ Revisar posición del mouse")
    
    # Recomendación adicional por tiempo de uso
    if factor_tiempo:
        recomendaciones.append("⚠️ Implementar pausas cada 45-60 minutos por uso continuo prolongado")
    
    if not recomendaciones:
        recomendaciones.append("✓ Puesto de trabajo en condiciones aceptables")
    
    resultados['recomendaciones'] = recomendaciones
    
    # Generar checklist visual
    checklist, rec_checklist = generar_checklist_visual(datos_usuario)
    resultados['checklist'] = checklist
    resultados['recomendaciones_checklist'] = rec_checklist
    
    return resultados


# ============================================================
# FUNCIÓN PARA RECOLECTAR DATOS DEL USUARIO (VERSIÓN MEJORADA)
# ============================================================

def recopilar_datos_rosa_interactivo():
    """
    Función interactiva para recopilar datos ROSA por consola
    Retorna diccionario con todas las respuestas
    """
    print("\n" + "=" * 60)
    print("📋 EVALUACIÓN ROSA - RAPID OFFICE STRAIN ASSESSMENT")
    print("=" * 60)
    print("Complete los siguientes datos sobre el puesto de oficina:\n")
    
    datos = {}
    
    # ===== FACTOR TIEMPO DE USO (CRÍTICO) =====
    print("--- FACTOR TIEMPO DE USO ---")
    uso_continuo = input("   ¿El trabajador utiliza este equipo de forma continuada durante más de 1 hora sin pausa? (s/n): ").lower()
    datos['uso_continuo'] = uso_continuo == 's'
    if datos['uso_continuo']:
        print("   ⚠️ Se añadirá 1 punto adicional por uso continuo prolongado")
    
    # ===== SILLA =====
    print("\n--- SILLA ---")
    silla = {}
    
    altura = input("   Altura del asiento (1=rodillas 90°, pies apoyados; 2=ligeramente incorrecta; 3=muy incorrecta): ")
    silla['altura'] = int(altura) if altura.isdigit() else 2
    
    print("   Profundidad del asiento (debe dejar espacio de 2-3 dedos detrás de la rodilla):")
    profundidad = input("      (adecuado/parcial/inadecuado): ").lower()
    if profundidad in ['adecuado', 'parcial', 'inadecuado']:
        silla['profundidad_asiento'] = profundidad
    else:
        silla['profundidad_asiento'] = 'no_se'
    
    print("   Apoyo lumbar (debe ajustarse a la curvatura de la espalda baja):")
    lumbar = input("      (ajustado/presente/ausente): ").lower()
    if lumbar in ['ajustado', 'presente', 'ausente']:
        silla['apoyo_lumbar'] = lumbar
    else:
        silla['apoyo_lumbar'] = 'no_se'
    
    print("   Reposabrazos altura (codos a 90-110°, hombros relajados):")
    altura_brazos = input("      (adecuado/ligero/incorrecto): ").lower()
    if altura_brazos in ['adecuado', 'ligero', 'incorrecto']:
        silla['apoyabrazos_altura'] = altura_brazos
    else:
        silla['apoyabrazos_altura'] = 'no_se'
    
    print("   Reposabrazos separación (debe permitir paso cómodo del cuerpo):")
    ancho_brazos = input("      (adecuado/parcial/inadecuado): ").lower()
    if ancho_brazos in ['adecuado', 'parcial', 'inadecuado']:
        silla['apoyabrazos_ancho'] = ancho_brazos
    else:
        silla['apoyabrazos_ancho'] = 'no_se'
    
    datos['silla'] = silla
    
    # ===== MONITOR =====
    print("\n--- MONITOR ---")
    monitor = {}
    
    altura_mon = input("   Altura monitor (1=ojos alineados, 2=ligera desviación, 3=mucha desviación): ")
    monitor['altura'] = int(altura_mon) if altura_mon.isdigit() else 2
    
    distancia_mon = input("   Distancia monitor en cm (45-70cm ideal): ")
    monitor['distancia'] = int(distancia_mon) if distancia_mon.isdigit() else 60
    
    inclinacion = input("   Inclinación monitor (perpendicular/ligera/significativa): ").lower()
    if inclinacion in ['perpendicular', 'ligera', 'significativa']:
        monitor['inclinacion'] = inclinacion
    else:
        monitor['inclinacion'] = 'no_se'
    
    reflejos = input("   ¿Hay reflejos o brillos en la pantalla? (s/n): ").lower()
    monitor['reflejos'] = reflejos == 's'
    
    datos['monitor'] = monitor
    
    # ===== TECLADO =====
    print("\n--- TECLADO ---")
    teclado = {}
    
    altura_tec = input("   Altura teclado (adecuado/ligero/incorrecto): ").lower()
    if altura_tec in ['adecuado', 'ligero', 'incorrecto']:
        teclado['altura'] = altura_tec
    else:
        teclado['altura'] = 'no_se'
    
    distancia_tec = input("   Distancia teclado (ángulo codo en grados, 90-110 ideal): ")
    teclado['distancia'] = int(distancia_tec) if distancia_tec.isdigit() else None
    
    inclinacion_tec = input("   Inclinación teclado (neutro/positiva/negativa): ").lower()
    if inclinacion_tec in ['neutro', 'positiva', 'negativa']:
        teclado['inclinacion'] = inclinacion_tec
    else:
        teclado['inclinacion'] = 'no_se'
    
    soporte = input("   Reposamuñecas (acolchado/basico/ausente): ").lower()
    if soporte in ['acolchado', 'basico', 'ausente']:
        teclado['reposamunecas'] = soporte
    else:
        teclado['reposamunecas'] = 'no_se'
    
    datos['teclado'] = teclado
    
    # ===== MOUSE =====
    print("\n--- MOUSE ---")
    mouse = {}
    
    altura_mouse = input("   Altura mouse (misma/ligera/diferente que teclado): ").lower()
    if altura_mouse in ['misma', 'ligera', 'diferente']:
        mouse['altura'] = altura_mouse
    else:
        mouse['altura'] = 'no_se'
    
    distancia_mouse = input("   Distancia mouse extra en cm (5-10cm ideal): ")
    mouse['distancia'] = int(distancia_mouse) if distancia_mouse.isdigit() else None
    
    posicion = input("   Posición mouse (frontal/ligera/lateral): ").lower()
    if posicion in ['frontal', 'ligera', 'lateral']:
        mouse['posicion'] = posicion
    else:
        mouse['posicion'] = 'no_se'
    
    datos['mouse'] = mouse
    
    # ===== TELÉFONO =====
    print("\n--- TELÉFONO (opcional) ---")
    telefono = {}
    
    usa_telefono = input("   ¿Usa teléfono frecuentemente? (s/n): ").lower()
    if usa_telefono == 's':
        manos_libres = input("   ¿Usa manos libres/auricular? (s/n): ").lower()
        telefono['manos_libres'] = manos_libres == 's'
        distancia_tel = input("   Distancia del teléfono (inmediato/alejado): ").lower()
        telefono['distancia'] = distancia_tel if distancia_tel in ['inmediato', 'alejado'] else 'inmediato'
    else:
        telefono['manos_libres'] = True
        telefono['distancia'] = 'inmediato'
    
    datos['telefono'] = telefono
    
    return datos


# ============================================================
# PRUEBA RÁPIDA (ejecutar directamente)
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DEL MÉTODO ROSA")
    print("=" * 60)
    
    # Datos de ejemplo
    datos_ejemplo = {
        'uso_continuo': True,
        'silla': {
            'altura': 1,
            'profundidad_asiento': 'adecuado',
            'apoyo_lumbar': 'ajustado',
            'apoyabrazos_altura': 'adecuado',
            'apoyabrazos_ancho': 'adecuado'
        },
        'monitor': {
            'altura': 1,
            'distancia': 60,
            'inclinacion': 'perpendicular',
            'reflejos': False
        },
        'teclado': {
            'altura': 'adecuado',
            'distancia': 95,
            'inclinacion': 'neutro',
            'reposamunecas': 'acolchado'
        },
        'mouse': {
            'altura': 'misma',
            'distancia': 5,
            'posicion': 'frontal'
        },
        'telefono': {
            'manos_libres': True,
            'distancia': 'inmediato'
        }
    }
    
    print("\n📊 Evaluando puesto de oficina de ejemplo...")
    resultado = evaluar_rosa(datos_ejemplo)
    
    print(f"\n📋 RESULTADOS ROSA:")
    print(f"   Silla: {resultado['silla']}/10")
    print(f"   Monitor: {resultado['monitor']}/10")
    print(f"   Teclado: {resultado['teclado']}/10")
    print(f"   Mouse: {resultado['mouse']}/10")
    print(f"\n   Puntuación base: {resultado['puntuacion_base']}/10")
    print(f"   Factor tiempo de uso: +{resultado['factor_tiempo']}")
    print(f"   PUNTUACIÓN FINAL: {resultado['puntuacion_final']}/10")
    print(f"   NIVEL DE RIESGO: {resultado['nivel_riesgo']}")
    print(f"   ACCIÓN: {resultado['accion']}")
    
    print(f"\n📋 RECOMENDACIONES:")
    for rec in resultado['recomendaciones']:
        print(f"   {rec}")
    
    print(f"\n📋 LISTA DE VERIFICACIÓN (CHECKLIST):")
    for item in resultado['checklist']:
        print(f"   {item}")
    
    print("\n" + "=" * 60)
    print("✅ Prueba completada")