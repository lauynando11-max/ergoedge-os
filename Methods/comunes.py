"""
ERGOEDGE OS - Funciones comunes compartidas
Entre main.py y web_flask.py para eliminar duplicación
"""

import numpy as np


def obtener_punto(keypoints, idx, conf_threshold=0.5):
    """
    Obtiene un punto de YOLO si tiene suficiente confianza
    
    Args:
        keypoints: Array de keypoints de YOLO (33 puntos)
        idx: Índice del punto (0-32)
        conf_threshold: Umbral de confianza (0-1)
    
    Returns:
        tuple (x, y) o None si no tiene confianza suficiente
    """
    if idx < len(keypoints) and keypoints[idx][2] > conf_threshold:
        return keypoints[idx][0], keypoints[idx][1]
    return None


def calcular_angulo_2d(p1, p2, p3):
    """
    Calcula ángulo entre tres puntos 2D con validación
    
    Args:
        p1, p2, p3: Tuplas (x, y) de los puntos (p2 es el vértice)
    
    Returns:
        float: Ángulo en grados (0-180)
    """
    if p1 is None or p2 is None or p3 is None:
        return 0
    try:
        a = np.array(p1)
        b = np.array(p2)
        c = np.array(p3)
        ba = a - b
        bc = c - b
        norma_ba = np.linalg.norm(ba)
        norma_bc = np.linalg.norm(bc)
        if norma_ba < 0.001 or norma_bc < 0.001:
            return 0
        cos = np.dot(ba, bc) / (norma_ba * norma_bc)
        cos = np.clip(cos, -1, 1)
        angulo = np.degrees(np.arccos(cos))
        return angulo
    except:
        return 0


def clasificar_riesgo_owas(codigo_espalda, codigo_brazo, codigo_piernas, codigo_carga):
    """
    Clasificación de riesgo OWAS según tabla oficial
    
    Args:
        codigo_espalda: 1-4
        codigo_brazo: 1-2
        codigo_piernas: 1-7
        codigo_carga: 1-3
    
    Returns:
        tuple: (nivel, categoria, accion)
    """
    # Riesgo Crítico (Nivel 4) - Intervención inmediata
    if (codigo_espalda >= 3 and codigo_piernas >= 4) or \
       (codigo_brazo == 2 and codigo_piernas >= 5) or \
       (codigo_carga == 3 and codigo_piernas >= 4) or \
       (codigo_espalda == 4):
        return 4, "CRÍTICO", "INTERVENCIÓN INMEDIATA"
    
    # Riesgo Alto (Nivel 3) - Corto plazo
    elif (codigo_espalda == 3 and codigo_piernas >= 3) or \
         (codigo_brazo == 2 and codigo_piernas >= 3) or \
         (codigo_carga >= 2 and codigo_piernas >= 3) or \
         (codigo_espalda == 3 and codigo_carga >= 2):
        return 3, "ALTO", "ACCIÓN CORTO PLAZO (30 DÍAS)"
    
    # Riesgo Moderado (Nivel 2) - Futuro
    elif (codigo_espalda == 2 and codigo_piernas >= 2) or \
         (codigo_brazo == 2) or \
         (codigo_carga == 2):
        return 2, "MODERADO", "ACCIÓN A FUTURO (90 DÍAS)"
    
    # Riesgo Normal (Nivel 1)
    else:
        return 1, "NORMAL", "NINGUNA ACCIÓN REQUERIDA"


def calcular_torsion_avanzada(hombro_izq, hombro_der, cadera_izq, cadera_der):
    """
    Calcula torsión de tronco usando ángulo entre hombros y caderas
    
    Args:
        hombro_izq, hombro_der, cadera_izq, cadera_der: tuplas (x, y) o None
    
    Returns:
        dict: {
            'detectada': bool,
            'angulo': float (grados),
            'direccion': 'izquierda' | 'derecha' | 'neutro',
            'incremento': int (0-3)
        }
    """
    if None in [hombro_izq, hombro_der, cadera_izq, cadera_der]:
        return {'detectada': False, 'angulo': 0, 'direccion': 'neutro', 'incremento': 0}
    
    # Vectores
    v_hombros = (hombro_der[0] - hombro_izq[0], hombro_der[1] - hombro_izq[1])
    v_caderas = (cadera_der[0] - cadera_izq[0], cadera_der[1] - cadera_izq[1])
    
    # Normas
    n_h = (v_hombros[0]**2 + v_hombros[1]**2)**0.5
    n_c = (v_caderas[0]**2 + v_caderas[1]**2)**0.5
    
    if n_h < 0.001 or n_c < 0.001:
        return {'detectada': False, 'angulo': 0, 'direccion': 'neutro', 'incremento': 0}
    
    # Ángulo entre vectores
    dot = v_hombros[0]*v_caderas[0] + v_hombros[1]*v_caderas[1]
    cos_ang = dot / (n_h * n_c)
    cos_ang = max(-1, min(1, cos_ang))
    angulo = np.degrees(np.arccos(cos_ang))
    
    # Dirección (producto cruz)
    cross = v_hombros[0]*v_caderas[1] - v_hombros[1]*v_caderas[0]
    if cross > 0.01:
        direccion = 'derecha'
    elif cross < -0.01:
        direccion = 'izquierda'
    else:
        direccion = 'neutro'
    
    # Incremento según severidad
    if angulo < 15:
        incremento = 0
        detectada = False
    elif angulo < 35:
        incremento = 1
        detectada = True
    elif angulo < 60:
        incremento = 2
        detectada = True
    else:
        incremento = 3
        detectada = True
    
    return {
        'detectada': detectada,
        'angulo': round(angulo, 1),
        'direccion': direccion,
        'incremento': incremento
    }


def detectar_carga_dinamica(keypoints, keypoints_anterior=None, peso_referencia=0):
    """
    Detecta si el operario está cargando algo y estima el código de carga OWAS
    
    Args:
        keypoints: Keypoints del frame actual
        keypoints_anterior: Keypoints del frame anterior (opcional)
        peso_referencia: Peso ingresado por el usuario (kg)
    
    Returns:
        dict: {
            'codigo_carga': int (1-3),
            'cargando': bool,
            'brusco': bool,
            'peso_estimado': float,
            'descripcion': str
        }
    """
    # Obtener puntos clave
    hombro_izq = obtener_punto(keypoints, 5)
    hombro_der = obtener_punto(keypoints, 6)
    codo_izq = obtener_punto(keypoints, 7)
    codo_der = obtener_punto(keypoints, 8)
    muneca_izq = obtener_punto(keypoints, 9)
    muneca_der = obtener_punto(keypoints, 10)
    cadera_izq = obtener_punto(keypoints, 11)
    cadera_der = obtener_punto(keypoints, 12)
    
    # 1. Detectar si las manos están adelante (posición de agarre)
    manos_adelante = False
    if muneca_izq and cadera_izq:
        if muneca_izq[0] > cadera_izq[0] - 30:
            manos_adelante = True
    if muneca_der and cadera_der:
        if muneca_der[0] > cadera_der[0] - 30:
            manos_adelante = True
    
    # 2. Detectar tensión en brazos (codos flexionados/extendidos)
    tension_brazos = False
    if codo_izq and hombro_izq and muneca_izq:
        ang_codo_izq = calcular_angulo_2d(hombro_izq, codo_izq, muneca_izq)
        if ang_codo_izq < 60 or ang_codo_izq > 100:
            tension_brazos = True
    if codo_der and hombro_der and muneca_der:
        ang_codo_der = calcular_angulo_2d(hombro_der, codo_der, muneca_der)
        if ang_codo_der < 60 or ang_codo_der > 100:
            tension_brazos = True
    
    # 3. Detectar inclinación del tronco
    inclinado = False
    angulo_espalda = 0
    if hombro_izq and cadera_izq:
        # Calcular ángulo de espalda (simplificado)
        punto_referencia = (cadera_izq[0], cadera_izq[1] + 50)
        angulo_espalda = calcular_angulo_2d(hombro_izq, cadera_izq, punto_referencia)
        if angulo_espalda > 20:
            inclinado = True
    
    # 4. Detectar movimiento brusco (si hay frame anterior)
    brusco = False
    if keypoints_anterior is not None:
        muneca_izq_ant = obtener_punto(keypoints_anterior, 9)
        if muneca_izq and muneca_izq_ant:
            # Velocidad de la muñeca (desplazamiento rápido = carga brusca)
            desplazamiento = ((muneca_izq[0] - muneca_izq_ant[0])**2 + 
                             (muneca_izq[1] - muneca_izq_ant[1])**2)**0.5
            if desplazamiento > 30:
                brusco = True
    
    # 5. Determinar si está cargando
    cargando = manos_adelante or tension_brazos or (inclinado and peso_referencia > 0)
    
    # 6. Calcular código de carga OWAS (1-3)
    if not cargando:
        codigo_carga = 1
        descripcion = "Sin carga detectable"
        peso_estimado = 0
    else:
        # Base: usar peso_referencia si existe, sino estimar
        if peso_referencia > 0:
            peso_estimado = peso_referencia
        else:
            # Estimación por postura
            if tension_brazos and inclinado:
                peso_estimado = 15
            elif tension_brazos or inclinado:
                peso_estimado = 8
            else:
                peso_estimado = 5
        
        # Asignar código según peso estimado
        if peso_estimado == 0:
            codigo_carga = 1
            descripcion = "Sin carga"
        elif peso_estimado <= 10:
            codigo_carga = 1
            descripcion = f"Carga ligera ({peso_estimado:.0f} kg)"
        elif peso_estimado <= 20:
            codigo_carga = 2
            descripcion = f"Carga media ({peso_estimado:.0f} kg)"
        else:
            codigo_carga = 3
            descripcion = f"Carga pesada ({peso_estimado:.0f} kg)"
        
        # Si es brusco, aumentar un nivel (máximo 3)
        if brusco and codigo_carga < 3:
            codigo_carga += 1
            descripcion += " [CARGA BRUSCA]"
    
    return {
        'codigo_carga': codigo_carga,
        'cargando': cargando,
        'brusco': brusco,
        'peso_estimado': round(peso_estimado, 1),
        'descripcion': descripcion
    }


def calcular_angulo_3d(p1, p2, p3):
    """
    Calcula ángulo 3D entre tres puntos (soporta puntos 2D y 3D)
    p2 es el vértice
    
    Args:
        p1, p2, p3: Tuplas (x, y) o (x, y, z) de los puntos
    
    Returns:
        float: Ángulo en grados (0-180)
    """
    # Convertir a arrays 3D (si son 2D, agregar z=0)
    def to_3d(p):
        if len(p) >= 3:
            return np.array([p[0], p[1], p[2]])
        else:
            return np.array([p[0], p[1], 0])
    
    try:
        a = to_3d(p1)
        b = to_3d(p2)
        c = to_3d(p3)
        
        ba = a - b
        bc = c - b
        norma_ba = np.linalg.norm(ba)
        norma_bc = np.linalg.norm(bc)
        
        if norma_ba < 0.001 or norma_bc < 0.001:
            return 0
        
        cos = np.dot(ba, bc) / (norma_ba * norma_bc)
        cos = np.clip(cos, -1, 1)
        return np.degrees(np.arccos(cos))
    except:
        return 0