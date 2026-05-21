from Methods.fusion_detector import FusionPoseDetector
import cv2

print('=' * 60)
print('PRUEBA DE DETECTOR FUSIONADO CON OWAS')
print('=' * 60)

detector = FusionPoseDetector()
cap = cv2.VideoCapture('test.mp4')

frame_count = 0
print('\n📊 Procesando frames...\n')

while cap.isOpened() and frame_count < 50:
    ret, frame = cap.read()
    if not ret:
        break
    
    landmarks = detector.get_landmarks_dict(frame)
    if landmarks:
        owas_data = detector.calculate_owas_data(landmarks)
        print(f'Frame {frame_count:3d}: '
              f'Espalda={owas_data["espalda_angulo"]:5.1f} | '
              f'Rotacion={owas_data["espalda_rotacion"]:5.1f} | '
              f'BrazoI={owas_data["brazo_izq"]:5.1f} | '
              f'BrazoD={owas_data["brazo_der"]:5.1f} | '
              f'Rodilla={owas_data["angulo_rodilla"]:5.1f} | '
              f'PiernasCod={owas_data["piernas_codigo"]}')
    else:
        print(f'Frame {frame_count:3d}: No se detecto persona')
    
    frame_count += 1

cap.release()
detector.release()

print('\n' + '=' * 60)
print('PRUEBA COMPLETADA')
print('=' * 60)