import cv2
import mediapipe as mp
import numpy as np

print("="*60)
print("     DIAGNÓSTICO DE ÁNGULOS - ERGOEDGE OS")
print("="*60)
print("Presiona 'q' para salir")

# Inicializar MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Abrir video
cap = cv2.VideoCapture("test.mp4")

if not cap.isOpened():
    print("❌ ERROR: No se pudo abrir test.mp4")
    print("   Verifica que el archivo existe en:", os.getcwd())
    exit()

frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("📹 Fin del video")
        break
    
    frame_count += 1
    
    # Procesar cada 3 frames
    if frame_count % 3 == 0:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        
        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            
            # Obtener puntos clave
            hombro = lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            cadera = lm[mp_pose.PoseLandmark.LEFT_HIP.value]
            rodilla = lm[mp_pose.PoseLandmark.LEFT_KNEE.value]
            codo = lm[mp_pose.PoseLandmark.LEFT_ELBOW.value]
            muñeca = lm[mp_pose.PoseLandmark.LEFT_WRIST.value]
            
            # ========== CÁLCULO DE ÁNGULO DE ESPALDA ==========
            # Vector cadera -> hombro
            v1 = np.array([hombro.x - cadera.x, hombro.y - cadera.y])
            # Vector cadera -> rodilla
            v2 = np.array([rodilla.x - cadera.x, rodilla.y - cadera.y])
            
            cos_ang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_ang = np.clip(cos_ang, -1, 1)
            ang_espalda = np.degrees(np.arccos(cos_ang))
            
            # ========== CÁLCULO DE ÁNGULO DE BRAZO ==========
            # Vector codo -> hombro
            v1_b = np.array([hombro.x - codo.x, hombro.y - codo.y])
            # Vector codo -> muñeca
            v2_b = np.array([muñeca.x - codo.x, muñeca.y - codo.y])
            
            cos_ang_b = np.dot(v1_b, v2_b) / (np.linalg.norm(v1_b) * np.linalg.norm(v2_b))
            cos_ang_b = np.clip(cos_ang_b, -1, 1)
            ang_brazo = np.degrees(np.arccos(cos_ang_b))
            
            # ========== INTERPRETACIÓN ==========
            # Espalda: normal < 20°, riesgo > 30°
            if ang_espalda < 20:
                estado_espalda = "NORMAL"
                color_esp = (0, 255, 0)
            elif ang_espalda < 40:
                estado_espalda = "MODERADO"
                color_esp = (0, 165, 255)
            else:
                estado_espalda = "RIESGO"
                color_esp = (0, 0, 255)
            
            # Brazo: normal < 30°, riesgo > 60°
            if ang_brazo < 30:
                estado_brazo = "NORMAL"
                color_bra = (0, 255, 0)
            elif ang_brazo < 60:
                estado_brazo = "MODERADO"
                color_bra = (0, 165, 255)
            else:
                estado_brazo = "RIESGO"
                color_bra = (0, 0, 255)
            
            # Mostrar en consola cada 50 frames
            if frame_count % 50 == 0:
                print(f"Frame {frame_count}: Espalda={ang_espalda:.1f}° ({estado_espalda}) | Brazo={ang_brazo:.1f}° ({estado_brazo})")
            
            # ========== DIBUJAR EN PANTALLA ==========
            # Convertir coordenadas a píxeles
            h_px = (int(hombro.x * frame.shape[1]), int(hombro.y * frame.shape[0]))
            c_px = (int(cadera.x * frame.shape[1]), int(cadera.y * frame.shape[0]))
            r_px = (int(rodilla.x * frame.shape[1]), int(rodilla.y * frame.shape[0]))
            cod_px = (int(codo.x * frame.shape[1]), int(codo.y * frame.shape[0]))
            m_px = (int(muñeca.x * frame.shape[1]), int(muñeca.y * frame.shape[0]))
            
            # Dibujar líneas del esqueleto
            cv2.line(frame, h_px, c_px, (0, 255, 0), 2)
            cv2.line(frame, c_px, r_px, (0, 255, 0), 2)
            cv2.line(frame, h_px, cod_px, (255, 255, 0), 2)
            cv2.line(frame, cod_px, m_px, (255, 255, 0), 2)
            
            # Dibujar círculos en las articulaciones
            cv2.circle(frame, h_px, 5, (0, 0, 255), -1)
            cv2.circle(frame, c_px, 5, (0, 0, 255), -1)
            cv2.circle(frame, r_px, 5, (0, 0, 255), -1)
            cv2.circle(frame, cod_px, 5, (0, 0, 255), -1)
            cv2.circle(frame, m_px, 5, (0, 0, 255), -1)
            
            # Mostrar ángulos en pantalla
            cv2.putText(frame, f"ESPALDA: {ang_espalda:.0f}°", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_esp, 2)
            cv2.putText(frame, f"BRAZO: {ang_brazo:.0f}°", (10, 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_bra, 2)
            
            # Mostrar interpretación
            cv2.putText(frame, f"Estado: {estado_espalda}", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_esp, 1)
            
    # Mostrar frame
    cv2.imshow("DIAGNOSTICO - Angulos Reales", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*60)
print("✅ Diagnóstico completado")
print("="*60)