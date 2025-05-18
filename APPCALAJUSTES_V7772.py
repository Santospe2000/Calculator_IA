import streamlit as st
from openai import OpenAI
import sqlite3
from fpdf import FPDF
import base64
from io import BytesIO
import re
import os

# Configuración inicial de la página
st.set_page_config(
    page_title="Taller de Bienes Raíces",
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

# Función para tooltips mejorados
def tooltip_icon(description):
    return f"""
    <span title="{description}" style="cursor: help; margin-left: 5px;">
        <button style="border: none; background: none; color: #1E3A8A; padding: 0; font-size: 14px;">ℹ️</button>
    </span>
    """

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
    try:
        if value is None or (isinstance(value, str) and value.strip() == "$ -":
            return "$ -"
        num = float(value)
        return f"$ {num:,.2f}"
    except:
        return "$ -"

# Función para extraer el valor numérico
def parse_currency(currency_str):
    if not currency_str or currency_str.strip() == "$ -":
        return 0.0
    num_str = re.sub(r'[^\d.]', '', currency_str)
    return float(num_str) if num_str else 0.0

# Función para generar PDF
def generate_pdf(usuario_data, finanzas_data, analisis_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Informe Financiero - Taller de Bienes Raíces", ln=1, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Análisis de Inversión en Bienes Raíces", ln=1, align='C')
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
        pdf.cell(200, 10, txt=f"Perfil de Inversión en Bienes Raíces: {analisis_data['perfil_inversion']['nivel']}", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analisis_data['perfil_inversion']['descripcion'])
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
    
    # Recomendaciones de cursos
    if 'recomendaciones_cursos' in analisis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Recomendaciones de Educación Financiera:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analisis_data['recomendaciones_cursos'])
    
    # Generar el PDF en memoria
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_bytes = pdf_output.getvalue()
    pdf_output.close()
    
    return pdf_bytes

# Crear la base de datos
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
def analizar_proyeccion_retiro(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro, patrimonio_neto, flujo_caja):
    años_ahorro = edad_retiro - edad_actual
    necesidad_total = (ingresos_retiro - gastos_retiro) * (100 - edad_retiro)
    ahorro_necesario_anual = (necesidad_total - ahorros_retiro) / años_ahorro if años_ahorro > 0 else 0
    
    # Análisis específico para bienes raíces
    recomendaciones = []
    cursos_recomendados = []
    
    if patrimonio_neto > 50000 and flujo_caja > 1000:
        nivel = "Alto"
        recomendaciones.append("Tienes un excelente perfil para comenzar a invertir en bienes raíces de inmediato.")
        recomendaciones.append("Considera propiedades generadoras de ingresos pasivos como apartamentos en arriendo o locales comerciales.")
        cursos_recomendados.append("Curso Avanzado de Inversión en Bienes Raíces")
    elif patrimonio_neto > 20000 and flujo_caja > 500:
        nivel = "Medio"
        recomendaciones.append("Tienes potencial para inversión en bienes raíces, pero necesitas mejorar tu flujo de caja.")
        recomendaciones.append("Considera comenzar con propiedades pequeñas o co-inversiones.")
        cursos_recomendados.append("Curso Intermedio de Bienes Raíces")
    else:
        nivel = "Bajo"
        recomendaciones.append("Necesitas fortalecer tu situación financiera antes de invertir en bienes raíces.")
        recomendaciones.append("Enfócate en aumentar tus ingresos y reducir deudas.")
        cursos_recomendados.append("Curso Básico de Educación Financiera para Bienes Raíces")
    
    recomendaciones.append("\nTe recomendamos estos recursos educativos:")
    recomendaciones.append("- https://www.youtube.com/@carlosdevis")
    recomendaciones.append("- https://landing.tallerdebienesraices.com/registro-ciclo-educativo/")
    
    return {
        "años_ahorro": años_ahorro,
        "necesidad_total": necesidad_total,
        "ahorro_necesario_anual": ahorro_necesario_anual,
        "nivel_inversion": nivel,
        "analisis": f"""
        Proyección de Retiro con Enfoque en Bienes Raíces:
        - Años hasta el retiro: {años_ahorro}
        - Necesidad total estimada: {format_currency(necesidad_total)}
        - Ahorros actuales: {format_currency(ahorros_retiro)}
        - Necesitas ahorrar aproximadamente {format_currency(ahorro_necesario_anual)} anuales para alcanzar tu meta.
        
        Perfil de Inversión: {nivel}
        
        Recomendaciones Específicas:
        {chr(10).join(recomendaciones)}
        
        Cursos Recomendados:
        {chr(10).join(cursos_recomendados)}
        """
    }

# Calcular y mostrar el análisis financiero
def analizar_situacion_financiera(ingresos, gastos, activos, pasivos):
    flujo_caja_mensual = ingresos - gastos
    patrimonio_neto = activos - pasivos
    
    # Determinar perfil de inversión en bienes raíces
    if patrimonio_neto > 50000 and flujo_caja_mensual > 1000:
        perfil = "Alto (70-100%)"
        descripcion = "Excelente perfil para inversión en bienes raíces. Tienes la capacidad financiera para comenzar a invertir en propiedades generadoras de ingresos pasivos."
    elif patrimonio_neto > 20000 and flujo_caja_mensual > 500:
        perfil = "Medio (40-69%)"
        descripcion = "Buen potencial para inversión en bienes raíces. Considera comenzar con propiedades pequeñas o co-inversiones mientras mejoras tu flujo de caja."
    else:
        perfil = "Bajo (0-39%)"
        descripcion = "Necesitas fortalecer tu situación financiera antes de invertir en bienes raíces. Enfócate en aumentar ingresos, reducir deudas y ahorrar."
    
    st.subheader("📊 Análisis Resumen de tu Situación Financiera")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Ingresos Mensuales", format_currency(ingresos))
        st.metric("Gastos Mensuales", format_currency(gastos))
    
    with col2:
        st.metric("Activos Totales", format_currency(activos))
        st.metric("Pasivos Totales", format_currency(pasivos))
    
    st.metric("Flujo de Caja Mensual", format_currency(flujo_caja_mensual), 
             delta="Positivo" if flujo_caja_mensual > 0 else "Negativo",
             delta_color="normal" if flujo_caja_mensual > 0 else "inverse")
    
    st.metric("Patrimonio Neto", format_currency(patrimonio_neto), 
             delta="Positivo" if patrimonio_neto > 0 else "Negativo",
             delta_color="normal" if patrimonio_neto > 0 else "inverse")
    
    st.subheader("🏡 Perfil de Inversión en Bienes Raíces")
    st.markdown(f"""
    <div class="calculator-container">
        <h4>Nivel: {perfil}</h4>
        <p>{descripcion}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🔍 Análisis Específico para Bienes Raíces")
    if flujo_caja_mensual > 0:
        st.success(f"Flujo de caja positivo de {format_currency(flujo_caja_mensual)}/mes. Podrías destinar parte de este excedente a inversión en propiedades.")
    else:
        st.error(f"Flujo de caja negativo de {format_currency(flujo_caja_mensual)}/mes. Necesitas equilibrar tus finanzas antes de considerar inversiones.")
    
    if patrimonio_neto > 50000:
        st.success("Patrimonio neto sólido. Podrías usar parte como garantía para financiamiento de propiedades.")
    elif patrimonio_neto > 0:
        st.warning("Patrimonio neto positivo pero modesto. Considera estrategias de bajo riesgo como alquiler de habitaciones.")
    else:
        st.error("Patrimonio neto negativo. Enfócate en reducir deudas antes de invertir.")
    
    st.subheader("🚀 Acciones Recomendadas para Bienes Raíces")
    st.write("""
    1. **Analiza tu capacidad de endeudamiento** para financiamiento hipotecario
    2. **Explora opciones de co-inversión** si tu capital es limitado
    3. **Considera propiedades con múltiples fuentes de ingreso** (alquiler, parking, lavandería)
    4. **Estudia el mercado local** para identificar oportunidades
    5. **Asiste a nuestros talleres** para aprender estrategias específicas
    """)
    
    return {
        "flujo_caja": flujo_caja_mensual,
        "patrimonio": patrimonio_neto,
        "perfil_inversion": {
            "nivel": perfil,
            "descripcion": descripcion
        },
        "resumen": f"""
        Situación Financiera Actual:
        - Ingresos Mensuales: {format_currency(ingresos)}
        - Gastos Mensuales: {format_currency(gastos)}
        - Flujo de Caja: {format_currency(flujo_caja_mensual)} ({'Positivo' if flujo_caja_mensual > 0 else 'Negativo'})
        - Activos Totales: {format_currency(activos)}
        - Pasivos Totales: {format_currency(pasivos)}
        - Patrimonio Neto: {format_currency(patrimonio_neto)} ({'Positivo' if patrimonio_neto > 0 else 'Negativo'})
        
        Perfil de Inversión en Bienes Raíces: {perfil}
        {descripcion}
        """
    }

# Generar plan de trabajo financiero
def generar_plan_trabajo(ingresos, gastos, activos, pasivos):
    if not st.session_state.get('openai_configured', False):
        return "Servicio de IA no disponible en este momento. Por favor configura tu clave de OpenAI API en secrets.toml para habilitar esta función."
    
    prompt = f"""
    Como experto en bienes raíces y finanzas personales (siguiendo la metodología de Carlos Devis), analiza esta situación financiera:
    - Ingresos: {format_currency(ingresos)}/mes
    - Gastos: {format_currency(gastos)}/mes
    - Activos: {format_currency(activos)}
    - Pasivos: {format_currency(pasivos)}
    
    Crea un plan detallado orientado específicamente a inversión en bienes raíces que incluya:
    1. Diagnóstico claro de la situación actual con enfoque en bienes raíces
    2. Estrategias para mejorar el flujo de caja aplicables a inversión inmobiliaria
    3. Plan de reducción de deudas que permita acceder a financiamiento hipotecario
    4. Recomendaciones de inversión en bienes raíces personalizadas según el perfil
    5. Metas a corto (3 meses), mediano (1 año) y largo plazo (5+ años) para construir patrimonio inmobiliario
    6. Ejercicios prácticos para identificar oportunidades locales
    7. Recomendaciones específicas de cursos y recursos del Taller de Bienes Raíces
    
    Usa un lenguaje claro y motivador, con ejemplos concretos de estrategias inmobiliarias.
    Incluye referencias a los principios enseñados por Carlos Devis en sus cursos.
    Respuesta en español.
    """
    
    try:
        with st.spinner('Generando tu plan personalizado para bienes raíces...'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asesor experto en inversión en bienes raíces que sigue la metodología de Carlos Devis. Responde en español con enfoque práctico para inversión inmobiliaria."},
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
        <img src="https://github.com/Santospe2000/Calculator_IA/raw/main/aaaaa.png" class="logo" alt="Logo Taller Bienes Raíces">
        <div>
            <h1 style="margin:0;color:#1E3A8A;">Taller de Bienes Raíces</h1>
            <h3 style="margin:0;color:#6B7280;">Calculadora Financiera para Inversión Inmobiliaria</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="calculator-container">
        Esta herramienta te ayudará a analizar tu capacidad para invertir en bienes raíces, 
        crear un plan de acción y establecer metas claras para construir patrimonio inmobiliario.
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
            **Ejercicio:** Comienza por hacer un presupuesto detallado de tu gasto diario y mensual. 
            Revisa extractos de cuentas y tarjetas, y anota todo lo que gastas en efectivo. 
            Identifica oportunidades para destinar recursos a inversión en bienes raíces.
            """)
            
            st.subheader("💰 Activos y Pasivos")
            
            # Definición de activos con tooltips
            activos_items = [
                {"nombre": "Inmueble 1", "descripcion": "Valor de mercado de tu primera propiedad (casa, apartamento o terreno)."},
                {"nombre": "Inmueble 2", "descripcion": "Valor de mercado de tu segunda propiedad (si aplica)."},
                {"nombre": "Automóvil 1", "descripcion": "Valor actual de tu vehículo principal."},
                {"nombre": "Automóvil 2", "descripcion": "Valor actual de tu segundo vehículo (si aplica)."},
                {"nombre": "Muebles", "descripcion": "Valor estimado de muebles y enseres."},
                {"nombre": "Joyas", "descripcion": "Valor estimado de joyas y artículos de valor."},
                {"nombre": "Arte", "descripcion": "Valor estimado de obras de arte y colecciones."},
                {"nombre": "Efectivo cuenta 1", "descripcion": "Saldo disponible en tu cuenta principal."},
                {"nombre": "Efectivo cuenta 2", "descripcion": "Saldo disponible en cuentas secundarias."},
                {"nombre": "Deudas por cobrar", "descripcion": "Dinero que te deben otras personas o empresas."},
                {"nombre": "Bonos o títulos valores", "descripcion": "Valor de tus inversiones financieras."},
                {"nombre": "Fondo de retiro", "descripcion": "Saldo acumulado en fondos de pensiones."},
                {"nombre": "Bonos o derechos laborales", "descripcion": "Valor de prestaciones laborales."}
            ]
            
            # Inicializar valores en session_state si no existen
            if 'activos_values' not in st.session_state:
                st.session_state['activos_values'] = {item['nombre']: {"valor": 0.0, "deuda": 0.0} for item in activos_items}
            
            # Crear tabla de activos
            st.markdown("""
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Descripción</th>
                        <th>Valor</th>
                        <th>Deuda</th>
                        <th>Activos</th>
                    </tr>
                </thead>
                <tbody>
            """, unsafe_allow_html=True)
            
            activos_total = {"valor": 0.0, "deuda": 0.0, "neto": 0.0}
            
            for item in activos_items:
                # Fila de la tabla
                st.markdown(f"""
                <tr>
                    <td>
                        {item['nombre']}
                        {tooltip_icon(item['descripcion'])}
                    </td>
                    <td><input type="text" id="activo_valor_{item['nombre']}" value="{format_currency(st.session_state['activos_values'][item['nombre']]['valor'])}"></td>
                    <td><input type="text" id="activo_deuda_{item['nombre']}" value="{format_currency(st.session_state['activos_values'][item['nombre']]['deuda'])}"></td>
                    <td>{format_currency(st.session_state['activos_values'][item['nombre']]['valor'] - st.session_state['activos_values'][item['nombre']]['deuda'])}</td>
                </tr>
                """, unsafe_allow_html=True)
                
                # Actualizar totales
                activos_total["valor"] += st.session_state['activos_values'][item['nombre']]['valor']
                activos_total["deuda"] += st.session_state['activos_values'][item['nombre']]['deuda']
                activos_total["neto"] += (st.session_state['activos_values'][item['nombre']]['valor'] - st.session_state['activos_values'][item['nombre']]['deuda'])
            
            # Fila de totales
            st.markdown(f"""
            <tr class="total-row">
                <td><strong>Total</strong></td>
                <td><strong>{format_currency(activos_total['valor'])}</strong></td>
                <td><strong>{format_currency(activos_total['deuda'])}</strong></td>
                <td><strong>{format_currency(activos_total['neto'])}</strong></td>
            </tr>
            </tbody>
            </table>
            """, unsafe_allow_html=True)
            
            # Flujo de caja mensual
            st.subheader("💸 Flujo de Caja Mensual")
            
            with st.expander("ℹ️ Información sobre Flujo de Caja"):
                st.markdown("""
                **¿Qué es el flujo de caja?**  
                El flujo de caja es la diferencia entre tus ingresos y gastos mensuales. 
                Un flujo positivo significa que tienes dinero disponible para ahorrar o invertir, 
                mientras que un flujo negativo indica que gastas más de lo que ganas.
                
                **Importancia para bienes raíces:**  
                - Te permite ahorrar para la cuota inicial de una propiedad  
                - Demuestra capacidad de pago para obtener financiamiento  
                - Puede usarse para cubrir gastos de propiedades en arriendo  
                - Es clave para evaluar tu capacidad de inversión
                """)
            
            # Ingresos mensuales
            st.markdown("<h4>Ingresos Mensuales</h4>", unsafe_allow_html=True)
            
            ingresos_items = [
                {"nombre": "Salario o ingresos principales", "descripcion": "Ingresos fijos por trabajo o negocio principal."},
                {"nombre": "Ingresos secundarios", "descripcion": "Ingresos adicionales por trabajos ocasionales o negocios secundarios."},
                {"nombre": "Ingresos por inversiones", "descripcion": "Dividendos, intereses o ganancias de capital."},
                {"nombre": "Ingresos por alquileres", "descripcion": "Dinero recibido por alquilar propiedades."},
                {"nombre": "Otros ingresos", "descripcion": "Cualquier otro ingreso no clasificado."}
            ]
            
            if 'ingresos_values' not in st.session_state:
                st.session_state['ingresos_values'] = {item['nombre']: 0.0 for item in ingresos_items}
            
            ingresos_total = 0.0
            
            for item in ingresos_items:
                cols = st.columns([4, 1])
                cols[0].markdown(f"""
                    {item['nombre']}
                    {tooltip_icon(item['descripcion'])}
                """, unsafe_allow_html=True)
                
                value = cols[1].text_input(
                    f"Ingreso {item['nombre']}",
                    value=format_currency(st.session_state['ingresos_values'][item['nombre']]),
                    key=f"ingreso_{item['nombre']}",
                    label_visibility="collapsed"
                )
                
                parsed_value = parse_currency(value)
                st.session_state['ingresos_values'][item['nombre']] = parsed_value
                ingresos_total += parsed_value
            
            # Gastos mensuales
            st.markdown("<h4>Gastos Mensuales</h4>", unsafe_allow_html=True)
            
            gastos_items = [
                {"nombre": "Vivienda", "descripcion": "Hipoteca, arriendo, administración, impuestos y mantenimiento."},
                {"nombre": "Alimentación", "descripcion": "Supermercado, restaurantes y gastos de comida."},
                {"nombre": "Transporte", "descripcion": "Gasolina, transporte público, mantenimiento vehicular."},
                {"nombre": "Servicios públicos", "descripcion": "Agua, luz, gas, internet, teléfono."},
                {"nombre": "Seguros", "descripcion": "Seguro de vida, vehicular, hogar, salud."},
                {"nombre": "Entretenimiento", "descripcion": "Salidas, viajes, suscripciones (Netflix, etc.)."},
                {"nombre": "Educación", "descripcion": "Colegiatura, universidad, cursos y materiales."},
                {"nombre": "Salud", "descripcion": "Medicinas, consultas médicas, tratamientos."},
                {"nombre": "Deudas", "descripcion": "Pagos de tarjetas de crédito, préstamos."},
                {"nombre": "Ahorros e inversiones", "descripcion": "Dinero destinado a ahorros o inversiones."},
                {"nombre": "Otros gastos", "descripcion": "Cualquier otro gasto no clasificado."}
            ]
            
            if 'gastos_values' not in st.session_state:
                st.session_state['gastos_values'] = {item['nombre']: 0.0 for item in gastos_items}
            
            gastos_total = 0.0
            
            for item in gastos_items:
                cols = st.columns([4, 1])
                cols[0].markdown(f"""
                    {item['nombre']}
                    {tooltip_icon(item['descripcion'])}
                """, unsafe_allow_html=True)
                
                value = cols[1].text_input(
                    f"Gasto {item['nombre']}",
                    value=format_currency(st.session_state['gastos_values'][item['nombre']]),
                    key=f"gasto_{item['nombre']}",
                    label_visibility="collapsed"
                )
                
                parsed_value = parse_currency(value)
                st.session_state['gastos_values'][item['nombre']] = parsed_value
                gastos_total += parsed_value
            
            # Calcular saldo mensual
            saldo_mensual = ingresos_total - gastos_total
            
            # Mostrar resumen de flujo de caja
            st.markdown(f"""
            <div class="calculator-container">
                <h4>Resumen Flujo de Caja</h4>
                <table style="width:100%">
                    <tr>
                        <td><strong>Total Ingresos:</strong></td>
                        <td class="positive-value">{format_currency(ingresos_total)}</td>
                    </tr>
                    <tr>
                        <td><strong>Total Gastos:</strong></td>
                        <td class="negative-value">{format_currency(gastos_total)}</td>
                    </tr>
                    <tr style="font-weight:bold; background-color:#EFF6FF;">
                        <td><strong>Saldo Mensual:</strong></td>
                        <td class="{ 'positive-value' if saldo_mensual >= 0 else 'negative-value' }">{format_currency(saldo_mensual)}</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            if saldo_mensual > 0:
                st.success(f"Tienes {format_currency(saldo_mensual)} disponibles cada mes para ahorrar o invertir en bienes raíces.")
            else:
                st.error(f"Estás gastando {format_currency(abs(saldo_mensual))} más de lo que ganas cada mes. Considera ajustar tus gastos.")
            
            if st.button("Analizar mi situación financiera para bienes raíces"):
                analisis = analizar_situacion_financiera(ingresos_total, gastos_total, activos_total['neto'], activos_total['deuda'])
                st.session_state['reporte_data']['finanzas'] = {
                    'ingresos': ingresos_total,
                    'gastos': gastos_total,
                    'activos': activos_total['neto'],
                    'pasivos': activos_total['deuda']
                }
                st.session_state['reporte_data']['analisis']['resumen'] = analisis['resumen']
                st.session_state['reporte_data']['analisis']['perfil_inversion'] = analisis['perfil_inversion']
                
                # Generar y mostrar plan de trabajo específico para bienes raíces
                plan = generar_plan_trabajo(ingresos_total, gastos_total, activos_total['neto'], activos_total['deuda'])
                st.subheader("📝 Plan de Trabajo para Inversión en Bienes Raíces")
                st.write(plan)
                st.session_state['reporte_data']['analisis']['plan_trabajo'] = plan
                
                # Recomendaciones de cursos según perfil
                if analisis['perfil_inversion']['nivel'].startswith("Alto"):
                    cursos = """
                    **Recomendaciones de Cursos:**
                    - Curso Avanzado de Estrategias Inmobiliarias
                    - Taller de Financiamiento Creativo para Propiedades
                    - Masterclass en Identificación de Oportunidades
                    """
                elif analisis['perfil_inversion']['nivel'].startswith("Medio"):
                    cursos = """
                    **Recomendaciones de Cursos:**
                    - Curso Intermedio de Inversión en Bienes Raíces
                    - Taller de Co-Inversiones y Sociedades
                    - Seminario de Análisis de Mercado Local
                    """
                else:
                    cursos = """
                    **Recomendaciones de Cursos:**
                    - Curso Básico de Educación Financiera
                    - Taller de Presupuesto y Ahorro
                    - Introducción a la Inversión en Bienes Raíces
                    """
                
                st.session_state['reporte_data']['analisis']['recomendaciones_cursos'] = cursos
                
                # Mostrar recursos adicionales
                st.subheader("🎓 Recursos Educativos Recomendados")
                st.markdown("""
                - [Canal de YouTube de Carlos Devis](https://www.youtube.com/@carlosdevis)
                - [Ciclo Educativo Taller de Bienes Raíces](https://landing.tallerdebienesraices.com/registro-ciclo-educativo/)
                - [Playlist: Estrategias Inmobiliarias](https://www.youtube.com/playlist?list=PL2qGhDf0PEjSF5zxLMa6SlVUxPd4273tl)
                - [Playlist: Financiamiento Creativo](https://www.youtube.com/playlist?list=PL2qGhDf0PEjT9Jy7ULNGfFQvTsruUAyCe)
                """)
    
    # Paso 3: Plan de inversión en bienes raíces
    if 'reporte_data' in st.session_state and st.session_state['reporte_data']['finanzas']:
        with st.container():
            st.subheader("📈 Plan de Inversión en Bienes Raíces")
            
            # Sección de tips como habladores
            with st.expander("💡 ESTRATEGIAS PARA INVERTIR EN BIENES RAÍCES"):
                st.markdown("""
                <div class="tips-container">
                    **1. Propiedades en Remate Bancario**  
                    Los bancos suelen vender propiedades embargadas por debajo del valor de mercado. Requiere investigación pero puede ofrecer excelentes oportunidades.
                    
                    **2. Compra con Opción de Compra**  
                    Negocia con el propietario el derecho a comprar la propiedad en el futuro a un precio acordado, mientras la alquilas.
                    
                    **3. Co-Inversiones**  
                    Asóciate con otros inversionistas para adquirir propiedades que individualmente no podrías comprar.
                    
                    **4. Propiedades con Dueño Directo**  
                    Muchas veces puedes encontrar mejores negocios tratando directamente con dueños que no usan agentes inmobiliarios.
                    
                    **5. Rehabilitación de Propiedades**  
                    Compra propiedades que necesiten reparaciones, haz mejoras estratégicas y véndelas con ganancia o alquílalas por mayor valor.
                    
                    **6. Rentas por Habitación**  
                    En lugar de alquilar una propiedad completa, alquila por habitaciones para maximizar el ingreso.
                    
                    **7. Propiedades Comerciales**  
                    Locales comerciales pueden ofrecer mayores rentabilidades que propiedades residenciales.
                    
                    **8. Terrenos con Potencial**  
                    Identifica terrenos en zonas con crecimiento futuro y adquiérelos antes de que suban de valor.
                    
                    **9. Propiedades con Múltiples Fuentes de Ingreso**  
                    Busca propiedades que permitan generar ingresos adicionales (lavandería, parqueaderos, etc.).
                    
                    **10. Rentas Vacacionales**  
                    Propiedades en zonas turísticas pueden generar ingresos significativos por rentas a corto plazo.
                </div>
                """, unsafe_allow_html=True)
            
            objetivos = st.text_input("Objetivos específicos con bienes raíces", 
                                    "Generar ingresos pasivos a través de propiedades en alquiler")
            horizonte = st.selectbox("Horizonte de inversión", 
                                   ["Corto plazo (1-3 años)", "Mediano plazo (3-5 años)", "Largo plazo (5+ años)"])
            estrategias = st.multiselect("Estrategias de interés", 
                                       ["Alquiler residencial", "Alquiler comercial", "Rehabilitación y venta", 
                                        "Terrenos", "Remates bancarios", "Rentas vacacionales", "Co-inversiones"])
            
            if st.button("Generar estrategia personalizada"):
                st.session_state['plan_inversion'] = (objetivos, horizonte, ", ".join(estrategias))
                ingresos = st.session_state['reporte_data']['finanzas']['ingresos']
                gastos = st.session_state['reporte_data']['finanzas']['gastos']
                activos = st.session_state['reporte_data']['finanzas']['activos']
                pasivos = st.session_state['reporte_data']['finanzas']['pasivos']
                
                analisis_ia = generar_plan_trabajo(ingresos, gastos, activos, pasivos)
                
                st.subheader("🧠 Estrategia Personalizada con IA")
                st.write(analisis_ia)
                st.session_state['reporte_data']['analisis']['analisis_ia'] = analisis_ia
    
    # Paso 4: Plan de retiro con bienes raíces
    if 'reporte_data' in st.session_state and st.session_state['reporte_data']['usuario']:
        with st.container():
            st.subheader("👴 Plan de Retiro con Bienes Raíces")
            
            col1, col2 = st.columns(2)
            edad_actual = col1.number_input("Tu edad actual", min_value=18, max_value=100, value=st.session_state['reporte_data']['usuario']['edad'])
            edad_retiro = col2.number_input("Edad de retiro deseada", min_value=edad_actual+1, max_value=100, value=65)
            
            ingresos_retiro = parse_currency(
                st.text_input("Ingresos anuales esperados durante el retiro", value="$40,000")
            )
            gastos_retiro = parse_currency(
                st.text_input("Gastos anuales esperados durante el retiro", value="$30,000")
            )
            ahorros_retiro = parse_currency(
                st.text_input("Ahorros actuales para el retiro", value="$10,000")
            )
            
            if st.button("Calcular proyección de retiro con bienes raíces"):
                ingresos = st.session_state['reporte_data']['finanzas']['ingresos']
                gastos = st.session_state['reporte_data']['finanzas']['gastos']
                activos = st.session_state['reporte_data']['finanzas']['activos']
                pasivos = st.session_state['reporte_data']['finanzas']['pasivos']
                
                flujo_caja = ingresos - gastos
                patrimonio_neto = activos - pasivos
                
                analisis = analizar_proyeccion_retiro(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro, patrimonio_neto, flujo_caja)
                st.session_state['reporte_data']['analisis']['proyeccion_retiro'] = analisis
                
                st.subheader("📊 Proyección de Retiro con Bienes Raíces")
                st.write(f"**Años hasta el retiro:** {analisis['años_ahorro']}")
                st.write(f"**Necesidad total estimada:** {format_currency(analisis['necesidad_total'])}")
                st.write(f"**Ahorros actuales:** {format_currency(ahorros_retiro)}")
                st.write(f"**Necesitas ahorrar aproximadamente:** {format_currency(analisis['ahorro_necesario_anual'])} anuales")
                
                st.subheader("🏡 Estrategias con Bienes Raíces para tu Retiro")
                st.write("1. **Propiedades generadoras de ingreso pasivo:** Adquiere propiedades en alquiler que cubran tus gastos de retiro")
                st.write("2. **Apreciación de capital:** Invierte en zonas con potencial de crecimiento para vender con ganancia al retirarte")
                st.write("3. **Fondos inmobiliarios (REITs):** Alternativa más líquida para exposición al mercado inmobiliario")
                
                st.subheader("🎓 Recursos Educativos para Preparar tu Retiro")
                st.markdown("""
                - [Curso: Bienes Raíces para el Retiro](https://www.tallerdebienesraices.com/cursos/retiro)
                - [Seminario: Estrategias de Ingreso Pasivo](https://www.tallerdebienesraices.com/seminarios/ingreso-pasivo)
                - [Guía: Planificación Financiera para el Retiro](https://www.tallerdebienesraices.com/guias/retiro)
                """)
    
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
        <h3>📌 Próximos Pasos</h3>
        <ul>
            <li>Revisa nuestro <a href="https://www.youtube.com/@carlosdevis" target="_blank">canal de YouTube</a> para más estrategias</li>
            <li>Inscríbete en nuestro <a href="https://landing.tallerdebienesraices.com/registro-ciclo-educativo/" target="_blank">ciclo educativo</a></li>
            <li>Asiste a nuestros eventos presenciales y online</li>
            <li>Comienza con una propiedad pequeña y escala progresivamente</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    crear_base_datos()
    main()
