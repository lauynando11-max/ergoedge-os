import cv2
import mediapipe as mp
from ultralytics import YOLO

def cargar_modelos_ia():
    # 1. Cargar YOLO para detección de objetos (Contexto)
    # Se descargará automáticamente la primera vez (aprox 15mb)
    modelo_yolo = YOLO('yolov8n.pt') 
    
    # 2. Cargar MediaPipe para Pose (Esqueleto)
    mp_pose = mp.solutions.pose
    pose_detector = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
    
    # 3. Utilidades de dibujo
    mp_drawing = mp.solutions.drawing_utils
    
    return modelo_yolo, pose_detector, mp_drawing, mp_pose