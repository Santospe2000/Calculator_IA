import streamlit as st
from openai import OpenAI
import sqlite3
from fpdf import FPDF
import base64
from io import BytesIO
import re
import os

# Configuración del cliente de OpenAI
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    st.session_state['openai_configured'] = True
except Exception as e:
    st.error(f"Error al configurar OpenAI: {str(e)}")
    st.session_state['openai_configured'] = False
    client = None

# Configuración inicial de la página con estilos personalizados
st.set_page_config(
    page_title="Analista IA Financiero Carlos Devis",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados para el formato de calculadora financiera
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
    return f"${value:,.2f}" if value else "$0.00"

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
    pdf.cell(200, 10, txt="Informe Financiero Personalizado", ln=1, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Analista IA Financiero Carlos Devis", ln=1, align='C')
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

# Función para analizar la proyección de retiro
def analizar_proyeccion_retiro(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro):
    años_ahorro = edad_retiro - edad_actual
    necesidad_total = (ingresos_retiro - gastos_retiro) * (100 - edad_retiro)  # Estimación simplificada
    ahorro_necesario_anual = (necesidad_total - ahorros_retiro) / años_ahorro if años_ahorro > 0 else 0
    
    return {
        "años_ahorro": años_ahorro,
        "necesidad_total": necesidad_total,
        "ahorro_necesario_anual": ahorro_necesario_anual,
        "analisis": f"""
        Proyección de Retiro:
        - Años hasta el retiro: {años_ahorro}
        - Necesidad total estimada: {format_currency(necesidad_total)}
        - Ahorros actuales: {format_currency(ahorros_retiro)}
        - Necesitas ahorrar aproximadamente {format_currency(ahorro_necesario_anual)} anuales para alcanzar tu meta.
        
        Recomendaciones:
        1. Considera aumentar tus aportes a fondos de retiro
        2. Diversifica tus inversiones para el largo plazo
        3. Revisa periódicamente tu plan de retiro
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

# Generar plan de trabajo financiero con OpenAI
def generar_plan_trabajo(ingresos, gastos, activos, pasivos):
    if not st.session_state.get('openai_configured'):
        return "Servicio de IA no disponible en este momento."
    
    prompt = f"""
    Como experto en finanzas personales, analiza la situación financiera con estos datos:
    - Ingresos: {format_currency(ingresos)}/mes
    - Gastos: {format_currency(gastos)}/mes
    - Activos: {format_currency(activos)}
    - Pasivos: {format_currency(pasivos)}
    
    Crea un plan detallado que incluya:
    1. Diagnóstico claro de la situación actual
    2. Estrategias para mejorar el flujo de caja
    3. Plan de reducción de deudas (si aplica)
    4. Recomendaciones de inversión personalizadas
    5. Metas a corto (3 meses), mediano (1 año) y largo plazo (5+ años)
    6. Ejercicios prácticos para implementar el plan
    
    Usa un lenguaje claro y motivador, con ejemplos concretos.
    Respuesta en español.
    """
    
    try:
        with st.spinner('Generando tu plan personalizado...'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asesor financiero experto que ayuda a personas a mejorar sus finanzas personales. Responde en español."},
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
            <h1 style="margin:0;color:#1E3A8A;">Analista IA Financiero</h1>
            <h3 style="margin:0;color:#6B7280;">Carlos Devis</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="calculator-container">
        Esta herramienta te ayudará a analizar tu situación financiera actual, crear un plan de acción 
        y establecer metas claras para tu futuro económico.
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
        nombre = st.text_input("Nombre completo")
        edad = st.number_input("Edad", min_value=18, max_value=100, value=30)
        email = st.text_input("Email")
        telefono = st.text_input("Teléfono")
        
        if st.button("Guardar información personal"):
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
            **Ejercicio:** Comienza tú también por hacer un presupuesto detallado de tu
            gasto diario y mensual, tanto el tuyo como el de cada una de las
            personas de tu familia. Mira los extractos de las cuentas y las
            tarjetas de débito y crédito, y anota también todo lo que gastas en
            efectivo. A partir de esta información, determina cuáles son los
            huecos que tiene tu tubería financiera y decide qué pasos tomar
            para empezar a cubrirlos. Una vez que encuentres el problema…
            ¡Manos a la obra!
            """)
            
            st.subheader("💰 Activos y Pasivos")
            
            # Lista de activos y pasivos
            activos_items = [
                "Inmueble 1", "Inmueble 2", "Automóvil 1", "Automóvil 2", 
                "Muebles", "Joyas", "Arte", "Efectivo cuenta 1", 
                "Efectivo cuenta 2", "Deudas por cobrar", "Bonos o títulos valores",
                "Fondo de retiro", "Bonos o derechos laborales"
            ]
            
            pasivos_items = [
                "Tarjeta de crédito 1", "Tarjeta de crédito 2", "Tarjeta de crédito 3",
                "Otra deuda 1", "Otra deuda 2", "Otra deuda 3", "Otros"
            ]
            
            # Inicializar valores en session_state si no existen
            if 'activos_values' not in st.session_state:
                st.session_state['activos_values'] = {item: 0.0 for item in activos_items}
            
            if 'pasivos_values' not in st.session_state:
                st.session_state['pasivos_values'] = {item: 0.0 for item in pasivos_items}
            
            # Tabla de activos
            st.markdown("<h4>Activos</h4>", unsafe_allow_html=True)
            activos_total = 0.0
            
            cols = st.columns(2)
            for i, item in enumerate(activos_items):
                col = cols[0] if i < len(activos_items)/2 else cols[1]
                value = col.text_input(
                    f"{item} ($)", 
                    value=format_currency(st.session_state['activos_values'][item]),
                    key=f"activo_{item}"
                )
                parsed_value = parse_currency(value)
                st.session_state['activos_values'][item] = parsed_value
                activos_total += parsed_value
            
            # Tabla de pasivos
            st.markdown("<h4>Pasivos</h4>", unsafe_allow_html=True)
            pasivos_total = 0.0
            
            cols = st.columns(2)
            for i, item in enumerate(pasivos_items):
                col = cols[0] if i < len(pasivos_items)/2 else cols[1]
                value = col.text_input(
                    f"{item} ($)", 
                    value=format_currency(st.session_state['pasivos_values'][item]),
                    key=f"pasivo_{item}"
                )
                parsed_value = parse_currency(value)
                st.session_state['pasivos_values'][item] = parsed_value
                pasivos_total += parsed_value
            
            # Mostrar totales
            st.markdown(f"""
            <div class="calculator-container">
                <h4>Totales</h4>
                <p><strong>Total Activos:</strong> <span class="positive-value">{format_currency(activos_total)}</span></p>
                <p><strong>Total Pasivos:</strong> <span class="negative-value">{format_currency(pasivos_total)}</span></p>
                <p><strong>Patrimonio Neto:</strong> {format_currency(activos_total - pasivos_total)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Flujo de caja mensual
            st.subheader("💸 Flujo de Caja Mensual")
            
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
            
            # Ingresos
            st.markdown("<h4>Ingresos</h4>", unsafe_allow_html=True)
            ingresos_total = 0.0
            
            for item in st.session_state['ingresos_values']:
                value = st.text_input(
                    f"{item} ($)", 
                    value=format_currency(st.session_state['ingresos_values'][item]),
                    key=f"ingreso_{item}"
                )
                parsed_value = parse_currency(value)
                st.session_state['ingresos_values'][item] = parsed_value
                ingresos_total += parsed_value
            
            # Gastos
            st.markdown("<h4>Gastos</h4>", unsafe_allow_html=True)
            gastos_total = 0.0
            
            cols = st.columns(2)
            for i, item in enumerate(st.session_state['gastos_values']):
                col = cols[0] if i < len(st.session_state['gastos_values'])/2 else cols[1]
                value = col.text_input(
                    f"{item} ($)", 
                    value=format_currency(st.session_state['gastos_values'][item]),
                    key=f"gasto_{item}"
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
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Analizar mi situación financiera"):
                st.session_state['datos_financieros'] = (ingresos_total, gastos_total, activos_total, pasivos_total)
                analisis = analizar_situacion_financiera(ingresos_total, gastos_total, activos_total, pasivos_total)
                st.session_state['reporte_data']['finanzas'] = {
                    'ingresos': ingresos_total,
                    'gastos': gastos_total,
                    'activos': activos_total,
                    'pasivos': pasivos_total
                }
                st.session_state['reporte_data']['analisis']['resumen'] = analisis['resumen']
                
                # Generar y mostrar plan de trabajo
                plan = generar_plan_trabajo(ingresos_total, gastos_total, activos_total, pasivos_total)
                st.subheader("📝 Plan de Trabajo Financiero Personalizado")
                st.write(plan)
                st.session_state['reporte_data']['analisis']['plan_trabajo'] = plan
    
    # Paso 3: Plan de inversión
    if 'datos_financieros' in st.session_state:
        with st.container():
            st.subheader("📈 Plan de Inversión")
            
            # Sección de tips como habladores
            with st.expander("💡 CÓMO ENCONTRAR LOS RECURSOS PARA INVERTIR"):
                st.markdown("""
                <div class="tips-container">
                    Uno de los argumentos que más escucho es: «Me gustaría invertir en bienes raíces, pero no tengo dinero».
                    
                    **1. Organiza tu presupuesto**  
                    Dice la psicología Gestalt que para lograr lo que quieres debes comenzar por valorar y agradecer lo que ya tienes: la fortuna más grande comenzó con un simple dólar.
                    
                    **2. Ordeña tu negocio**  
                    Recuerdo cuando tenía una empresa con 300 empleados y muchas quincenas sufría para poder pagar los salarios, rogándole al banco que me prestara dinero o a los clientes que pagaran lo que debían, para aun al final llegar a casa sin un centavo para mi familia.
                    
                    **3. Vende cosas que no estás usando**  
                    ¿Cuántas cosas tienes en tu armario o en tu garaje que no estás usando y que probablemente nunca usarás? Ese automóvil, bote, moto... todo se puede vender y convertir en liquidez para tu próxima propiedad.
                    
                    **Aprende a vender mejor tu talento o producto**  
                    Belén tiene 28 años y estudió una carrera técnica para ayudar a las mujeres a prepararse mejor para el parto y que tengan menos dolor, aplicando técnicas sencillas para cuidar más de los cuerpos de las madres y la salud de los bebés.
                    
                    **4. Vende bienes raíces**  
                    Una manera que yo les sugiero a mis alumnos para que aprendan de bienes raíces, ganen algo de dinero y encuentren oportunidades, es que se vuelvan agentes de bienes raíces, que se acerquen a varias oficinas y digan que quieren trabajar en ello.
                    
                    **5. Ofrece tus servicios profesionales**  
                    Ingrid es arquitecta y vive en Berlín. Pensaba que para ella comprar un apartamento en esa ciudad era imposible y con su esposo hacían lo posible para llegar a fin de mes.
                    
                    **6. Cambia de trabajo**  
                    Cuando alguien me cuenta que no le gusta su trabajo o que no le pagan bien, yo le pregunto:  
                    —¿Has buscado otro trabajo?  
                    —Sí, estoy pensando en cambiar —me responde normalmente la persona.
                    
                    **7. Auto promuévete dentro de tu propia empresa**  
                    No siempre es necesario salir de la empresa, a veces es posible buscar un cambio dentro de ella. Habla, prepárate para lo que quieres conseguir y mantén el foco, la actitud y las acciones para lograrlo.
                    
                    **8. Sal de todos los «negocios» que no te están produciendo**  
                    Recuerdo una historia que se cuenta mucho de un borrachito que decía: «¡Pero, cómo voy a dejar el trago después de toda la plata que he gastado!».
                    
                    **9. Cambia tu automóvil por una cuota inicial**  
                    Para la mentalidad del consumidor es muy importante tener un buen automóvil, «El auto del año» como le dicen los vendedores. No te imaginas cuántas familias arruinan su capacidad de crecer financieramente porque aceptan unas cuotas desproporcionadas para sus ingresos solo por poder comprarse «un buen auto».
                </div>
                """, unsafe_allow_html=True)
            
            objetivos = st.text_input("Objetivos financieros (ej: comprar casa, retiro temprano)", 
                                    "Crear fuentes de ingreso pasivo")
            horizonte = st.selectbox("Horizonte de inversión", 
                                   ["Corto plazo (1-3 años)", "Mediano plazo (3-5 años)", "Largo plazo (5+ años)"])
            preferencias = st.multiselect("Preferencias de inversión", 
                                        ["Bienes raíces", "Acciones", "Bonos", "Fondos", "Formación", "Negocios"])
            
            if st.button("Analizar plan de inversión"):
                st.session_state['plan_inversion'] = (objetivos, horizonte, ", ".join(preferencias))
                ingresos, gastos, activos, pasivos = st.session_state['datos_financieros']
                analisis_ia = generar_plan_trabajo(ingresos, gastos, activos, pasivos)
                
                st.subheader("🧠 Análisis Profundo con Inteligencia Artificial")
                st.write(analisis_ia)
                st.session_state['reporte_data']['analisis']['analisis_ia'] = analisis_ia
    
    # Paso 4: Plan de retiro
    if 'usuario_id' in st.session_state:
        with st.container():
            st.subheader("👴 Plan de Retiro")
            
            col1, col2 = st.columns(2)
            edad_actual = col1.number_input("Tu edad actual", min_value=18, max_value=100, value=30)
            edad_retiro = col2.number_input("Edad de retiro deseada", min_value=edad_actual+1, max_value=100, value=65)
            
            ingresos_retiro = parse_currency(
                st.text_input("Ingresos anuales esperados durante el retiro ($)", value="$40,000")
            )
            gastos_retiro = parse_currency(
                st.text_input("Gastos anuales esperados durante el retiro ($)", value="$30,000")
            )
            ahorros_retiro = parse_currency(
                st.text_input("Ahorros actuales para el retiro ($)", value="$10,000")
            )
            
            if st.button("Calcular proyección de retiro"):
                analisis = analizar_proyeccion_retiro(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro)
                st.session_state['reporte_data']['analisis']['proyeccion_retiro'] = analisis
                
                st.subheader("📊 Proyección de Retiro")
                st.write(f"**Años hasta el retiro:** {analisis['años_ahorro']}")
                st.write(f"**Necesidad total estimada:** {format_currency(analisis['necesidad_total'])}")
                st.write(f"**Ahorros actuales:** {format_currency(ahorros_retiro)}")
                st.write(f"**Necesitas ahorrar aproximadamente:** {format_currency(analisis['ahorro_necesario_anual'])} anuales")
                
                st.subheader("📌 Recomendaciones")
                st.write("1. Considera aumentar tus aportes a fondos de retiro")
                st.write("2. Diversifica tus inversiones para el largo plazo")
                st.write("3. Revisa periódicamente tu plan de retiro")
    
    # Botón para descargar PDF
    if 'reporte_data' in st.session_state and st.session_state['reporte_data']['usuario']:
        if st.button("📄 Descargar Reporte Completo en PDF"):
            pdf_bytes = generate_pdf(
                st.session_state['reporte_data']['usuario'],
                st.session_state['reporte_data']['finanzas'],
                st.session_state['reporte_data']['analisis']
            )
            
            st.success("Reporte generado con éxito!")
            
            # Crear enlace de descarga
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="reporte_financiero.pdf">Haz clic aquí para descargar tu reporte</a>'
            st.markdown(href, unsafe_allow_html=True)
    
    # Pie de página
    st.markdown("---")
    st.markdown("""
    <div class="calculator-container">
        <h3>📌 Recomendaciones Finales</h3>
        <ul>
            <li>Revisa periódicamente tu situación financiera</li>
            <li>Implementa los cambios de manera consistente</li>
            <li>Considera asesoría profesional para estrategias avanzadas</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    crear_base_datos()
    main()