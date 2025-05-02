import streamlit as st
from openai import OpenAI
import sqlite3
from fpdf import FPDF
import base64
from io import BytesIO
import re
import os
from PIL import Image  # Para manejar el logo

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
    page_title="Taller de Bienes Raíces",
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
    pdf.cell(200, 10, txt="Taller de Bienes Raíces", ln=1, align='C')
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
    
    # Perfil de inversionista
    if 'perfil_inversionista' in analisis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Perfil de Inversionista:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analisis_data['perfil_inversionista'])
    
    # Cursos recomendados
    if 'cursos_recomendados' in analisis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Cursos Recomendados:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analisis_data['cursos_recomendados'])
    
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
    Como experto en bienes raíces y finanzas personales según la metodología de Carlos Devis, analiza la situación financiera con estos datos:
    - Ingresos: {format_currency(ingresos)}/mes
    - Gastos: {format_currency(gastos)}/mes
    - Activos: {format_currency(activos)}
    - Pasivos: {format_currency(pasivos)}
    
    Crea un plan detallado que incluya:
    1. Diagnóstico claro de la situación actual enfocado en bienes raíces
    2. Estrategias para mejorar el flujo de caja según metodología Carlos Devis
    3. Plan de reducción de deudas (si aplica) con enfoque en inversión inmobiliaria
    4. Recomendaciones de inversión en bienes raíces personalizadas
    5. Metas a corto (3 meses), mediano (1 año) y largo plazo (5+ años)
    6. Ejercicios prácticos para implementar el plan basados en los cursos de Carlos Devis
    
    Además, determina el perfil de inversionista (conservador, moderado, agresivo) según los datos y recomienda cursos específicos del programa de Carlos Devis que podrían ayudar al usuario.
    
    Usa un lenguaje claro y motivador, con ejemplos concretos de bienes raíces.
    Respuesta en español.
    """
    
    try:
        with st.spinner('Generando tu plan personalizado...'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asesor financiero experto en bienes raíces que sigue la metodología de Carlos Devis. Responde en español."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error al generar el plan: {str(e)}")
        return "No se pudo generar el plan en este momento."

# Generar perfil de inversionista y recomendaciones de cursos
def generar_perfil_y_cursos(ingresos, gastos, activos, pasivos, objetivos, preferencias):
    if not st.session_state.get('openai_configured'):
        return "Servicio no disponible", ""
    
    prompt = f"""
    Basado en los siguientes datos financieros:
    - Ingresos: {format_currency(ingresos)}/mes
    - Gastos: {format_currency(gastos)}/mes
    - Activos: {format_currency(activos)}
    - Pasivos: {format_currency(pasivos)}
    - Objetivos: {objetivos}
    - Preferencias de inversión: {preferencias}
    
    Determina:
    1. Perfil de inversionista (conservador, moderado, agresivo) con explicación detallada
    2. Recomendación de 3 cursos del programa de Carlos Devis que mejor se adapten al perfil y objetivos
    3. Explicación de cómo cada curso puede ayudar al usuario
    
    Respuesta en español, dividida claramente en las 3 secciones solicitadas.
    """
    
    try:
        with st.spinner('Analizando tu perfil...'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en clasificación de perfiles de inversionistas y conocedor del programa de formación de Carlos Devis. Responde en español."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error al generar el perfil: {str(e)}")
        return "No se pudo generar el perfil en este momento.", ""

# Interfaz principal de Streamlit
def main():
    load_css()  # Cargar estilos CSS personalizados
    
    # Encabezado con logo - Versión con imagen local
    try:
        # Intenta cargar el logo desde el archivo local
        logo = Image.open("aaaaa.png")  # Asegúrate de tener el archivo aaaaa.png en el mismo directorio
        st.markdown("""
        <div class="header-container">
        """, unsafe_allow_html=True)
        
        # Mostrar el logo con st.image
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(logo, width=80)  # Ajusta el ancho según necesites
        
        with col2:
            st.markdown("""
            <div>
                <h1 style="margin:0;color:#1E3A8A;">Taller de Bienes Raíces</h1>
                <h3 style="margin:0;color:#6B7280;">Carlos Devis</h3>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    except FileNotFoundError:
        # Si no encuentra el logo, muestra solo el texto
        st.markdown("""
        <div class="header-container">
            <div>
                <h1 style="margin:0;color:#1E3A8A;">Taller de Bienes Raíces</h1>
                <h3 style="margin:0;color:#6B7280;">Carlos Devis</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.warning("No se encontró el archivo del logo (aaaaa.png)")
    
    st.markdown("""
    <div class="calculator-container">
        Esta herramienta te ayudará a analizar tu situación financiera actual, crear un plan de acción 
        y establecer metas claras para tu futuro económico en bienes raíces.
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
            
            # Explicación de los campos
            with st.expander("ℹ️ Explicación de los campos"):
                st.markdown("""
                **Inmueble:** Propiedades como apartamentos, casas, terrenos, locales comerciales, etc.
                **Automóvil:** Vehículos personales o de trabajo.
                **Muebles:** Mobiliario de tu hogar u oficina.
                **Joyas:** Piezas de valor como anillos, collares, relojes, etc.
                **Arte:** Pinturas, esculturas u otras obras de arte de valor.
                **Efectivo:** Dinero en cuentas bancarias o en efectivo.
                **Deudas por cobrar:** Dinero que otras personas o empresas te deben.
                **Bonos o títulos valores:** Inversiones en instrumentos financieros.
                **Fondo de retiro:** Ahorros en fondos de pensiones o retiro.
                **Bonos o derechos laborales:** Beneficios acumulados en tu trabajo.
                **Tarjetas de crédito:** Deudas en tarjetas de crédito.
                **Otras deudas:** Préstamos personales, hipotecas, etc.
                """)
            
            # Lista de activos y pasivos consolidados
            items = [
                "Inmueble 1", "Inmueble 2", "Automóvil 1", "Automóvil 2", 
                "Muebles", "Joyas", "Arte", "Efectivo cuenta 1", 
                "Efectivo cuenta 2", "Deudas por cobrar", "Bonos o títulos valores",
                "Fondo de retiro", "Bonos o derechos laborales",
                "Tarjeta de crédito 1", "Tarjeta de crédito 2", "Tarjeta de crédito 3",
                "Otra deuda 1", "Otra deuda 2", "Otra deuda 3", "Otros"
            ]
            
            # Inicializar valores en session_state si no existen
            if 'valores_consolidados' not in st.session_state:
                st.session_state['valores_consolidados'] = {
                    item: {'valor': 0.0, 'deuda': 0.0, 'activo': True} for item in items
                }
                # Marcar pasivos como no activos
                for pasivo in ["Tarjeta de crédito 1", "Tarjeta de crédito 2", "Tarjeta de crédito 3",
                             "Otra deuda 1", "Otra deuda 2", "Otra deuda 3", "Otros"]:
                    st.session_state['valores_consolidados'][pasivo]['activo'] = False
            
            # Tabla consolidada
            st.markdown("""
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Descripción</th>
                        <th>Valor ($)</th>
                        <th>Deuda ($)</th>
                        <th>Activo</th>
                    </tr>
                </thead>
                <tbody>
            """, unsafe_allow_html=True)
            
            activos_total = 0.0
            pasivos_total = 0.0
            
            for item in items:
                # Determinar si es activo o pasivo
                es_activo = st.session_state['valores_consolidados'][item]['activo']
                
                # Crear filas de la tabla
                st.markdown(f"""
                <tr>
                    <td>{item}</td>
                    <td><input type="text" id="valor_{item}" value="{format_currency(st.session_state['valores_consolidados'][item]['valor'])}"></td>
                    <td><input type="text" id="deuda_{item}" value="{format_currency(st.session_state['valores_consolidados'][item]['deuda'])}"></td>
                    <td>{"✅" if es_activo else "❌"}</td>
                </tr>
                """, unsafe_allow_html=True)
                
                # Obtener valores actualizados
                valor_str = st.session_state.get(f"valor_{item}", format_currency(st.session_state['valores_consolidados'][item]['valor']))
                deuda_str = st.session_state.get(f"deuda_{item}", format_currency(st.session_state['valores_consolidados'][item]['deuda']))
                
                # Parsear valores
                valor = parse_currency(valor_str)
                deuda = parse_currency(deuda_str)
                
                # Actualizar session_state
                st.session_state['valores_consolidados'][item]['valor'] = valor
                st.session_state['valores_consolidados'][item]['deuda'] = deuda
                
                # Sumar a totales
                if es_activo:
                    activos_total += valor
                else:
                    pasivos_total += deuda
            
            st.markdown("""
                </tbody>
            </table>
            """, unsafe_allow_html=True)
            
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
            
            # Explicación de los campos
            with st.expander("ℹ️ Explicación de los campos"):
                st.markdown("""
                **Ingresos mensuales:** Salarios, ingresos por alquileres, negocios, inversiones, etc.
                **Gastos fijos:** Hipoteca/alquiler, servicios públicos, seguros, transporte, etc.
                **Gastos variables:** Alimentación, entretenimiento, ropa, etc.
                **Gastos esporádicos:** Vacaciones, reparaciones, regalos, etc.
                """)
            
            # Inicializar valores en session_state si no existen
            if 'ingresos_values' not in st.session_state:
                st.session_state['ingresos_values'] = {
                    "Ingresos mensuales adulto 1": 0.0,
                    "Ingresos mensuales adulto 2": 0.0,
                    "Otros ingresos": 0.0
                }
            
            if 'gastos_values' not in st.session_state:
                st.session_state['gastos_values'] = {
                    "Gasto de vivienda (hipoteca/alquiler)": 0.0,
                    "Alimentación": 0.0,
                    "Educación": 0.0,
                    "Transporte": 0.0,
                    "Salud": 0.0,
                    "Entretenimiento": 0.0,
                    "Servicios públicos": 0.0,
                    "Seguros": 0.0,
                    "Otros gastos fijos": 0.0,
                    "Gastos variables": 0.0
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
            st.subheader("📈 Plan de Inversión en Bienes Raíces")
            
            # Sección de tips como habladores
            with st.expander("💡 CÓMO ENCONTRAR LOS RECURSOS PARA INVERTIR EN BIENES RAÍCES"):
                st.markdown("""
                <div class="tips-container">
                    **1. Organiza tu presupuesto**  
                    Comienza por valorar y agradecer lo que ya tienes: la fortuna más grande comenzó con un simple dólar.
                    
                    **2. Ordeña tu negocio**  
                    Optimiza los ingresos de tu negocio actual para generar fondos para inversión.
                    
                    **3. Vende cosas que no estás usando**  
                    Convierte activos no productivos en liquidez para tu próxima propiedad.
                    
                    **4. Vende bienes raíces**  
                    Conviértete en agente de bienes raíces para aprender, ganar dinero y encontrar oportunidades.
                    
                    **5. Ofrece tus servicios profesionales**  
                    Usa tus habilidades para generar ingresos adicionales destinados a inversión.
                    
                    **6. Cambia de trabajo o promuévete**  
                    Aumenta tus ingresos principales para destinar más a inversiones.
                    
                    **7. Sal de negocios no productivos**  
                    Libera recursos atrapados en actividades que no generan retorno.
                    
                    **8. Optimiza tus gastos en automóvil**  
                    Considera reducir gastos en vehículos para destinar más a inversiones.
                </div>
                """, unsafe_allow_html=True)
            
            objetivos = st.selectbox("Objetivos de inversión", 
                                   ["Comprar casa propia", "Formación en inversión financiera", "Generar ingresos pasivos", "Otros"])
            
            horizonte = st.selectbox("Horizonte de inversión", 
                                   ["Corto plazo (1-3 años)", "Mediano plazo (3-5 años)", "Largo plazo (5+ años)"])
            
            preferencias = st.multiselect("Preferencias de inversión", 
                                        ["Inversión en bienes raíces", "Educación financiera"])
            
            if st.button("Analizar plan de inversión"):
                ingresos, gastos, activos, pasivos = st.session_state['datos_financieros']
                analisis_ia = generar_plan_trabajo(ingresos, gastos, activos, pasivos)
                
                st.subheader("🧠 Análisis Profundo con Inteligencia Artificial")
                st.write(analisis_ia)
                st.session_state['reporte_data']['analisis']['analisis_ia'] = analisis_ia
                
                # Generar perfil de inversionista y recomendaciones de cursos
                perfil, cursos = generar_perfil_y_cursos(ingresos, gastos, activos, pasivos, objetivos, ", ".join(preferencias))
                
                st.subheader("👤 Perfil de Inversionista")
                st.write(perfil)
                st.session_state['reporte_data']['analisis']['perfil_inversionista'] = perfil
                
                st.subheader("🎓 Cursos Recomendados")
                st.write(cursos)
                st.session_state['reporte_data']['analisis']['cursos_recomendados'] = cursos
    
    # Paso 4: Plan de retiro
    if 'usuario_id' in st.session_state:
        with st.container():
            st.subheader("👴 Plan de Retiro con Bienes Raíces")
            
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
                
                st.subheader("📊 Proyección de Retiro con Bienes Raíces")
                st.write(f"**Años hasta el retiro:** {analisis['años_ahorro']}")
                st.write(f"**Necesidad total estimada:** {format_currency(analisis['necesidad_total'])}")
                st.write(f"**Ahorros actuales:** {format_currency(ahorros_retiro)}")
                st.write(f"**Necesitas ahorrar aproximadamente:** {format_currency(analisis['ahorro_necesario_anual'])} anuales")
                
                st.subheader("📌 Estrategias con Bienes Raíces para el Retiro")
                st.write("1. **Adquiere propiedades para alquiler:** Genera ingresos pasivos")
                st.write("2. **Invierte en propiedades en desarrollo:** Aprovecha la plusvalía")
                st.write("3. **Considera REITs:** Inversión en bienes raíces sin gestión directa")
                st.write("4. **Diversifica geográficamente:** Reduce riesgos locales")
    
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
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="reporte_bienes_raices.pdf">Haz clic aquí para descargar tu reporte</a>'
            st.markdown(href, unsafe_allow_html=True)
    
    # Pie de página
    st.markdown("---")
    st.markdown("""
    <div class="calculator-container">
        <h3>📌 Recomendaciones Finales</h3>
        <ul>
            <li>Revisa periódicamente tu situación financiera</li>
            <li>Implementa los cambios de manera consistente</li>
            <li>Considera los cursos recomendados para profundizar tu conocimiento</li>
            <li>Visita nuestro canal de YouTube para más recursos: <a href="https://www.youtube.com/channel/UCKwyUxdM1x5xqMEqqdQaPgQ" target="_blank">Canal de Carlos Devis</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    crear_base_datos()
    main()