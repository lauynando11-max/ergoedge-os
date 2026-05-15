import numpy as np

class SimpleDepthEstimator:
    def __init__(self):
        self.depth_rules = {
            'head': 0.15, 'shoulders': 0.25, 'elbows': 0.30,
            'wrists': 0.35, 'hips': 0.05, 'knees': 0.10, 'ankles': 0.00
        }
        self.idx_to_category = {
            0:'head',1:'head',2:'head',3:'head',4:'head',
            5:'shoulders',6:'shoulders',7:'elbows',8:'elbows',
            9:'wrists',10:'wrists',11:'hips',12:'hips',
            13:'knees',14:'knees',15:'ankles',16:'ankles'
        }
    
    def estimate(self, kp, w=640, h=480):
        result = np.zeros((len(kp), 3))
        for i, p in enumerate(kp):
            conf = p[2] if len(p) > 2 else 1.0
            if conf < 0.4:
                result[i] = [0,0,0.1]
                continue
            x = (p[0]/w)*2-1
            y = (p[1]/h)*2-1
            cat = self.idx_to_category.get(i, 'hips')
            z = self.depth_rules.get(cat, 0.1)
            result[i] = [x, y, z]
        return result

def calcular_angulo_3d(p1, p2, p3):
    a, b, c = [np.array(x) for x in [p1, p2, p3]]
    ba, bc = a-b, c-b
    n1, n2 = np.linalg.norm(ba), np.linalg.norm(bc)
    if n1 < 0.001 or n2 < 0.001:
        return 0.0
    cos = np.dot(ba, bc) / (n1 * n2)
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))

def calcular_abduccion_simplificada(kp3d):
    izq, der, codo = kp3d[5], kp3d[6], kp3d[7]
    lateral = der - izq
    brazo = codo - izq
    if np.linalg.norm(lateral) > 0 and np.linalg.norm(brazo) > 0:
        lat_n = lateral / np.linalg.norm(lateral)
        brazo_n = brazo / np.linalg.norm(brazo)
        ang = np.degrees(np.arccos(np.clip(abs(np.dot(brazo_n, lat_n)), -1, 1)))
        return ang if ang <= 90 else 180 - ang
    return 0

def detectar_torsion_tronco_3d(kp3d, umbral=20):
    """
    Detecta torsión de tronco con umbral ajustable (grados)
    MEJORADO: Retorna (bool, angulo_torsion)
    
    Args:
        kp3d: keypoints 3D
        umbral: ángulo mínimo para considerar torsión (grados)
    
    Returns:
        bool: True si hay torsión
        float: ángulo de torsión en grados
    """
    h_izq, h_der = kp3d[5], kp3d[6]
    c_izq, c_der = kp3d[11], kp3d[12]
    
    v_h = h_der - h_izq
    v_c = c_der - c_izq
    
    if np.linalg.norm(v_h) > 0 and np.linalg.norm(v_c) > 0:
        n_h = v_h / np.linalg.norm(v_h)
        n_c = v_c / np.linalg.norm(v_c)
        angulo = np.degrees(np.arccos(np.clip(np.dot(n_h, n_c), -1, 1)))
        return angulo > umbral, round(angulo, 1)
    
    return False, 0