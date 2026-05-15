"""
ERGOEDGE OS - Servidor Web con Flask
Soporte para OWAS, RULA, REBA y ROSA
"""

import sys
import os
import tempfile
import uuid
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, request, redirect, url_for, send_file, session, jsonify
from flask_session import Session
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from ultralytics import YOLO

# ==== Para autenticación ====
import hashlib
import secrets
from datetime import datetime
import time

# ==== Variables de entorno ====
from dotenv import load_dotenv
load_dotenv()

# ==== IMPORTAR BASE DE DATOS SQLITE ====
from database import (
    init_db, crear_usuario, obtener_usuario_por_token,
    obtener_usuario_por_email, guardar_analisis,
    obtener_historial_usuario, obtener_analisis_por_id
)

# Importar métodos
from Methods.metodologias.rosa import evaluar_rosa
from Methods.metodologias.rula import evaluar_rula
from Methods.metodologias.reba_3d.reba_calculator import RebaCalculator
# Importar funciones de Gemini
from main import generar_dictamen_gemini_unificado
# Importar generadores de PDF
from Methods.reports import generar_reporte_rosa, generar_reporte_reba, generar_reporte_generico

# ==================== DICTAMEN PROFESIONAL DE RESPALDO ====================
def generar_dictamen_profesional(metodo, resultados, datos_operario):
    """Genera dictamen profesional basado en especialistas (sin Gemini)"""
    
    nombre = datos_operario.get('nombre', 'Operario')
    edad = datos_operario.get('edad', '')
    antiguedad = datos_operario.get('antiguedad', '')
    patologias = datos_operario.get('patologias', '')
    patologia_riesgo = any(p in patologias.lower() for p in ['hernia', 'disco', 'lumbar', 'cervical', 'dolor', 'escoliosis'])
    
    if metodo == 'OWAS':
        nivel = resultados.get('puntuacion', 1)
        codigo = resultados.get('codigo_owas', 'N/A')
        peso_carga = resultados.get('peso_carga', 0)
        
        if nivel >= 4 or patologia_riesgo:
            return f"""DICTAMEN ERGONÓMICO - RIESGO CRÍTICO

El operario {nombre} ({edad} años, {antiguedad} años de antigüedad) presenta exposición MUY DAÑINA según evaluación OWAS (Código {codigo}). {'⚠️ ATENCIÓN: Patologías preexistentes agravan el riesgo.' if patologia_riesgo else ''}

🔴 RECOMENDACIONES URGENTES (Ingeniería):
• Rediseñar el puesto con mesas de altura regulable (rango 70-110 cm)
• Instalar ayudas mecánicas obligatorias (balancines, polipastos)
• Rotar tareas cada 30 minutos
• Evaluación médica en un plazo NO MAYOR a 7 días

📋 MEDIDAS ORGANIZACIONALES:
• Capacitación en técnicas de levantamiento seguro
• Recordatorios de cambio postural cada 15 minutos
• Pausas activas obligatorias cada 30 minutos"""
        
        elif nivel >= 3:
            return f"""DICTAMEN ERGONÓMICO - RIESGO ALTO

El trabajador {nombre} requiere intervención en el corto plazo (30 días).

Recomendaciones:
• Ajustar altura del plano de trabajo (espalda <20° flexión)
• Instalar apoyabrazos ergonómicos ajustables
• Pausas activas cada 45 minutos
• Seguimiento médico semestral"""
        
        elif nivel >= 2:
            return f"""DICTAMEN ERGONÓMICO - RIESGO MODERADO

El puesto evaluado requiere ajustes programados (90 días).

Recomendaciones:
• Reorganizar elementos al alcance frontal
• Capacitación en auto-corrección postural
• Monitoreo ergonómico trimestral"""
        
        else:
            return f"""DICTAMEN ERGONÓMICO - RIESGO BAJO

Las condiciones posturales del operario {nombre} son aceptables.

Recomendaciones preventivas:
• Mantener pausas activas diarias
• Auditorías ergonómicas anuales"""
    
    elif metodo == 'RULA':
        punt = resultados.get('puntuacion', 1)
        peso_carga = resultados.get('peso_carga', 0)
        if punt >= 6:
            return f"""DICTAMEN ERGONÓMICO - RIESGO MUY ALTO (RULA)

El operario {nombre} presenta riesgo crítico en miembros superiores ({punt}/7).

{'⚠️ La carga de ' + str(peso_carga) + ' kg agrava significativamente el riesgo.' if peso_carga > 10 else ''}

Recomendaciones URGENTES:
• Rediseñar inmediatamente la tarea
• Instalar apoyabrazos y soporte ergonómico
• Evaluación médica urgente"""
        elif punt >= 4:
            return f"""DICTAMEN ERGONÓMICO - RIESGO MEDIO (RULA)

Recomendaciones: Ajustar alturas de trabajo y reducir alcances."""
        else:
            return f"""DICTAMEN ERGONÓMICO - RIESGO BAJO (RULA)

Mantener buenas prácticas posturales."""
    
    elif metodo == 'REBA':
        punt = resultados.get('puntuacion', 1)
        peso_carga = resultados.get('peso_carga', 0)
        if punt >= 11:
            return f"""DICTAMEN ERGONÓMICO - RIESGO MUY ALTO (REBA)

¡INTERVENCIÓN INMEDIATA REQUERIDA!
Puntuación REBA: {punt}/15. Suspender tarea hasta rediseño completo.

{'⚠️ La carga de ' + str(peso_carga) + ' kg requiere asistencia mecánica inmediata.' if peso_carga > 10 else ''}"""
        elif punt >= 8:
            return f"""DICTAMEN ERGONÓMICO - RIESGO ALTO (REBA)

Rediseñar el puesto en 30 días. Mejorar agarre y reducir carga."""
        else:
            return f"""DICTAMEN ERGONÓMICO - RIESGO BAJO (REBA)

Mantener buenas prácticas."""
    
    elif metodo == 'ROSA':
        punt = resultados.get('puntuacion_final', 1)
        if punt >= 8:
            return f"""DICTAMEN ERGONÓMICO - RIESGO MUY ALTO (ROSA)

Intervención inmediata en el puesto de oficina (puntuación: {punt}/10)."""
        else:
            return f"""DICTAMEN ERGONÓMICO - RIESGO {resultados.get('nivel_riesgo', 'MEDIO')}

Revisar ajustes de silla, monitor y teclado."""
    
    return "Consulte a un especialista en ergonomía para un dictamen detallado."


# Configurar la carpeta de templates
template_dir = os.path.join(os.path.dirname(__file__), 'web_app', 'templates')
app = Flask(__name__, template_folder=template_dir)

# Configurar sesión
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ergoedge_secret_key_2026')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

# ==================== INICIALIZAR BASE DE DATOS SQLITE ====================
init_db()
print("🗄️ Base de datos SQLite inicializada")


def hash_password(password: str) -> str:
    """Hashea una contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def get_usuario_actual():
    """Obtiene el usuario actual de la sesión usando SQLite"""
    token = session.get('user_token')
    if token:
        return obtener_usuario_por_token(token)
    return None


# ==================== FUNCIÓN PARA GUARDAR FRAMES DE RIESGO ====================
def guardar_frame_riesgo(frame, nivel, metodo, nombre_base):
    """Guarda un frame como imagen si tiene alto riesgo"""
    try:
        # Crear carpeta frames si no existe
        frames_dir = os.path.join(os.path.dirname(__file__), 'static', 'frames')
        os.makedirs(frames_dir, exist_ok=True)
        
        # Generar nombre único
        timestamp = int(time.time())
        img_path = os.path.join(frames_dir, f"{nombre_base}_{metodo}_riesgo_{nivel}_{timestamp}.jpg")
        
        # Guardar imagen
        cv2.imwrite(img_path, frame)
        
        # Devolver ruta relativa para la web
        return f"/static/frames/{os.path.basename(img_path)}"
    except Exception as e:
        print(f"⚠️ Error guardando frame: {e}")
        return None


# ============ RUTAS DE AUTENTICACIÓN ============

@app.route('/login')
def login_page():
    usuario = get_usuario_actual()
    if usuario:
        return redirect(url_for('dashboard'))
    return render_template('login.html', error=None, usuario=None)


@app.route('/registro')
def registro_page():
    usuario = get_usuario_actual()
    if usuario:
        return redirect(url_for('dashboard'))
    return render_template('registro.html', error=None, usuario=None)


@app.route('/registro', methods=['POST'])
def registro_post():
    nombre = request.form.get('nombre')
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Verificar si el email ya existe usando SQLite
    if obtener_usuario_por_email(email):
        return render_template('registro.html', error="Este correo ya está registrado", usuario=None)
    
    # Crear nuevo usuario
    token = secrets.token_urlsafe(32)
    password_hash = hash_password(password)
    
    try:
        crear_usuario(token, nombre, email, password_hash)
        return redirect(url_for('login_page'))
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        return render_template('registro.html', error="Error al crear usuario", usuario=None)


@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    hashed = hash_password(password)
    
    # Buscar usuario usando SQLite
    usuario = obtener_usuario_por_email(email)
    
    if usuario and usuario['password_hash'] == hashed:
        session['user_token'] = usuario['token']
        session['user_name'] = usuario['nombre']
        session['user_email'] = usuario['email']
        return redirect(url_for('dashboard'))
    
    return render_template('login.html', error="Correo o contraseña incorrectos", usuario=None)


@app.route('/dashboard')
def dashboard():
    usuario = get_usuario_actual()
    if not usuario:
        return redirect(url_for('login_page'))
    
    # Obtener historial desde SQLite
    token = session.get('user_token')
    historial = obtener_historial_usuario(token, limite=50)
    
    # Pasar historial como JSON para el frontend
    import json
    historial_json = json.dumps(historial, ensure_ascii=False)
    
    return render_template('dashboard.html', usuario=usuario, historial=historial, historial_json=historial_json)


# ============ API PARA EL DASHBOARD ============

@app.route('/api/analisis/<int:id>')
def api_analisis(id):
    """API para obtener los detalles de un análisis por ID usando SQLite"""
    token = session.get('user_token')
    if not token:
        return jsonify({"error": "No autorizado"}), 401
    
    analisis = obtener_analisis_por_id(id, token)
    if analisis:
        # Devolver el resultado completo
        return jsonify(analisis.get('resultado', {}))
    
    return jsonify({"error": "No encontrado"}), 404


@app.route('/api/ultimo_analisis')
def api_ultimo_analisis():
    """Devuelve el último análisis del usuario actual (para la vista previa)"""
    token = session.get('user_token')
    if not token:
        return jsonify({"error": "No autorizado"}), 401
    
    historial = obtener_historial_usuario(token, limite=1)
    if not historial:
        return jsonify({"error": "No hay análisis"}), 404
    
    # Obtener el análisis completo
    analisis = obtener_analisis_por_id(historial[0]['id'], token)
    if analisis:
        return jsonify(analisis.get('resultado', {}))
    
    return jsonify({"error": "No encontrado"}), 404


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# Configurar carpeta de uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB límite
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Cargar modelo YOLO
print("📥 Cargando modelo YOLO11 Pose...")
try:
    modelo_yolo = YOLO('yolo11x-pose.pt')
    modelo_yolo.overrides['conf'] = 0.4
    modelo_yolo.overrides['iou'] = 0.6
    modelo_yolo.overrides['max_det'] = 1
    print("✅ Modelo YOLO11x-pose cargado")
except:
    modelo_yolo = YOLO('yolo11m-pose.pt')
    print("✅ Modelo YOLO11m-pose cargado")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== FUNCIONES DE PROCESAMIENTO ====================

def procesar_frame_owas(keypoints, frame, codigo_carga_constante=1, keypoints_anterior=None):
    from Methods.comunes import obtener_punto, calcular_angulo_2d, clasificar_riesgo_owas, calcular_torsion_avanzada, detectar_carga_dinamica
    
    hombro = obtener_punto(keypoints, 5)
    cadera = obtener_punto(keypoints, 11)
    rodilla_izq = obtener_punto(keypoints, 13)
    rodilla_der = obtener_punto(keypoints, 14)
    tobillo_izq = obtener_punto(keypoints, 15)
    tobillo_der = obtener_punto(keypoints, 16)
    hombro_der = obtener_punto(keypoints, 6)
    
    # ========== ESPALDA (Código 1-4) ==========
    if hombro and cadera and rodilla_izq:
        angulo_espalda = calcular_angulo_2d(hombro, cadera, rodilla_izq)
        if angulo_espalda > 90:
            angulo_espalda = 180 - angulo_espalda
    else:
        angulo_espalda = 0
    
    # ========== TORSIÓN AVANZADA ==========
    hombro_izq_punto = obtener_punto(keypoints, 5)
    hombro_der_punto = obtener_punto(keypoints, 6)
    cadera_izq_punto = obtener_punto(keypoints, 11)
    cadera_der_punto = obtener_punto(keypoints, 12)
    
    torsion_data = calcular_torsion_avanzada(hombro_izq_punto, hombro_der_punto, cadera_izq_punto, cadera_der_punto)
    torsion = 1 if torsion_data['detectada'] else 0
    
    if angulo_espalda <= 20:
        codigo_espalda = 1
    elif angulo_espalda <= 60:
        codigo_espalda = 2
    elif angulo_espalda <= 90:
        codigo_espalda = 3
    else:
        codigo_espalda = 4
    
    # Aplicar torsión con incremento según severidad
    if torsion_data['detectada']:
        codigo_espalda = min(codigo_espalda + torsion_data['incremento'], 4)
        print(f"   🔄 Torsión: {torsion_data['angulo']}° hacia {torsion_data['direccion']} (+{torsion_data['incremento']})")
    
    # ========== BRAZOS (Código 1-2) ==========
    hombro_brazo = obtener_punto(keypoints, 5)
    hombro_brazo_der = obtener_punto(keypoints, 6)
    muneca = obtener_punto(keypoints, 9)
    muneca_der = obtener_punto(keypoints, 10)
    
    brazo_sobre_hombro = 0
    if muneca and hombro_brazo:
        if muneca[1] < hombro_brazo[1] - 30:
            brazo_sobre_hombro = 1
    if muneca_der and hombro_brazo_der:
        if muneca_der[1] < hombro_brazo_der[1] - 30:
            brazo_sobre_hombro = 1
    
    codigo_brazo = 2 if brazo_sobre_hombro else 1
    
    # ========== PIERNAS (Código 1-7 OWAS oficial) ==========
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
    angulo_rodilla_der = 180
    pierna_izq_flexionada = False
    pierna_der_flexionada = False
    
    if cadera and rodilla_izq and tobillo_izq:
        angulo_rodilla_izq = calcular_angulo_2d(cadera, rodilla_izq, tobillo_izq)
        if angulo_rodilla_izq < 150:
            pierna_izq_flexionada = True
    
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
    
    # ========== CARGA DINÁMICA ==========
    carga_data = detectar_carga_dinamica(keypoints, keypoints_anterior, codigo_carga_constante)
    codigo_carga = carga_data['codigo_carga']
    estado_carga = carga_data['descripcion']
    
    if carga_data['cargando']:
        print(f"   📦 Carga: {carga_data['descripcion']} (código {codigo_carga})")
    
    nivel_riesgo, categoria, accion = clasificar_riesgo_owas(codigo_espalda, codigo_brazo, codigo_piernas, codigo_carga)
    codigo_owas = f"{codigo_espalda}{codigo_brazo}{codigo_piernas}{codigo_carga}"
    
    return {
        'nivel_riesgo': nivel_riesgo,
        'categoria': categoria,
        'accion': accion,
        'codigo_owas': codigo_owas,
        'angulo_espalda': angulo_espalda,
        'torsion': torsion,
        'torsion_angulo': torsion_data['angulo'] if torsion_data['detectada'] else 0,
        'torsion_direccion': torsion_data['direccion'] if torsion_data['detectada'] else 'neutro',
        'carga_detectada': carga_data['cargando'],
        'carga_codigo': codigo_carga,
        'carga_descripcion': carga_data['descripcion'],
        'sentado': sentado,
        'arrodillado': arrodillado,
        'caminando': caminando,
        'pierna_izq_flexionada': pierna_izq_flexionada,
        'pierna_der_flexionada': pierna_der_flexionada,
        'angulo_rodilla_izq': round(angulo_rodilla_izq, 1),
        'angulo_rodilla_der': round(angulo_rodilla_der, 1)
    }


def procesar_owas(filepath, es_video, datos_operario_ia=None):
    from Methods.comunes import obtener_punto, calcular_angulo_2d, clasificar_riesgo_owas, calcular_torsion_avanzada, detectar_carga_dinamica
    
    print(f"\n🔍 PROCESANDO OWAS - Archivo: {filepath}")
    print(f"   Tipo: {'Video' if es_video else 'Foto'}")
    
    peso_carga = 0
    if datos_operario_ia:
        peso_carga = datos_operario_ia.get('peso_carga', 0)
        try:
            peso_carga = float(peso_carga)
        except:
            peso_carga = 0
    
    if peso_carga == 0:
        codigo_carga_constante = 1
    elif peso_carga <= 10:
        codigo_carga_constante = 1
    elif peso_carga <= 20:
        codigo_carga_constante = 2
    else:
        codigo_carga_constante = 3
    
    print(f"   📦 Peso de carga: {peso_carga} kg - Código OWAS base: {codigo_carga_constante}")
    
    if es_video:
        cap = cv2.VideoCapture(filepath)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        
        frame_count = 0
        resultados = []
        evolucion_temporal = []
        ultimo_porcentaje = 0
        mejores_frames = []
        nombre_base = f"{datos_operario_ia.get('nombre', 'operario')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        MIN_FRAME_SEPARACION = 30
        
        keypoints_anterior = None
        frame_anterior = None
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % 15 == 0:  # Optimizado: procesa 1 de cada 15 frames
                results = modelo_yolo(frame, verbose=False)
                if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
                    keypoints = results[0].keypoints.data[0].cpu().numpy()
                    
                    resultado = procesar_frame_owas(keypoints, frame, codigo_carga_constante, keypoints_anterior)
                    resultados.append(resultado)
                    
                    tiempo_seg = frame_count / fps if fps > 0 else frame_count / 30
                    evolucion_temporal.append([tiempo_seg, resultado['nivel_riesgo']])
                    
                    if resultado['nivel_riesgo'] >= 3:
                        es_momento_distinto = True
                        for _, _, frame_guardado in mejores_frames:
                            if abs(frame_guardado - frame_count) < MIN_FRAME_SEPARACION:
                                es_momento_distinto = False
                                break
                        
                        if es_momento_distinto and len(mejores_frames) < 5:
                            img_path = guardar_frame_riesgo(frame, resultado['nivel_riesgo'], 'OWAS', nombre_base)
                            if img_path:
                                mejores_frames.append((resultado['nivel_riesgo'], img_path, frame_count))
                                mejores_frames.sort(key=lambda x: x[0], reverse=True)
                                mejores_frames = mejores_frames[:3]
                    
                    keypoints_anterior = keypoints
                    frame_anterior = frame
                
                if total_frames > 0:
                    porcentaje = int((frame_count / total_frames) * 100)
                    if porcentaje >= ultimo_porcentaje + 5:
                        ultimo_porcentaje = porcentaje
                        print(f"   ⏳ Progreso: {porcentaje}%")
            
            frame_count += 1
        
        cap.release()
        print(f"   ✅ Procesamiento completado. {len(resultados)} frames analizados")
        
        if resultados:
            niveles = [r['nivel_riesgo'] for r in resultados]
            nivel_max = max(niveles)
            codigo_mas_comun = max(set([r['codigo_owas'] for r in resultados]), key=[r['codigo_owas'] for r in resultados].count)
            
            recomendaciones = []
            if nivel_max >= 3:
                recomendaciones.append("🔴 INTERVENCIÓN INMEDIATA: Rediseñar el puesto de trabajo")
                recomendaciones.append("🔴 Instalar ayudas mecánicas para manipulación de cargas")
            elif nivel_max >= 2:
                recomendaciones.append("⚠️ Implementar rotación de tareas")
                recomendaciones.append("⚠️ Ajustar altura de superficies de trabajo")
            else:
                recomendaciones.append("✓ Mantener programa de pausas activas")
            
            if peso_carga > 10:
                recomendaciones.append(f"⚠️ La carga de {peso_carga} kg requiere asistencia mecánica o reducción de peso")
            
            dictamen_ia = None
            if datos_operario_ia:
                try:
                    print(f"   🤖 Generando dictamen IA para OWAS...")
                    datos_ia = {'codigo_owas': codigo_mas_comun, 'riesgo_max': nivel_max, 'peso_carga': peso_carga}
                    dictamen_ia = generar_dictamen_gemini_unificado('OWAS', datos_ia, datos_operario_ia, None)
                    if dictamen_ia:
                        print(f"   ✅ Dictamen IA generado correctamente")
                except Exception as e:
                    print(f"   ❌ Error en dictamen IA OWAS: {e}")
            
            if not dictamen_ia or dictamen_ia == 'No se pudo generar dictamen. Consulte a un especialista en ergonomía.':
                dictamen_ia = generar_dictamen_profesional('OWAS', {'puntuacion': nivel_max, 'codigo_owas': codigo_mas_comun, 'peso_carga': peso_carga}, datos_operario_ia)
                print(f"   📋 Usando dictamen profesional para OWAS")
            
            imagenes_riesgo = [img_path for _, img_path, _ in mejores_frames]
            
            return {
                'puntuacion': nivel_max,
                'nivel_riesgo': {1: 'Normal', 2: 'Moderado', 3: 'Alto', 4: 'Crítico'}.get(nivel_max, 'Desconocido'),
                'codigo_owas': codigo_mas_comun,
                'recomendaciones': recomendaciones,
                'dictamen_ia': dictamen_ia,
                'imagenes_riesgo': imagenes_riesgo,
                'evolucion_temporal': evolucion_temporal,
                'peso_carga': peso_carga
            }
        else:
            return {'puntuacion': 1, 'nivel_riesgo': 'Sin datos', 'recomendaciones': ['No se detectaron personas'], 'evolucion_temporal': []}
    else:
        frame = cv2.imread(filepath)
        if frame is None:
            return {'error': 'No se pudo cargar la imagen'}
        
        results = modelo_yolo(frame, verbose=False)
        if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
            keypoints = results[0].keypoints.data[0].cpu().numpy()
            resultado = procesar_frame_owas(keypoints, frame, codigo_carga_constante)
            
            recomendaciones = []
            if resultado['nivel_riesgo'] >= 3:
                recomendaciones.append("🔴 INTERVENCIÓN INMEDIATA requerida")
            elif resultado['nivel_riesgo'] >= 2:
                recomendaciones.append("⚠️ Se requieren mejoras en el puesto")
            else:
                recomendaciones.append("✓ Postura aceptable")
            
            if peso_carga > 10:
                recomendaciones.append(f"⚠️ La carga de {peso_carga} kg requiere asistencia mecánica")
            
            dictamen_ia = None
            if datos_operario_ia:
                try:
                    print(f"   🤖 Generando dictamen IA para OWAS (foto)...")
                    datos_ia = {'codigo_owas': resultado['codigo_owas'], 'riesgo_max': resultado['nivel_riesgo'], 'peso_carga': peso_carga}
                    dictamen_ia = generar_dictamen_gemini_unificado('OWAS', datos_ia, datos_operario_ia, None)
                except Exception as e:
                    print(f"   ❌ Error en dictamen IA OWAS: {e}")
            
            if not dictamen_ia or dictamen_ia == 'No se pudo generar dictamen. Consulte a un especialista en ergonomía.':
                dictamen_ia = generar_dictamen_profesional('OWAS', resultado, datos_operario_ia)
                print(f"   📋 Usando dictamen profesional para OWAS")
            
            return {
                'puntuacion': resultado['nivel_riesgo'],
                'nivel_riesgo': resultado['categoria'],
                'codigo_owas': resultado['codigo_owas'],
                'recomendaciones': recomendaciones,
                'dictamen_ia': dictamen_ia,
                'evolucion_temporal': [[0, resultado['nivel_riesgo']]],
                'peso_carga': peso_carga
            }
        else:
            return {'puntuacion': 1, 'nivel_riesgo': 'Sin datos', 'recomendaciones': ['No se detectó ninguna persona'], 'evolucion_temporal': []}


def procesar_rula(filepath, es_video, datos_operario_ia=None):
    from Methods.metodologias.rula import evaluar_rula
    
    print(f"\n🔍 PROCESANDO RULA - Archivo: {filepath}")
    print(f"   Tipo: {'Video' if es_video else 'Foto'}")
    
    peso_carga = 0
    if datos_operario_ia:
        peso_carga = datos_operario_ia.get('peso_carga', 0)
        try:
            peso_carga = float(peso_carga)
        except:
            peso_carga = 0
    
    print(f"   📦 Peso de carga: {peso_carga} kg")
    
    if es_video:
        cap = cv2.VideoCapture(filepath)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        
        frame_count = 0
        resultados = []
        evolucion_temporal = []
        ultimo_porcentaje = 0
        mejores_frames = []
        nombre_base = f"{datos_operario_ia.get('nombre', 'operario')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        MIN_FRAME_SEPARACION = 30
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % 15 == 0:  # Optimizado: procesa 1 de cada 15 frames
                results = modelo_yolo(frame, verbose=False)
                if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
                    keypoints = results[0].keypoints.data[0].cpu().numpy()
                    try:
                        resultado = evaluar_rula(keypoints, peso_carga=peso_carga)
                        resultados.append(resultado)
                        
                        tiempo_seg = frame_count / fps if fps > 0 else frame_count / 30
                        evolucion_temporal.append([tiempo_seg, resultado.get('puntuacion_final', 1)])
                        
                        if resultado.get('puntuacion_final', 0) >= 5:
                            es_momento_distinto = True
                            for _, _, frame_guardado in mejores_frames:
                                if abs(frame_guardado - frame_count) < MIN_FRAME_SEPARACION:
                                    es_momento_distinto = False
                                    break
                            
                            if es_momento_distinto and len(mejores_frames) < 5:
                                img_path = guardar_frame_riesgo(frame, resultado.get('puntuacion_final', 0), 'RULA', nombre_base)
                                if img_path:
                                    mejores_frames.append((resultado.get('puntuacion_final', 0), img_path, frame_count))
                                    mejores_frames.sort(key=lambda x: x[0], reverse=True)
                                    mejores_frames = mejores_frames[:3]
                    except Exception as e:
                        print(f"   ⚠️ Error en frame {frame_count}: {e}")
                        pass
                
                if total_frames > 0:
                    porcentaje = int((frame_count / total_frames) * 100)
                    if porcentaje >= ultimo_porcentaje + 5:
                        ultimo_porcentaje = porcentaje
                        print(f"   ⏳ Progreso: {porcentaje}%")
            
            frame_count += 1
        
        cap.release()
        
        if resultados:
            puntuaciones = [r['puntuacion_final'] for r in resultados]
            punt_max = max(puntuaciones)
            nivel_riesgo = {1: 'Bajo', 2: 'Bajo', 3: 'Medio', 4: 'Medio', 5: 'Alto', 6: 'Alto', 7: 'Muy alto'}.get(punt_max, 'Desconocido')
            
            recomendaciones = []
            if punt_max >= 6:
                recomendaciones.append("🔴 INTERVENCIÓN INMEDIATA")
            elif punt_max >= 4:
                recomendaciones.append("⚠️ Ajustar altura del plano de trabajo")
            else:
                recomendaciones.append("✓ Postura aceptable")
            
            if peso_carga > 10:
                recomendaciones.append(f"⚠️ La carga de {peso_carga} kg incrementa el riesgo en miembros superiores")
            
            dictamen_ia = None
            if datos_operario_ia:
                try:
                    print(f"   🤖 Generando dictamen IA para RULA...")
                    dictamen_ia = generar_dictamen_gemini_unificado('RULA', {'puntuacion_max': punt_max, 'peso_carga': peso_carga}, datos_operario_ia, None)
                    if dictamen_ia:
                        print(f"   ✅ Dictamen IA generado correctamente")
                except Exception as e:
                    print(f"   ❌ Error en dictamen IA RULA: {e}")
            
            if not dictamen_ia or dictamen_ia == 'No se pudo generar dictamen. Consulte a un especialista en ergonomía.':
                dictamen_ia = generar_dictamen_profesional('RULA', {'puntuacion': punt_max, 'peso_carga': peso_carga}, datos_operario_ia)
                print(f"   📋 Usando dictamen profesional para RULA")
            
            imagenes_riesgo = [img_path for _, img_path, _ in mejores_frames]
            
            return {
                'puntuacion': punt_max,
                'nivel_riesgo': nivel_riesgo,
                'recomendaciones': recomendaciones,
                'dictamen_ia': dictamen_ia,
                'imagenes_riesgo': imagenes_riesgo,
                'evolucion_temporal': evolucion_temporal,
                'peso_carga': peso_carga
            }
        else:
            return {'puntuacion': 1, 'nivel_riesgo': 'Sin datos', 'recomendaciones': ['No se detectaron personas'], 'evolucion_temporal': []}
    else:
        frame = cv2.imread(filepath)
        if frame is None:
            return {'error': 'No se pudo cargar la imagen'}
        
        results = modelo_yolo(frame, verbose=False)
        if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
            keypoints = results[0].keypoints.data[0].cpu().numpy()
            resultado = evaluar_rula(keypoints, peso_carga=peso_carga)
            
            punt = resultado['puntuacion_final']
            recomendaciones = []
            if punt >= 6:
                recomendaciones.append("🔴 Riesgo muy alto")
            elif punt >= 4:
                recomendaciones.append("⚠️ Riesgo medio")
            else:
                recomendaciones.append("✓ Riesgo bajo")
            
            if peso_carga > 10:
                recomendaciones.append(f"⚠️ La carga de {peso_carga} kg incrementa el riesgo")
            
            dictamen_ia = None
            if datos_operario_ia:
                try:
                    print(f"   🤖 Generando dictamen IA para RULA (foto)...")
                    dictamen_ia = generar_dictamen_gemini_unificado('RULA', {'puntuacion_max': punt, 'peso_carga': peso_carga}, datos_operario_ia, None)
                except Exception as e:
                    print(f"   ❌ Error en dictamen IA RULA: {e}")
            
            if not dictamen_ia or dictamen_ia == 'No se pudo generar dictamen. Consulte a un especialista en ergonomía.':
                dictamen_ia = generar_dictamen_profesional('RULA', {'puntuacion': punt, 'peso_carga': peso_carga}, datos_operario_ia)
                print(f"   📋 Usando dictamen profesional para RULA")
            
            return {
                'puntuacion': punt,
                'nivel_riesgo': resultado['nivel_riesgo'],
                'recomendaciones': recomendaciones,
                'dictamen_ia': dictamen_ia,
                'evolucion_temporal': [[0, punt]],
                'peso_carga': peso_carga
            }
        else:
            return {'puntuacion': 1, 'nivel_riesgo': 'Sin datos', 'recomendaciones': ['No se detectó ninguna persona'], 'evolucion_temporal': []}


def procesar_reba(filepath, es_video, datos_operario_ia=None):
    reba_calc = RebaCalculator()
    print(f"\n🔍 PROCESANDO REBA - Archivo: {filepath}")
    print(f"   Tipo: {'Video' if es_video else 'Foto'}")
    
    peso_carga = 0
    if datos_operario_ia:
        peso_carga = datos_operario_ia.get('peso_carga', 0)
        try:
            peso_carga = float(peso_carga)
        except:
            peso_carga = 0
    
    print(f"   📦 Peso de carga: {peso_carga} kg")
    
    if es_video:
        cap = cv2.VideoCapture(filepath)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        
        frame_count = 0
        resultados = []
        evolucion_temporal = []
        ultimo_porcentaje = 0
        mejores_frames = []
        nombre_base = f"{datos_operario_ia.get('nombre', 'operario')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        MIN_FRAME_SEPARACION = 30
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % 15 == 0:  # Optimizado: procesa 1 de cada 15 frames
                results = modelo_yolo(frame, verbose=False)
                if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
                    keypoints = results[0].keypoints.data[0].cpu().numpy()
                    try:
                        resultado = reba_calc.evaluar(keypoints, frame.shape[1], frame.shape[0], peso_carga=peso_carga, acople=0)
                        resultados.append(resultado)
                        
                        tiempo_seg = frame_count / fps if fps > 0 else frame_count / 30
                        evolucion_temporal.append([tiempo_seg, resultado.get('puntuacion_final', 1)])
                        
                        if resultado.get('puntuacion_final', 0) >= 8:
                            es_momento_distinto = True
                            for _, _, frame_guardado in mejores_frames:
                                if abs(frame_guardado - frame_count) < MIN_FRAME_SEPARACION:
                                    es_momento_distinto = False
                                    break                            
                            if es_momento_distinto and len(mejores_frames) < 5:
                                img_path = guardar_frame_riesgo(frame, resultado.get('puntuacion_final', 0), 'REBA', nombre_base)
                                if img_path:
                                    mejores_frames.append((resultado.get('puntuacion_final', 0), img_path, frame_count))
                                    mejores_frames.sort(key=lambda x: x[0], reverse=True)
                                    mejores_frames = mejores_frames[:3]
                    except Exception as e:
                        print(f"   ⚠️ Error en frame {frame_count}: {e}")
                        pass
                
                if total_frames > 0:
                    porcentaje = int((frame_count / total_frames) * 100)
                    if porcentaje >= ultimo_porcentaje + 5:
                        ultimo_porcentaje = porcentaje
                        print(f"   ⏳ Progreso: {porcentaje}%")
            
            frame_count += 1
        
        cap.release()
        
        if resultados:
            puntuaciones = [r['puntuacion_final'] for r in resultados]
            punt_max = max(puntuaciones)
            nivel_riesgo = resultados[0]['nivel_riesgo'] if resultados else 'Desconocido'
            
            recomendaciones = []
            if punt_max >= 11:
                recomendaciones.append("🆘 PARALIZAR TAREA - INTERVENCIÓN INMEDIATA")
            elif punt_max >= 8:
                recomendaciones.append("🔴 INTERVENCIÓN PRONTA - Rediseñar puesto")
            elif punt_max >= 4:
                recomendaciones.append("⚠️ Implementar rotación de tareas")
            else:
                recomendaciones.append("✓ Riesgo bajo - Mantener buenas prácticas")
            
            if peso_carga > 10:
                recomendaciones.append(f"⚠️ La carga de {peso_carga} kg requiere asistencia mecánica")
            
            dictamen_ia = None
            if datos_operario_ia:
                try:
                    print(f"   🤖 Generando dictamen IA para REBA...")
                    dictamen_ia = generar_dictamen_gemini_unificado('REBA', {'puntuacion_max': punt_max, 'peso_carga': peso_carga}, datos_operario_ia, None)
                    if dictamen_ia:
                        print(f"   ✅ Dictamen IA generado correctamente")
                except Exception as e:
                    print(f"   ❌ Error en dictamen IA REBA: {e}")
            
            if not dictamen_ia or dictamen_ia == 'No se pudo generar dictamen. Consulte a un especialista en ergonomía.':
                dictamen_ia = generar_dictamen_profesional('REBA', {'puntuacion': punt_max, 'peso_carga': peso_carga}, datos_operario_ia)
                print(f"   📋 Usando dictamen profesional para REBA")
            
            imagenes_riesgo = [img_path for _, img_path, _ in mejores_frames]
            
            return {
                'puntuacion': punt_max,
                'nivel_riesgo': nivel_riesgo,
                'recomendaciones': recomendaciones,
                'dictamen_ia': dictamen_ia,
                'imagenes_riesgo': imagenes_riesgo,
                'evolucion_temporal': evolucion_temporal,
                'peso_carga': peso_carga
            }
        else:
            return {'puntuacion': 1, 'nivel_riesgo': 'Sin datos', 'recomendaciones': ['No se detectaron personas'], 'evolucion_temporal': []}
    else:
        frame = cv2.imread(filepath)
        if frame is None:
            return {'error': 'No se pudo cargar la imagen'}
        
        results = modelo_yolo(frame, verbose=False)
        if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
            keypoints = results[0].keypoints.data[0].cpu().numpy()
            resultado = reba_calc.evaluar(keypoints, frame.shape[1], frame.shape[0], peso_carga=peso_carga, acople=0)
            
            punt = resultado['puntuacion_final']
            recomendaciones = []
            if punt >= 11:
                recomendaciones.append("🆘 RIESGO MUY ALTO - INTERVENCIÓN INMEDIATA")
            elif punt >= 8:
                recomendaciones.append("🔴 RIESGO ALTO - Intervención pronta")
            elif punt >= 4:
                recomendaciones.append("⚠️ RIESGO MEDIO - Mejoras necesarias")
            else:
                recomendaciones.append("✓ RIESGO BAJO - Mantener prácticas")
            
            if peso_carga > 10:
                recomendaciones.append(f"⚠️ La carga de {peso_carga} kg requiere asistencia mecánica")
            
            dictamen_ia = None
            if datos_operario_ia:
                try:
                    print(f"   🤖 Generando dictamen IA para REBA (foto)...")
                    dictamen_ia = generar_dictamen_gemini_unificado('REBA', {'puntuacion_max': punt, 'peso_carga': peso_carga}, datos_operario_ia, None)
                except Exception as e:
                    print(f"   ❌ Error en dictamen IA REBA: {e}")
            
            if not dictamen_ia or dictamen_ia == 'No se pudo generar dictamen. Consulte a un especialista en ergonomía.':
                dictamen_ia = generar_dictamen_profesional('REBA', {'puntuacion': punt, 'peso_carga': peso_carga}, datos_operario_ia)
                print(f"   📋 Usando dictamen profesional para REBA")
            
            return {
                'puntuacion': punt,
                'nivel_riesgo': resultado['nivel_riesgo'],
                'recomendaciones': recomendaciones,
                'dictamen_ia': dictamen_ia,
                'evolucion_temporal': [[0, punt]],
                'peso_carga': peso_carga
            }
        else:
            return {'puntuacion': 1, 'nivel_riesgo': 'Sin datos', 'recomendaciones': ['No se detectó ninguna persona'], 'evolucion_temporal': []}


# ==================== RUTAS EXISTENTES ====================

@app.route('/')
def home():
    usuario = get_usuario_actual()
    return render_template('index.html', usuario=usuario)


@app.route('/analisis')
def analisis():
    usuario = get_usuario_actual()
    return render_template('analisis.html', usuario=usuario)


@app.route('/rosa')
def rosa_form():
    usuario = get_usuario_actual()
    return render_template('rosa_form.html', usuario=usuario)


@app.route('/rosa/calcular', methods=['POST'])
def rosa_calcular():
    usuario = get_usuario_actual()
    empresa = request.form.get('empresa', '')
    puesto = request.form.get('puesto', '')
    evaluador = request.form.get('evaluador', '')
    operario_nombre = request.form.get('operario_nombre', '')
    operario_edad = request.form.get('operario_edad', 0)
    operario_antiguedad = request.form.get('operario_antiguedad', '')
    operario_patologias = request.form.get('operario_patologias', '')
    uso_continuo = request.form.get('uso_continuo') == 'true'
    
    datos_rosa = {
        "silla": {"altura": 2, "apoyo_lumbar": "presente", "profundidad_asiento": "parcial", 
                  "apoyabrazos_altura": "ligero", "apoyabrazos_ancho": "parcial"},
        "monitor": {"altura": 2, "distancia": 60, "inclinacion": "perpendicular", "reflejos": False},
        "teclado": {"altura": "ligero", "distancia": 95, "inclinacion": "neutro", "reposamunecas": "basico"},
        "mouse": {"altura": "misma", "distancia": 5, "posicion": "frontal"},
        "uso_continuo": uso_continuo
    }
    
    datos_operario_ia = {
        'nombre': operario_nombre,
        'edad': operario_edad,
        'antiguedad': operario_antiguedad,
        'patologias': operario_patologias if operario_patologias else 'Ninguna'
    }
    
    resultado = evaluar_rosa(datos_rosa)
    
    dictamen_ia = None
    try:
        dictamen_ia = generar_dictamen_gemini_unificado('ROSA', resultado, datos_operario_ia, {'uso_continuo': uso_continuo})
        resultado['dictamen_ia'] = dictamen_ia
        print(f"   🤖 Dictamen IA para ROSA generado correctamente")
    except Exception as e:
        print(f"   ⚠️ Error generando dictamen IA para ROSA: {e}")
    
    if resultado.get('dictamen_ia') == 'No se pudo generar dictamen. Consulte a un especialista en ergonomía.' or not resultado.get('dictamen_ia'):
        resultado['dictamen_ia'] = generar_dictamen_profesional('ROSA', resultado, datos_operario_ia)
        print(f"   📋 Dictamen profesional para ROSA generado (modo local)")
    
    return render_template('resultado_rosa.html', 
                          resultado=resultado,
                          empresa=empresa,
                          puesto=puesto,
                          evaluador=evaluador,
                          operario_nombre=operario_nombre,
                          operario_edad=operario_edad,
                          operario_antiguedad=operario_antiguedad,
                          operario_patologias=operario_patologias,
                          usuario=usuario)


@app.route('/video')
def video_form():
    usuario = get_usuario_actual()
    return render_template('video_form.html', usuario=usuario)


@app.route('/procesar', methods=['POST'])
def procesar_archivo():
    print("\n" + "=" * 50)
    print("📥 NUEVA SOLICITUD DE ANÁLISIS")
    print("=" * 50)
    
    metodo = request.form.get('metodo')
    empresa = request.form.get('empresa')
    puesto = request.form.get('puesto')
    evaluador = request.form.get('evaluador')
    operario_nombre = request.form.get('operario_nombre')
    operario_edad = request.form.get('operario_edad')
    operario_antiguedad = request.form.get('operario_antiguedad')
    operario_patologias = request.form.get('operario_patologias', '')
    peso_carga = request.form.get('peso_carga', 0)
    
    try:
        peso_carga = float(peso_carga)
    except:
        peso_carga = 0
    
    print(f"📋 Datos: Empresa={empresa}, Puesto={puesto}, Método={metodo}, Peso carga={peso_carga} kg")
    
    if 'archivo' not in request.files:
        return "No se seleccionó ningún archivo", 400
    
    archivo = request.files['archivo']
    if archivo.filename == '':
        return "No se seleccionó ningún archivo", 400
    
    if not allowed_file(archivo.filename):
        return "Formato no permitido", 400
    
    filename = secure_filename(f"{uuid.uuid4()}_{archivo.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    archivo.save(filepath)
    print(f"💾 Archivo guardado: {filepath}")
    
    ext = filename.rsplit('.', 1)[1].lower()
    es_video = ext in ['mp4', 'avi', 'mov']
    
    datos_operario_ia = {
        'nombre': operario_nombre,
        'edad': operario_edad,
        'antiguedad': operario_antiguedad,
        'patologias': operario_patologias if operario_patologias else 'Ninguna',
        'peso_carga': peso_carga
    }
    
    # PRIMERO: Procesar el archivo para obtener el resultado
    if metodo == 'owas':
        resultado = procesar_owas(filepath, es_video, datos_operario_ia)
    elif metodo == 'rula':
        resultado = procesar_rula(filepath, es_video, datos_operario_ia)
    elif metodo == 'reba':
        resultado = procesar_reba(filepath, es_video, datos_operario_ia)
    else:
        return "Método no válido", 400
    
    # Asegurar que evolucion_temporal siempre exista
    if 'evolucion_temporal' not in resultado:
        resultado['evolucion_temporal'] = []
        print("⚠️ Se agregó evolucion_temporal vacío al resultado")
    
    # SEGUNDO: Agregar los datos básicos al resultado
    resultado['empresa'] = empresa
    resultado['puesto'] = puesto
    resultado['evaluador'] = evaluador
    resultado['operario_nombre'] = operario_nombre
    resultado['operario_edad'] = operario_edad
    resultado['operario_antiguedad'] = operario_antiguedad
    resultado['operario_patologias'] = operario_patologias if operario_patologias else "Ninguna"
    resultado['metodo'] = metodo.upper()
    
    # TERCERO: Agregar datos de normativa si corresponde
    cumple_normativa = request.form.get('cumple_normativa') == 'true'
    resultado['cumple_normativa'] = cumple_normativa
    
    if cumple_normativa:
        peso_carga_srt = request.form.get('peso_carga_srt', peso_carga)
        try:
            peso_carga_srt = float(peso_carga_srt)
        except:
            peso_carga_srt = peso_carga
        
        resultado['cantidad_trabajadores'] = request.form.get('cantidad_trabajadores', '1')
        resultado['horas_exposicion'] = request.form.get('horas_exposicion', '8')
        resultado['dias_semana'] = request.form.get('dias_semana', '5')
        resultado['peso_carga'] = peso_carga_srt
        resultado['frecuencia_levantamiento'] = request.form.get('frecuencia_levantamiento', '20')
        resultado['distancia_vertical'] = request.form.get('distancia_vertical', '50')
        resultado['tipo_bipedestacion'] = request.form.get('tipo_bipedestacion', 'Fija')
        resultado['confort_termico'] = request.form.get('confort_termico', 'Adecuado')
        resultado['estres_contacto'] = request.form.get('estres_contacto', 'No')
        resultado['descripcion_tarea'] = request.form.get('descripcion_tarea', 'Trabajo en posición bípeda/sedente con manipulación de cargas')
        resultado['observaciones_srt'] = request.form.get('observaciones_srt', '')
    else:
        resultado['peso_carga'] = peso_carga
    
    print(f"📦 Resultado a guardar (normativa: {cumple_normativa})")
    print(f"   Dictamen IA incluido: {'Sí' if resultado.get('dictamen_ia') else 'No'}")
    
    session['resultado'] = resultado
    
    # ============ GUARDAR EN HISTORIAL USANDO SQLITE ============
    token = session.get('user_token')
    if token:
        try:
            guardar_analisis(token, resultado)
            print(f"📊 Análisis guardado en base de datos")
        except Exception as e:
            print(f"❌ Error guardando análisis: {e}")
    
    print("=" * 50)
    print("✅ ANÁLISIS COMPLETADO - Redirigiendo al dashboard")
    print("=" * 50 + "\n")
    
    return redirect(url_for('dashboard'))


@app.route('/resultado_video')
def resultado_video():
    usuario = get_usuario_actual()
    resultado = session.get('resultado', {})
    print(f"📦 Recuperando de sesión: {resultado}")
    if not resultado:
        print("⚠️ No hay resultado en sesión, redirigiendo a video_form")
        return redirect(url_for('video_form'))
    return render_template('resultado_video.html', resultado=resultado, usuario=usuario)


# ==================== RUTA PARA EXPORTAR PDF ====================

@app.route('/exportar_pdf')
def exportar_pdf():
    """Exporta el resultado del análisis a PDF (soporta ID de historial)"""
    
    # Verificar si viene un ID de análisis desde el historial
    analisis_id = request.args.get('id', type=int)
    token = session.get('user_token')
    
    # Si hay ID y token, buscar en el historial usando SQLite
    if analisis_id is not None and token:
        analisis = obtener_analisis_por_id(analisis_id, token)
        if analisis:
            resultado = analisis.get('resultado', {})
        else:
            resultado = None
        
        if not resultado:
            return "Análisis no encontrado", 404
    else:
        # Si no, usar el último análisis de la sesión
        resultado = session.get('resultado', {})
        if not resultado:
            return redirect(url_for('video_form'))
    
    try:
        # Extraer datos
        metodo = resultado.get('metodo', 'OWAS')
        empresa = resultado.get('empresa', 'No especificada')
        puesto = resultado.get('puesto', 'No especificado')
        evaluador = resultado.get('evaluador', 'No especificado')
        op_nombre = resultado.get('operario_nombre', 'No especificado')
        op_edad = resultado.get('operario_edad', 'N/A')
        op_antiguedad = resultado.get('operario_antiguedad', 'N/A')
        op_patologias = resultado.get('operario_patologias', 'Ninguna')
        
        print(f"📄 Exportando PDF - Método: {metodo}, Empresa: {empresa}, ID: {analisis_id}")
        
        # Crear carpeta reports si no existe
        reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Preparar datos para el reporte según el método
        if metodo == 'ROSA':
            # Datos ROSA
            datos_rosa_ejemplo = {
                "silla": {"altura": 2, "apoyo_lumbar": "presente", "profundidad_asiento": "parcial", 
                          "apoyabrazos_altura": "ligero", "apoyabrazos_ancho": "parcial"},
                "monitor": {"altura": 2, "distancia": 60, "inclinacion": "perpendicular", "reflejos": False},
                "teclado": {"altura": "ligero", "distancia": 95, "inclinacion": "neutro", "reposamunecas": "basico"},
                "mouse": {"altura": "misma", "distancia": 5, "posicion": "frontal"},
                "uso_continuo": False
            }
            
            generar_reporte_rosa(
                resultado_rosa=resultado,
                empresa_input=empresa,
                puesto_input=puesto,
                evaluador_input=evaluador,
                op_nombre=op_nombre,
                op_edad=op_edad,
                op_antiguedad=op_antiguedad,
                op_patologias=op_patologias,
                logo_path=None,
                datos_rosa=datos_rosa_ejemplo
            )
        elif metodo == 'REBA':
            # Para REBA
            resultados_lista = [{
                'puntuacion_final': resultado.get('puntuacion', 1),
                'puntuacion_A': 0,
                'puntuacion_B': 0,
                'nivel_riesgo': resultado.get('nivel_riesgo', 'Desconocido'),
                'detalles': {}
            }]
            
            generar_reporte_reba(
                resultados_reba=resultados_lista,
                empresa_input=empresa,
                puesto_input=puesto,
                evaluador_input=evaluador,
                op_nombre=op_nombre,
                op_edad=op_edad,
                op_antiguedad=op_antiguedad,
                op_patologias=op_patologias,
                logo_path=None,
                imagenes_riesgo=[],
                muestras_posturales=[],
                carga=0,
                acople=0
            )
        else:
            # Para OWAS y RULA (uso del generador genérico)
            generar_reporte_generico(
                resultado=resultado,
                empresa_input=empresa,
                puesto_input=puesto,
                evaluador_input=evaluador,
                op_nombre=op_nombre,
                op_edad=op_edad,
                op_antiguedad=op_antiguedad,
                op_patologias=op_patologias,
                logo_path=None,
                metodo=metodo
            )
        
        # Buscar el PDF generado
        import glob
        import time
        
        archivos_pdf = glob.glob(f"reports/YOLO_*.pdf")
        
        if archivos_pdf:
            pdf_path = max(archivos_pdf, key=os.path.getctime)
            return send_file(pdf_path, as_attachment=True, download_name=f"informe_{metodo}_{empresa}.pdf")
        else:
            return "No se pudo generar el PDF", 500
            
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        return f"Error al generar el PDF: {str(e)}", 500


if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 5000))
    print("=" * 50)
    print("🚀 ERGOEDGE OS - Servidor Web (Flask)")
    print("=" * 50)
    print(f"🌐 Abrir en navegador: http://0.0.0.0:{port}")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=port)
