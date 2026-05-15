# metodologias/rula.py
# RULA - Rapid Upper Limb Assessment
# Basado en McAtamney & Corlett (1993)
# Puntuación final: 1 a 7

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import calcular_angulo, calcular_angulo_2d

# ==================== FUNCIONES AUXILIARES ====================

def obtener_punto(keypoints, idx, conf_threshold=0.5):
    """Obtiene un punto de YOLO si tiene suficiente confianza"""
    try:
        if idx < len(keypoints) and keypoints[idx][2] > conf_threshold:
            return (keypoints[idx][0], keypoints[idx][1])
    except:
        pass
    return None


def calcular_angulo_seguro(p1, p2, p3):
    """Versión segura de calcular_angulo que maneja None y errores"""
    if p1 is None or p2 is None or p3 is None:
        return 0
    try:
        resultado = calcular_angulo(p1, p2, p3)
        if resultado is None:
            return 0
        return resultado
    except Exception as e:
        print(f"  [Advertencia] Error calculando ángulo: {e}")
        return 0


def obtener_brazo_dominante(keypoints):
    """
    Determina el brazo dominante basado en la posición de los hombros
    y muñecas. Por defecto usa el derecho si está visible.
    """
    hombro_izq = obtener_punto(keypoints, 5)
    hombro_der = obtener_punto(keypoints, 6)
    muneca_izq = obtener_punto(keypoints, 9)
    muneca_der = obtener_punto(keypoints, 10)
    
    # Si solo un brazo es visible, usar ese
    if muneca_izq is not None and muneca_der is None:
        return "izquierdo"
    if muneca_der is not None and muneca_izq is None:
        return "derecho"
    
    # Si ambos visibles, usar el derecho por defecto
    if muneca_der is not None:
        return "derecho"
    if muneca_izq is not None:
        return "izquierdo"
    
    return "derecho"  # Default


# ==================== PUNTUACIONES RULA ====================

def puntuar_brazo(keypoints, lado="derecho"):
    """
    Puntúa la posición del brazo (Score A: 1-6)
    MEJORADO: Calcula ángulo respecto a tronco (cadera-hombro-codo)
    Retorna: (puntuacion, detalles)
    """
    if lado == "izquierdo":
        hombro = obtener_punto(keypoints, 5)
        codo = obtener_punto(keypoints, 7)
        muneca = obtener_punto(keypoints, 9)
    else:
        hombro = obtener_punto(keypoints, 6)
        codo = obtener_punto(keypoints, 8)
        muneca = obtener_punto(keypoints, 10)
    
    if hombro is None or codo is None:
        return 3, {"error": "Brazo no detectado"}
    
    # MEJORADO: Calcular ángulo respecto a tronco (cadera-hombro-codo)
    cadera = obtener_punto(keypoints, 11) or obtener_punto(keypoints, 12)
    
    if cadera is not None:
        # Ángulo entre brazo y tronco
        angulo = calcular_angulo_seguro(cadera, hombro, codo)
        usar_tronco = True
    else:
        # Fallback a método anterior (vertical)
        punto_arriba = (hombro[0], hombro[1] - 100)
        angulo = calcular_angulo_seguro(punto_arriba, hombro, codo)
        usar_tronco = False
    
    # Puntuación base (rangos ajustados para ángulo tronco-brazo)
    if angulo <= 20:
        base = 1
        desc = "Brazo neutro (0°-20° respecto a tronco)"
    elif angulo <= 45:
        base = 2
        desc = "Flexión 20°-45°"
    elif angulo <= 90:
        base = 3
        desc = "Flexión 45°-90°"
    else:
        base = 4
        desc = "Flexión >90°"
    
    # Ajustes
    ajustes = 0
    
    # Abducción (brazo separado del cuerpo)
    if abs(codo[0] - hombro[0]) > 50:
        ajustes += 1
        desc += " + abducción"
    
    # Elevación del hombro (muñeca por encima del hombro)
    if muneca is not None and muneca[1] < hombro[1]:
        ajustes += 1
        desc += " + elevación"
    
    # Brazo apoyado (si el codo está cerca de la cadera)
    if cadera is not None and abs(codo[1] - cadera[1]) < 30:
        ajustes -= 1
        desc += " + apoyo"
    
    final = max(1, min(base + ajustes, 6))
    
    return final, {
        'angulo': round(angulo, 1),
        'base': base,
        'ajustes': ajustes,
        'descripcion': desc,
        'usar_tronco': usar_tronco
    }


def puntuar_antebrazo(keypoints, lado="derecho"):
    """
    Puntúa la posición del antebrazo (Score B: 1-2)
    Retorna: (puntuacion, detalles)
    """
    if lado == "izquierdo":
        hombro = obtener_punto(keypoints, 5)
        codo = obtener_punto(keypoints, 7)
        muneca = obtener_punto(keypoints, 9)
    else:
        hombro = obtener_punto(keypoints, 6)
        codo = obtener_punto(keypoints, 8)
        muneca = obtener_punto(keypoints, 10)
    
    if codo is None or muneca is None:
        return 2, {"error": "Antebrazo no detectado"}
    
    if hombro is not None:
        angulo = calcular_angulo_seguro(hombro, codo, muneca)
    else:
        angulo = 60
    
    if 60 <= angulo <= 100:
        return 1, {'angulo': round(angulo, 1), 'descripcion': "Rango neutro (60°-100°)"}
    else:
        return 2, {'angulo': round(angulo, 1), 'descripcion': "Fuera de rango (<60° o >100°)"}


def puntuar_muneca(keypoints, lado="derecho"):
    """
    Puntúa la posición de la muñeca (Score C: 1-4)
    RULA original: flexión/extensión + desviación radial/cubital
    MEJORADO: Mejor fallback cuando no hay nudillos
    """
    if lado == "izquierdo":
        codo = obtener_punto(keypoints, 7)
        muneca = obtener_punto(keypoints, 9)
        nudillo = obtener_punto(keypoints, 21)  # Índice izquierdo
    else:
        codo = obtener_punto(keypoints, 8)
        muneca = obtener_punto(keypoints, 10)
        nudillo = obtener_punto(keypoints, 22)  # Índice derecho
    
    if codo is None or muneca is None:
        return 2, {"error": "Muñeca no detectada", "descripcion": "No se pudo detectar", "puntuacion": 2}
    
    puntuacion = 1  # Base neutra
    angulo_flexion = 0
    descripcion = ""
    
    # Flexión/Extensión
    if nudillo is not None:
        angulo_flexion = calcular_angulo_2d(codo, muneca, nudillo)
        
        if angulo_flexion <= 10:
            puntuacion = 1
            descripcion = f"Muñeca neutra ({angulo_flexion:.0f}°)"
        elif angulo_flexion <= 20:
            puntuacion = 2
            descripcion = f"Flexión/Extensión leve ({angulo_flexion:.0f}°)"
        else:
            puntuacion = 3
            descripcion = f"Flexión/Extensión pronunciada ({angulo_flexion:.0f}°)"
    else:
        # MEJORADO: Fallback usando diferencia vertical codo-muñeca
        diff_y = abs(muneca[1] - codo[1])
        if diff_y < 15:
            puntuacion = 1
            descripcion = f"Muñeca neutra (estimado, dif={diff_y:.0f}px)"
        elif diff_y < 30:
            puntuacion = 2
            descripcion = f"Flexión moderada (estimado, dif={diff_y:.0f}px)"
        else:
            puntuacion = 3
            descripcion = f"Flexión pronunciada (estimado, dif={diff_y:.0f}px)"
    
    # Desviación radial/cubital (estimada por posición horizontal)
    desviacion = 0
    if muneca is not None and codo is not None:
        diferencia_x = abs(muneca[0] - codo[0])
        if diferencia_x > 40:
            desviacion = 1
            descripcion += " + desviación"
    
    puntuacion += desviacion
    puntuacion = max(1, min(puntuacion, 4))
    
    return puntuacion, {
        "angulo": round(angulo_flexion, 1),
        "desviacion": desviacion,
        "descripcion": descripcion,
        "puntuacion": puntuacion
    }


def puntuar_cuello(keypoints):
    """
    Puntúa la posición del cuello (Score D: 1-4)
    Retorna: (puntuacion, detalles)
    """
    nariz = obtener_punto(keypoints, 0)
    hombro_izq = obtener_punto(keypoints, 5)
    hombro_der = obtener_punto(keypoints, 6)
    
    if nariz is None:
        return 2, {"error": "Cuello no detectado"}
    
    # Estimar base del cuello (punto medio entre hombros)
    if hombro_izq and hombro_der:
        base_cuello = ((hombro_izq[0] + hombro_der[0]) / 2,
                       (hombro_izq[1] + hombro_der[1]) / 2)
    elif hombro_izq:
        base_cuello = hombro_izq
    elif hombro_der:
        base_cuello = hombro_der
    else:
        return 2, {"error": "Hombros no detectados"}
    
    # Calcular flexión del cuello
    punto_referencia = (base_cuello[0], base_cuello[1] - 100)
    angulo = calcular_angulo_seguro(punto_referencia, base_cuello, nariz)
    
    if angulo <= 10:
        puntuacion = 1
        desc = "Cuello neutro (0°-10°)"
    elif angulo <= 20:
        puntuacion = 2
        desc = "Flexión 10°-20°"
    elif angulo <= 30:
        puntuacion = 3
        desc = "Flexión 20°-30°"
    else:
        puntuacion = 4
        desc = "Flexión >30°"
    
    # Ajuste por rotación (si los hombros están desalineados)
    rotacion = 0
    if hombro_izq and hombro_der:
        if abs(hombro_izq[0] - hombro_der[0]) < 30:
            rotacion = 1
            desc += " + rotación"
    
    # Ajuste por inclinación lateral
    inclinacion = 0
    if hombro_izq and hombro_der:
        if abs(hombro_izq[1] - hombro_der[1]) > 30:
            inclinacion = 1
            desc += " + inclinación"
    
    puntuacion += rotacion + inclinacion
    puntuacion = max(1, min(puntuacion, 6))
    
    return puntuacion, {'angulo': round(angulo, 1), 'descripcion': desc}


def puntuar_tronco(keypoints):
    """
    Puntúa la posición del tronco (Score E: 1-4)
    Retorna: (puntuacion, detalles)
    """
    hombro_izq = obtener_punto(keypoints, 5)
    hombro_der = obtener_punto(keypoints, 6)
    cadera_izq = obtener_punto(keypoints, 11)
    cadera_der = obtener_punto(keypoints, 12)
    
    if (hombro_izq is None and hombro_der is None) or (cadera_izq is None and cadera_der is None):
        return 2, {"error": "Tronco no detectado"}
    
    # Punto medio de hombros
    if hombro_izq and hombro_der:
        hombro_medio = ((hombro_izq[0] + hombro_der[0]) / 2,
                        (hombro_izq[1] + hombro_der[1]) / 2)
    elif hombro_izq:
        hombro_medio = hombro_izq
    else:
        hombro_medio = hombro_der
    
    # Punto medio de cadera
    if cadera_izq and cadera_der:
        cadera_medio = ((cadera_izq[0] + cadera_der[0]) / 2,
                        (cadera_izq[1] + cadera_der[1]) / 2)
    elif cadera_izq:
        cadera_medio = cadera_izq
    else:
        cadera_medio = cadera_der
    
    # Calcular flexión del tronco
    punto_referencia = (cadera_medio[0], cadera_medio[1] - 100)
    angulo = calcular_angulo_seguro(punto_referencia, cadera_medio, hombro_medio)
    
    if angulo <= 10:
        puntuacion = 1
        desc = "Tronco neutro (0°-10°)"
    elif angulo <= 20:
        puntuacion = 2
        desc = "Flexión 10°-20°"
    elif angulo <= 60:
        puntuacion = 3
        desc = "Flexión 20°-60°"
    else:
        puntuacion = 4
        desc = "Flexión >60°"
    
    # Ajuste por rotación (hombros y caderas desalineados)
    rotacion = 0
    if hombro_medio and cadera_medio:
        if abs(hombro_medio[0] - cadera_medio[0]) > 40:
            rotacion = 1
            desc += " + rotación"
    
    puntuacion += rotacion
    puntuacion = max(1, min(puntuacion, 6))
    
    return puntuacion, {'angulo': round(angulo, 1), 'descripcion': desc}


def puntuar_piernas(keypoints):
    """
    Puntúa la posición de las piernas (Score F: 1-2)
    Retorna: (puntuacion, detalles)
    """
    cadera = obtener_punto(keypoints, 11) or obtener_punto(keypoints, 12)
    rodilla = obtener_punto(keypoints, 13) or obtener_punto(keypoints, 14)
    tobillo = obtener_punto(keypoints, 15) or obtener_punto(keypoints, 16)
    
    if cadera is None or rodilla is None:
        return 1, {"error": "Piernas no detectadas"}
    
    # Verificar si está sentado (rodilla más abajo que cadera)
    if rodilla[1] > cadera[1] + 50:
        # Sentado con soporte
        return 1, {'descripcion': "Sentado con soporte bilateral"}
    
    # Verificar si está de pie con soporte unilateral
    if tobillo is not None and abs(tobillo[0] - cadera[0]) > 30:
        return 2, {'descripcion': "De pie con soporte unilateral"}
    
    return 1, {'descripcion': "De pie con soporte bilateral"}


def puntuar_carga(peso_kg):
    """
    Puntúa la carga/manipulación (0-3)
    Basado en peso y tipo de agarre
    """
    if peso_kg <= 0:
        return 0
    elif peso_kg <= 2:
        return 1
    elif peso_kg <= 10:
        return 2
    else:
        return 3


def puntuar_actividad(postura_estatica=False, repetitivo=False):
    """
    Puntúa la actividad (0-1)
    +1 si la postura es estática o hay movimientos repetitivos
    """
    if postura_estatica or repetitivo:
        return 1
    return 0


# ==================== TABLAS RULA ====================

# Tabla A: Brazo + Antebrazo -> Score C temporal (1-9)
TABLA_A = {
    (1, 1): 1, (1, 2): 2,
    (2, 1): 2, (2, 2): 2,
    (3, 1): 2, (3, 2): 3,
    (4, 1): 3, (4, 2): 3,
    (5, 1): 3, (5, 2): 4,
    (6, 1): 4, (6, 2): 4,
}

# Tabla B: Cuello + Tronco -> Score D temporal (1-8)
TABLA_B = {
    (1, 1): 1, (1, 2): 2, (1, 3): 3, (1, 4): 4,
    (2, 1): 2, (2, 2): 2, (2, 3): 3, (2, 4): 4,
    (3, 1): 2, (3, 2): 3, (3, 3): 3, (3, 4): 4,
    (4, 1): 3, (4, 2): 3, (4, 3): 3, (4, 4): 4,
    (5, 1): 3, (5, 2): 3, (5, 3): 4, (5, 4): 4,
    (6, 1): 3, (6, 2): 4, (6, 3): 4, (6, 4): 4,
}

# Tabla C: Score C + Score D -> Puntuación base (1-7)
TABLA_C = {
    (1, 1): 1, (1, 2): 2, (1, 3): 3, (1, 4): 3, (1, 5): 4, (1, 6): 4, (1, 7): 5, (1, 8): 5,
    (2, 1): 2, (2, 2): 2, (2, 3): 3, (2, 4): 4, (2, 5): 4, (2, 6): 4, (2, 7): 5, (2, 8): 5,
    (3, 1): 2, (3, 2): 3, (3, 3): 3, (3, 4): 4, (3, 5): 4, (3, 6): 5, (3, 7): 5, (3, 8): 6,
    (4, 1): 3, (4, 2): 3, (4, 3): 3, (4, 4): 4, (4, 5): 5, (4, 6): 5, (4, 7): 6, (4, 8): 6,
    (5, 1): 3, (5, 2): 3, (5, 3): 4, (5, 4): 4, (5, 5): 5, (5, 6): 6, (5, 7): 6, (5, 8): 7,
    (6, 1): 3, (6, 2): 4, (6, 3): 4, (6, 4): 5, (6, 5): 5, (6, 6): 6, (6, 7): 7, (6, 8): 7,
    (7, 1): 4, (7, 2): 4, (7, 3): 4, (7, 4): 5, (7, 5): 6, (7, 6): 7, (7, 7): 7, (7, 8): 7,
    (8, 1): 4, (8, 2): 4, (8, 3): 5, (8, 4): 6, (8, 5): 6, (8, 6): 7, (8, 7): 7, (8, 8): 7,
    (9, 1): 4, (9, 2): 5, (9, 3): 5, (9, 4): 6, (9, 5): 7, (9, 6): 7, (9, 7): 7, (9, 8): 7,
}


# ==================== FUNCIÓN PRINCIPAL ====================

def evaluar_rula(keypoints, peso_carga=0, postura_estatica=False, repetitivo=False):
    """
    Evalúa RULA completo y retorna puntuación final y nivel de riesgo
    Parámetros:
        keypoints: puntos clave de YOLO
        peso_carga: peso de la carga en kg (0-10+)
        postura_estatica: True si la postura se mantiene >1 min
        repetitivo: True si hay movimientos repetitivos >4 veces/minuto
    Retorna: dict con puntuacion_final, nivel_riesgo, accion, detalles
    """
    # Determinar brazo dominante
    lado = obtener_brazo_dominante(keypoints)
    
    # Calcular todas las puntuaciones
    score_brazo, det_brazo = puntuar_brazo(keypoints, lado)
    score_antebrazo, det_antebrazo = puntuar_antebrazo(keypoints, lado)
    score_muneca, det_muneca = puntuar_muneca(keypoints, lado)
    score_cuello, det_cuello = puntuar_cuello(keypoints)
    score_tronco, det_tronco = puntuar_tronco(keypoints)
    score_piernas, det_piernas = puntuar_piernas(keypoints)
    
    # Score C temporal (Tabla A)
    score_c_temp = TABLA_A.get((score_brazo, score_antebrazo), 3)
    
    # Score C final = Score C temporal + puntuación de muñeca
    score_c = score_c_temp + score_muneca
    score_c = max(1, min(score_c, 9))
    
    # Score D (Tabla B)
    score_d = TABLA_B.get((score_cuello, score_tronco), 3)
    
    # Puntuación base (Tabla C)
    puntuacion_base = TABLA_C.get((score_c, score_d), 4)
    
    # Ajustes finales
    ajuste_carga = puntuar_carga(peso_carga)
    ajuste_actividad = puntuar_actividad(postura_estatica, repetitivo)
    ajuste_piernas = score_piernas
    
    puntuacion_final = puntuacion_base + ajuste_carga + ajuste_actividad + ajuste_piernas
    puntuacion_final = max(1, min(puntuacion_final, 7))
    
    # Nivel de riesgo
    if puntuacion_final <= 2:
        nivel = "BAJO"
        accion = "Aceptable. No requiere acción inmediata."
    elif puntuacion_final <= 4:
        nivel = "MEDIO"
        accion = "Investigar más a fondo. Puede requerir cambios en el puesto."
    elif puntuacion_final <= 6:
        nivel = "ALTO"
        accion = "Requiere intervención en el corto plazo."
    else:
        nivel = "MUY ALTO"
        accion = "Requiere intervención inmediata."
    
    return {
        'puntuacion_final': puntuacion_final,
        'nivel_riesgo': nivel,
        'accion': accion,
        'detalles': {
            'brazo': {'puntuacion': score_brazo, **det_brazo},
            'antebrazo': {'puntuacion': score_antebrazo, **det_antebrazo},
            'muneca': {'puntuacion': score_muneca, **det_muneca},
            'cuello': {'puntuacion': score_cuello, **det_cuello},
            'tronco': {'puntuacion': score_tronco, **det_tronco},
            'piernas': {'puntuacion': score_piernas, **det_piernas},
            'ajustes': {
                'carga': ajuste_carga,
                'actividad': ajuste_actividad,
                'piernas': ajuste_piernas
            }
        }
    }