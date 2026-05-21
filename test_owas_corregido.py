from Methods.fusion_detector import FusionPoseDetector
from Methods.metodologias.owas import analizar_owas_completo
import cv2

d = FusionPoseDetector()
cap = cv2.VideoCapture('video 2.mp4')

print('=' * 70)
print('PRUEBA OWAS CORREGIDO - video 2.mp4')
print('=' * 70)
print('Frame | Espalda | Codigo OWAS | Nivel')
print('-' * 50)

for i in range(30):
    ret, frame = cap.read()
    if not ret:
        break
    lm = d.get_landmarks_dict(frame)
    if lm:
        data = d.calculate_owas_data(lm)
        
        owas_input = {
            'espalda_angulo': data['espalda_angulo'],
            'espalda_rotacion': data['espalda_rotacion'],
            'brazo_izq': data['brazo_izq'],
            'brazo_der': data['brazo_der'],
            'piernas_codigo': data['piernas_codigo'],
            'carga_kg': 0,
            'movimiento_forzado': False
        }
        
        resultado = analizar_owas_completo(owas_input)
        print(f'{i:5d} | {data["espalda_angulo"]:7.1f} | {resultado["codigo"]:>10} | {resultado["categoria_riesgo"]}/4')
    else:
        print(f'{i:5d} | Sin deteccion')

cap.release()
d.release()
print('=' * 70)
