"""
ERGOEDGE OS - Lógica principal de ergonomía
Compartida entre CLI (main.py) y Web (web_flask.py)
"""

import cv2
import numpy as np
from Methods.procesadores import (
    obtener_punto, calcular_angulo_2d, guardar_frame_riesgo, calcular_torsion_avanzada
)


def clasificar_riesgo_owas(codigo_espalda, codigo_brazo, codigo_piernas, codigo_carga):
    """Clasifica el riesgo según la matriz OWAS original"""
    # Riesgo Crítico (Nivel 4)
    if (codigo_espalda >= 3 and codigo_piernas >= 4) or \
       (codigo_brazo == 2 and codigo_piernas >= 5) or \
       (codigo_espalda == 4):
        return 4, "CRÍTICO", "INTERVENCIÓN INMEDIATA"
    
    # Riesgo Alto (Nivel 3)
    elif (codigo_espalda == 3 and codigo_piernas >= 3) or \
         (codigo_brazo == 2 and codigo_piernas >= 3):
        return 3, "ALTO", "ACCIÓN CORTO PLAZO (30 DÍAS)"
    
    # Riesgo Moderado (Nivel 2)
    elif (codigo_espalda == 2 and codigo_piernas >= 2) or \
         (codigo_brazo == 2):
        return 2, "MODERADO", "ACCIÓN A FUTURO (90 DÍAS)"
    
    # Riesgo Normal (Nivel 1)
    else:
        return 1, "NORMAL", "NINGUNA ACCIÓN REQUERIDA"


def procesar_frame_owas(keypoints, frame, codigo_carga=1, keypoints_anterior=None):
    """Procesa un frame con método OWAS"""
    hombro = obtener_punto(keypoints, 5)
    cadera = obtener_punto(keypoints, 11)
    rodilla_izq = obtener_punto(keypoints, 13)
    rodilla_der = obtener_punto(keypoints, 14)
    tobillo_izq = obtener_punto(keypoints, 15)
    tobillo_der = obtener_punto(keypoints, 16)
    hombro_der = obtener_punto(keypoints, 6)
    
    # ========== ESPALDA ==========
    if hombro and cadera and rodilla_izq:
        angulo_espalda = calcular_angulo_2d(hombro, cadera, rodilla_izq)
        if angulo_espalda > 90:
            angulo_espalda = 180 - angulo_espalda
    else:
        angulo_espalda = 0
    
    if angulo_espalda <= 20:
        codigo_espalda = 1
    elif angulo_espalda <= 60:
        codigo_espalda = 2
    elif angulo_espalda <= 90:
        codigo_espalda = 3
    else:
        codigo_espalda = 4
    
    # ========== TORSIÓN AVANZADA ==========
    hombro_izq_pto = obtener_punto(keypoints, 5)
    hombro_der_pto = obtener_punto(keypoints, 6)
    cadera_izq_pto = obtener_punto(keypoints, 11)
    cadera_der_pto = obtener_punto(keypoints, 12)
    
    torsion_data = calcular_torsion_avanzada(hombro_izq_pto, hombro_der_pto, cadera_izq_pto, cadera_der_pto)
    
    if torsion_data['detectada']:
        codigo_espalda = min(codigo_espalda + torsion_data['incremento'], 4)
    
    # ========== BRAZOS ==========
    muneca = obtener_punto(keypoints, 9)
    brazo_sobre_hombro = 0
    if muneca and hombro:
        if muneca[1] < hombro[1] - 30:
            brazo_sobre_hombro = 1
    
    codigo_brazo = 2 if brazo_sobre_hombro else 1
    
    # ========== PIERNAS ==========
    sentado = False
    if cadera and rodilla_izq:
        if cadera[1] > rodilla_izq[1] + 50:
            sentado = True
    
    arrodillado = False
    if rodilla_izq and tobillo_izq:
        distancia_rodilla_tobillo = abs(rodilla_izq[1] - tobillo_izq[1])
        if distancia_rodilla_tobillo < 40:
            arrodillado = True
    
    angulo_rodilla_izq = 180
    pierna_izq_flexionada = False
    if cadera and rodilla_izq and tobillo_izq:
        angulo_rodilla_izq = calcular_angulo_2d(cadera, rodilla_izq, tobillo_izq)
        if angulo_rodilla_izq < 150:
            pierna_izq_flexionada = True
    
    angulo_rodilla_der = 180
    pierna_der_flexionada = False
    if cadera and rodilla_der and tobillo_der:
        angulo_rodilla_der = calcular_angulo_2d(cadera, rodilla_der, tobillo_der)
        if angulo_rodilla_der < 150:
            pierna_der_flexionada = True
    
    caminando = False
    if keypoints_anterior is not None:
        cadera_ant = obtener_punto(keypoints_anterior, 11)
        if cadera and cadera_ant:
            desplazamiento = abs(cadera[0] - cadera_ant[0])
            if desplazamiento > 20:
                caminando = True
    
    if sentado:
        codigo_piernas = 1
    elif arrodillado:
        codigo_piernas = 6
    elif caminando:
        codigo_piernas = 7
    elif pierna_izq_flexionada and pierna_der_flexionada:
        codigo_piernas = 4
    elif pierna_izq_flexionada or pierna_der_flexionada:
        codigo_piernas = 5
    else:
        codigo_piernas = 2
    
    nivel_riesgo, categoria, accion = clasificar_riesgo_owas(codigo_espalda, codigo_brazo, codigo_piernas, codigo_carga)
    codigo_owas = f"{codigo_espalda}{codigo_brazo}{codigo_piernas}{codigo_carga}"
    
    return {
        'nivel_riesgo': nivel_riesgo,
        'categoria': categoria,
        'accion': accion,
        'codigo_owas': codigo_owas,
        'angulo_espalda': angulo_espalda,
        'torsion': torsion_data['angulo'] if torsion_data['detectada'] else 0,
        'torsion_direccion': torsion_data['direccion'] if torsion_data['detectada'] else 'neutro',
        'sentado': sentado,
        'arrodillado': arrodillado,
        'caminando': caminando,
        'angulo_rodilla_izq': round(angulo_rodilla_izq, 1),
        'angulo_rodilla_der': round(angulo_rodilla_der, 1)
    }