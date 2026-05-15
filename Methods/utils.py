import numpy as np

def calcular_angulo(p1, p2, p3):
    """Calcula el ángulo entre tres puntos (x, y)"""
    a = np.array(p1)
    b = np.array(p2)  # Vértice
    c = np.array(p3)
    
    radianes = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angulo = np.abs(radianes * 180.0 / np.pi)
    
    if angulo > 180.0:
        angulo = 360 - angulo
        
    return angulo


def calcular_angulo_2d(p1, p2, p3):
    """Calcula ángulo entre tres puntos 2D con validación"""
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