def detectar_metodo_adecuado(detecciones_yolo):
    """
    Analiza las etiquetas de YOLO y decide el método.
    """
    # Extraemos solo los nombres de las clases detectadas
    labels = [d.get('name') for d in detecciones_yolo]
    
    # Lógica de decisión
    if 'chair' in labels or 'laptop' in labels or 'keyboard' in labels:
        return "ROSA", "Puesto de Oficina detectado"
    
    if 'box' in labels or 'pantry' in labels:
        return "NIOSH", "Manipulación de cargas detectada"
        
    if 'hammer' in labels or 'wrench' in labels or 'bench' in labels:
        return "OWAS", "Entorno industrial/herramientas detectado"

    # Si no detecta objetos específicos, por defecto usamos análisis postural
    return "RULA/REBA", "Análisis postural general"