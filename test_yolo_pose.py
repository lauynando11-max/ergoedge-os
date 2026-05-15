import cv2
from ultralytics import YOLO

# Cargar el modelo (se descargará automáticamente la primera vez)
print("📥 Cargando modelo YOLO11 Pose...")
model = YOLO("yolo11n-pose.pt")  # Modelo nano (rápido)
print("✅ Modelo cargado correctamente")

# Probar con un video
cap = cv2.VideoCapture("test.mp4")

if not cap.isOpened():
    print("❌ No se pudo abrir test.mp4")
    exit()

print("🚀 Procesando video... Presiona 'q' para salir")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Realizar inferencia
    results = model(frame, verbose=False)
    
    # Obtener puntos clave
    if results[0].keypoints is not None:
        keypoints = results[0].keypoints.data[0].cpu().numpy()
        
        # Mostrar cantidad de puntos detectados
        puntos_visibles = sum(1 for kp in keypoints if kp[2] > 0.5)
        cv2.putText(frame, f"Puntos: {puntos_visibles}/17", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Dibujar skeleton
    annotated_frame = results[0].plot()
    
    cv2.imshow("YOLO11 Pose Test", annotated_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("✅ Prueba completada")