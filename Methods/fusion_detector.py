"""
Methods/fusion_detector.py
Detector híbrido YOLO + MediaPipe para análisis ergonómico
"""

import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from typing import Dict, Optional
import math

class FusionPoseDetector:
    def __init__(self,
                 yolo_model_path: str = "yolo11n-pose.pt",
                 min_confidence: float = 0.5):
        
        # YOLO para detección rápida
        print("📥 Cargando YOLO...")
        self.yolo = YOLO(yolo_model_path)
        self.yolo.overrides['conf'] = min_confidence
        
        # MediaPipe con API tasks
        print("📥 Cargando MediaPipe Pose...")
        model_path = 'pose_landmarker_heavy.task'
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=min_confidence,
            min_pose_presence_confidence=min_confidence,
            min_tracking_confidence=min_confidence
        )
        self.pose_landmarker = vision.PoseLandmarker.create_from_options(options)
        print("✅ Detector Fusionado listo")
    
    def get_landmarks_dict(self, frame: np.ndarray) -> Optional[Dict]:
        """Obtiene landmarks usando MediaPipe"""
        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = self.pose_landmarker.detect(mp_image)
        
        if not detection_result.pose_landmarks:
            return None
        
        nombres = [
            'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
            'right_eye_inner', 'right_eye', 'right_eye_outer',
            'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
            'left_index', 'right_index', 'left_thumb', 'right_thumb',
            'left_hip', 'right_hip', 'left_knee', 'right_knee',
            'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
            'left_foot_index', 'right_foot_index'
        ]
        
        landmarks = detection_result.pose_landmarks[0]
        landmarks_dict = {}
        
        for i, lm in enumerate(landmarks):
            if i < len(nombres):
                x = lm.x * w
                y = lm.y * h
                z = lm.z
                landmarks_dict[nombres[i]] = (x, y, z)
        
        return landmarks_dict
    
    def get_landmarks_array(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Retorna landmarks como array numpy de 33x3"""
        landmarks_dict = self.get_landmarks_dict(frame)
        if landmarks_dict:
            orden = [
                'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
                'right_eye_inner', 'right_eye', 'right_eye_outer',
                'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
                'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
                'left_index', 'right_index', 'left_thumb', 'right_thumb',
                'left_hip', 'right_hip', 'left_knee', 'right_knee',
                'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
                'left_foot_index', 'right_foot_index'
            ]
            arr = []
            for nombre in orden:
                if nombre in landmarks_dict:
                    arr.append(landmarks_dict[nombre])
                else:
                    arr.append((0, 0, 0))
            return np.array(arr)
        return None
    
    def calculate_owas_data(self, landmarks_dict: Dict) -> Dict:
        """
        Calcula los datos necesarios para OWAS a partir de los landmarks de MediaPipe
        """
        def get_point(name):
            p = landmarks_dict.get(name)
            return np.array([p[0], p[1], p[2]]) if p else None
        
        def angle_3d(a, b, c):
            if a is None or b is None or c is None:
                return 0
            a, b, c = np.array(a), np.array(b), np.array(c)
            ba = a - b
            bc = c - b
            cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
            return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
        
        # Puntos clave
        hombro_izq = get_point('left_shoulder')
        hombro_der = get_point('right_shoulder')
        cadera_izq = get_point('left_hip')
        cadera_der = get_point('right_hip')
        rodilla_izq = get_point('left_knee')
        rodilla_der = get_point('right_knee')
        tobillo_izq = get_point('left_ankle')
        tobillo_der = get_point('right_ankle')
        muneca_izq = get_point('left_wrist')
        muneca_der = get_point('right_wrist')
        
        # 1. Ángulo de espalda (flexión)
        espalda_angulo = 0
        if hombro_izq is not None and cadera_izq is not None and rodilla_izq is not None:
            espalda_angulo = angle_3d(hombro_izq, cadera_izq, rodilla_izq)
            if espalda_angulo > 90:
                espalda_angulo = 180 - espalda_angulo
        
        # 2. Rotación de torso
        espalda_rotacion = 0
        if hombro_izq is not None and hombro_der is not None and cadera_izq is not None and cadera_der is not None:
            vector_hombros = hombro_der[:2] - hombro_izq[:2]
            vector_caderas = cadera_der[:2] - cadera_izq[:2]
            norm_h = np.linalg.norm(vector_hombros)
            norm_c = np.linalg.norm(vector_caderas)
            if norm_h > 0 and norm_c > 0:
                cos_rot = np.dot(vector_hombros, vector_caderas) / (norm_h * norm_c)
                espalda_rotacion = np.degrees(np.arccos(np.clip(cos_rot, -1.0, 1.0)))
        
        # 3. Ángulo de brazos (elevación)
        brazo_izq = 0
        if hombro_izq is not None and muneca_izq is not None:
            vertical = np.array([0, -1, 0])
            brazo = muneca_izq - hombro_izq
            if np.linalg.norm(brazo) > 0:
                brazo_unit = brazo / np.linalg.norm(brazo)
                cos_ang = np.dot(brazo_unit, vertical)
                brazo_izq = np.degrees(np.arccos(np.clip(cos_ang, -1.0, 1.0)))
        
        brazo_der = 0
        if hombro_der is not None and muneca_der is not None:
            vertical = np.array([0, -1, 0])
            brazo = muneca_der - hombro_der
            if np.linalg.norm(brazo) > 0:
                brazo_unit = brazo / np.linalg.norm(brazo)
                cos_ang = np.dot(brazo_unit, vertical)
                brazo_der = np.degrees(np.arccos(np.clip(cos_ang, -1.0, 1.0)))
        
        # 4. Código de piernas OWAS
        piernas_codigo = 2
        if cadera_izq is not None and rodilla_izq is not None and tobillo_izq is not None:
            ang_rodilla = angle_3d(cadera_izq, rodilla_izq, tobillo_izq)
            
            if cadera_izq[1] > rodilla_izq[1] + 50:
                piernas_codigo = 1
            elif ang_rodilla < 100:
                piernas_codigo = 5
            elif ang_rodilla < 150:
                piernas_codigo = 4
            else:
                piernas_codigo = 2
        
        # 5. Ángulo de rodilla
        angulo_rodilla = 0
        if cadera_izq is not None and rodilla_izq is not None and tobillo_izq is not None:
            angulo_rodilla = angle_3d(cadera_izq, rodilla_izq, tobillo_izq)
        
        return {
            'espalda_angulo': espalda_angulo,
            'espalda_rotacion': espalda_rotacion,
            'brazo_izq': brazo_izq,
            'brazo_der': brazo_der,
            'piernas_codigo': piernas_codigo,
            'angulo_rodilla': angulo_rodilla
        }
    
    def release(self):
        """Libera recursos"""
        self.pose_landmarker.close()