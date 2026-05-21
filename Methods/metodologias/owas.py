import numpy as np
import math

def calcular_angulo_3d(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radianes = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angulo = np.abs(radianes * 180.0 / np.pi)
    return 360 - angulo if angulo > 180.0 else angulo

def calcular_rotacion_torso(hombro_izq, hombro_der, cadera_izq, cadera_der):
    vector_hombros = np.array([hombro_der[0] - hombro_izq[0], hombro_der[2] - hombro_izq[2]])
    vector_caderas = np.array([cadera_der[0] - cadera_izq[0], cadera_der[2] - cadera_izq[2]])
    norma_h = np.linalg.norm(vector_hombros)
    norma_c = np.linalg.norm(vector_caderas)
    if norma_h == 0 or norma_c == 0:
        return 0
    cos_angulo = np.dot(vector_hombros, vector_caderas) / (norma_h * norma_c)
    cos_angulo = max(-1, min(1, cos_angulo))
    angulo = np.arccos(cos_angulo)
    return np.degrees(angulo)

def detectar_postura_piernas(landmarks):
    try:
        cadera_izq = landmarks.get('left_hip')
        cadera_der = landmarks.get('right_hip')
        rodilla_izq = landmarks.get('left_knee')
        rodilla_der = landmarks.get('right_knee')
        tobillo_izq = landmarks.get('left_ankle')
        tobillo_der = landmarks.get('right_ankle')
        if not all([cadera_izq, rodilla_izq, tobillo_izq]):
            return 2
        ang_rodilla_izq = calcular_angulo_3d(cadera_izq, rodilla_izq, tobillo_izq)
        ang_rodilla_der = calcular_angulo_3d(cadera_der, rodilla_der, tobillo_der)
        altura_cadera = (cadera_izq[1] + cadera_der[1]) / 2
        altura_rodilla = (rodilla_izq[1] + rodilla_der[1]) / 2
        if altura_rodilla < altura_cadera - 0.15:
            return 1
        if ang_rodilla_izq < 100 or ang_rodilla_der < 100:
            return 5
        if ang_rodilla_izq < 150 or ang_rodilla_der < 150:
            return 4
        if abs(ang_rodilla_izq - ang_rodilla_der) > 30:
            return 3
        return 2
    except:
        return 2

def estimar_carga_detectada(detecciones_yolo):
    tabla_pesos = {'chair': 5, 'book': 1, 'laptop': 2, 'keyboard': 1, 'cell phone': 0.3, 'backpack': 8, 'suitcase': 15, 'bottle': 1, 'cup': 0.3, 'box': 10, 'crate': 12, 'tools': 3, 'hammer': 2, 'screwdriver': 0.5}
    peso_total = 0
    for det in detecciones_yolo:
        objeto = det.get('name', '').lower()
        if objeto in tabla_pesos:
            peso_total += tabla_pesos[objeto]
    return min(peso_total, 30)

def analizar_owas_completo(datos):
    espalda_deg = datos.get('espalda_angulo', 0)
    espalda_rot = datos.get('espalda_rotacion', 0)
    
    if espalda_deg < 20:
        if espalda_rot > 20:
            c_espalda = 3
            desc_espalda = "Recta con rotacion"
        else:
            c_espalda = 1
            desc_espalda = "Recta"
    elif espalda_deg <= 60:
        if espalda_rot > 20:
            c_espalda = 3
            desc_espalda = "Inclinada con rotacion"
        else:
            c_espalda = 2
            desc_espalda = "Inclinada"
    elif espalda_deg <= 90:
        if espalda_rot > 20:
            c_espalda = 3
            desc_espalda = "Muy inclinada con rotacion"
        else:
            c_espalda = 2
            desc_espalda = "Muy inclinada"
    else:
        c_espalda = 4
        desc_espalda = "Extrema peligrosa"
    
    brazo_izq = datos.get('brazo_izq', 0)
    brazo_der = datos.get('brazo_der', 0)
    elevado_izq = brazo_izq < 90 if brazo_izq <= 180 else False
    elevado_der = brazo_der < 90 if brazo_der <= 180 else False
    
    if not elevado_izq and not elevado_der:
        c_brazos = 1
        desc_brazos = "Ambos brazos bajo hombro"
    elif elevado_izq != elevado_der:
        c_brazos = 2
        desc_brazos = "Un brazo sobre hombro"
    else:
        c_brazos = 3
        desc_brazos = "Ambos brazos sobre hombro"
    
    c_piernas = datos.get('piernas_codigo', 2)
    mapeo_piernas = {1: ("Sentado", "Normal", "Bajo"), 2: ("Parado piernas rectas", "Normal", "Bajo"), 3: ("Parado una pierna flexionada", "Riesgo bajo", "Bajo-Moderado"), 4: ("Parado piernas flexionadas", "Riesgo moderado", "Moderado"), 5: ("Sentadilla profunda", "Riesgo alto", "Alto"), 6: ("Arrodillado", "Riesgo alto", "Alto"), 7: ("Caminando", "Riesgo moderado", "Moderado")}
    desc_piernas, estado_piernas, riesgo_piernas = mapeo_piernas.get(c_piernas, ("Parado piernas rectas", "Normal", "Bajo"))
    
    carga_kg = datos.get('carga_kg', 0)
    if carga_kg < 10:
        c_carga = 1
        desc_carga = f"{carga_kg} kg"
    elif carga_kg <= 20:
        c_carga = 2
        desc_carga = f"{carga_kg} kg"
    else:
        c_carga = 3
        desc_carga = f"{carga_kg} kg"
    
    if (c_espalda == 4) or (c_piernas >= 5) or (c_espalda >= 3 and c_brazos >= 3):
        riesgo_n = 4
    elif (c_espalda >= 3) or (c_brazos >= 3) or (c_piernas == 4):
        riesgo_n = 3
    elif (c_espalda == 2) or (c_brazos == 2) or (c_carga == 2) or (c_piernas == 3):
        riesgo_n = 2
    else:
        riesgo_n = 1
    
    dictamen = f"DICTAMEN OWAS - Nivel {riesgo_n}/4 - Espalda: {desc_espalda}, Brazos: {desc_brazos}, Piernas: {desc_piernas}"
    
    return {
        "metodo": "OWAS",
        "codigo": f"{c_espalda}{c_brazos}{c_piernas}{c_carga}",
        "categoria_riesgo": riesgo_n,
        "recomendacion_ia": dictamen,
        "detalles": {"espalda": desc_espalda, "brazos": desc_brazos, "piernas": desc_piernas, "carga": desc_carga},
        "estados": {"espalda": estado_piernas, "brazos": "", "piernas": "", "carga": ""}
    }

def generar_dictamen_profesional(categoria, detalles, angulos):
    return f"DICTAMEN OWAS - Nivel {categoria}/4"
