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

# Logo en base64 (aaaaa.png)
LOGO_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4AkEEjIZJ3zJ9QAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAAJklEQVQ4y2NgGAWjYBSMglEwCkbBKBgFgw0wQjVfYGBg+D8QNQEAL1QBdQdXg0QAAAAASUVORK5CYII="

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
        
        .help-icon {
            color: var(--azul-oscuro);
            cursor: pointer;
            margin-left: 5px;
        }
        
        .help-text {
            display: none;
            background-color: white;
            border: 1px solid var(--gris);
            padding: 10px;
            border-radius: 5px;
            z-index: 100;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            width: 300px;
            position: absolute;
            margin-top: 20px;
        }
        
        .help-icon:focus + .help-text,
        .help-icon:hover + .help-text {
            display: block;
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
            
            .help-text {
                width: 200px;
                font-size: 12px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# Función para mostrar el encabezado con logo
def show_header():
    st.markdown(f"""
    <div class="header-container">
        <img src="data:image/png;base64,{LOGO_BASE64}" class="logo" alt="Logo Taller Bienes Raíces">
        <div>
            <h1 style="margin:0;color:#1E3A8A;">Taller de Bienes Raíces</h1>
            <h3 style="margin:0;color:#6B7280;">Calculadora Financiera para Inversión Inmobiliaria</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Funciones auxiliares
def format_currency(value):
    return f"${value:,.2f}" if value else "$0.00"

def parse_currency(currency_str):
    if not currency_str:
        return 0.0
    num_str = re.sub(r'[^\d.]', '', currency_str)
    return float(num_str) if num_str else 0.0

def help_tooltip(text):
    st.markdown(f"""
    <span class="help-icon" tabindex="0">?
        <span class="help-text">{text}</span>
    </span>
    """, unsafe_allow_html=True)

# Funciones de base de datos
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

# Funciones de análisis financiero
def analizar_proyeccion_retiro(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro, patrimonio_neto, flujo_caja):
    años_ahorro = edad_retiro - edad_actual
    necesidad_total = (ingresos_retiro - gastos_retiro) * (100 - edad_retiro)
    ahorro_necesario_anual = (necesidad_total - ahorros_retiro) / años_ahorro if años_ahorro > 0 else 0
    
    if patrimonio_neto > 50000 and flujo_caja > 1000:
        nivel = "Alto (70-100%)"
        recomendaciones = [
            "Excelente perfil para inversión en bienes raíces.",
            "Considera propiedades generadoras de ingresos pasivos."
        ]
    elif patrimonio_neto > 20000 and flujo_caja > 500:
        nivel = "Medio (40-69%)"
        recomendaciones = [
            "Buen potencial para inversión en bienes raíces.",
            "Considera comenzar con propiedades pequeñas."
        ]
    else:
        nivel = "Bajo (0-39%)"
        recomendaciones = [
            "Enfócate en aumentar ingresos y reducir deudas.",
            "Considera cursos básicos de educación financiera."
        ]
    
    return {
        "años_ahorro": años_ahorro,
        "necesidad_total": necesidad_total,
        "ahorro_necesario_anual": ahorro_necesario_anual,
        "nivel_inversion": nivel,
        "analisis": f"""
        Proyección de Retiro:
        - Años hasta el retiro: {años_ahorro}
        - Necesidad total estimada: {format_currency(necesidad_total)}
        - Ahorros actuales: {format_currency(ahorros_retiro)}
        - Ahorro anual necesario: {format_currency(ahorro_necesario_anual)}
        
        Perfil de Inversión: {nivel}
        Recomendaciones:
        {chr(10).join(recomendaciones)}
        """
    }

def analizar_situacion_financiera(ingresos, gastos, activos, pasivos):
    flujo_caja_mensual = ingresos - gastos
    patrimonio_neto = activos - pasivos
    
    if patrimonio_neto > 50000 and flujo_caja_mensual > 1000:
        perfil = "Alto (70-100%)"
        descripcion = "Excelente perfil para inversión en bienes raíces."
    elif patrimonio_neto > 20000 and flujo_caja_mensual > 500:
        perfil = "Medio (40-69%)"
        descripcion = "Buen potencial para inversión en bienes raíces."
    else:
        perfil = "Bajo (0-39%)"
        descripcion = "Enfócate en mejorar tu situación financiera."
    
    return {
        "flujo_caja": flujo_caja_mensual,
        "patrimonio": patrimonio_neto,
        "perfil_inversion": {
            "nivel": perfil,
            "descripcion": descripcion
        },
        "resumen": f"""
        Situación Financiera:
        - Ingresos: {format_currency(ingresos)}/mes
        - Gastos: {format_currency(gastos)}/mes
        - Flujo de caja: {format_currency(flujo_caja_mensual)}
        - Patrimonio neto: {format_currency(patrimonio_neto)}
        
        Perfil: {perfil}
        {descripcion}
        """
    }

def generar_plan_trabajo(ingresos, gastos, activos, pasivos):
    if not st.session_state.get('openai_configured', False):
        return "Servicio de IA no disponible."
    
    prompt = f"""
    Como experto en bienes raíces, analiza esta situación:
    - Ingresos: {format_currency(ingresos)}/mes
    - Gastos: {format_currency(gastos)}/mes
    - Activos: {format_currency(activos)}
    - Pasivos: {format_currency(pasivos)}
    
    Crea un plan detallado para inversión en bienes raíces.
    Incluye diagnóstico, estrategias y recomendaciones.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asesor experto en bienes raíces."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al generar el plan: {str(e)}"

def generate_pdf(usuario_data, finanzas_data, analisis_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Informe Financiero", ln=1, align='C')
    pdf.cell(200, 10, txt="Taller de Bienes Raíces", ln=1, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Datos Personales:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Nombre: {usuario_data.get('nombre', '')}", ln=1)
    pdf.cell(200, 10, txt=f"Email: {usuario_data.get('email', '')}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Situación Financiera:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Ingresos: {format_currency(finanzas_data.get('ingresos', 0))}/mes", ln=1)
    pdf.cell(200, 10, txt=f"Gastos: {format_currency(finanzas_data.get('gastos', 0))}/mes", ln=1)
    pdf.cell(200, 10, txt=f"Patrimonio: {format_currency(finanzas_data.get('activos', 0) - finanzas_data.get('pasivos', 0))}", ln=1)
    pdf.ln(5)
    
    if 'perfil_inversion' in analisis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Perfil: {analisis_data['perfil_inversion']['nivel']}", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analisis_data['perfil_inversion']['descripcion'])
        pdf.ln(5)
    
    if 'plan_trabajo' in analisis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Plan de Trabajo:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analisis_data['plan_trabajo'])
    
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_bytes = pdf_output.getvalue()
    pdf_output.close()
    return pdf_bytes

# Interfaz principal
def main():
    load_css()
    show_header()
    
    st.markdown("""
    <div class="calculator-container">
        Herramienta para analizar tu capacidad de inversión en bienes raíces 
        y crear un plan de acción personalizado.
    </div>
    """, unsafe_allow_html=True)
    
    if 'reporte_data' not in st.session_state:
        st.session_state['reporte_data'] = {'usuario': {}, 'finanzas': {}, 'analisis': {}}
    
    # Sección 1: Información personal
    with st.expander("📝 Información Personal", expanded=True):
        nombre = st.text_input("Nombre completo")
        edad = st.number_input("Edad", min_value=18, max_value=100, value=30)
        email = st.text_input("Email")
        telefono = st.text_input("Teléfono")
        
        if st.button("Guardar información"):
            if nombre and email:
                usuario_id = registrar_usuario(nombre, edad, email, telefono)
                st.session_state['usuario_id'] = usuario_id
                st.session_state['reporte_data']['usuario'] = {
                    'nombre': nombre, 'edad': edad, 'email': email, 'telefono': telefono
                }
                st.success("Información guardada")
            else:
                st.warning("Completa los campos obligatorios")
    
    # Sección 2: Activos y Pasivos
    if 'usuario_id' in st.session_state:
        with st.expander("💰 Activos y Pasivos", expanded=True):
            st.markdown("""
            <h4 style="color: var(--azul-oscuro);">Activos</h4>
            <p>Ingresa el valor de tus activos y sus deudas asociadas</p>
            """, unsafe_allow_html=True)
            
            activos_items = [
                {"nombre": "Inmueble 1", "help": "Valor de mercado de tu propiedad principal"},
                {"nombre": "Inmueble 2", "help": "Valor de otras propiedades"},
                {"nombre": "Vehículos", "help": "Valor de tus automóviles"},
                {"nombre": "Inversiones", "help": "Valor de tus inversiones financieras"}
            ]
            
            if 'activos_values' not in st.session_state:
                st.session_state['activos_values'] = {item['nombre']: {"valor": 0.0, "deuda": 0.0} for item in activos_items}
            
            cols = st.columns([3, 1, 1, 1])
            cols[0].markdown("<b>Descripción</b>", unsafe_allow_html=True)
            cols[1].markdown("<b>Valor ($)</b>", unsafe_allow_html=True)
            cols[2].markdown("<b>Deuda ($)</b>", unsafe_allow_html=True)
            cols[3].markdown("<b>Neto ($)</b>", unsafe_allow_html=True)
            
            activos_total = 0.0
            for item in activos_items:
                cols = st.columns([3, 1, 1, 1])
                with cols[0]:
                    st.markdown(item['nombre'])
                    help_tooltip(item['help'])
                
                valor = cols[1].text_input(
                    f"Valor {item['nombre']}",
                    value=format_currency(st.session_state['activos_values'][item['nombre']]['valor']),
                    key=f"val_{item['nombre']}",
                    label_visibility="collapsed"
                )
                
                deuda = cols[2].text_input(
                    f"Deuda {item['nombre']}",
                    value=format_currency(st.session_state['activos_values'][item['nombre']]['deuda']),
                    key=f"deuda_{item['nombre']}",
                    label_visibility="collapsed"
                )
                
                valor_num = parse_currency(valor)
                deuda_num = parse_currency(deuda)
                neto = valor_num - deuda_num
                
                cols[3].markdown(f"<div>{format_currency(neto)}</div>", unsafe_allow_html=True)
                
                st.session_state['activos_values'][item['nombre']] = {
                    'valor': valor_num, 
                    'deuda': deuda_num
                }
                activos_total += neto
            
            st.markdown(f"""
            <div class="calculator-container">
                <h4>Totales</h4>
                <p><strong>Total Activos Netos:</strong> {format_currency(activos_total)}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Sección 3: Flujo de caja
    if 'usuario_id' in st.session_state:
        with st.expander("💸 Flujo de Caja Mensual", expanded=True):
            st.markdown("""
            <h4 style="color: var(--azul-oscuro);">Ingresos y Gastos</h4>
            <p>Ingresa tus ingresos y gastos mensuales</p>
            """, unsafe_allow_html=True)
            
            if 'ingresos_values' not in st.session_state:
                st.session_state['ingresos_values'] = {
                    "Sueldo": {"valor": 0.0, "help": "Ingresos por salario o honorarios"},
                    "Otros ingresos": {"valor": 0.0, "help": "Otros ingresos adicionales"}
                }
            
            if 'gastos_values' not in st.session_state:
                st.session_state['gastos_values'] = {
                    "Vivienda": {"valor": 0.0, "help": "Gastos de hipoteca/arriendo, servicios"},
                    "Alimentación": {"valor": 0.0, "help": "Gastos en comida y supermercado"},
                    "Transporte": {"valor": 0.0, "help": "Gastos en transporte y vehículos"},
                    "Otros gastos": {"valor": 0.0, "help": "Otros gastos mensuales"}
                }
            
            st.markdown("<h5>Ingresos</h5>", unsafe_allow_html=True)
            ingresos_total = 0.0
            for item, data in st.session_state['ingresos_values'].items():
                cols = st.columns([4, 1])
                with cols[0]:
                    st.markdown(item)
                    help_tooltip(data['help'])
                valor = cols[1].text_input(
                    f"Ingreso {item}",
                    value=format_currency(data['valor']),
                    key=f"ing_{item}",
                    label_visibility="collapsed"
                )
                valor_num = parse_currency(valor)
                st.session_state['ingresos_values'][item]['valor'] = valor_num
                ingresos_total += valor_num
            
            st.markdown("<h5>Gastos</h5>", unsafe_allow_html=True)
            gastos_total = 0.0
            for item, data in st.session_state['gastos_values'].items():
                cols = st.columns([4, 1])
                with cols[0]:
                    st.markdown(item)
                    help_tooltip(data['help'])
                valor = cols[1].text_input(
                    f"Gasto {item}",
                    value=format_currency(data['valor']),
                    key=f"gasto_{item}",
                    label_visibility="collapsed"
                )
                valor_num = parse_currency(valor)
                st.session_state['gastos_values'][item]['valor'] = valor_num
                gastos_total += valor_num
            
            flujo_caja = ingresos_total - gastos_total
            st.markdown(f"""
            <div class="calculator-container">
                <h4>Resumen</h4>
                <p><strong>Total Ingresos:</strong> {format_currency(ingresos_total)}</p>
                <p><strong>Total Gastos:</strong> {format_currency(gastos_total)}</p>
                <p><strong>Flujo de Caja:</strong> <span class="{'positive-value' if flujo_caja >=0 else 'negative-value'}">
                    {format_currency(flujo_caja)}
                </span></p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Analizar mi situación"):
                pasivos_total = sum(item['deuda'] for item in st.session_state['activos_values'].values())
                analisis = analizar_situacion_financiera(
                    ingresos_total, 
                    gastos_total, 
                    activos_total, 
                    pasivos_total
                )
                
                st.session_state['reporte_data']['finanzas'] = {
                    'ingresos': ingresos_total,
                    'gastos': gastos_total,
                    'activos': activos_total,
                    'pasivos': pasivos_total
                }
                st.session_state['reporte_data']['analisis'] = analisis
                
                st.subheader("📊 Resultados del Análisis")
                st.write(analisis['resumen'])
                
                plan = generar_plan_trabajo(ingresos_total, gastos_total, activos_total, pasivos_total)
                st.session_state['reporte_data']['analisis']['plan_trabajo'] = plan
                st.subheader("📝 Plan de Trabajo")
                st.write(plan)
    
    # Sección 4: Plan de retiro
    if 'usuario_id' in st.session_state and 'reporte_data' in st.session_state and st.session_state['reporte_data']['finanzas']:
        with st.expander("👴 Plan de Retiro", expanded=False):
            edad_actual = st.session_state['reporte_data']['usuario'].get('edad', 30)
            edad_retiro = st.number_input("Edad de retiro deseada", min_value=edad_actual+1, max_value=100, value=65)
            
            if st.button("Calcular proyección de retiro"):
                finanzas = st.session_state['reporte_data']['finanzas']
                analisis = analizar_proyeccion_retiro(
                    edad_actual,
                    edad_retiro,
                    finanzas['ingresos'] * 12 * 0.7,  # 70% de ingresos actuales
                    finanzas['gastos'] * 12 * 0.8,    # 80% de gastos actuales
                    finanzas['activos'] * 0.5,        # 50% de activos como ahorro
                    finanzas['activos'] - finanzas['pasivos'],
                    finanzas['ingresos'] - finanzas['gastos']
                )
                
                st.session_state['reporte_data']['analisis']['proyeccion_retiro'] = analisis
                st.write(analisis['analisis'])
    
    # Generar PDF
    if 'reporte_data' in st.session_state and st.session_state['reporte_data']['usuario']:
        if st.button("📄 Generar Reporte PDF"):
            pdf_bytes = generate_pdf(
                st.session_state['reporte_data']['usuario'],
                st.session_state['reporte_data']['finanzas'],
                st.session_state['reporte_data']['analisis']
            )
            
            st.success("Reporte generado correctamente")
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="reporte_bienes_raices.pdf">Descargar PDF</a>'
            st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    crear_base_datos()
    main()