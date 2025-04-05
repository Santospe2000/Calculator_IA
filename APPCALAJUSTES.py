import streamlit as st
from openai import OpenAI
import sqlite3
from fpdf import FPDF
import base64
from io import BytesIO

# Configuración del cliente de OpenAI (versión más robusta)
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

# Estilos CSS personalizados para los colores de tu marca
def load_css():
    st.markdown("""
    <style>
        :root {
            --azul-oscuro: #1E3A8A;
            --gris: #6B7280;
            --blanco: #FFFFFF;
        }
        
        .stApp {
            max-width: 800px;
            margin: auto;
            font-family: 'Arial', sans-serif;
        }
        
        .stButton>button {
            background-color: var(--azul-oscuro);
            color: white;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: bold;
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
        
        .stMarkdown h1 {
            color: var(--azul-oscuro);
        }
        
        .stMetric {
            border-left: 4px solid var(--azul-oscuro);
            padding-left: 12px;
        }
        
        .stSuccess {
            background-color: #D1FAE5;
            color: #065F46;
            border-radius: 8px;
            padding: 12px;
        }
        
        .stError {
            background-color: #FEE2E2;
            color: #B91C1C;
            border-radius: 8px;
            padding: 12px;
        }
        
        .logo-container {
            position: absolute;
            top: 10px;
            right: 10px;
        }
        
        .data-table {
            width: 100%;
            margin-bottom: 20px;
            border-collapse: collapse;
        }
        
        .data-table th, .data-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        .data-table th {
            background-color: #f2f2f2;
        }
        
        .data-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .tips-container {
            background-color: #f8f9fa;
            border-left: 4px solid var(--azul-oscuro);
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 0 8px 8px 0;
        }
        
        @media (max-width: 768px) {
            .logo-container {
                position: static;
                text-align: center;
                margin-bottom: 20px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

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
    pdf.cell(200, 10, txt=f"Ingresos Mensuales: ${finanzas_data.get('ingresos', 0):,.2f}", ln=1)
    pdf.cell(200, 10, txt=f"Gastos Mensuales: ${finanzas_data.get('gastos', 0):,.2f}", ln=1)
    pdf.cell(200, 10, txt=f"Activos Totales: ${finanzas_data.get('activos', 0):,.2f}", ln=1)
    pdf.cell(200, 10, txt=f"Pasivos Totales: ${finanzas_data.get('pasivos', 0):,.2f}", ln=1)
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

# Calcular y mostrar el análisis financiero
def analizar_situacion_financiera(ingresos, gastos, activos, pasivos):
    flujo_caja_mensual = ingresos - gastos
    patrimonio_neto = activos - pasivos
    
    st.subheader("Análisis Resumen de tu Situación Financiera Actual")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Ingresos Mensuales", f"${ingresos:,.2f}")
        st.metric("Gastos Mensuales", f"${gastos:,.2f}")
        st.metric("Flujo de Caja Mensual", f"${flujo_caja_mensual:,.2f}", 
                 delta="Positivo" if flujo_caja_mensual > 0 else "Negativo")
    
    with col2:
        st.metric("Activos Totales", f"${activos:,.2f}")
        st.metric("Pasivos Totales", f"${pasivos:,.2f}")
        st.metric("Patrimonio Neto", f"${patrimonio_neto:,.2f}", 
                 delta="Positivo" if patrimonio_neto > 0 else "Negativo")
    
    st.subheader("Análisis")
    if flujo_caja_mensual > 0:
        st.success(f"Tienes un flujo de caja mensual positivo de ${flujo_caja_mensual:,.2f}, lo cual indica que estás generando más ingresos de los que gastas.")
    else:
        st.error(f"Tienes un flujo de caja mensual negativo de ${flujo_caja_mensual:,.2f}, lo cual indica que estás gastando más de lo que generas.")
    
    if patrimonio_neto > 0:
        st.success("Tu patrimonio neto es sólido, lo que sugiere una buena salud financiera en general.")
    else:
        st.error("Tu patrimonio neto es negativo, lo que sugiere que tienes más deudas que activos.")
    
    st.subheader("Acciones Recomendadas")
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
        - Ingresos Mensuales: ${ingresos:,.2f}
        - Gastos Mensuales: ${gastos:,.2f}
        - Flujo de Caja: ${flujo_caja_mensual:,.2f} ({'Positivo' if flujo_caja_mensual > 0 else 'Negativo'})
        - Activos Totales: ${activos:,.2f}
        - Pasivos Totales: ${pasivos:,.2f}
        - Patrimonio Neto: ${patrimonio_neto:,.2f} ({'Positivo' if patrimonio_neto > 0 else 'Negativo'})
        
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
    - Ingresos: ${ingresos}/mes
    - Gastos: ${gastos}/mes
    - Activos: ${activos}
    - Pasivos: ${pasivos}
    
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

# Analizar y mostrar el plan de inversión
def analizar_plan_inversion(objetivos, horizonte, preferencias):
    st.subheader("Análisis de tu Plan de Inversión")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Objetivos", objetivos)
    col2.metric("Horizonte", horizonte)
    col3.metric("Preferencias", preferencias)
    
    st.subheader("Análisis Detallado")
    if "corto plazo" in horizonte.lower():
        st.write("""
        - **Horizonte corto**: Considera inversiones líquidas y de bajo riesgo
        - **Opciones recomendadas**: Fondos del mercado monetario, certificados de depósito
        """)
    else:
        st.write("""
        - **Horizonte largo**: Puedes considerar inversiones con mayor potencial de crecimiento
        - **Opciones recomendadas**: Índices bursátiles, bienes raíces, fondos de inversión
        """)
    
    if "bienes raíces" in preferencias.lower():
        st.write("""
        - **Bienes raíces**: Excelente para generar ingresos pasivos
        - **Recomendación**: Investiga el mercado local y considera propiedades en zonas con crecimiento
        """)
    
    return {
        "objetivos": objetivos,
        "horizonte": horizonte,
        "preferencias": preferencias,
        "resumen": f"""
        Plan de Inversión:
        - Objetivos: {objetivos}
        - Horizonte: {horizonte}
        - Preferencias: {preferencias}
        
        Recomendaciones:
        {'Para horizonte corto, considera inversiones líquidas y de bajo riesgo como fondos del mercado monetario o certificados de depósito.' if "corto plazo" in horizonte.lower() else 'Para horizonte largo, puedes considerar inversiones con mayor potencial de crecimiento como índices bursátiles o bienes raíces.'}
        {'Incluye recomendaciones específicas para bienes raíces.' if "bienes raíces" in preferencias.lower() else ''}
        """
    }

# Analizar y mostrar la proyección de retiro
def analizar_proyeccion_retiro(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro):
    años_para_retiro = edad_retiro - edad_actual
    necesidad_total = gastos_retiro * 25  # Regla del 4%
    ahorro_necesario_anual = (necesidad_total - ahorros_retiro) / años_para_retiro if años_para_retiro > 0 else 0
    
    st.subheader("Proyección de Retiro")
    
    cols = st.columns(2)
    cols[0].metric("Edad Actual", edad_actual)
    cols[1].metric("Edad de Retiro", edad_retiro, f"En {años_para_retiro} años")
    
    cols = st.columns(3)
    cols[0].metric("Ingresos Anuales", f"${ingresos_retiro:,.2f}")
    cols[1].metric("Gastos Anuales", f"${gastos_retiro:,.2f}")
    cols[2].metric("Ahorros Actuales", f"${ahorros_retiro:,.2f}")
    
    st.progress(min(ahorros_retiro/necesidad_total, 1.0), text="Progreso hacia tu meta de retiro")
    
    st.subheader("Análisis Detallado")
    st.metric("Necesidad total estimada (regla del 4%)", f"${necesidad_total:,.2f}")
    st.metric("Ahorro anual necesario", f"${ahorro_necesario_anual:,.2f}")
    
    if ahorros_retiro < necesidad_total * 0.1:
        st.error("Tus ahorros actuales son insuficientes para tu retiro. Necesitas aumentar tus contribuciones.")
    
    st.write("""
    **Acciones recomendadas:**
    1. Aumenta tus contribuciones a cuentas de retiro
    2. Considera inversiones que generen ingresos pasivos
    3. Revisa tu asignación de activos periódicamente
    """)
    
    return {
        "edad_actual": edad_actual,
        "edad_retiro": edad_retiro,
        "años_para_retiro": años_para_retiro,
        "necesidad_total": necesidad_total,
        "ahorro_necesario_anual": ahorro_necesario_anual,
        "resumen": f"""
        Proyección de Retiro:
        - Edad Actual: {edad_actual}
        - Edad de Retiro: {edad_retiro} (en {años_para_retiro} años)
        - Necesidad Total Estimada (Regla del 4%): ${necesidad_total:,.2f}
        - Ahorro Anual Necesario: ${ahorro_necesario_anual:,.2f}
        - Progreso Actual: {(ahorros_retiro/necesidad_total)*100:.1f}%
        
        {'Tus ahorros actuales son insuficientes para tu retiro. Necesitas aumentar tus contribuciones.' if ahorros_retiro < necesidad_total * 0.1 else 'Vas por buen camino con tus ahorros para el retiro.'}
        """
    }

# Función para generar un análisis profundo utilizando OpenAI
def generar_analisis_profundo(ingresos, gastos, activos, pasivos, objetivos, horizonte, preferencias):
    if not st.session_state.get('openai_configured'):
        return "Servicio de IA no disponible en este momento."
    
    prompt = f"""
    Como experto en finanzas personales y bienes raíces, analiza esta situación:
    
    **Datos financieros:**
    - Ingresos: ${ingresos}/mes
    - Gastos: ${gastos}/mes
    - Activos: ${activos}
    - Pasivos: ${pasivos}
    - Objetivos: {objetivos}
    - Horizonte: {horizonte}
    - Preferencias: {preferencias}

    Realiza un análisis que incluya:
    1. Diagnóstico financiero completo
    2. Estrategias para optimizar ingresos/gastos
    3. Plan de inversión personalizado
    4. Casos prácticos aplicables
    5. Ejercicios y pasos accionables

    Usa analogías financieras y un estilo motivador pero realista.
    Respuesta en español.
    """
    
    try:
        with st.spinner('Generando análisis profundo con IA...'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un analista financiero especializado en finanzas personales y bienes raíces. Proporciona consejos prácticos y personalizados. Responde en español."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error al generar el análisis: {str(e)}")
        return "No se pudo generar el análisis en este momento."

# Interfaz principal de Streamlit
def main():
    load_css()  # Cargar estilos CSS personalizados
    
    # Logo en la parte superior derecha
    st.markdown("""
    <div class="logo-container">
        <!-- Reemplaza con tu logo en base64 o URL -->
        <img src="aaaaa.png" width="100">
    </div>
    """, unsafe_allow_html=True)
    
    st.title("Analista IA Financiero Carlos Devis")
    st.markdown("""
    <style>
        .stMarkdown h1 {
            color: #1E3A8A;
            font-size: 28px;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    Esta herramienta te ayudará a analizar tu situación financiera actual, crear un plan de acción 
    y establecer metas claras para tu futuro económico.
    """)
    
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
    
    # Paso 2: Datos financieros - Modificado según lo solicitado
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
            
            st.subheader("Activos y Pasivos")
            st.markdown("""
            <table class="data-table">
                <tr>
                    <th>Descripción</th>
                    <th>Valor ($)</th>
                </tr>
                <tr>
                    <td>Inmueble 1</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Inmueble 2</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Automóvil 1</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Automóvil 2</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Muebles</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Joyas</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Arte</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Efectivo cuenta 1</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Efectivo cuenta 2</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Deudas por cobrar</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Bonos o títulos valores</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Fondo de retiro</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Bonos o derechos laborales</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Tarjeta de crédito 1</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Tarjeta de crédito 2</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Tarjeta de crédito 3</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Otra deuda 1</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Otra deuda 2</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Otra deuda 3</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Otros</td>
                    <td><input type="number" min="0" step="1000"></td>
                </tr>
                <tr>
                    <td>Total</td>
                    <td><input type="number" min="0" step="1000" readonly></td>
                </tr>
            </table>
            """, unsafe_allow_html=True)
            
            st.subheader("Veamos ahora tu flujo de caja mensual")
            st.markdown("""
            **Ten en cuenta que algunos de los gastos de este presupuesto no
            son mensuales sino anuales.**
            
            Por ejemplo, si el impuesto de la casa es de 1.200 dólares al año,
            debes dividirlo por 12, lo que te arrojará un resultado de 100
            dólares mensuales. Entonces colocarás en el presupuesto 100
            dólares. Lo mismo puede suceder con la ropa o las vacaciones. Se
            hace un presupuesto y se reserva cada mes una doceava parte.
            """)
            
            st.markdown("""
            **Ejercicio:** Haz tu Flujo de caja mensual
            <table class="data-table">
                <tr>
                    <th>Detalle</th>
                    <th>Subtotal ($)</th>
                    <th>Total ($)</th>
                    <th>% de ingresos</th>
                </tr>
                <tr>
                    <td>Gasto de Inmueble 1</td>
                    <td><input type="number" min="0" step="10"></td>
                    <td><input type="number" min="0" step="10" readonly></td>
                    <td><input type="number" min="0" max="100" step="0.1" readonly></td>
                </tr>
                <!-- Se han eliminado filas redundantes para simplificar el ejemplo -->
                <!-- En la implementación real deberías incluir todas las filas necesarias -->
                <tr>
                    <td>Total gastos mensuales</td>
                    <td><input type="number" min="0" step="10" readonly></td>
                    <td><input type="number" min="0" step="10" readonly></td>
                    <td><input type="number" min="0" max="100" step="0.1" readonly></td>
                </tr>
                <tr>
                    <td>Ingresos mensuales adulto 1</td>
                    <td><input type="number" min="0" step="10"></td>
                    <td><input type="number" min="0" step="10" readonly></td>
                    <td><input type="number" min="0" max="100" step="0.1" readonly></td>
                </tr>
                <tr>
                    <td>Ingresos mensuales adulto 2</td>
                    <td><input type="number" min="0" step="10"></td>
                    <td><input type="number" min="0" step="10" readonly></td>
                    <td><input type="number" min="0" max="100" step="0.1" readonly></td>
                </tr>
                <tr>
                    <td>Otros ingresos</td>
                    <td><input type="number" min="0" step="10"></td>
                    <td><input type="number" min="0" step="10" readonly></td>
                    <td><input type="number" min="0" max="100" step="0.1" readonly></td>
                </tr>
                <tr>
                    <td>Saldo mensual</td>
                    <td><input type="number" min="0" step="10" readonly></td>
                    <td><input type="number" min="0" step="10" readonly></td>
                    <td><input type="number" min="0" max="100" step="0.1" readonly></td>
                </tr>
            </table>
            """, unsafe_allow_html=True)
            
            # Campos para ingresar los totales
            col1, col2 = st.columns(2)
            ingresos = col1.number_input("Ingresos Mensuales Totales ($)", min_value=0.0, value=3000.0, step=100.0)
            gastos = col1.number_input("Gastos Mensuales Totales ($)", min_value=0.0, value=2500.0, step=100.0)
            activos = col2.number_input("Activos Totales ($)", min_value=0.0, value=50000.0, step=1000.0)
            pasivos = col2.number_input("Pasivos Totales ($)", min_value=0.0, value=20000.0, step=1000.0)
            
            if st.button("Analizar mi situación financiera"):
                st.session_state['datos_financieros'] = (ingresos, gastos, activos, pasivos)
                analisis = analizar_situacion_financiera(ingresos, gastos, activos, pasivos)
                st.session_state['reporte_data']['finanzas'] = {
                    'ingresos': ingresos,
                    'gastos': gastos,
                    'activos': activos,
                    'pasivos': pasivos
                }
                st.session_state['reporte_data']['analisis']['resumen'] = analisis['resumen']
                
                # Generar y mostrar plan de trabajo
                plan = generar_plan_trabajo(ingresos, gastos, activos, pasivos)
                st.subheader("📝 Plan de Trabajo Financiero Personalizado")
                st.write(plan)
                st.session_state['reporte_data']['analisis']['plan_trabajo'] = plan
    
    # Paso 3: Plan de inversión con los ajustes solicitados
    if 'datos_financieros' in st.session_state:
        with st.container():
            st.subheader("📈 Plan de Inversión")
            
            # Sección de tips como habladores
            with st.expander("💡 CÓMO ENCONTRAR LOS RECURSOS PARA INVERTIR"):
                st.markdown("""
                <div class="tips-container">
                    <p><strong>Uno de los argumentos que más escucho es:</strong> «Me gustaría invertir en bienes raíces, pero no tengo dinero».</p>
                    
                    <p><strong>1. Organiza tu presupuesto</strong><br>
                    Dice la psicología Gestalt que para lograr lo que quieres debes comenzar por valorar y agradecer lo que ya tienes: la fortuna más grande comenzó con un simple dólar.</p>
                    
                    <p><strong>2. Ordeña tu negocio</strong><br>
                    Recuerdo cuando tenía una empresa con 300 empleados y muchas quincenas sufría para poder pagar los salarios, rogándole al banco que me prestara dinero o a los clientes que pagaran lo que debían, para aun al final llegar a casa sin un centavo para mi familia.</p>
                    
                    <p><strong>3. Vende cosas que no estás usando</strong><br>
                    ¿Cuántas cosas tienes en tu armario o en tu garaje que no estás usando y que probablemente nunca usarás? Ese automóvil, bote, moto... todo se puede vender y convertir en liquidez para tu próxima propiedad.</p>
                    
                    <p><strong>Aprende a vender mejor tu talento o producto</strong><br>
                    Belén tiene 28 años y estudió una carrera técnica para ayudar a las mujeres a prepararse mejor para el parto y que tengan menos dolor, aplicando técnicas sencillas para cuidar más de los cuerpos de las madres y la salud de los bebés.</p>
                    
                    <p><strong>4. Vende bienes raíces</strong><br>
                    Una manera que yo les sugiero a mis alumnos para que aprendan de bienes raíces, ganen algo de dinero y encuentren oportunidades, es que se vuelvan agentes de bienes raíces, que se acerquen a varias oficinas y digan que quieren trabajar en ello.</p>
                    
                    <p><strong>5. Ofrece tus servicios profesionales</strong><br>
                    Ingrid es arquitecta y vive en Berlín. Pensaba que para ella comprar un apartamento en esa ciudad era imposible y con su esposo hacían lo posible para llegar a fin de mes.</p>
                    
                    <p><strong>6. Cambia de trabajo</strong><br>
                    Cuando alguien me cuenta que no le gusta su trabajo o que no le pagan bien, yo le pregunto:<br>
                    —¿Has buscado otro trabajo?<br>
                    —Sí, estoy pensando en cambiar —me responde normalmente la persona.</p>
                    
                    <p><strong>7. Auto promuévete dentro de tu propia empresa</strong><br>
                    No siempre es necesario salir de la empresa, a veces es posible buscar un cambio dentro de ella. Habla, prepárate para lo que quieres conseguir y mantén el foco, la actitud y las acciones para lograrlo.</p>
                    
                    <p><strong>8. Sal de todos los «negocios» que no te están produciendo</strong><br>
                    Recuerdo una historia que se cuenta mucho de un borrachito que decía: «¡Pero, cómo voy a dejar el trago después de toda la plata que he gastado!».</p>
                    
                    <p><strong>9. Cambia tu automóvil por una cuota inicial</strong><br>
                    Para la mentalidad del consumidor es muy importante tener un buen automóvil, «El auto del año» como le dicen los vendedores. No te imaginas cuántas familias arruinan su capacidad de crecer financieramente porque aceptan unas cuotas desproporcionadas para sus ingresos solo por poder comprarse «un buen auto».</p>
                </div>
                """, unsafe_allow_html=True)
            
            objetivos = st.text_input("Objetivos financieros (ej: comprar casa, retiro temprano)", 
                                    "Crear fuentes de ingreso pasivo")
            horizonte = st.selectbox("Horizonte de inversión", 
                                   ["Corto plazo (1-3 años)", "Mediano plazo (3-5 años)", "Largo plazo (5+ años)"])
            preferencias = st.multiselect("Preferencias de inversión", 
                                        ["Bienes raíces", "Acciones", "Bonos", "Fondos", "Formación en finanzas", "Negocios"])
            
            if st.button("Analizar plan de inversión"):
                st.session_state['plan_inversion'] = (objetivos, horizonte, ", ".join(preferencias))
                analisis = analizar_plan_inversion(objetivos, horizonte, ", ".join(preferencias))
                st.session_state['reporte_data']['analisis']['plan_inversion'] = analisis['resumen']
                
                # Análisis profundo con IA
                ingresos, gastos, activos, pasivos = st.session_state['datos_financieros']
                analisis_ia = generar_analisis_profundo(ingresos, gastos, activos, pasivos, objetivos, horizonte, ", ".join(preferencias))
                
                st.subheader("🧠 Análisis Profundo con Inteligencia Artificial")
                st.write(analisis_ia)
                st.session_state['reporte_data']['analisis']['analisis_ia'] = analisis_ia
    
    # Paso 4: Proyección de retiro
    if 'datos_financieros' in st.session_state:
        with st.container():
            st.subheader("👵 Proyección de Retiro")
            
            col1, col2 = st.columns(2)
            edad_actual = col1.number_input("Tu edad actual", min_value=18, max_value=100, value=30)
            edad_retiro = col2.number_input("Edad de retiro deseada", min_value=edad_actual+1, max_value=100, value=65)
            
            ingresos_retiro = st.number_input("Ingresos anuales esperados durante el retiro ($)", 
                                            min_value=0.0, value=40000.0, step=1000.0)
            gastos_retiro = st.number_input("Gastos anuales esperados durante el retiro ($)", 
                                          min_value=0.0, value=30000.0, step=1000.0)
            ahorros_retiro = st.number_input("Ahorros actuales para el retiro ($)", 
                                           min_value=0.0, value=10000.0, step=1000.0)
            
            if st.button("Calcular proyección de retiro"):
                analisis = analizar_proyeccion_retiro(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro)
                st.session_state['reporte_data']['analisis']['proyeccion_retiro'] = analisis['resumen']
    
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
    ### 📌 Recomendaciones Finales
    - Revisa periódicamente tu situación financiera
    - Implementa los cambios de manera consistente
    - Considera asesoría profesional para estrategias avanzadas
    """)

if __name__ == "__main__":
    crear_base_datos()
    main()