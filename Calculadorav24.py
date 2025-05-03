import streamlit as st
from openai import OpenAI
import sqlite3
from fpdf import FPDF
import base64
from io import BytesIO
import re
import os
from PIL import Image

# Configuración del cliente de OpenAI
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    st.session_state['openai_configured'] = True
except Exception as e:
    st.error(f"Error al configurar OpenAI: {str(e)}")
    st.session_state['openai_configured'] = False
    client = None

# Configuración inicial de la página
st.set_page_config(
    page_title="Taller de Bienes Raíces",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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
        
        .positive-value {
            color: var(--verde);
            font-weight: bold;
        }
        
        .negative-value {
            color: var(--rojo);
            font-weight: bold;
        }
        
        .assets-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        
        .assets-table th, .assets-table td {
            border: 1px solid #dddddd;
            padding: 8px;
            text-align: left;
        }
        
        .assets-table th {
            background-color: var(--azul-oscuro);
            color: white;
        }
        
        .assets-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .assets-table input {
            width: 95%;
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        .tips-container {
            background-color: #f8f9fa;
            border-left: 4px solid var(--azul-oscuro);
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 0 8px 8px 0;
        }
    </style>
    """, unsafe_allow_html=True)

def format_currency(value):
    return f"${value:,.2f}" if value else "$0.00"

def parse_currency(currency_str):
    if not currency_str:
        return 0.0
    num_str = re.sub(r'[^\d.]', '', currency_str)
    return float(num_str) if num_str else 0.0

def generate_pdf(usuario_data, finanzas_data, analisis_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Informe Financiero Personalizado", ln=1, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Taller de Bienes Raíces", ln=1, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Datos Personales:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Nombre: {usuario_data.get('nombre', '')}", ln=1)
    pdf.cell(200, 10, txt=f"Edad: {usuario_data.get('edad', '')}", ln=1)
    pdf.cell(200, 10, txt=f"Email: {usuario_data.get('email', '')}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Situación Financiera:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Ingresos Mensuales: {format_currency(finanzas_data.get('ingresos', 0))}", ln=1)
    pdf.cell(200, 10, txt=f"Gastos Mensuales: {format_currency(finanzas_data.get('gastos', 0))}", ln=1)
    pdf.cell(200, 10, txt=f"Activos Totales: {format_currency(finanzas_data.get('activos', 0))}", ln=1)
    pdf.cell(200, 10, txt=f"Pasivos Totales: {format_currency(finanzas_data.get('pasivos', 0))}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Análisis y Recomendaciones:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=analisis_data.get('resumen', ''))
    pdf.ln(5)
    
    if 'perfil_inversionista' in analisis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Perfil de Inversionista:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analisis_data['perfil_inversionista'])
    
    if 'cursos_recomendados' in analisis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Cursos Recomendados:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analisis_data['cursos_recomendados'])
    
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_bytes = pdf_output.getvalue()
    pdf_output.close()
    
    return pdf_bytes

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

def analizar_proyeccion_retiro(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro):
    años_ahorro = edad_retiro - edad_actual
    necesidad_total = (ingresos_retiro - gastos_retiro) * (100 - edad_retiro)
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
        """
    }

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
        st.success(f"Tienes un flujo de caja mensual positivo de {format_currency(flujo_caja_mensual)}.")
    else:
        st.error(f"Tienes un flujo de caja mensual negativo de {format_currency(flujo_caja_mensual)}.")
    
    if patrimonio_neto > 0:
        st.success("Tu patrimonio neto es sólido.")
    else:
        st.error("Tu patrimonio neto es negativo.")
    
    return {
        "flujo_caja": flujo_caja_mensual,
        "patrimonio": patrimonio_neto,
        "resumen": f"""
        Situación Financiera Actual:
        - Ingresos Mensuales: {format_currency(ingresos)}
        - Gastos Mensuales: {format_currency(gastos)}
        - Flujo de Caja: {format_currency(flujo_caja_mensual)}
        - Activos Totales: {format_currency(activos)}
        - Pasivos Totales: {format_currency(pasivos)}
        - Patrimonio Neto: {format_currency(patrimonio_neto)}
        """
    }

def generar_plan_trabajo(ingresos, gastos, activos, pasivos):
    if not st.session_state.get('openai_configured'):
        return "Servicio de IA no disponible en este momento."
    
    prompt = f"""
    Como experto en bienes raíces según la metodología de Carlos Devis, analiza:
    - Ingresos: {format_currency(ingresos)}/mes
    - Gastos: {format_currency(gastos)}/mes
    - Activos: {format_currency(activos)}
    - Pasivos: {format_currency(pasivos)}
    
    Crea un plan que incluya:
    1. Diagnóstico de situación actual
    2. Estrategias para bienes raíces
    3. Plan de reducción de deudas
    4. Recomendaciones de inversión
    5. Metas a corto, mediano y largo plazo
    6. Ejercicios prácticos
    
    Determina también el perfil de inversionista y recomienda cursos específicos del programa de Carlos Devis.
    Respuesta en español.
    """
    
    try:
        with st.spinner('Generando tu plan personalizado...'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asesor financiero experto en bienes raíces. Responde en español."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error al generar el plan: {str(e)}")
        return "No se pudo generar el plan en este momento."

def generar_perfil_y_cursos(ingresos, gastos, activos, pasivos, objetivos, preferencias):
    if not st.session_state.get('openai_configured'):
        return "Servicio no disponible", ""
    
    prompt = f"""
    Basado en:
    - Ingresos: {format_currency(ingresos)}/mes
    - Gastos: {format_currency(gastos)}/mes
    - Activos: {format_currency(activos)}
    - Pasivos: {format_currency(pasivos)}
    - Objetivos: {objetivos}
    - Preferencias: {preferencias}
    
    Determina:
    1. Perfil de inversionista (conservador, moderado, agresivo)
    2. Recomendación de 3 cursos de Carlos Devis
    3. Explicación de cómo cada curso puede ayudar
    
    Respuesta en español.
    """
    
    try:
        with st.spinner('Analizando tu perfil...'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en clasificación de perfiles de inversionistas. Responde en español."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error al generar el perfil: {str(e)}")
        return "No se pudo generar el perfil en este momento.", ""

def mostrar_tabla_activos_pasivos():
    items = [
        "Inmueble 1", "Inmueble 2", "Automóvil 1", "Automóvil 2",
        "Muebles", "Joyas", "Arte", "Efectivo cuenta 1",
        "Efectivo cuenta 2", "Deudas por cobrar", "Bonos o títulos valores",
        "Fondo de retiro", "Bonos o derechos laborales"
    ]
    
    if 'activos_pasivos' not in st.session_state:
        st.session_state['activos_pasivos'] = {item: {'valor': 0.0, 'deuda': 0.0} for item in items}
    
    # Crear tabla con 4 columnas exactas
    st.markdown("""
    <table class="assets-table">
        <thead>
            <tr>
                <th style="width:35%">Descripción</th>
                <th style="width:20%">Valor ($)</th>
                <th style="width:20%">Deuda ($)</th>
                <th style="width:25%">Activos ($)</th>
            </tr>
        </thead>
        <tbody>
    """, unsafe_allow_html=True)
    
    total_valor = 0.0
    total_deuda = 0.0
    total_activos = 0.0
    
    for item in items:
        # Obtener valores actuales
        valor = st.session_state['activos_pasivos'][item]['valor']
        deuda = st.session_state['activos_pasivos'][item]['deuda']
        
        # Inputs para Valor y Deuda
        col1, col2, col3 = st.columns([3.5, 2, 2])
        
        with col1:
            st.markdown(f"<div style='padding:6px 8px;'>{item}</div>", unsafe_allow_html=True)
        
        with col2:
            nuevo_valor = st.text_input(
                f"Valor_{item}", value=format_currency(valor),
                key=f"valor_{item}", label_visibility="collapsed"
            )
            valor = parse_currency(nuevo_valor)
            st.session_state['activos_pasivos'][item]['valor'] = valor
        
        with col3:
            nueva_deuda = st.text_input(
                f"Deuda_{item}", value=format_currency(deuda),
                key=f"deuda_{item}", label_visibility="collapsed"
            )
            deuda = parse_currency(nueva_deuda)
            st.session_state['activos_pasivos'][item]['deuda'] = deuda
        
        # Calcular Activos (Valor - Deuda)
        activo = valor - deuda
        activo_class = "negative-value" if activo < 0 else "positive-value"
        
        # Mostrar fila en la tabla
        st.markdown(f"""
        <tr>
            <td>{item}</td>
            <td>{format_currency(valor)}</td>
            <td>{format_currency(deuda)}</td>
            <td class="{activo_class}">{format_currency(activo)}</td>
        </tr>
        """, unsafe_allow_html=True)
        
        # Sumar a totales
        total_valor += valor
        total_deuda += deuda
        total_activos += activo
    
    st.markdown("</tbody></table>", unsafe_allow_html=True)
    
    # Mostrar totales
    total_activos_class = "negative-value" if total_activos < 0 else "positive-value"
    st.markdown(f"""
    <div style="margin-top: 20px;">
        <h4>Totales</h4>
        <p><strong>Total Valor:</strong> {format_currency(total_valor)}</p>
        <p><strong>Total Deuda:</strong> <span class="negative-value">{format_currency(total_deuda)}</span></p>
        <p><strong>Total Activos Netos:</strong> <span class="{total_activos_class}">{format_currency(total_activos)}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    return total_valor, total_deuda, total_activos

def mostrar_flujo_caja():
    if 'ingresos_values' not in st.session_state:
        st.session_state['ingresos_values'] = {
            "Ingresos mensuales adulto 1": 0.0,
            "Ingresos mensuales adulto 2": 0.0,
            "Otros ingresos": 0.0
        }
    
    if 'gastos_values' not in st.session_state:
        st.session_state['gastos_values'] = {
            "Gasto de vivienda": 0.0,
            "Alimentación": 0.0,
            "Educación": 0.0,
            "Transporte": 0.0,
            "Salud": 0.0,
            "Entretenimiento": 0.0,
            "Servicios públicos": 0.0,
            "Seguros": 0.0,
            "Otros gastos": 0.0
        }
    
    st.subheader("💸 Flujo de Caja Mensual")
    
    ingresos_total = 0.0
    st.markdown("<h4>Ingresos</h4>", unsafe_allow_html=True)
    for item in st.session_state['ingresos_values']:
        value = st.text_input(
            f"{item} ($)", 
            value=format_currency(st.session_state['ingresos_values'][item]),
            key=f"ingreso_{item}"
        )
        parsed_value = parse_currency(value)
        st.session_state['ingresos_values'][item] = parsed_value
        ingresos_total += parsed_value
    
    gastos_total = 0.0
    st.markdown("<h4>Gastos</h4>", unsafe_allow_html=True)
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
    
    saldo_mensual = ingresos_total - gastos_total
    
    st.markdown(f"""
    <div class="calculator-container">
        <h4>Resumen Flujo de Caja</h4>
        <p><strong>Total Ingresos:</strong> <span class="positive-value">{format_currency(ingresos_total)}</span></p>
        <p><strong>Total Gastos:</strong> <span class="negative-value">{format_currency(gastos_total)}</span></p>
        <p><strong>Saldo Mensual:</strong> <span class="{ 'positive-value' if saldo_mensual >= 0 else 'negative-value' }">{format_currency(saldo_mensual)}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    return ingresos_total, gastos_total

def mostrar_plan_inversion():
    st.subheader("📈 Plan de Inversión en Bienes Raíces")
    
    with st.expander("💡 CÓMO ENCONTRAR LOS RECURSOS PARA INVERTIR EN BIENES RAÍCES"):
        st.markdown("""
        <div class="tips-container">
            **1. Organiza tu presupuesto**  
            Comienza por valorar y agradecer lo que ya tienes: la fortuna más grande comenzó con un simple dólar.
            
            **2. Ordeña tu negocio**  
            Optimiza los ingresos de tu negocio actual para generar fondos para inversión.
            
            **3. Vende cosas que no estás usando**  
            Convierte activos no productivos en liquidez para tu próxima propiedad.
        </div>
        """, unsafe_allow_html=True)
    
    objetivos = st.selectbox("Objetivos de inversión", 
                           ["Comprar casa propia", "Formación en inversión financiera", "Generar ingresos pasivos"])
    
    horizonte = st.selectbox("Horizonte de inversión", 
                           ["Corto plazo (1-3 años)", "Mediano plazo (3-5 años)", "Largo plazo (5+ años)"])
    
    preferencias = st.multiselect("Preferencias de inversión", 
                                ["Inversión en bienes raíces", "Educación financiera"])
    
    if st.button("Analizar plan de inversión"):
        ingresos, gastos = st.session_state.get('flujo_caja', (0, 0))
        activos, pasivos = st.session_state.get('totales_activos_pasivos', (0, 0, 0))[:2]
        
        analisis_ia = generar_plan_trabajo(ingresos, gastos, activos, pasivos)
        
        st.subheader("🧠 Análisis Profundo")
        st.write(analisis_ia)
        st.session_state['reporte_data']['analisis']['analisis_ia'] = analisis_ia
        
        perfil, cursos = generar_perfil_y_cursos(ingresos, gastos, activos, pasivos, objetivos, ", ".join(preferencias))
        
        st.subheader("👤 Perfil de Inversionista")
        st.write(perfil)
        st.session_state['reporte_data']['analisis']['perfil_inversionista'] = perfil
        
        st.subheader("🎓 Cursos Recomendados")
        st.write(cursos)
        st.session_state['reporte_data']['analisis']['cursos_recomendados'] = cursos
    
    return objetivos, horizonte, preferencias

def mostrar_plan_retiro():
    st.subheader("👴 Plan de Retiro con Bienes Raíces")
    
    col1, col2 = st.columns(2)
    edad_actual = col1.number_input("Tu edad actual", min_value=18, max_value=100, value=30)
    edad_retiro = col2.number_input("Edad de retiro deseada", min_value=edad_actual+1, max_value=100, value=65)
    
    ingresos_retiro = parse_currency(st.text_input("Ingresos anuales esperados ($)", value="$40,000"))
    gastos_retiro = parse_currency(st.text_input("Gastos anuales esperados ($)", value="$30,000"))
    ahorros_retiro = parse_currency(st.text_input("Ahorros actuales ($)", value="$10,000"))
    
    if st.button("Calcular proyección de retiro"):
        analisis = analizar_proyeccion_retiro(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro)
        st.session_state['reporte_data']['analisis']['proyeccion_retiro'] = analisis
        
        st.subheader("📊 Proyección de Retiro")
        st.write(f"**Años hasta el retiro:** {analisis['años_ahorro']}")
        st.write(f"**Necesidad total estimada:** {format_currency(analisis['necesidad_total'])}")
        st.write(f"**Ahorros actuales:** {format_currency(ahorros_retiro)}")
        st.write(f"**Ahorro anual necesario:** {format_currency(analisis['ahorro_necesario_anual'])}")
    
    return edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro

def main():
    load_css()
    
    try:
        logo = Image.open("aaaaa.png")
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(logo, width=80)
        with col2:
            st.markdown("""
            <div>
                <h1 style="margin:0;color:#1E3A8A;">Taller de Bienes Raíces</h1>
                <h3 style="margin:0;color:#6B7280;">Carlos Devis</h3>
            </div>
            """, unsafe_allow_html=True)
    except FileNotFoundError:
        st.markdown("""
        <div class="header-container">
            <div>
                <h1 style="margin:0;color:#1E3A8A;">Taller de Bienes Raíces</h1>
                <h3 style="margin:0;color:#6B7280;">Carlos Devis</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="calculator-container">
        Herramienta para analizar tu situación financiera y crear un plan de acción en bienes raíces.
    </div>
    """, unsafe_allow_html=True)
    
    if 'reporte_data' not in st.session_state:
        st.session_state['reporte_data'] = {'usuario': {}, 'finanzas': {}, 'analisis': {}}
    
    # Registro de usuario
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
                    'nombre': nombre, 'edad': edad, 'email': email, 'telefono': telefono
                }
                st.success("Información guardada correctamente")
    
    # Sección financiera
    if 'usuario_id' in st.session_state:
        # Activos y Pasivos
        total_valor, total_deuda, total_activos = mostrar_tabla_activos_pasivos()
        st.session_state['totales_activos_pasivos'] = (total_valor, total_deuda, total_activos)
        
        # Flujo de Caja
        ingresos_total, gastos_total = mostrar_flujo_caja()
        st.session_state['flujo_caja'] = (ingresos_total, gastos_total)
        
        if st.button("Analizar mi situación financiera"):
            analisis = analizar_situacion_financiera(ingresos_total, gastos_total, total_valor, total_deuda)
            st.session_state['reporte_data']['finanzas'] = {
                'ingresos': ingresos_total, 'gastos': gastos_total,
                'activos': total_valor, 'pasivos': total_deuda
            }
            st.session_state['reporte_data']['analisis']['resumen'] = analisis['resumen']
            
            plan = generar_plan_trabajo(ingresos_total, gastos_total, total_valor, total_deuda)
            st.subheader("📝 Plan de Trabajo")
            st.write(plan)
            st.session_state['reporte_data']['analisis']['plan_trabajo'] = plan
        
        # Plan de Inversión
        mostrar_plan_inversion()
        
        # Plan de Retiro
        mostrar_plan_retiro()
    
    # Descargar PDF
    if 'reporte_data' in st.session_state and st.session_state['reporte_data']['usuario']:
        if st.button("📄 Descargar Reporte Completo en PDF"):
            pdf_bytes = generate_pdf(
                st.session_state['reporte_data']['usuario'],
                st.session_state['reporte_data']['finanzas'],
                st.session_state['reporte_data']['analisis']
            )
            
            st.success("Reporte generado con éxito!")
            
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="reporte_bienes_raices.pdf">Haz clic aquí para descargar tu reporte</a>'
            st.markdown(href, unsafe_allow_html=True)
    
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