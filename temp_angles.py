from Methods.fusion_detector import FusionPoseDetector
import cv2

d = FusionPoseDetector()
cap = cv2.VideoCapture('video 2.mp4')

for i in range(30):
    ret, frame = cap.read()
    if not ret:
        break
    lm = d.get_landmarks_dict(frame)
    if lm:
        data = d.calculate_owas_data(lm)
        print(f'Frame {i}: Espalda={data["espalda_angulo"]:.1f} | Rodilla={data["angulo_rodilla"]:.1f} | PiernasCod={data["piernas_codigo"]}')
    else:
        print(f'Frame {i}: Sin deteccion')

cap.release()
d.release()
