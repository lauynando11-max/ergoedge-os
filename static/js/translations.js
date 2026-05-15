// translations.js - Sistema de idiomas para ERGOEDGE OS
// Idiomas: español (es), inglés (en), portugués (pt)

const translations = {
    // ESPAÑOL
    es: {
        // Navbar
        'nav.brand': 'ERGOEDGE OS',
        'nav.ia_badge': 'IA Integrada',
        'nav.login': 'Ingresar',
        'nav.register': 'Registrarse',
        'nav.dashboard': 'Dashboard',
        'nav.logout': 'Cerrar Sesión',
        
        // Hero
        'hero.badge': 'IA Integrada · Tecnología de vanguardia',
        'hero.title': 'Análisis Ergonómico con',
        'hero.title_ia': 'IA',
        'hero.subtitle': 'Evalúa la postura de trabajadores usando inteligencia artificial y métodos certificados.',
        'hero.btn_start': 'Comenzar Análisis',
        'hero.btn_demo': 'Ver Demo',
        
        // Estadísticas
        'stats.precision': 'Precisión diagnóstica',
        'stats.methods': 'Métodos certificados',
        'stats.postures': 'Posturas analizadas',
        
        // Esqueleto 3D
        'skeleton.title': 'Análisis postural 3D con IA',
        'skeleton.active': 'Análisis en tiempo real',
        'skeleton.step1': 'Detección',
        'skeleton.step2': 'Puntos articulares',
        'skeleton.step3': 'Cálculo de ángulos',
        'skeleton.step4': 'Generando informe',
        
        // Métodos
        'methods.badge': 'MÉTODOS CERTIFICADOS',
        'methods.title': 'Evaluación Ergonómica Profesional',
        'methods.subtitle': 'Basados en los estándares internacionales más reconocidos',
        
        'method.owas.title': 'OWAS',
        'method.owas.desc': 'Análisis de cuerpo completo en posturas industriales',
        'method.owas.badge1': 'Biomecánica',
        'method.owas.badge2': '+ IA',
        
        'method.rula.title': 'RULA',
        'method.rula.desc': 'Evaluación detallada de miembros superiores',
        'method.rula.badge1': 'Ángulos',
        'method.rula.badge2': '+ IA',
        
        'method.reba.title': 'REBA 3D',
        'method.reba.desc': 'Análisis completo con estimación tridimensional',
        'method.reba.badge1': 'Estimación 3D',
        'method.reba.badge2': '+ IA',
        
        'method.rosa.title': 'ROSA',
        'method.rosa.desc': 'Ergonomía específica para entornos de oficina',
        'method.rosa.badge1': 'Postura laboral',
        'method.rosa.badge2': '+ IA',
        
        // Why Choose Us
        'why.badge': 'WHY CHOOSE US',
        'why.title': '¿Por qué elegir ERGOEDGE OS?',
        'why.subtitle': 'Tecnología de vanguardia al servicio de la salud postural',
        'why.ia.title': 'IA Integrada',
        'why.ia.desc': 'Análisis automático de postura usando inteligencia artificial avanzada',
        'why.methods.title': 'Métodos Certificados',
        'why.methods.desc': 'RULA, REBA, OWAS y ROSA respaldados por la comunidad científica',
        'why.prevention.title': 'Prevención Proactiva',
        'why.prevention.desc': 'Reduce lesiones por esfuerzo repetitivo y mejora la productividad',
        
        // Tecnología
        'tech.badge': 'TECNOLOGÍA',
        'tech.title': 'Potenciado por IA',
        'tech.subtitle': 'Combinamos lo mejor de la visión artificial con métodos ergonómicos certificados',
        'tech.vision.title': 'Visión Artificial',
        'tech.vision.desc': 'Detección precisa de puntos clave del cuerpo humano',
        'tech.realtime.title': 'Análisis en Tiempo Real',
        'tech.realtime.desc': 'Procesamiento instantáneo de datos posturales',
        'tech.reports.title': 'Reportes Detallados',
        'tech.reports.desc': 'Resultados claros con recomendaciones accionables',
        
        // Footer
        'footer.powered': 'Powered by YOLOv11 + Gemini IA',
        'footer.copyright': 'Ingeniería de Factores Humanos',
        
        // Login
        'login.title': 'Bienvenido',
        'login.subtitle': 'Ingresa a tu cuenta',
        'login.email': 'Correo electrónico',
        'login.password': 'Contraseña',
        'login.button': 'Iniciar Sesión',
        'login.register_link': '¿No tienes cuenta? Regístrate aquí',
        
        // Registro
        'register.title': 'Crear Cuenta',
        'register.subtitle': 'Regístrate para comenzar',
        'register.name': 'Nombre completo',
        'register.email': 'Correo electrónico',
        'register.password': 'Contraseña',
        'register.button': 'Registrarse',
        'register.login_link': '¿Ya tienes cuenta? Inicia Sesión',
        
        // Dashboard (completo)
        'dashboard.welcome': 'Panel de Control',
        
        // Perfil / Columna izquierda
        'dashboard.perfil.titulo_nombre': '', // Deja vacío porque es dinámico con {{ usuario.nombre }}
        'dashboard.perfil.email': '', // Dinámico
        'dashboard.perfil.miembro_desde': 'Miembro desde',
        'dashboard.perfil.boton_nuevo_analisis': 'Nuevo Análisis',
        'dashboard.perfil.boton_cerrar_sesion': 'Cerrar Sesión',
        'dashboard.perfil.info_cuenta_titulo': 'Información de la cuenta',
        'dashboard.perfil.label_nombre': 'Nombre:',
        'dashboard.perfil.label_correo': 'Correo:',
        'dashboard.perfil.label_registro': 'Registro:',
        
        // Historial
        'dashboard.historial.titulo': 'Historial de Análisis',
        'dashboard.historial.contador_analisis': 'análisis',
        'dashboard.historial.tabla_fecha': 'FECHA',
        'dashboard.historial.tabla_metodo': 'MÉTODO',
        'dashboard.historial.tabla_empresa': 'EMPRESA',
        'dashboard.historial.tabla_operario': 'OPERARIO',
        'dashboard.historial.tabla_riesgo': 'RIESGO',
        'dashboard.historial.tabla_acciones': 'ACCIONES',
        'dashboard.historial.texto_ultimos_analisis': 'Últimos análisis realizados',
        'dashboard.historial.sin_analisis_mensaje': 'No tienes análisis realizados todavía.',
        'dashboard.historial.boton_comenzar_primer_analisis': 'Comenzar primer análisis',
        'dashboard.historial.boton_ver_detalle_title': 'Ver detalle',
        'dashboard.historial.boton_exportar_pdf_title': 'Exportar PDF',
        
        // Modal de detalle
        'dashboard.modal.titulo_detalle': 'Detalle del Análisis',
        'dashboard.modal.cerrar': 'Cerrar',
        'dashboard.modal.cargando_estado': 'Cargando...',
        'dashboard.modal.cargando_mensaje': 'Cargando detalles...',
        'dashboard.modal.error_cargar': 'Error al cargar los detalles',
        'dashboard.modal.puntuacion_texto': 'Puntuación:',
        'dashboard.modal.nivel_riesgo_label': 'Nivel de Riesgo:',
        'dashboard.modal.empresa_label': 'EMPRESA',
        'dashboard.modal.puesto_label': 'PUESTO',
        'dashboard.modal.evaluador_label': 'EVALUADOR',
        'dashboard.modal.operario_label': 'OPERARIO',
        'dashboard.modal.codigo_owas_label': 'Código OWAS:',
        'dashboard.modal.codigo_owas_formato': ' (Formato: Espalda/Brazo/Piernas/Carga)',
        'dashboard.modal.recomendaciones_titulo': 'Recomendaciones',
        'dashboard.modal.sin_recomendaciones': 'No hay recomendaciones disponibles',
        'dashboard.modal.dictamen_ia_titulo': 'Dictamen con IA:',
        'dashboard.modal.boton_exportar_pdf': 'Exportar PDF',
        'dashboard.modal.boton_cerrar': 'Cerrar',
        
        // ANALISIS (nuevo)
        'analisis.title': 'Nuevo Análisis Ergonómico',
        'analisis.subtitle': 'Seleccione el método de evaluación',
        'analisis.opcion_video_titulo': 'Video / Foto',
        'analisis.opcion_video_desc': 'Para OWAS, RULA, REBA',
        'analisis.opcion_video_badge': 'Disponible',
        'analisis.opcion_rosa_titulo': 'ROSA',
        'analisis.opcion_rosa_desc': 'Evaluación de oficina',
        'analisis.opcion_rosa_badge': 'Disponible',
        
        // Video Form
        'video.title': 'Análisis por Video / Foto',
        'video.subtitle': 'Complete los datos para comenzar el análisis ergonómico',
        'video.method': 'Método de Análisis',
        'video.company': 'Datos de la Empresa',
        'video.company_name': 'Empresa',
        'video.position': 'Puesto',
        'video.worker': 'Datos del Operario',
        'video.worker_name': 'Nombre',
        'video.worker_age': 'Edad',
        'video.worker_seniority': 'Antigüedad',
        'video.worker_evaluator': 'Evaluador',
        'video.worker_pathologies': 'Patologías previas',
        'video.worker_load': 'Peso de la carga (kg)',
        'video.worker_load_help': 'Si no manipula carga, dejar en 0',
        'video.file': 'Archivo a Analizar',
        'video.file_label': 'Video (mp4, avi, mov) o Foto (jpg, png)',
        'video.file_help': 'Suba un video de la actividad laboral o una foto de la postura (Máx 100MB)',
        'video.analyze': 'Analizar',
        'video.progress': 'Preparando...',
        
        // SRT Modal
        'srt.title': 'Cumplimiento Normativo',
        'srt.question': '¿Desea que el informe cumpla con la',
        'srt.resolution': 'Resolución SRT 886/2015',
        'srt.protocol': '(Protocolo de Ergonomía)?',
        'srt.description': 'Esto agregará las Planillas del Anexo I al reporte PDF y requerirá datos adicionales.',
        'srt.fields_title': 'Datos requeridos por la normativa SRT 886/2015:',
        'srt.workers': 'Cantidad de trabajadores expuestos',
        'srt.hours': 'Tiempo de exposición diaria (horas)',
        'srt.days': 'Frecuencia semanal (días)',
        'srt.weight': 'Peso de la carga (kg) - Planilla 2.A',
        'srt.weight_help': 'Si ya ingresó peso en datos del operario, se usará automáticamente',
        'srt.frequency': 'Frecuencia de levantamiento (por hora)',
        'srt.distance': 'Distancia vertical (cm)',
        'srt.standing': 'Tipo de bipedestación',
        'srt.standing_fixed': 'Fija (sin desplazamiento)',
        'srt.standing_moving': 'Con desplazamiento',
        'srt.standing_mixed': 'Mixta (sentado/bipedestación)',
        'srt.thermal': 'Confort térmico',
        'srt.thermal_adequate': 'Adecuado',
        'srt.thermal_cold': 'Frío',
        'srt.thermal_hot': 'Calor',
        'srt.thermal_very_cold': 'Muy frío',
        'srt.thermal_very_hot': 'Muy caluroso',
        'srt.contact': '¿Hay estrés de contacto?',
        'srt.contact_no': 'No',
        'srt.contact_occasional': 'Sí, ocasional',
        'srt.contact_frequent': 'Sí, frecuente',
        'srt.task_desc': 'Descripción de la tarea',
        'srt.observations': 'Observaciones adicionales',
        'srt.no': 'No, reporte simple',
        'srt.yes': 'Sí, cumplir normativa',
        'srt.cancel': 'Cancelar',
        'srt.confirm': 'Confirmar y continuar',
        
        // Toast
        'toast.welcome': '¡Bienvenido a ERGOEDGE OS! 🧬'
    },
    
    // ENGLISH
    en: {
        'nav.brand': 'ERGOEDGE OS',
        'nav.ia_badge': 'AI Integrated',
        'nav.login': 'Login',
        'nav.register': 'Sign Up',
        'nav.dashboard': 'Dashboard',
        'nav.logout': 'Logout',
        
        'hero.badge': 'AI Integrated · Cutting-edge Technology',
        'hero.title': 'Ergonomic Analysis with',
        'hero.title_ia': 'AI',
        'hero.subtitle': 'Evaluate workers\' posture using artificial intelligence and certified methods.',
        'hero.btn_start': 'Start Analysis',
        'hero.btn_demo': 'Watch Demo',
        
        'stats.precision': 'Diagnostic accuracy',
        'stats.methods': 'Certified methods',
        'stats.postures': 'Postures analyzed',
        
        'skeleton.title': '3D postural analysis with AI',
        'skeleton.active': 'Real-time analysis',
        'skeleton.step1': 'Detection',
        'skeleton.step2': 'Key points',
        'skeleton.step3': 'Angle calculation',
        'skeleton.step4': 'Generating report',
        
        'methods.badge': 'CERTIFIED METHODS',
        'methods.title': 'Professional Ergonomic Assessment',
        'methods.subtitle': 'Based on the most recognized international standards',
        
        'method.owas.title': 'OWAS',
        'method.owas.desc': 'Full body analysis in industrial postures',
        'method.owas.badge1': 'Biomechanics',
        'method.owas.badge2': '+ AI',
        
        'method.rula.title': 'RULA',
        'method.rula.desc': 'Detailed upper limb assessment',
        'method.rula.badge1': 'Angles',
        'method.rula.badge2': '+ AI',
        
        'method.reba.title': 'REBA 3D',
        'method.reba.desc': 'Complete analysis with 3D estimation',
        'method.reba.badge1': '3D Estimation',
        'method.reba.badge2': '+ AI',
        
        'method.rosa.title': 'ROSA',
        'method.rosa.desc': 'Office-specific ergonomics',
        'method.rosa.badge1': 'Work posture',
        'method.rosa.badge2': '+ AI',
        
        'why.badge': 'WHY CHOOSE US',
        'why.title': 'Why choose ERGOEDGE OS?',
        'why.subtitle': 'Cutting-edge technology for postural health',
        'why.ia.title': 'AI Integrated',
        'why.ia.desc': 'Automatic posture analysis using advanced artificial intelligence',
        'why.methods.title': 'Certified Methods',
        'why.methods.desc': 'RULA, REBA, OWAS and ROSA backed by the scientific community',
        'why.prevention.title': 'Proactive Prevention',
        'why.prevention.desc': 'Reduce repetitive strain injuries and improve productivity',
        
        'tech.badge': 'TECHNOLOGY',
        'tech.title': 'Powered by AI',
        'tech.subtitle': 'We combine the best of computer vision with certified ergonomic methods',
        'tech.vision.title': 'Computer Vision',
        'tech.vision.desc': 'Precise detection of key points of the human body',
        'tech.realtime.title': 'Real-time Analysis',
        'tech.realtime.desc': 'Instant processing of postural data',
        'tech.reports.title': 'Detailed Reports',
        'tech.reports.desc': 'Clear results with actionable recommendations',
        
        'footer.powered': 'Powered by YOLOv11 + Gemini AI',
        'footer.copyright': 'Human Factors Engineering',
        
        'login.title': 'Welcome',
        'login.subtitle': 'Login to your account',
        'login.email': 'Email address',
        'login.password': 'Password',
        'login.button': 'Login',
        'login.register_link': 'Don\'t have an account? Sign up here',
        
        'register.title': 'Create Account',
        'register.subtitle': 'Sign up to get started',
        'register.name': 'Full name',
        'register.email': 'Email address',
        'register.password': 'Password',
        'register.button': 'Sign Up',
        'register.login_link': 'Already have an account? Login here',
        
        // Dashboard
        'dashboard.welcome': 'Control Panel',
        
        // Perfil
        'dashboard.perfil.miembro_desde': 'Member since',
        'dashboard.perfil.boton_nuevo_analisis': 'New Analysis',
        'dashboard.perfil.boton_cerrar_sesion': 'Logout',
        'dashboard.perfil.info_cuenta_titulo': 'Account Information',
        'dashboard.perfil.label_nombre': 'Name:',
        'dashboard.perfil.label_correo': 'Email:',
        'dashboard.perfil.label_registro': 'Registered:',
        
        // Historial
        'dashboard.historial.titulo': 'Analysis History',
        'dashboard.historial.contador_analisis': 'analyses',
        'dashboard.historial.tabla_fecha': 'DATE',
        'dashboard.historial.tabla_metodo': 'METHOD',
        'dashboard.historial.tabla_empresa': 'COMPANY',
        'dashboard.historial.tabla_operario': 'WORKER',
        'dashboard.historial.tabla_riesgo': 'RISK',
        'dashboard.historial.tabla_acciones': 'ACTIONS',
        'dashboard.historial.texto_ultimos_analisis': 'Last analyses performed',
        'dashboard.historial.sin_analisis_mensaje': 'You have no analyses yet.',
        'dashboard.historial.boton_comenzar_primer_analisis': 'Start first analysis',
        'dashboard.historial.boton_ver_detalle_title': 'View details',
        'dashboard.historial.boton_exportar_pdf_title': 'Export PDF',
        
        // Modal
        'dashboard.modal.titulo_detalle': 'Analysis Details',
        'dashboard.modal.cerrar': 'Close',
        'dashboard.modal.cargando_estado': 'Loading...',
        'dashboard.modal.cargando_mensaje': 'Loading details...',
        'dashboard.modal.error_cargar': 'Error loading details',
        'dashboard.modal.puntuacion_texto': 'Score:',
        'dashboard.modal.nivel_riesgo_label': 'Risk Level:',
        'dashboard.modal.empresa_label': 'COMPANY',
        'dashboard.modal.puesto_label': 'POSITION',
        'dashboard.modal.evaluador_label': 'EVALUATOR',
        'dashboard.modal.operario_label': 'WORKER',
        'dashboard.modal.codigo_owas_label': 'OWAS Code:',
        'dashboard.modal.codigo_owas_formato': ' (Format: Back/Arms/Legs/Load)',
        'dashboard.modal.recomendaciones_titulo': 'Recommendations',
        'dashboard.modal.sin_recomendaciones': 'No recommendations available',
        'dashboard.modal.dictamen_ia_titulo': 'AI Assessment:',
        'dashboard.modal.boton_exportar_pdf': 'Export PDF',
        'dashboard.modal.boton_cerrar': 'Close',
        
        // ANALYSIS (new)
        'analisis.title': 'New Ergonomic Analysis',
        'analisis.subtitle': 'Select evaluation method',
        'analisis.opcion_video_titulo': 'Video / Photo',
        'analisis.opcion_video_desc': 'For OWAS, RULA, REBA',
        'analisis.opcion_video_badge': 'Available',
        'analisis.opcion_rosa_titulo': 'ROSA',
        'analisis.opcion_rosa_desc': 'Office evaluation',
        'analisis.opcion_rosa_badge': 'Available',
        
        // Video Form
        'video.title': 'Video / Photo Analysis',
        'video.subtitle': 'Complete the data to start the ergonomic analysis',
        'video.method': 'Analysis Method',
        'video.company': 'Company Data',
        'video.company_name': 'Company',
        'video.position': 'Position',
        'video.worker': 'Worker Data',
        'video.worker_name': 'Name',
        'video.worker_age': 'Age',
        'video.worker_seniority': 'Seniority',
        'video.worker_evaluator': 'Evaluator',
        'video.worker_pathologies': 'Previous pathologies',
        'video.worker_load': 'Load weight (kg)',
        'video.worker_load_help': 'If no load, leave 0',
        'video.file': 'File to Analyze',
        'video.file_label': 'Video (mp4, avi, mov) or Photo (jpg, png)',
        'video.file_help': 'Upload a video of the work activity or a photo of the posture (Max 100MB)',
        'video.analyze': 'Analyze',
        'video.progress': 'Preparing...',
        
        // SRT Modal
        'srt.title': 'Regulatory Compliance',
        'srt.question': 'Do you want the report to comply with',
        'srt.resolution': 'Resolution SRT 886/2015',
        'srt.protocol': '(Ergonomics Protocol)?',
        'srt.description': 'This will add the Annex I forms to the PDF report and require additional data.',
        'srt.fields_title': 'Data required by SRT 886/2015 regulations:',
        'srt.workers': 'Number of exposed workers',
        'srt.hours': 'Daily exposure time (hours)',
        'srt.days': 'Weekly frequency (days)',
        'srt.weight': 'Load weight (kg) - Form 2.A',
        'srt.weight_help': 'If you already entered weight in worker data, it will be used automatically',
        'srt.frequency': 'Lifting frequency (per hour)',
        'srt.distance': 'Vertical distance (cm)',
        'srt.standing': 'Type of standing',
        'srt.standing_fixed': 'Fixed (no displacement)',
        'srt.standing_moving': 'With displacement',
        'srt.standing_mixed': 'Mixed (sitting/standing)',
        'srt.thermal': 'Thermal comfort',
        'srt.thermal_adequate': 'Adequate',
        'srt.thermal_cold': 'Cold',
        'srt.thermal_hot': 'Hot',
        'srt.thermal_very_cold': 'Very cold',
        'srt.thermal_very_hot': 'Very hot',
        'srt.contact': 'Is there contact stress?',
        'srt.contact_no': 'No',
        'srt.contact_occasional': 'Yes, occasional',
        'srt.contact_frequent': 'Yes, frequent',
        'srt.task_desc': 'Task description',
        'srt.observations': 'Additional observations',
        'srt.no': 'No, simple report',
        'srt.yes': 'Yes, comply with regulations',
        'srt.cancel': 'Cancel',
        'srt.confirm': 'Confirm and continue',
        
        'toast.welcome': 'Welcome to ERGOEDGE OS! 🧬'
    },
    
    // PORTUGUÊS
    pt: {
        'nav.brand': 'ERGOEDGE OS',
        'nav.ia_badge': 'IA Integrada',
        'nav.login': 'Entrar',
        'nav.register': 'Registrar',
        'nav.dashboard': 'Painel',
        'nav.logout': 'Sair',
        
        'hero.badge': 'IA Integrada · Tecnologia de ponta',
        'hero.title': 'Análise Ergonômica com',
        'hero.title_ia': 'IA',
        'hero.subtitle': 'Avalie a postura dos trabalhadores usando inteligência artificial e métodos certificados.',
        'hero.btn_start': 'Iniciar Análise',
        'hero.btn_demo': 'Ver Demo',
        
        'stats.precision': 'Precisão diagnóstica',
        'stats.methods': 'Métodos certificados',
        'stats.postures': 'Posturas analisadas',
        
        'skeleton.title': 'Análise postural 3D com IA',
        'skeleton.active': 'Análise em tempo real',
        'skeleton.step1': 'Detecção',
        'skeleton.step2': 'Pontos articulares',
        'skeleton.step3': 'Cálculo de ângulos',
        'skeleton.step4': 'Gerando relatório',
        
        'methods.badge': 'MÉTODOS CERTIFICADOS',
        'methods.title': 'Avaliação Ergonômica Profissional',
        'methods.subtitle': 'Baseados nos padrões internacionais mais reconhecidos',
        
        'method.owas.title': 'OWAS',
        'method.owas.desc': 'Análise de corpo completo em posturas industriais',
        'method.owas.badge1': 'Biomecânica',
        'method.owas.badge2': '+ IA',
        
        'method.rula.title': 'RULA',
        'method.rula.desc': 'Avaliação detalhada dos membros superiores',
        'method.rula.badge1': 'Ângulos',
        'method.rula.badge2': '+ IA',
        
        'method.reba.title': 'REBA 3D',
        'method.reba.desc': 'Análise completa com estimativa 3D',
        'method.reba.badge1': 'Estimativa 3D',
        'method.reba.badge2': '+ IA',
        
        'method.rosa.title': 'ROSA',
        'method.rosa.desc': 'Ergonomia específica para escritórios',
        'method.rosa.badge1': 'Postura laboral',
        'method.rosa.badge2': '+ IA',
        
        'why.badge': 'POR QUE ESCOLHER',
        'why.title': 'Por que escolher ERGOEDGE OS?',
        'why.subtitle': 'Tecnologia de ponta a serviço da saúde postural',
        'why.ia.title': 'IA Integrada',
        'why.ia.desc': 'Análise automática de postura usando inteligência artificial avançada',
        'why.methods.title': 'Métodos Certificados',
        'why.methods.desc': 'RULA, REBA, OWAS e ROSA respaldados pela comunidade científica',
        'why.prevention.title': 'Prevenção Proativa',
        'why.prevention.desc': 'Reduz lesões por esforço repetitivo e melhora a produtividade',
        
        'tech.badge': 'TECNOLOGIA',
        'tech.title': 'Potencializado por IA',
        'tech.subtitle': 'Combinamos o melhor da visão computacional com métodos ergonômicos certificados',
        'tech.vision.title': 'Visão Computacional',
        'tech.vision.desc': 'Detecção precisa de pontos-chave do corpo humano',
        'tech.realtime.title': 'Análise em Tempo Real',
        'tech.realtime.desc': 'Processamento instantâneo de dados posturais',
        'tech.reports.title': 'Relatórios Detalhados',
        'tech.reports.desc': 'Resultados claros com recomendações acionáveis',
        
        'footer.powered': 'Desenvolvido com YOLOv11 + IA Gemini',
        'footer.copyright': 'Engenharia de Fatores Humanos',
        
        'login.title': 'Bem-vindo',
        'login.subtitle': 'Entre na sua conta',
        'login.email': 'E-mail',
        'login.password': 'Senha',
        'login.button': 'Entrar',
        'login.register_link': 'Não tem conta? Registre-se aqui',
        
        'register.title': 'Criar Conta',
        'register.subtitle': 'Registre-se para começar',
        'register.name': 'Nome completo',
        'register.email': 'E-mail',
        'register.password': 'Senha',
        'register.button': 'Registrar',
        'register.login_link': 'Já tem conta? Faça login',
        
        // Dashboard
        'dashboard.welcome': 'Painel de Controle',
        
        // Perfil
        'dashboard.perfil.miembro_desde': 'Membro desde',
        'dashboard.perfil.boton_nuevo_analisis': 'Nova Análise',
        'dashboard.perfil.boton_cerrar_sesion': 'Sair',
        'dashboard.perfil.info_cuenta_titulo': 'Informações da conta',
        'dashboard.perfil.label_nombre': 'Nome:',
        'dashboard.perfil.label_correo': 'E-mail:',
        'dashboard.perfil.label_registro': 'Registro:',
        
        // Historial
        'dashboard.historial.titulo': 'Histórico de Análises',
        'dashboard.historial.contador_analisis': 'análises',
        'dashboard.historial.tabla_fecha': 'DATA',
        'dashboard.historial.tabla_metodo': 'MÉTODO',
        'dashboard.historial.tabla_empresa': 'EMPRESA',
        'dashboard.historial.tabla_operario': 'OPERADOR',
        'dashboard.historial.tabla_riesgo': 'RISCO',
        'dashboard.historial.tabla_acciones': 'AÇÕES',
        'dashboard.historial.texto_ultimos_analisis': 'Últimas análises realizadas',
        'dashboard.historial.sin_analisis_mensaje': 'Você ainda não tem análises realizadas.',
        'dashboard.historial.boton_comenzar_primer_analisis': 'Iniciar primeira análise',
        'dashboard.historial.boton_ver_detalle_title': 'Ver detalhe',
        'dashboard.historial.boton_exportar_pdf_title': 'Exportar PDF',
        
        // Modal
        'dashboard.modal.titulo_detalle': 'Detalhe da Análise',
        'dashboard.modal.cerrar': 'Fechar',
        'dashboard.modal.cargando_estado': 'Carregando...',
        'dashboard.modal.cargando_mensaje': 'Carregando detalhes...',
        'dashboard.modal.error_cargar': 'Erro ao carregar detalhes',
        'dashboard.modal.puntuacion_texto': 'Pontuação:',
        'dashboard.modal.nivel_riesgo_label': 'Nível de Risco:',
        'dashboard.modal.empresa_label': 'EMPRESA',
        'dashboard.modal.puesto_label': 'CARGO',
        'dashboard.modal.evaluador_label': 'AVALIADOR',
        'dashboard.modal.operario_label': 'OPERADOR',
        'dashboard.modal.codigo_owas_label': 'Código OWAS:',
        'dashboard.modal.codigo_owas_formato': ' (Formato: Costas/Braços/Pernas/Carga)',
        'dashboard.modal.recomendaciones_titulo': 'Recomendações',
        'dashboard.modal.sin_recomendaciones': 'Não há recomendações disponíveis',
        'dashboard.modal.dictamen_ia_titulo': 'Parecer da IA:',
        'dashboard.modal.boton_exportar_pdf': 'Exportar PDF',
        'dashboard.modal.boton_cerrar': 'Fechar',
        
        // ANÁLISE (novo)
        'analisis.title': 'Nova Análise Ergonômica',
        'analisis.subtitle': 'Selecione o método de avaliação',
        'analisis.opcion_video_titulo': 'Vídeo / Foto',
        'analisis.opcion_video_desc': 'Para OWAS, RULA, REBA',
        'analisis.opcion_video_badge': 'Disponível',
        'analisis.opcion_rosa_titulo': 'ROSA',
        'analisis.opcion_rosa_desc': 'Avaliação de escritório',
        'analisis.opcion_rosa_badge': 'Disponível',
        
        // Video Form
        'video.title': 'Análise por Vídeo / Foto',
        'video.subtitle': 'Complete os dados para iniciar a análise ergonômica',
        'video.method': 'Método de Análise',
        'video.company': 'Dados da Empresa',
        'video.company_name': 'Empresa',
        'video.position': 'Cargo',
        'video.worker': 'Dados do Operador',
        'video.worker_name': 'Nome',
        'video.worker_age': 'Idade',
        'video.worker_seniority': 'Antiguidade',
        'video.worker_evaluator': 'Avaliador',
        'video.worker_pathologies': 'Patologias prévias',
        'video.worker_load': 'Peso da carga (kg)',
        'video.worker_load_help': 'Se não manipular carga, deixar 0',
        'video.file': 'Arquivo a Analisar',
        'video.file_label': 'Vídeo (mp4, avi, mov) ou Foto (jpg, png)',
        'video.file_help': 'Envie um vídeo da atividade laboral ou uma foto da postura (Máx 100MB)',
        'video.analyze': 'Analisar',
        'video.progress': 'Preparando...',
        
        // SRT Modal
        'srt.title': 'Conformidade Regulatória',
        'srt.question': 'Deseja que o relatório atenda à',
        'srt.resolution': 'Resolução SRT 886/2015',
        'srt.protocol': '(Protocolo de Ergonomia)?',
        'srt.description': 'Isso adicionará os Anexos I ao relatório PDF e exigirá dados adicionais.',
        'srt.fields_title': 'Dados exigidos pela norma SRT 886/2015:',
        'srt.workers': 'Número de trabalhadores expostos',
        'srt.hours': 'Tempo de exposição diária (horas)',
        'srt.days': 'Frequência semanal (dias)',
        'srt.weight': 'Peso da carga (kg) - Planilha 2.A',
        'srt.weight_help': 'Se já inseriu peso nos dados do operador, será usado automaticamente',
        'srt.frequency': 'Frequência de levantamento (por hora)',
        'srt.distance': 'Distância vertical (cm)',
        'srt.standing': 'Tipo de bipedestação',
        'srt.standing_fixed': 'Fixa (sem deslocamento)',
        'srt.standing_moving': 'Com deslocamento',
        'srt.standing_mixed': 'Mista (sentado/bipedestação)',
        'srt.thermal': 'Conforto térmico',
        'srt.thermal_adequate': 'Adequado',
        'srt.thermal_cold': 'Frio',
        'srt.thermal_hot': 'Calor',
        'srt.thermal_very_cold': 'Muito frio',
        'srt.thermal_very_hot': 'Muito quente',
        'srt.contact': 'Há estresse de contato?',
        'srt.contact_no': 'Não',
        'srt.contact_occasional': 'Sim, ocasional',
        'srt.contact_frequent': 'Sim, frequente',
        'srt.task_desc': 'Descrição da tarefa',
        'srt.observations': 'Observações adicionais',
        'srt.no': 'Não, relatório simples',
        'srt.yes': 'Sim, cumprir norma',
        'srt.cancel': 'Cancelar',
        'srt.confirm': 'Confirmar e continuar',
        
        'toast.welcome': 'Bem-vindo ao ERGOEDGE OS! 🧬'
    }
};

// Idioma actual (por defecto español)
let currentLang = localStorage.getItem('ergo_lang') || 'es';

// Función para obtener el texto traducido
function t(key) {
    if (translations[currentLang] && translations[currentLang][key]) {
        return translations[currentLang][key];
    }
    if (translations.es && translations.es[key]) {
        return translations.es[key];
    }
    return key;
}

// Función para cambiar el idioma
function setLanguage(lang) {
    if (translations[lang]) {
        currentLang = lang;
        localStorage.setItem('ergo_lang', lang);
        updatePageTexts();
        if (typeof showToast === 'function') {
            showToast(`Idioma cambiado a ${lang === 'es' ? 'Español' : lang === 'en' ? 'English' : 'Português'}`, 'success', 2000);
        }
    }
}

// Función para actualizar todos los textos de la página con el idioma actual
function updatePageTexts() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translation = t(key);
        if (translation && translation !== '') {
            // Para elementos que contienen HTML o valores dinámicos, preservar
            if (el.children.length === 0 || key === 'dashboard.historial.contador_analisis') {
                el.textContent = translation;
            }
        }
    });
    
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const translation = t(key);
        if (translation) {
            el.placeholder = translation;
        }
    });
    
    // Actualizar tooltips/atributos title
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const translation = t(key);
        if (translation) {
            el.title = translation;
        }
    });
    
    document.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang: currentLang } }));
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    updatePageTexts();
});