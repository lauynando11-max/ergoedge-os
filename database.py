"""
ERGOEDGE OS - Base de datos SQLite
Gestión de usuarios y análisis con persistencia
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

import os
DB_PATH = '/app/instance/ergoedge.db'


@contextmanager
def get_db():
    """Context manager para conexiones a DB"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Inicializa la base de datos con todas las tablas"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                fecha_registro TEXT NOT NULL
            )
        ''')
        
        # Tabla de análisis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analisis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_token TEXT NOT NULL,
                fecha TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                metodo TEXT NOT NULL,
                empresa TEXT NOT NULL,
                puesto TEXT NOT NULL,
                evaluador TEXT NOT NULL,
                operario_nombre TEXT NOT NULL,
                operario_edad TEXT NOT NULL,
                puntuacion INTEGER,
                nivel_riesgo TEXT,
                imagenes_riesgo TEXT,
                resultado_json TEXT NOT NULL,
                FOREIGN KEY (usuario_token) REFERENCES usuarios(token)
            )
        ''')
        
        # Índices para búsquedas rápidas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuario_token ON usuarios(token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analisis_usuario ON analisis(usuario_token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analisis_timestamp ON analisis(timestamp)')
        
        print("✅ Base de datos inicializada correctamente")


def crear_usuario(token, nombre, email, password_hash):
    """Crea un nuevo usuario"""
    with get_db() as conn:
        cursor = conn.cursor()
        fecha = datetime.now().strftime("%d/%m/%Y")
        cursor.execute('''
            INSERT INTO usuarios (token, nombre, email, password_hash, fecha_registro)
            VALUES (?, ?, ?, ?, ?)
        ''', (token, nombre, email, password_hash, fecha))
        return cursor.lastrowid


def obtener_usuario_por_token(token):
    """Obtiene un usuario por su token"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE token = ?', (token,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def obtener_usuario_por_email(email):
    """Obtiene un usuario por su email"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def obtener_todos_usuarios():
    """Obtiene todos los usuarios (para migración)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios')
        return [dict(row) for row in cursor.fetchall()]


def guardar_analisis(usuario_token, resultado):
    """
    Guarda un análisis en la base de datos
    
    Args:
        usuario_token: token del usuario
        resultado: dict con todos los datos del análisis
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Extraer datos del resultado
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        timestamp = int(datetime.now().timestamp())
        metodo = resultado.get('metodo', 'OWAS')
        empresa = resultado.get('empresa', '')
        puesto = resultado.get('puesto', '')
        evaluador = resultado.get('evaluador', '')
        operario_nombre = resultado.get('operario_nombre', '')
        operario_edad = resultado.get('operario_edad', '')
        puntuacion = resultado.get('puntuacion')
        nivel_riesgo = resultado.get('nivel_riesgo', '')
        imagenes_riesgo = json.dumps(resultado.get('imagenes_riesgo', []))
        resultado_json = json.dumps(resultado, ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO analisis (
                usuario_token, fecha, timestamp, metodo, empresa, puesto,
                evaluador, operario_nombre, operario_edad, puntuacion,
                nivel_riesgo, imagenes_riesgo, resultado_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (usuario_token, fecha, timestamp, metodo, empresa, puesto,
              evaluador, operario_nombre, operario_edad, puntuacion,
              nivel_riesgo, imagenes_riesgo, resultado_json))
        
        return cursor.lastrowid


def obtener_historial_usuario(usuario_token, limite=50):
    """Obtiene el historial de análisis de un usuario (ordenado por fecha desc)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, fecha, metodo, empresa, puesto, operario_nombre,
                   puntuacion, nivel_riesgo, timestamp, imagenes_riesgo
            FROM analisis
            WHERE usuario_token = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (usuario_token, limite))
        
        historial = []
        for row in cursor.fetchall():
            item = dict(row)
            # Parsear imágenes
            if item.get('imagenes_riesgo'):
                try:
                    item['imagenes_riesgo'] = json.loads(item['imagenes_riesgo'])
                except:
                    item['imagenes_riesgo'] = []
            else:
                item['imagenes_riesgo'] = []
            historial.append(item)
        
        return historial


def obtener_analisis_por_id(analisis_id, usuario_token):
    """Obtiene un análisis completo por ID (verificando que pertenezca al usuario)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM analisis
            WHERE id = ? AND usuario_token = ?
        ''', (analisis_id, usuario_token))
        
        row = cursor.fetchone()
        if row:
            item = dict(row)
            # Parsear resultado_json
            if item.get('resultado_json'):
                try:
                    item['resultado'] = json.loads(item['resultado_json'])
                except:
                    item['resultado'] = {}
            # Parsear imágenes
            if item.get('imagenes_riesgo'):
                try:
                    item['imagenes_riesgo'] = json.loads(item['imagenes_riesgo'])
                except:
                    item['imagenes_riesgo'] = []
            return item
        return None


def eliminar_analisis(analisis_id, usuario_token):
    """Elimina un análisis (solo si pertenece al usuario)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM analisis
            WHERE id = ? AND usuario_token = ?
        ''', (analisis_id, usuario_token))
        return cursor.rowcount > 0


def migrar_desde_memoria(usuarios_memoria, analisis_memoria):
    """
    Migra datos desde memoria a SQLite (útil para primera ejecución)
    """
    print("🔄 Migrando datos desde memoria a SQLite...")
    
    usuarios_agregados = 0
    analisis_agregados = 0
    
    for token, user_data in usuarios_memoria.items():
        # Verificar si ya existe
        existente = obtener_usuario_por_token(token)
        if not existente:
            crear_usuario(
                token,
                user_data['nombre'],
                user_data['email'],
                user_data['password']
            )
            usuarios_agregados += 1
    
    for token, analisis_list in analisis_memoria.items():
        for analisis in analisis_list:
            # Verificar si el resultado ya existe (por timestamp)
            # Guardar el análisis
            resultado = analisis.get('resultado', {})
            guardar_analisis(token, resultado)
            analisis_agregados += 1
    
    print(f"✅ Migración completada: {usuarios_agregados} usuarios, {analisis_agregados} análisis")
