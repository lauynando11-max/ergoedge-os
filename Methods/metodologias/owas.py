import numpy as np
import math

def calcular_angulo_3d(a, b, c):
    """Calcula ángulo en 3D entre tres puntos"""
    a, b, c = np.array(a), np.array(b), np.array(c)
    radianes = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angulo = np.abs(radianes * 180.0 / np.pi)
    return 360 - angulo if angulo > 180.0 else angulo

def calcular_rotacion_torso(hombro_izq, hombro_der, cadera_izq, cadera_der):
    """Calcula la rotación del torso para OWAS"""
    vector_hombros = np.array([hombro_der[0] - hombro_izq[0], hombro_der[2] - hombro_izq[2]])
    vector_caderas = np.array([cadera_der[0] - cadera_izq[0], cadera_der[2] - cadera_izq[2]])
    
    norma_h = np.linalg.norm(vector_hombros)
    norma_c = np.linalg.norm(vector_caderas)
    
    if norma_h == 0 or norma_c == 0:
        return 0
    
    cos_angulo = np.dot(vector_hombros, vector_caderas) / (norma_h * norma_c)
    cos_angulo = max(-1, min(1, cos_angulo))  # Clip para evitar errores numéricos
    
    angulo = np.arccos(cos_angulo)
    return np.degrees(angulo)

def detectar_postura_piernas(landmarks):
    """Detecta la postura de piernas según OWAS (7 categorías)"""
    try:
        cadera_izq = landmarks.get('left_hip')
        cadera_der = landmarks.get('right_hip')
        rodilla_izq = landmarks.get('left_knee')
        rodilla_der = landmarks.get('right_knee')
        tobillo_izq = landmarks.get('left_ankle')
        tobillo_der = landmarks.get('right_ankle')
        
        if not all([cadera_izq, rodilla_izq, tobillo_izq]):
            return 2  # Default: parado con piernas rectas
        
        # Calcular ángulos de rodilla
        ang_rodilla_izq = calcular_angulo_3d(cadera_izq, rodilla_izq, tobillo_izq)
        ang_rodilla_der = calcular_angulo_3d(cadera_der, rodilla_der, tobillo_der)
        
        # Promedio de altura de caderas y rodillas
        altura_cadera = (cadera_izq[1] + cadera_der[1]) / 2
        altura_rodilla = (rodilla_izq[1] + rodilla_der[1]) / 2
        
        # 1 = Sentado
        if altura_rodilla < altura_cadera - 0.15:
            return 1
        
        # 5 = Sentadilla profunda (ángulo de rodilla < 100°)
        if ang_rodilla_izq < 100 or ang_rodilla_der < 100:
            return 5
        
        # 4 = Parado con piernas flexionadas
        if ang_rodilla_izq < 150 or ang_rodilla_der < 150:
            return 4
        
        # 3 = Parado con una pierna flexionada
        if abs(ang_rodilla_izq - ang_rodilla_der) > 30:
            return 3
        
        # 2 = Parado con piernas rectas
        return 2
        
    except:
        return 2  # Default

def estimar_carga_detectada(detecciones_yolo):
    """Estima el peso de carga basado en objetos detectados por YOLO"""
    # Mapeo de objetos a pesos en kg
    tabla_pesos = {
        'chair': 5, 'book': 1, 'laptop': 2, 'keyboard': 1,
        'cell phone': 0.3, 'backpack': 8, 'suitcase': 15,
        'bottle': 1, 'cup': 0.3, 'box': 10, 'crate': 12,
        'tools': 3, 'hammer': 2, 'screwdriver': 0.5
    }
    
    peso_total = 0
    objetos_detectados = []
    
    for det in detecciones_yolo:
        objeto = det.get('name', '').lower()
        objetos_detectados.append(objeto)
        if objeto in tabla_pesos:
            peso_total += tabla_pesos[objeto]
    
    return min(peso_total, 30)  # Máximo 30 kg

def analizar_owas_completo(datos):
    """
    Implementación COMPLETA y CORRECTA del método OWAS
    
    Datos esperados:
    - espalda_angulo: ángulo de flexión de espalda en grados
    - espalda_rotacion: ángulo de rotación de torso en grados
    - brazo_izq: ángulo de elevación brazo izquierdo
    - brazo_der: ángulo de elevación brazo derecho
    - piernas_codigo: código de postura de piernas (1-7)
    - carga_kg: peso en kilogramos
    - movimiento_forzado: boolean (True/False)
    """
    
    # ==================== 1. ESPALDA (Dígito 1) ====================
    espalda_deg = datos.get('espalda_angulo', 0)
    espalda_rot = datos.get('espalda_rotacion', 0)
    
    if espalda_deg < 5:
        c_espalda = 1
        desc_espalda = "Recta"
        estado_espalda = "Normal"
        riesgo_espalda = "Bajo"
    elif espalda_deg < 20:
        if espalda_rot > 20:
            c_espalda = 3  # Torcida con rotación
            desc_espalda = "Torcida con rotación"
            estado_espalda = "Riesgo moderado"
            riesgo_espalda = "Moderado"
        else:
            c_espalda = 2
            desc_espalda = "Torcida"
            estado_espalda = "Riesgo bajo"
            riesgo_espalda = "Bajo-Moderado"
    elif espalda_deg < 60:
        if espalda_rot > 20:
            c_espalda = 3
            desc_espalda = "Torcida con rotación"
            estado_espalda = "Riesgo alto"
            riesgo_espalda = "Alto"
        else:
            c_espalda = 3
            desc_espalda = "Torcida significativa"
            estado_espalda = "Riesgo alto"
            riesgo_espalda = "Alto"
    else:
        c_espalda = 4
        desc_espalda = "Inclinación peligrosa"
        estado_espalda = "Riesgo crítico"
        riesgo_espalda = "Crítico"
    
    # ==================== 2. BRAZOS (Dígito 2) ====================
    brazo_izq = datos.get('brazo_izq', 0)
    brazo_der = datos.get('brazo_der', 0)
    brazo_max = max(brazo_izq, brazo_der)
    brazo_min = min(brazo_izq, brazo_der)
    movimiento_forzado = datos.get('movimiento_forzado', False)
    
    if movimiento_forzado:
        c_brazos = 4
        desc_brazos = "Movimiento forzado/repetitivo"
        estado_brazos = "Riesgo alto"
        riesgo_brazos = "Alto"
    elif brazo_max < 90:
        c_brazos = 1
        desc_brazos = "Ambos brazos bajo hombro"
        estado_brazos = "Normal"
        riesgo_brazos = "Bajo"
    elif brazo_min >= 90:
        c_brazos = 3
        desc_brazos = "Ambos brazos sobre hombro"
        estado_brazos = "Riesgo alto"
        riesgo_brazos = "Alto"
    else:
        c_brazos = 2
        desc_brazos = "Un brazo sobre hombro"
        estado_brazos = "Riesgo moderado"
        riesgo_brazos = "Moderado"
    
    # ==================== 3. PIERNAS (Dígito 3) ====================
    c_piernas = datos.get('piernas_codigo', 2)
    
    mapeo_piernas = {
        1: ("Sentado", "Normal", "Bajo"),
        2: ("Parado piernas rectas", "Normal", "Bajo"),
        3: ("Parado una pierna flexionada", "Riesgo bajo", "Bajo-Moderado"),
        4: ("Parado piernas flexionadas", "Riesgo moderado", "Moderado"),
        5: ("Sentadilla profunda", "Riesgo alto", "Alto"),
        6: ("Arrodillado", "Riesgo alto", "Alto"),
        7: ("Caminando", "Riesgo moderado", "Moderado")
    }
    
    desc_piernas, estado_piernas, riesgo_piernas = mapeo_piernas.get(c_piernas, ("Parado piernas rectas", "Normal", "Bajo"))
    
    # ==================== 4. CARGA (Dígito 4) ====================
    carga_kg = datos.get('carga_kg', 0)
    
    if carga_kg < 10:
        c_carga = 1
        desc_carga = f"{carga_kg} kg"
        estado_carga = "Normal"
        riesgo_carga = "Bajo"
    elif carga_kg <= 20:
        c_carga = 2
        desc_carga = f"{carga_kg} kg"
        estado_carga = "Riesgo moderado"
        riesgo_carga = "Moderado"
    else:
        c_carga = 3
        desc_carga = f"{carga_kg} kg"
        estado_carga = "Riesgo alto"
        riesgo_carga = "Alto"
    
    # ==================== 5. CÁLCULO DE RIESGO OWAS ====================
    # Matriz de decisión según código OWAS
    
    # Combinaciones de Nivel 4 (Acción inmediata)
    if (c_espalda >= 3 and c_brazos >= 3) or \
       (c_espalda == 4) or \
       (c_brazos == 4) or \
       (c_piernas >= 5) or \
       (c_carga == 3 and c_espalda >= 2) or \
       (c_carga == 3 and c_brazos >= 2):
        riesgo_n = 4
    
    # Combinaciones de Nivel 3 (Acción corto plazo)
    elif (c_espalda >= 3) or \
         (c_brazos >= 3) or \
         (c_piernas == 4) or \
         (c_carga >= 2 and (c_espalda >= 2 or c_brazos >= 2)):
        riesgo_n = 3
    
    # Combinaciones de Nivel 2 (Acción futuro)
    elif (c_espalda == 2) or \
         (c_brazos == 2) or \
         (c_carga == 2) or \
         (c_piernas == 3):
        riesgo_n = 2
    
    # Nivel 1 (Sin acción)
    else:
        riesgo_n = 1
    
    # ==================== 6. DICTAMEN INTELIGENTE ====================
    dictamen = generar_dictamen_profesional(riesgo_n, {
        'espalda': desc_espalda,
        'brazos': desc_brazos,
        'piernas': desc_piernas,
        'carga': desc_carga
    }, {
        'espalda': espalda_deg,
        'brazos': brazo_max,
        'rotacion': espalda_rot
    })
    
    return {
        "metodo": "OWAS",
        "codigo": f"{c_espalda}{c_brazos}{c_piernas}{c_carga}",
        "categoria_riesgo": riesgo_n,
        "recomendacion_ia": dictamen,
        "detalles": {
            "espalda": f"{desc_espalda} ({round(espalda_deg, 1)}°, rotación {round(espalda_rot, 1)}°)",
            "brazos": f"{desc_brazos} (máx: {round(brazo_max, 1)}°)",
            "piernas": desc_piernas,
            "carga": desc_carga
        },
        "estados": {
            "espalda": estado_espalda,
            "brazos": estado_brazos,
            "piernas": estado_piernas,
            "carga": estado_carga
        },
        "angulos_crudos": {
            "espalda": f"{round(espalda_deg, 1)}°",
            "brazo_izq": f"{round(brazo_izq, 1)}°",
            "brazo_der": f"{round(brazo_der, 1)}°",
            "rotacion": f"{round(espalda_rot, 1)}°"
        }
    }

def generar_dictamen_profesional(categoria, detalles, angulos):
    """Genera recomendaciones profesionales basadas en OWAS"""
    
    niveles = {
        1: "SIN RIESGO SIGNIFICATIVO",
        2: "RIESGO MODERADO - Requiere monitoreo",
        3: "RIESGO ALTO - Intervención necesaria",
        4: "RIESGO CRÍTICO - Acción inmediata"
    }
    
    recomendaciones = []
    
    # Recomendaciones específicas por segmento
    if "Inclinación peligrosa" in detalles['espalda']:
        recomendaciones.append("🔴 ELEVAR la superficie de trabajo 20-30 cm")
        recomendaciones.append("🔴 Implementar ayudas mecánicas para manipulación")
        recomendaciones.append("🔴 Reducir peso de carga o frecuencia de levantamiento")
    
    if "Torcida" in detalles['espalda']:
        recomendaciones.append("🟡 Reorganizar área de trabajo para evitar giros")
        recomendaciones.append("🟡 Colocar materiales frente al operario")
    
    if "Ambos brazos sobre hombro" in detalles['brazos']:
        recomendaciones.append("🔴 REDUCIR altura de almacenamiento")
        recomendaciones.append("🔴 Instalar plataformas elevadoras")
    
    if "Sentadilla" in detalles['piernas']:
        recomendaciones.append("🟡 Proporcionar asiento regulable")
        recomendaciones.append("🟡 Rediseñar tarea para posición de pie")
    
    if "kg" in detalles['carga'] and "> 10" in detalles['carga']:
        kg = int(detalles['carga'].split()[0])
        if kg > 20:
            recomendaciones.append("🔴 REDUCIR peso por unidad o implementar ayudas mecánicas")
        else:
            recomendaciones.append("🟡 Capacitar en técnicas de levantamiento seguro")
    
    if not recomendaciones:
        recomendaciones.append("✅ Mantener buenas prácticas ergonómicas")
    
    dictamen_texto = f"""
╔══════════════════════════════════════════════════════════════╗
║              DICTAMEN ERGONÓMICO - MÉTODO OWAS               ║
╚══════════════════════════════════════════════════════════════╝

📊 NIVEL DE RIESGO: {niveles.get(categoria, 'No clasificado')} (Nivel {categoria}/4)

🔍 ANÁLISIS DETALLADO:
• Espalda: {detalles['espalda']}
• Brazos: {detalles['brazos']}
• Piernas: {detalles['piernas']}
• Carga: {detalles['carga']}

🛠️ RECOMENDACIONES PRIORITARIAS:
{chr(10).join(recomendaciones)}

📌 Código OWAS: {categoria}/4
"""
    return dictamen_texto