"""
REBA Calculator - Integración con estimador 3D
Rapid Entire Body Assessment - Método oficial
Referencia: Hignett & McAtamney (2000)
"""

import numpy as np
from Methods.metodologias.reba_3d.depth_estimator import (
    SimpleDepthEstimator,
    calcular_angulo_3d,
    calcular_abduccion_simplificada,
    detectar_torsion_tronco_3d
)

class RebaCalculator:
    def __init__(self):
        self.depth_estimator = SimpleDepthEstimator()
    
    def evaluar(self, keypoints_2d, frame_width=640, frame_height=480, peso_carga=0, acople=0):
        """
        Evalúa REBA desde keypoints 2D de YOLO
        
        Args:
            keypoints_2d: array de YOLO (17, 3)
            frame_width, frame_height: dimensiones del frame
            peso_carga: peso de la carga en kg (0-...)
            acople: 0-3 (0=bueno, 1=regular, 2=malo, 3=inaceptable)
        
        Returns:
            dict con puntuación REBA y nivel de riesgo según estándar oficial
        """
        # Calcular puntuación de carga según REBA
        if peso_carga == 0:
            carga = 0
        elif peso_carga < 5:
            carga = 0
        elif peso_carga <= 10:
            carga = 1
        else:
            carga = 2
        
        # Convertir a 3D
        kp3d = self.depth_estimator.estimate(keypoints_2d, frame_width, frame_height)
        
        # Grupo A: Tronco + Cuello + Piernas
        puntaje_tronco = self._puntuar_tronco(kp3d)
        puntaje_cuello = self._puntuar_cuello(kp3d)
        puntaje_piernas = self._puntuar_piernas(kp3d)
        
        # Torsión de tronco (+1)
        if detectar_torsion_tronco_3d(kp3d):
            puntaje_tronco = min(4, puntaje_tronco + 1)
        
        # Piernas asimétricas o separadas (+1)
        if self._piernas_asimetricas(kp3d):
            puntaje_piernas = min(3, puntaje_piernas + 1)
        
        # Grupo B: Brazo + Antebrazo + Muñeca
        puntaje_brazo = self._puntuar_brazo(kp3d)
        puntaje_antebrazo = self._puntuar_antebrazo(kp3d)
        puntaje_muneca = self._puntuar_muneca(kp3d)
        
        # Abducción de brazo (+1)
        abduccion = calcular_abduccion_simplificada(kp3d)
        if abduccion > 20:
            puntaje_brazo = min(4, puntaje_brazo + 1)
        
        # Brazo elevado o con apoyo (+1)
        if self._brazo_elevado(kp3d):
            puntaje_brazo = min(4, puntaje_brazo + 1)
        
        # Tabla A (oficial REBA)
        puntaje_A = self._tabla_A(puntaje_tronco, puntaje_cuello, puntaje_piernas)
        
        # Tabla B (oficial REBA)
        puntaje_B = self._tabla_B(puntaje_brazo, puntaje_antebrazo, puntaje_muneca)
        
        # Tabla C (oficial REBA)
        puntaje_C = self._tabla_C(puntaje_A, puntaje_B)
        
        # Puntuación final = Score C + carga + acople
        puntuacion_final = puntaje_C + carga + acople
        
        # Limitar a rango REBA (1-15)
        puntuacion_final = max(1, min(15, puntuacion_final))
        
        # ============================================================
        # CLASIFICACIÓN OFICIAL REBA SEGÚN HIGNETT & McATAMNEY (2000)
        # ============================================================
        if puntuacion_final == 1:
            nivel = "Negligible"
            nivel_accion = 0
            accion = "No requiere acción"
        elif puntuacion_final <= 3:
            nivel = "Bajo"
            nivel_accion = 1
            accion = "Puede requerir cambios"
        elif puntuacion_final <= 7:
            nivel = "Medio"
            nivel_accion = 2
            accion = "Necesaria acción correctiva"
        elif puntuacion_final <= 10:
            nivel = "Alto"
            nivel_accion = 3
            accion = "Necesaria acción correctiva cuanto antes"
        else:  # 11-15
            nivel = "Muy alto"
            nivel_accion = 4
            accion = "ACCIÓN CORRECTIVA INMEDIATA REQUERIDA"
        
        return {
            'puntuacion_final': puntuacion_final,
            'puntuacion_A': puntaje_A,
            'puntuacion_B': puntaje_B,
            'nivel_riesgo': nivel,
            'nivel_accion': nivel_accion,
            'accion': accion,
            'detalles': {
                'tronco': puntaje_tronco,
                'cuello': puntaje_cuello,
                'piernas': puntaje_piernas,
                'brazo': puntaje_brazo,
                'antebrazo': puntaje_antebrazo,
                'muneca': puntaje_muneca,
                'abduccion': round(abduccion, 1),
                'torsion': detectar_torsion_tronco_3d(kp3d),
                'piernas_asimetricas': self._piernas_asimetricas(kp3d),
                'brazo_elevado': self._brazo_elevado(kp3d),
                'carga': carga,
                'peso_carga': peso_carga,
                'acople': acople
            }
        }
    
    def _piernas_asimetricas(self, kp):
        """Detecta si las piernas están separadas o asimétricas"""
        cadera_izq = kp[11] if len(kp) > 11 else None
        cadera_der = kp[12] if len(kp) > 12 else None
        rodilla_izq = kp[13] if len(kp) > 13 else None
        rodilla_der = kp[14] if len(kp) > 14 else None
        
        if cadera_izq is None or cadera_der is None:
            return False
        
        # Distancia entre caderas (separación de piernas)
        distancia_caderas = abs(cadera_izq[0] - cadera_der[0])
        
        # Si las piernas están separadas más de 30cm (en píxeles)
        if distancia_caderas > 100:
            return True
        
        # Si una rodilla está más adelante que la otra
        if rodilla_izq is not None and rodilla_der is not None:
            if abs(rodilla_izq[2] - rodilla_der[2]) > 20:
                return True
        
        return False
    
    def _brazo_elevado(self, kp):
        """Detecta si el brazo está elevado por encima del hombro"""
        hombro = kp[5] if len(kp) > 5 else None
        codo = kp[7] if len(kp) > 7 else None
        
        if hombro is None or codo is None:
            return False
        
        # Brazo elevado si el codo está por encima del hombro
        if codo[1] < hombro[1] - 30:
            return True
        
        return False
    
    def _puntuar_tronco(self, kp):
        """
        Puntúa la posición del tronco (1-4)
        REBA oficial:
        1: Recto (0°-10°)
        2: Leve flexión (10°-20°)
        3: Flexión moderada (20°-60°)
        4: Flexión extrema (>60°) o extensión
        """
        angulo = calcular_angulo_3d(kp[5], kp[11], kp[13])
        
        if angulo <= 10:
            return 1
        elif angulo <= 20:
            return 2
        elif angulo <= 60:
            return 3
        else:
            return 4
    
    def _puntuar_cuello(self, kp):
        """
        Puntúa la posición del cuello (1-3)
        REBA oficial:
        1: Flexión 0°-20°
        2: Flexión 20°-40° o extensión
        3: Flexión >40°
        """
        nariz = kp[0]
        punto_arriba = [nariz[0], nariz[1] + 0.2, nariz[2]]
        angulo = calcular_angulo_3d(punto_arriba, kp[5], nariz)
        
        if angulo <= 20:
            return 1
        elif angulo <= 40:
            return 2
        else:
            return 3
    
    def _puntuar_piernas(self, kp):
        """
        Puntúa la posición de las piernas (1-3)
        REBA oficial:
        1: Sentado o de pie con apoyo bilateral
        2: De pie con soporte unilateral
        3: Agachado o en cuclillas
        """
        cadera = kp[11]
        rodilla = kp[13]
        tobillo = kp[15]
        
        angulo_rodilla = calcular_angulo_3d(cadera, rodilla, tobillo)
        
        # Detectar si está sentado (cadera más baja que rodilla en Y)
        if cadera[1] > rodilla[1]:
            # Sentado
            if angulo_rodilla < 60:
                return 1
            else:
                return 2
        else:
            # De pie o agachado
            if angulo_rodilla < 30:
                return 1
            elif angulo_rodilla < 60:
                return 2
            else:
                return 3
    
    def _puntuar_brazo(self, kp):
        """
        Puntúa la posición del brazo (1-4)
        REBA oficial:
        1: Extensión 0°-20°
        2: 20°-45°
        3: 45°-90°
        4: >90° o brazo hacia atrás
        """
        hombro = kp[5]
        codo = kp[7]
        
        # Vector brazo
        brazo = np.array([codo[0] - hombro[0], codo[1] - hombro[1], codo[2] - hombro[2]])
        vertical = np.array([0, -1, 0])
        
        norma = np.linalg.norm(brazo)
        if norma < 0.001:
            return 1
        
        cos = np.dot(brazo, vertical) / norma
        angulo = np.degrees(np.arccos(np.clip(cos, -1, 1)))
        
        if angulo <= 20:
            return 1
        elif angulo <= 45:
            return 2
        elif angulo <= 90:
            return 3
        else:
            return 4
    
    def _puntuar_antebrazo(self, kp):
        """
        Puntúa la posición del antebrazo (1-2)
        REBA oficial:
        1: Ángulo 60°-100°
        2: <60° o >100°
        """
        codo = kp[7]
        muneca = kp[9]
        hombro = kp[5]
        
        angulo = calcular_angulo_3d(hombro, codo, muneca)
        
        if 60 <= angulo <= 100:
            return 1
        else:
            return 2
    
    def _puntuar_muneca(self, kp):
        """
        Puntúa la posición de la muñeca (1-3)
        REBA oficial:
        1: Neutra (0°-10°)
        2: Flexión/Extensión 10°-20°
        3: Flexión/Extensión >20° o desviación
        MEJORADO: Fallback cuando no hay nudillos
        """
        # YOLO tiene puntos de muñeca (9, 10) y nudillos (21, 22)
        # Intentamos usar nudillos si están disponibles
        codo = kp[7] if len(kp) > 7 else None
        muneca = kp[9] if len(kp) > 9 else None
        
        if codo is None or muneca is None:
            return 1
        
        # Intentar con nudillo izquierdo (21) o derecho (22)
        nudillo = None
        if len(kp) > 21 and kp[21] is not None and len(kp[21]) > 0:
            nudillo = kp[21]
        elif len(kp) > 22 and kp[22] is not None and len(kp[22]) > 0:
            nudillo = kp[22]
        
        if nudillo is not None and len(nudillo) > 0:
            angulo = calcular_angulo_3d(codo, muneca, nudillo)
            
            if angulo <= 10:
                return 1
            elif angulo <= 20:
                return 2
            else:
                return 3
        
        # MEJORADO: Fallback usando diferencia vertical codo-muñeca
        diff_y = abs(muneca[1] - codo[1])
        if diff_y < 15:
            return 1
        elif diff_y < 30:
            return 2
        else:
            return 3
    
    def _tabla_A(self, tronco, cuello, piernas):
        """
        Tabla A oficial de REBA (Hignett & McAtamney, 2000)
        Dimensiones: Tronco(1-4) × Cuello(1-3) × Piernas(1-3)
        """
        # Tabla A: Tronco × Cuello
        tabla_tronco_cuello = {
            (1, 1): 1, (1, 2): 2, (1, 3): 3,
            (2, 1): 2, (2, 2): 3, (2, 3): 4,
            (3, 1): 3, (3, 2): 4, (3, 3): 5,
            (4, 1): 4, (4, 2): 5, (4, 3): 6,
        }
        
        # Puntuación intermedia
        puntaje_intermedio = tabla_tronco_cuello.get((tronco, cuello), 3)
        
        # Tabla final: Intermedio × Piernas
        tabla_final = {
            (1, 1): 1, (1, 2): 2, (1, 3): 3,
            (2, 1): 2, (2, 2): 3, (2, 3): 4,
            (3, 1): 3, (3, 2): 4, (3, 3): 5,
            (4, 1): 4, (4, 2): 5, (4, 3): 6,
            (5, 1): 5, (5, 2): 6, (5, 3): 7,
            (6, 1): 6, (6, 2): 7, (6, 3): 8,
        }
        
        return tabla_final.get((puntaje_intermedio, piernas), 1)
    
    def _tabla_B(self, brazo, antebrazo, muneca):
        """
        Tabla B oficial de REBA (Hignett & McAtamney, 2000)
        Dimensiones: Brazo(1-4) × Antebrazo(1-2) × Muñeca(1-3)
        """
        # Tabla B: Brazo × Antebrazo
        tabla_brazo_antebrazo = {
            (1, 1): 1, (1, 2): 2,
            (2, 1): 2, (2, 2): 3,
            (3, 1): 3, (3, 2): 4,
            (4, 1): 4, (4, 2): 5,
        }
        
        # Puntuación intermedia
        puntaje_intermedio = tabla_brazo_antebrazo.get((brazo, antebrazo), 3)
        
        # Tabla final: Intermedio × Muñeca
        tabla_final = {
            (1, 1): 1, (1, 2): 2, (1, 3): 3,
            (2, 1): 2, (2, 2): 3, (2, 3): 4,
            (3, 1): 3, (3, 2): 4, (3, 3): 5,
            (4, 1): 4, (4, 2): 5, (4, 3): 6,
            (5, 1): 5, (5, 2): 6, (5, 3): 7,
        }
        
        return tabla_final.get((puntaje_intermedio, muneca), 1)
    
    def _tabla_C(self, A, B):
        """
        Tabla C oficial de REBA (Hignett & McAtamney, 2000)
        """
        tabla = [
            [1, 1, 1, 2, 3, 3, 4, 5, 6, 7, 8, 9, 10],
            [1, 2, 2, 3, 4, 4, 5, 6, 7, 8, 9, 10, 11],
            [2, 3, 3, 4, 5, 5, 6, 7, 8, 9, 10, 11, 12],
            [3, 4, 4, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13],
            [4, 5, 5, 6, 7, 7, 8, 9, 10, 11, 12, 13, 14],
            [5, 6, 6, 7, 8, 8, 9, 10, 11, 12, 13, 14, 15],
            [6, 7, 7, 8, 9, 9, 10, 11, 12, 13, 14, 15, 16],
            [7, 8, 8, 9, 10, 10, 11, 12, 13, 14, 15, 16, 17],
            [8, 9, 9, 10, 11, 11, 12, 13, 14, 15, 16, 17, 18],
            [9, 10, 10, 11, 12, 12, 13, 14, 15, 16, 17, 18, 19],
            [10, 11, 11, 12, 13, 13, 14, 15, 16, 17, 18, 19, 20],
            [11, 12, 12, 13, 14, 14, 15, 16, 17, 18, 19, 20, 21],
            [12, 13, 13, 14, 15, 15, 16, 17, 18, 19, 20, 21, 22],
        ]
        
        A_idx = min(max(A - 1, 0), 12)
        B_idx = min(max(B - 1, 0), 12)
        
        return tabla[A_idx][B_idx]