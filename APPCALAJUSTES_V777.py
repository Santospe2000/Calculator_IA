import streamlit as st
from openai import OpenAI
import sqlite3
from fpdf import FPDF
import base64
from io import BytesIO
import re
import os
import pandas as pd

# Configuración inicial de la página
st.set_page_config(
    page_title="Taller de Bienes Raíces - Carlos Devis",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Configuración del cliente de OpenAI
client = None
if 'OPENAI_API_KEY' in st.secrets:
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        st.session_state['openai_configured'] = True
    except Exception as e:
        st.error(f"Error al configurar OpenAI: {str(e)}")
        st.session_state['openai_configured'] = False
else:
    st.warning("Funcionalidad de IA limitada - No se configuró OPENAI_API_KEY")
    st.session_state['openai_configured'] = False

# Estilos CSS personalizados
def load_css():
    st.markdown("""
    <style>
        :root {
            --azul-oscuro: #1E3A8A;
            --gris: #6B7280;
            --blanco: #FFFFFF;
            --verde: #10B981;
            --rojo: #EF4444;
        }
        
        .stApp {
            max-width: 900px;
            margin: auto;
            font-family: 'Arial', sans-serif;
            background-color: #F9FAFB;
        }
        
        .header-container {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .logo {
            height: 60px;
            margin-right: 20px;
        }
        
        .calculator-container {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        
        .stButton>button {
            background-color: var(--azul-oscuro);
            color: white;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: bold;
            width: 100%;
        }
        
        .stButton>button:hover {
            background-color: #1E40AF;
            color: white;
        }
        
        .stTextInput>div>div>input, 
        .stNumberInput>div>div>input,
        .stSelectbox>div>div>select,
        .stMultiselect>div>div>div {
            border-radius: 8px;
            border: 1px solid var(--gris);
        }
        
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: var(--azul-oscuro);
        }
        
        .stMetric {
            border-left: 4px solid var(--azul-oscuro);
            padding-left: 12px;
            background-color: white;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .positive-value {
            color: var(--verde);
            font-weight: bold;
        }
        
        .negative-value {
            color: var(--rojo);
            font-weight: bold;
        }
        
        .data-table {
            width: 100%;
            margin-bottom: 20px;
            border-collapse: collapse;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .data-table th {
            background-color: var(--azul-oscuro);
            color: white;
            padding: 10px;
            text-align: left;
        }
        
        .data-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        .data-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .data-table input {
            width: 100%;
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        .data-table .total-row {
            background-color: #EFF6FF;
            font-weight: bold;
        }
        
        .tips-container {
            background-color: #f8f9fa;
            border-left: 4px solid var(--azul-oscuro);
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 0 8px 8px 0;
        }
        
        @media (max-width: 768px) {
            .header-container {
                flex-direction: column;
                text-align: center;
            }
            
            .logo {
                margin-right: 0;
                margin-bottom: 10px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# Función para formatear números como moneda
def format_currency(value):
    return f"${value:,.2f}" if value is not None else "$0.00"

# Función para extraer el valor numérico de un string de moneda
def parse_currency(currency_str):
    if not currency_str:
        return 0.0
    # Eliminar símbolos de moneda y comas
    num_str = re.sub(r'[^\d.]', '', currency_str)
    return float(num_str) if num_str else 0.0

# Función para generar PDF
def generate_pdf(usuario_data, finanzas_data, analisis_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Taller de Bienes Raíces - Reporte Financiero", ln=1, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Carlos Devis", ln=1, align='C')
    pdf.ln(10)
    
    # Datos personales
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Datos Personales:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Nombre: {usuario_data.get('nombre', '')}", ln=1)
    pdf.cell(200, 10, txt=f"Edad: {usuario_data.get('edad', '')}", ln=1)
    pdf.cell(200, 10, txt=f"Email: {usuario_data.get('email', '')}", ln=1)
    pdf.ln(5)
    
    # Datos financieros
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Situación Financiera:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Ingresos Mensuales: {format_currency(finanzas_data.get('ingresos', 0))}", ln=1)
    pdf.cell(200, 10, txt=f"Gastos Mensuales: {format_currency(finanzas_data.get('gastos', 0))}", ln=1)
    pdf.cell(200, 10, txt=f"Activos Totales: {format_currency(finanzas_data.get('activos', 0))}", ln=1)
    pdf.cell(200, 10, txt=f"Pasivos Totales: {format_currency(finanzas_data.get('pasivos', 0))}", ln=1)
    pdf.ln(5)
    
    # Perfil de inversión
    if 'perfil_inversion' in analisis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Perfil de Inversión en Bienes Raíces:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=f"Nivel: {analisis_data['perfil_inversion']['nivel']} ({analisis_data['perfil_inversion']['puntaje']}%)")
        pdf.multi_cell(0, 10, txt=analisis_data['perfil_inversion']['analisis'])
        pdf.ln(5)
    
    # Análisis
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Análisis y Recomendaciones:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=analisis_data.get('resumen', ''))
    pdf.ln(5)
    
    # Plan de trabajo
    if 'plan_trabajo' in analisis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Plan de Trabajo Personalizado:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analisis_data['plan_trabajo'])
    
    # Proyección de retiro
    if 'proyeccion_retiro' in analisis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Proyección de Retiro con Bienes Raíces:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analisis_data['proyeccion_retiro']['analisis'])
    
    # Generar el PDF en memoria
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_bytes = pdf_output.getvalue()
    pdf_output.close()
    
    return pdf_bytes

# Crear la base de datos y la tabla de usuarios
def crear_base_datos():
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            edad INTEGER,
            email TEXT,
            telefono TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finanzas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            ingresos_mensuales REAL,
            gastos_mensuales REAL,
            activos_totales REAL,
            pasivos_totales REAL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')
    conn.commit()
    conn.close()

# Registrar un nuevo usuario
def registrar_usuario(nombre, edad, email, telefono):
    if edad < 18:
        st.warning("Debes ser mayor de 18 años para usar este programa.")
        return None
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO usuarios (nombre, edad, email, telefono)
        VALUES (?, ?, ?, ?)
    ''', (nombre, edad, email, telefono))
    usuario_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return usuario_id

# Función para analizar la proyección de retiro con enfoque en bienes raíces
def analizar_proyeccion_retiro_bienes_raices(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro, datos_financieros):
    años_ahorro = edad_retiro - edad_actual
    necesidad_total = (ingresos_retiro - gastos_retiro) * (100 - edad_retiro)  # Estimación simplificada
    ahorro_necesario_anual = (necesidad_total - ahorros_retiro) / años_ahorro if años_ahorro > 0 else 0
    
    # Estrategias específicas para bienes raíces
    ingresos, gastos, activos, pasivos = datos_financieros
    flujo_caja = ingresos - gastos
    
    estrategias = """
    Estrategias con Bienes Raíces para tu Retiro:
    
    1. **Propiedades generadoras de ingreso**:
       - Invierte en propiedades que puedas arrendar para generar flujo mensual
       - Considera propiedades multifamiliares para diversificar riesgo
       
    2. **Apreciación a largo plazo**:
       - Compra propiedades en zonas con potencial de crecimiento
       - Mantén las propiedades hasta tu retiro para beneficiarte de la apreciación
       
    3. **Estrategia BRRRR (Buy, Rehab, Rent, Refinance, Repeat)**:
       - Compra propiedades que necesiten reparaciones menores
       - Renóvalas y refinancia para recuperar tu inversión inicial
       - Repite el proceso para construir un portafolio
    
    4. **Venta gradual en retiro**:
       - Construye un portafolio de varias propiedades
       - Durante el retiro, vende una propiedad cada 5-7 años para complementar ingresos
    """
    
    if flujo_caja > 1000:
        estrategias += """
        \n**Para tu perfil (alto flujo de caja)**:
        - Considera comprar una propiedad cada 2-3 años
        - Usa el flujo de caja excedente para pagar hipotecas más rápido
        """
    elif flujo_caja > 500:
        estrategias += """
        \n**Para tu perfil (flujo de caja moderado)**:
        - Empieza con una propiedad pequeña y escala gradualmente
        - Considera co-inversiones para acceder a mejores propiedades
        """
    else:
        estrategias += """
        \n**Para tu perfil (flujo de caja limitado)**:
        - Enfócate primero en aumentar tus ingresos y reducir gastos
        - Considera propiedades en zonas emergentes con mayor potencial de crecimiento
        """
    
    return {
        "años_ahorro": años_ahorro,
        "necesidad_total": necesidad_total,
        "ahorro_necesario_anual": ahorro_necesario_anual,
        "estrategias_bienes_raices": estrategias,
        "analisis": f"""
        Proyección de Retiro con Bienes Raíces:
        - Años hasta el retiro: {años_ahorro}
        - Necesidad total estimada: {format_currency(necesidad_total)}
        - Ahorros actuales: {format_currency(ahorros_retiro)}
        - Necesitas ahorrar aproximadamente {format_currency(ahorro_necesario_anual)} anuales
        
        Estrategias recomendadas:
        {estrategias}
        """
    }

# Calcular y mostrar el análisis financiero
def analizar_situacion_financiera(ingresos, gastos, activos, pasivos):
    flujo_caja_mensual = ingresos - gastos
    patrimonio_neto = activos - pasivos
    
    st.subheader("📊 Análisis Resumen de tu Situación Financiera Actual")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Ingresos Mensuales", format_currency(ingresos))
        st.metric("Gastos Mensuales", format_currency(gastos))
        st.metric("Flujo de Caja Mensual", format_currency(flujo_caja_mensual), 
                 delta="Positivo" if flujo_caja_mensual > 0 else "Negativo",
                 delta_color="normal" if flujo_caja_mensual > 0 else "inverse")
    
    with col2:
        st.metric("Activos Totales", format_currency(activos))
        st.metric("Pasivos Totales", format_currency(pasivos))
        st.metric("Patrimonio Neto", format_currency(patrimonio_neto), 
                 delta="Positivo" if patrimonio_neto > 0 else "Negativo",
                 delta_color="normal" if patrimonio_neto > 0 else "inverse")
    
    st.subheader("🔍 Análisis")
    if flujo_caja_mensual > 0:
        st.success(f"Tienes un flujo de caja mensual positivo de {format_currency(flujo_caja_mensual)}, lo cual indica que estás generando más ingresos de los que gastas.")
    else:
        st.error(f"Tienes un flujo de caja mensual negativo de {format_currency(flujo_caja_mensual)}, lo cual indica que estás gastando más de lo que generas.")
    
    if patrimonio_neto > 0:
        st.success("Tu patrimonio neto es sólido, lo que sugiere una buena salud financiera en general.")
    else:
        st.error("Tu patrimonio neto es negativo, lo que sugiere que tienes más deudas que activos.")
    
    st.subheader("🚀 Acciones Recomendadas")
    st.write("""
    1. **Maximiza tu flujo de caja**: Considera aumentar tus ingresos o reducir gastos
    2. **Diversifica tus inversiones**: Distribuye tus activos para reducir riesgos
    3. **Crea un presupuesto detallado**: Identifica todos tus gastos
    4. **Establece metas claras**: Define objetivos a corto, mediano y largo plazo
    """)
    
    return {
        "flujo_caja": flujo_caja_mensual,
        "patrimonio": patrimonio_neto,
        "resumen": f"""
        Situación Financiera Actual:
        - Ingresos Mensuales: {format_currency(ingresos)}
        - Gastos Mensuales: {format_currency(gastos)}
        - Flujo de Caja: {format_currency(flujo_caja_mensual)} ({'Positivo' if flujo_caja_mensual > 0 else 'Negativo'})
        - Activos Totales: {format_currency(activos)}
        - Pasivos Totales: {format_currency(pasivos)}
        - Patrimonio Neto: {format_currency(patrimonio_neto)} ({'Positivo' if patrimonio_neto > 0 else 'Negativo'})
        
        Análisis:
        {'Tienes un flujo de caja mensual positivo, lo cual indica que estás generando más ingresos de los que gastas.' if flujo_caja_mensual > 0 else 'Tienes un flujo de caja mensual negativo, lo cual indica que estás gastando más de lo que generas.'}
        {'Tu patrimonio neto es sólido, lo que sugiere una buena salud financiera en general.' if patrimonio_neto > 0 else 'Tu patrimonio neto es negativo, lo que sugiere que tienes más deudas que activos.'}
        """
    }

# Función para determinar perfil de inversión
def determinar_perfil_inversion(ingresos, gastos, activos, pasivos, flujo_caja):
    # Calcular ratios clave
    ratio_deuda_ingresos = (pasivos / ingresos) * 100 if ingresos > 0 else 100
    ratio_ahorro = (flujo_caja / ingresos) * 100 if ingresos > 0 else 0
    patrimonio_neto = activos - pasivos
    
    # Puntaje basado en múltiples factores
    puntaje = 0
    
    # Flujo de caja positivo suma puntos
    if flujo_caja > 0:
        puntaje += 20 + min(20, (flujo_caja / ingresos * 100) if ingresos > 0 else 0)
    
    # Patrimonio neto positivo suma puntos
    if patrimonio_neto > 0:
        puntaje += 20 + min(20, (patrimonio_neto / (activos + 0.01)) * 100)
    
    # Ratio de ahorro suma puntos
    if ratio_ahorro > 10:
        puntaje += min(30, ratio_ahorro)
    
    # Deuda controlada suma puntos
    if ratio_deuda_ingresos < 30:
        puntaje += 30 - ratio_deuda_ingresos
    
    # Ajustar puntaje a rango 0-100
    puntaje = max(0, min(100, puntaje))
    
    # Determinar nivel
    if puntaje >= 70:
        nivel = "Alto"
        analisis = """
        ¡Excelente! Tienes un perfil financiero sólido para comenzar a invertir en bienes raíces. 
        Recomendaciones:
        - Considera estrategias más avanzadas como compra con descuento o propiedades multifamiliares
        - Puedes acceder a financiamiento bancario con buenas condiciones
        - Enfócate en propiedades que generen flujo de caja positivo
        """
    elif puntaje >= 40:
        nivel = "Medio"
        analisis = """
        Tienes potencial para invertir en bienes raíces, pero necesitas hacer algunos ajustes. 
        Recomendaciones:
        - Empieza con propiedades pequeñas y de bajo mantenimiento
        - Considera estrategias como arrendamiento con opción a compra
        - Trabaja en aumentar tu flujo de caja mensual
        - Reduce deudas de alto interés primero
        """
    else:
        nivel = "Bajo"
        analisis = """
        Actualmente tu perfil no es óptimo para inversiones en bienes raíces, pero puedes mejorarlo. 
        Recomendaciones:
        - Enfócate primero en crear un colchón de seguridad
        - Reduce gastos y aumenta ingresos
        - Paga deudas de alto interés
        - Comienza con educación financiera antes de invertir
        """
    
    return {
        "nivel": nivel,
        "puntaje": round(puntaje),
        "analisis": analisis,
        "metricas": {
            "flujo_caja_mensual": flujo_caja,
            "ratio_ahorro": ratio_ahorro,
            "ratio_deuda_ingresos": ratio_deuda_ingresos,
            "patrimonio_neto": patrimonio_neto
        }
    }

# Generar plan de trabajo financiero con OpenAI orientado a bienes raíces
def generar_plan_bienes_raices(ingresos, gastos, activos, pasivos, flujo_caja):
    if not st.session_state.get('openai_configured', False):
        return "Servicio de IA no disponible en este momento. Por favor configura tu clave de OpenAI API en secrets.toml para habilitar esta función."
    
    prompt = f"""
    Como experto en finanzas personales y bienes raíces (siguiendo la metodología de Carlos Devis), 
    analiza esta situación financiera:
    - Ingresos: {format_currency(ingresos)}/mes
    - Gastos: {format_currency(gastos)}/mes
    - Flujo de caja: {format_currency(flujo_caja)}/mes
    - Activos: {format_currency(activos)}
    - Pasivos: {format_currency(pasivos)}
    
    Crea un plan detallado para invertir en bienes raíces que incluya:
    1. Diagnóstico de capacidad de inversión actual
    2. Estrategias para comenzar en bienes raíces según el perfil
    3. Tipos de propiedades recomendadas para empezar
    4. Formas de financiamiento adecuadas
    5. Plan de acción con metas a 3, 6 y 12 meses
    6. Errores comunes a evitar según el perfil
    
    Usa un lenguaje claro y motivador, con ejemplos concretos de estrategias como:
    - Compra con descuento
    - Arrendamiento con opción a compra
    - Propiedades generadoras de flujo
    - Reparación y venta
    
    Respuesta en español, máximo 500 palabras.
    """
    
    try:
        with st.spinner('Generando tu plan de inversión en bienes raíces...'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asesor financiero experto en bienes raíces que ayuda a personas a comenzar a invertir en propiedades. Responde en español siguiendo la metodología de Carlos Devis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error al generar el plan: {str(e)}")
        return "No se pudo generar el plan en este momento."

# Interfaz principal de Streamlit
def main():
    load_css()  # Cargar estilos CSS personalizados
    
    # Encabezado con logo
    st.markdown("""
    <div class="header-container">
        <img src="https://via.placeholder.com/60" class="logo" alt="Logo Financiero">
        <div>
            <h1 style="margin:0;color:#1E3A8A;">Taller de Bienes Raíces</h1>
            <h3 style="margin:0;color:#6B7280;">Carlos Devis</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="calculator-container">
        Esta herramienta te ayudará a analizar tu situación financiera actual, evaluar tu capacidad 
        para invertir en bienes raíces y establecer metas claras para tu futuro económico.
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar variables de sesión para el reporte
    if 'reporte_data' not in st.session_state:
        st.session_state['reporte_data'] = {
            'usuario': {},
            'finanzas': {},
            'analisis': {}
        }
    
    # Paso 1: Registro de usuario
    with st.container():
        st.subheader("📝 Información Personal")
        nombre = st.text_input("Nombre completo", key="nombre_input")
        edad = st.number_input("Edad", min_value=18, max_value=100, value=30, key="edad_input")
        email = st.text_input("Email", key="email_input")
        telefono = st.text_input("Teléfono", key="telefono_input")
        
        if st.button("Guardar información personal", key="guardar_info_btn"):
            if nombre and email:
                usuario_id = registrar_usuario(nombre, edad, email, telefono)
                st.session_state['usuario_id'] = usuario_id
                st.session_state['reporte_data']['usuario'] = {
                    'nombre': nombre,
                    'edad': edad,
                    'email': email,
                    'telefono': telefono
                }
                st.success("Información guardada correctamente")
            else:
                st.warning("Por favor completa todos los campos obligatorios")
    
    # Paso 2: Datos financieros - Activos y Pasivos
    if 'usuario_id' in st.session_state:
        with st.container():
            st.subheader("📊 Elaborar mi presupuesto")
            st.markdown("""
            **Ejercicio:** Comienza por hacer un presupuesto detallado de tus activos y pasivos.
            Identifica los huecos en tu tubería financiera y decide qué pasos tomar para empezar a cubrirlos.
            """)
            
            st.subheader("💰 Activos y Pasivos")
            
            # Definir los tooltips
            tooltips = {
                "Inmueble 1": "Valor de tu primera propiedad (casa, apartamento, terreno)",
                "Inmueble 2": "Valor de tu segunda propiedad (si aplica)",
                "Automóvil 1": "Valor de tu vehículo principal",
                "Automóvil 2": "Valor de tu segundo vehículo (si aplica)",
                "Muebles": "Valor estimado de muebles y enseres",
                "Joyas": "Valor estimado de joyas y artículos de valor",
                "Arte": "Valor de obras de arte o colecciones",
                "Efectivo cuenta 1": "Saldo disponible en tu cuenta principal",
                "Efectivo cuenta 2": "Saldo disponible en cuentas secundarias",
                "Deudas por cobrar": "Dinero que te deben otras personas/empresas",
                "Bonos o títulos valores": "Inversiones en bonos o instrumentos financieros",
                "Fondo de retiro": "Ahorros acumulados en fondos de pensiones",
                "Bonos o derechos laborales": "Beneficios acumulados en tu trabajo",
                "Tarjeta de crédito 1": "Saldo pendiente en tu tarjeta principal",
                "Tarjeta de crédito 2": "Saldo pendiente en tarjetas secundarias",
                "Tarjeta de crédito 3": "Otras deudas con tarjetas de crédito",
                "Otra deuda 1": "Otros préstamos o deudas personales",
                "Otra deuda 2": "Obligaciones financieras adicionales",
                "Otra deuda 3": "Cualquier otra deuda no contemplada",
                "Otros": "Otros activos o pasivos no listados"
            }
            
            # Lista de activos y pasivos
            items = [
                "Inmueble 1", "Inmueble 2", "Automóvil 1", "Automóvil 2", 
                "Muebles", "Joyas", "Arte", "Efectivo cuenta 1", 
                "Efectivo cuenta 2", "Deudas por cobrar", "Bonos o títulos valores",
                "Fondo de retiro", "Bonos o derechos laborales", "Tarjeta de crédito 1",
                "Tarjeta de crédito 2", "Tarjeta de crédito 3", "Otra deuda 1",
                "Otra deuda 2", "Otra deuda 3", "Otros"
            ]
            
            # Inicializar valores en session_state si no existen
            if 'finanzas_values' not in st.session_state:
                st.session_state['finanzas_values'] = {
                    item: {'valor': 0.0, 'deuda': 0.0, 'activo': 0.0} for item in items
                }
            
            # Crear tabla con pandas para mejor manejo
            df = pd.DataFrame(columns=['Descripción', 'Valor', 'Deuda', 'Activos'])
            
            # Llenar la tabla con inputs
            for idx, item in enumerate(items):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    # Agregar tooltip con información
                    st.markdown(f"""
                    <div title="{tooltips.get(item, '')}">
                        {item} <span style="color: #6B7280; font-size: 0.8em;">(?)</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    valor = st.text_input(
                        f"Valor {item} ($)", 
                        value=format_currency(st.session_state['finanzas_values'][item]['valor']),
                        key=f"valor_{idx}_{item}",
                        label_visibility="collapsed"
                    )
                    st.session_state['finanzas_values'][item]['valor'] = parse_currency(valor)
                
                with col3:
                    # Solo mostrar campo deuda para activos (no para pasivos)
                    if item not in ["Tarjeta de crédito 1", "Tarjeta de crédito 2", "Tarjeta de crédito 3", 
                                   "Otra deuda 1", "Otra deuda 2", "Otra deuda 3"]:
                        deuda = st.text_input(
                            f"Deuda {item} ($)", 
                            value=format_currency(st.session_state['finanzas_values'][item]['deuda']),
                            key=f"deuda_{idx}_{item}",
                            label_visibility="collapsed"
                        )
                        st.session_state['finanzas_values'][item]['deuda'] = parse_currency(deuda)
                    else:
                        st.text_input(
                            "", 
                            value="", 
                            disabled=True, 
                            key=f"disabled_{idx}_{item}",
                            label_visibility="collapsed"
                        )
                
                # Calcular activos automáticamente (Valor - Deuda)
                valor_num = st.session_state['finanzas_values'][item]['valor']
                deuda_num = st.session_state['finanzas_values'][item]['deuda']
                st.session_state['finanzas_values'][item]['activo'] = max(0, valor_num - deuda_num)
                
                # Agregar fila al DataFrame
                df.loc[len(df)] = [
                    item,
                    st.session_state['finanzas_values'][item]['valor'],
                    st.session_state['finanzas_values'][item]['deuda'],
                    st.session_state['finanzas_values'][item]['activo']
                ]
            
            # Calcular totales
            total_valor = df['Valor'].sum()
            total_deuda = df['Deuda'].sum() + df[df['Descripción'].isin([
                "Tarjeta de crédito 1", "Tarjeta de crédito 2", "Tarjeta de crédito 3",
                "Otra deuda 1", "Otra deuda 2", "Otra deuda 3"
            ])]['Valor'].sum()
            total_activos = df['Activos'].sum()
            
            # Agregar fila de totales
            df.loc[len(df)] = ['Total', total_valor, total_deuda, total_activos]
            
            # Mostrar tabla
            st.table(df.style.format({
                'Valor': lambda x: format_currency(x),
                'Deuda': lambda x: format_currency(x),
                'Activos': lambda x: format_currency(x)
            }).applymap(lambda x: 'color: green' if isinstance(x, (int, float)) and x > 0 else 'color: black'))
            
            # Flujo de caja mensual
            st.subheader("💸 Flujo de Caja Mensual")
            
            # Tooltips para flujo de caja
            flujo_tooltips = {
                "Ingresos mensuales adulto 1": "Salario, ingresos por negocios o inversiones del primer adulto en el hogar",
                "Ingresos mensuales adulto 2": "Salario, ingresos por negocios o inversiones del segundo adulto en el hogar",
                "Otros ingresos": "Ingresos adicionales como alquileres, intereses, dividendos, etc.",
                "Gasto de Inmueble 1": "Todos los gastos relacionados con tu primera propiedad (hipoteca, impuestos, mantenimiento)",
                "Gasto de Inmueble 2": "Gastos de tu segunda propiedad (si aplica)",
                "Alimentación": "Supermercado, restaurantes, comida en general",
                "Educación": "Colegiatura, materiales, cursos, etc.",
                "Transporte": "Gasolina, transporte público, mantenimiento de vehículos",
                "Salud": "Seguros médicos, medicinas, consultas",
                "Entretenimiento": "Salidas, suscripciones, hobbies",
                "Servicios públicos": "Luz, agua, gas, internet, teléfono",
                "Seguros": "Seguros de vida, vehiculares, de hogar, etc.",
                "Otros gastos": "Cualquier otro gasto no categorizado"
            }
            
            # Inicializar valores en session_state si no existen
            if 'ingresos_values' not in st.session_state:
                st.session_state['ingresos_values'] = {
                    "Ingresos mensuales adulto 1": 0.0,
                    "Ingresos mensuales adulto 2": 0.0,
                    "Otros ingresos": 0.0
                }
            
            if 'gastos_values' not in st.session_state:
                st.session_state['gastos_values'] = {
                    "Gasto de Inmueble 1": 0.0,
                    "Gasto de Inmueble 2": 0.0,
                    "Alimentación": 0.0,
                    "Educación": 0.0,
                    "Transporte": 0.0,
                    "Salud": 0.0,
                    "Entretenimiento": 0.0,
                    "Servicios públicos": 0.0,
                    "Seguros": 0.0,
                    "Otros gastos": 0.0
                }
            
            # Ingresos con tooltips
            st.markdown("<h4>Ingresos</h4>", unsafe_allow_html=True)
            ingresos_total = 0.0
            
            for idx, item in enumerate(st.session_state['ingresos_values']):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    <div title="{flujo_tooltips.get(item, '')}">
                        {item} <span style="color: #6B7280; font-size: 0.8em;">(?)</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    value = st.text_input(
                        f"{item} ($)", 
                        value=format_currency(st.session_state['ingresos_values'][item]),
                        key=f"ingreso_{idx}_{item}",
                        label_visibility="collapsed"
                    )
                    parsed_value = parse_currency(value)
                    st.session_state['ingresos_values'][item] = parsed_value
                    ingresos_total += parsed_value
            
            # Gastos con tooltips
            st.markdown("<h4>Gastos</h4>", unsafe_allow_html=True)
            gastos_total = 0.0
            
            for idx, item in enumerate(st.session_state['gastos_values']):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    <div title="{flujo_tooltips.get(item, '')}">
                        {item} <span style="color: #6B7280; font-size: 0.8em;">(?)</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    value = st.text_input(
                        f"{item} ($)", 
                        value=format_currency(st.session_state['gastos_values'][item]),
                        key=f"gasto_{idx}_{item}",
                        label_visibility="collapsed"
                    )
                    parsed_value = parse_currency(value)
                    st.session_state['gastos_values'][item] = parsed_value
                    gastos_total += parsed_value
            
            # Calcular saldo mensual
            saldo_mensual = ingresos_total - gastos_total
            
            # Mostrar resumen de flujo de caja
            st.markdown(f"""
            <div class="calculator-container">
                <h4>Resumen Flujo de Caja</h4>
                <p><strong>Total Ingresos:</strong> <span class="positive-value">{format_currency(ingresos_total)}</span></p>
                <p><strong>Total Gastos:</strong> <span class="negative-value">{format_currency(gastos_total)}</span></p>
                <p><strong>Saldo Mensual:</strong> <span class="{ 'positive-value' if saldo_mensual >= 0 else 'negative-value' }">{format_currency(saldo_mensual)}</span></p>
                <p><strong>Porcentaje para inversión:</strong> {format_currency(saldo_mensual)} ({saldo_mensual/ingresos_total*100:.1f}% de tus ingresos)</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Analizar mi situación financiera", key="analizar_finanzas_btn"):
                activos_total = total_activos
                pasivos_total = total_deuda
                
                st.session_state['datos_financieros'] = (ingresos_total, gastos_total, activos_total, pasivos_total)
                analisis = analizar_situacion_financiera(ingresos_total, gastos_total, activos_total, pasivos_total)
                st.session_state['reporte_data']['finanzas'] = {
                    'ingresos': ingresos_total,
                    'gastos': gastos_total,
                    'activos': activos_total,
                    'pasivos': pasivos_total
                }
                st.session_state['reporte_data']['analisis']['resumen'] = analisis['resumen']
                
                # Generar y mostrar plan de trabajo con enfoque en bienes raíces
                plan = generar_plan_bienes_raices(ingresos_total, gastos_total, activos_total, pasivos_total, saldo_mensual)
                st.subheader("📝 Plan de Inversión en Bienes Raíces")
                st.write(plan)
                st.session_state['reporte_data']['analisis']['plan_trabajo'] = plan
                
                # Determinar perfil de inversión
                perfil = determinar_perfil_inversion(ingresos_total, gastos_total, activos_total, pasivos_total, saldo_mensual)
                st.session_state['reporte_data']['analisis']['perfil_inversion'] = perfil
                
                st.subheader("🧐 Perfil de Inversión en Bienes Raíces")
                if perfil['nivel'] == "Alto":
                    st.success(f"✅ Perfil de Inversión: {perfil['nivel']} ({perfil['puntaje']}%)")
                elif perfil['nivel'] == "Medio":
                    st.warning(f"⚠️ Perfil de Inversión: {perfil['nivel']} ({perfil['puntaje']}%)")
                else:
                    st.error(f"❌ Perfil de Inversión: {perfil['nivel']} ({perfil['puntaje']}%)")
                
                st.write(perfil['analisis'])
                
                # Recomendaciones de cursos
                st.subheader("🎓 Recomendaciones de Educación Financiera")
                st.markdown("""
                Para mejorar tu perfil de inversionista en bienes raíces, te recomendamos los siguientes recursos de Carlos Devis:
                
                - [Ciclo Educativo de Bienes Raíces](https://landing.tallerdebienesraices.com/registro-ciclo-educativo/)
                - [Cómo empezar en bienes raíces con poco dinero](https://www.youtube.com/@carlosdevis)
                - [Estrategias para encontrar propiedades con descuento](https://www.youtube.com/playlist?list=PL2qGhDf0PEjSF5zxLMa6SlVUxPd4273tl)
                - [Cómo financiar tu primera propiedad](https://www.youtube.com/playlist?list=PL2qGhDf0PEjT9Jy7ULNGfFQvTsruUAyCe)
                
                Estos cursos te ayudarán a desarrollar las habilidades necesarias para invertir con éxito.
                """)
    
    # Paso 3: Plan de retiro con enfoque en bienes raíces
    if 'datos_financieros' in st.session_state:
        with st.container():
            st.subheader("👴 Plan de Retiro con Bienes Raíces")
            
            col1, col2 = st.columns(2)
            edad_actual = col1.number_input("Tu edad actual", min_value=18, max_value=100, value=30, key="edad_actual_input")
            edad_retiro = col2.number_input("Edad de retiro deseada", min_value=edad_actual+1, max_value=100, value=65, key="edad_retiro_input")
            
            ingresos_retiro = parse_currency(
                st.text_input("Ingresos anuales esperados durante el retiro ($)", value="$40,000", key="ingresos_retiro_input")
            )
            gastos_retiro = parse_currency(
                st.text_input("Gastos anuales esperados durante el retiro ($)", value="$30,000", key="gastos_retiro_input")
            )
            ahorros_retiro = parse_currency(
                st.text_input("Ahorros actuales para el retiro ($)", value="$10,000", key="ahorros_retiro_input")
            )
            
            if st.button("Calcular proyección de retiro", key="calcular_retiro_btn"):
                analisis = analizar_proyeccion_retiro_bienes_raices(
                    edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, 
                    ahorros_retiro, st.session_state['datos_financieros']
                )
                st.session_state['reporte_data']['analisis']['proyeccion_retiro'] = analisis
                
                st.subheader("📊 Proyección de Retiro con Bienes Raíces")
                st.write(f"**Años hasta el retiro:** {analisis['años_ahorro']}")
                st.write(f"**Necesidad total estimada:** {format_currency(analisis['necesidad_total'])}")
                st.write(f"**Ahorros actuales:** {format_currency(ahorros_retiro)}")
                st.write(f"**Necesitas ahorrar aproximadamente:** {format_currency(analisis['ahorro_necesario_anual'])} anuales")
                
                st.subheader("🏡 Estrategias con Bienes Raíces")
                st.write(analisis['estrategias_bienes_raices'])
                
                st.subheader("📚 Cursos Recomendados")
                st.markdown("""
                Para construir un portafolio de propiedades que genere ingresos pasivos para tu retiro:
                
                - [Cómo crear ingresos pasivos con bienes raíces](https://www.youtube.com/@carlosdevis)
                - [Administración de propiedades rentables](https://www.youtube.com/playlist?list=PL2qGhDf0PEjSF5zxLMa6SlVUxPd4273tl)
                - [Estrategias de inversión a largo plazo](https://www.youtube.com/playlist?list=PL2qGhDf0PEjT9Jy7ULNGfFQvTsruUAyCe)
                """)
    
    # Botón para descargar PDF
    if 'reporte_data' in st.session_state and st.session_state['reporte_data']['usuario']:
        if st.button("📄 Descargar Reporte Completo en PDF", key="descargar_pdf_btn"):
            pdf_bytes = generate_pdf(
                st.session_state['reporte_data']['usuario'],
                st.session_state['reporte_data']['finanzas'],
                st.session_state['reporte_data']['analisis']
            )
            
            st.success("Reporte generado con éxito!")
            
            # Crear enlace de descarga
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="reporte_bienes_raices.pdf">Haz clic aquí para descargar tu reporte</a>'
            st.markdown(href, unsafe_allow_html=True)
    
    # Pie de página
    st.markdown("---")
    st.markdown("""
    <div class="calculator-container">
        <h3>📌 Recomendaciones Finales</h3>
        <ul>
            <li>Revisa periódicamente tu situación financiera</li>
            <li>Considera invertir en educación financiera con los cursos de Carlos Devis</li>
            <li>Empieza con pequeñas inversiones y escala gradualmente</li>
        </ul>
        <p>Visita <a href="https://www.youtube.com/@carlosdevis" target="_blank">el canal de YouTube</a> para más consejos sobre inversión en bienes raíces.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    crear_base_datos()
    main()