"""
ERGOEDGE OS - Procesadores base
Funciones comunes para cálculo de ángulos, puntos, etc.
"""

import cv2
import numpy as np
import os
import time


def obtener_punto(keypoints, idx, conf_threshold=0.5):
    """Obtiene un punto de YOLO si tiene suficiente confianza"""
    if idx < len(keypoints) and keypoints[idx][2] > conf_threshold:
        return keypoints[idx][0], keypoints[idx][1]
    return None


def calcular_angulo_2d(p1, p2, p3):
    """Calcula ángulo entre tres puntos 2D"""
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


def guardar_frame_riesgo(frame, nivel, metodo, nombre_base, frames_dir=None):
    """Guarda un frame como imagen si tiene alto riesgo"""
    try:
        if frames_dir is None:
            frames_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'frames')
        
        os.makedirs(frames_dir, exist_ok=True)
        
        timestamp = int(time.time())
        img_path = os.path.join(frames_dir, f"{nombre_base}_{metodo}_riesgo_{nivel}_{timestamp}.jpg")
        
        cv2.imwrite(img_path, frame)
        
        # Devolver ruta relativa para la web
        return f"/static/frames/{os.path.basename(img_path)}"
    except Exception as e:
        print(f"⚠️ Error guardando frame: {e}")
        return None


def calcular_torsion_avanzada(hombro_izq, hombro_der, cadera_izq, cadera_der):
    """Calcula torsión de tronco usando ángulo entre hombros y caderas"""
    if None in [hombro_izq, hombro_der, cadera_izq, cadera_der]:
        return {'detectada': False, 'angulo': 0, 'direccion': 'neutro', 'incremento': 0}
    
    v_hombros = (hombro_der[0] - hombro_izq[0], hombro_der[1] - hombro_izq[1])
    v_caderas = (cadera_der[0] - cadera_izq[0], cadera_der[1] - cadera_izq[1])
    
    n_h = (v_hombros[0]**2 + v_hombros[1]**2)**0.5
    n_c = (v_caderas[0]**2 + v_caderas[1]**2)**0.5
    
    if n_h < 0.001 or n_c < 0.001:
        return {'detectada': False, 'angulo': 0, 'direccion': 'neutro', 'incremento': 0}
    
    dot = v_hombros[0]*v_caderas[0] + v_hombros[1]*v_caderas[1]
    cos_ang = dot / (n_h * n_c)
    cos_ang = max(-1, min(1, cos_ang))
    angulo = np.degrees(np.arccos(cos_ang))
    
    cross = v_hombros[0]*v_caderas[1] - v_hombros[1]*v_caderas[0]
    direccion = 'derecha' if cross > 0.01 else 'izquierda' if cross < -0.01 else 'neutro'
    
    if angulo < 15:
        return {'detectada': False, 'angulo': round(angulo, 1), 'direccion': direccion, 'incremento': 0}
    elif angulo < 35:
        return {'detectada': True, 'angulo': round(angulo, 1), 'direccion': direccion, 'incremento': 1}
    elif angulo < 60:
        return {'detectada': True, 'angulo': round(angulo, 1), 'direccion': direccion, 'incremento': 2}
    else:
        return {'detectada': True, 'angulo': round(angulo, 1), 'direccion': direccion, 'incremento': 3}