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
        
        .field-description {
            font-size: 0.85rem;
            color: var(--gris);
            margin-top: -10px;
            margin-bottom: 10px;
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
        **Resumen Financiero:**
        
        - **Ingresos Mensuales:** {format_currency(ingresos)}
        - **Gastos Mensuales:** {format_currency(gastos)}
        - **Flujo de Caja:** {format_currency(flujo_caja_mensual)} ({'Positivo' if flujo_caja_mensual > 0 else 'Negativo'})
        - **Patrimonio Neto:** {format_currency(patrimonio_neto)}
        
        **Perfil de Inversión:** {perfil}
        {descripcion}
        """
    }

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
        st.markdown("**Nombre completo**")
        st.markdown('<div class="field-description">Ingresa tu nombre completo como aparece en tus documentos</div>', unsafe_allow_html=True)
        nombre = st.text_input("Nombre", label_visibility="collapsed")
        
        st.markdown("**Edad**")
        st.markdown('<div class="field-description">Debes ser mayor de 18 años para usar esta herramienta</div>', unsafe_allow_html=True)
        edad = st.number_input("Edad", min_value=18, max_value=100, value=30, label_visibility="collapsed")
        
        st.markdown("**Email**")
        st.markdown('<div class="field-description">Ingresa un email válido para recibir tu reporte</div>', unsafe_allow_html=True)
        email = st.text_input("Email", label_visibility="collapsed")
        
        st.markdown("**Teléfono**")
        st.markdown('<div class="field-description">Número de contacto opcional</div>', unsafe_allow_html=True)
        telefono = st.text_input("Teléfono", label_visibility="collapsed")
        
        if st.button("Guardar información personal"):
            if nombre and email:
                usuario_id = registrar_usuario(nombre, edad, email, telefono)
                st.session_state['usuario_id'] = usuario_id
                st.session_state['reporte_data']['usuario'] = {
                    'nombre': nombre, 'edad': edad, 'email': email, 'telefono': telefono
                }
                st.success("Información guardada correctamente")
            else:
                st.warning("Por favor completa los campos obligatorios (Nombre y Email)")
    
    # Sección 2: Activos y Pasivos
    if 'usuario_id' in st.session_state:
        with st.expander("💰 Activos y Pasivos", expanded=True):
            st.markdown("""
            <h4 style="color: var(--azul-oscuro);">Activos</h4>
            <p class="field-description">Ingresa el valor de mercado de tus activos y cualquier deuda asociada</p>
            """, unsafe_allow_html=True)
            
            activos_items = [
                {"nombre": "Propiedad Principal", "desc": "Valor de mercado de tu vivienda principal"},
                {"nombre": "Otras Propiedades", "desc": "Valor de otras propiedades que poseas"},
                {"nombre": "Vehículos", "desc": "Valor actual de tus automóviles"},
                {"nombre": "Inversiones Financieras", "desc": "Valor de cuentas de ahorro, acciones, fondos, etc."}
            ]
            
            if 'activos_values' not in st.session_state:
                st.session_state['activos_values'] = {item['nombre']: {"valor": 0.0, "deuda": 0.0} for item in activos_items}
            
            activos_total = 0.0
            for item in activos_items:
                st.markdown(f"**{item['nombre']}**")
                st.markdown(f'<div class="field-description">{item["desc"]}</div>', unsafe_allow_html=True)
                
                cols = st.columns(2)
                with cols[0]:
                    valor = st.text_input(
                        f"Valor {item['nombre']}",
                        value=format_currency(st.session_state['activos_values'][item['nombre']]['valor']),
                        key=f"val_{item['nombre']}",
                        label_visibility="collapsed"
                    )
                
                with cols[1]:
                    deuda = st.text_input(
                        f"Deuda {item['nombre']}",
                        value=format_currency(st.session_state['activos_values'][item['nombre']]['deuda']),
                        key=f"deuda_{item['nombre']}",
                        label_visibility="collapsed"
                    )
                
                valor_num = parse_currency(valor)
                deuda_num = parse_currency(deuda)
                neto = valor_num - deuda_num
                
                st.session_state['activos_values'][item['nombre']] = {
                    'valor': valor_num, 
                    'deuda': deuda_num
                }
                activos_total += neto
            
            st.markdown(f"""
            <div class="calculator-container">
                <h4>Resumen de Activos</h4>
                <p><strong>Total Activos Netos:</strong> {format_currency(activos_total)}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Sección 3: Flujo de caja
    if 'usuario_id' in st.session_state:
        with st.expander("💸 Flujo de Caja Mensual", expanded=True):
            st.markdown("""
            <h4 style="color: var(--azul-oscuro);">Ingresos y Gastos Mensuales</h4>
            <p class="field-description">Ingresa tus ingresos y gastos mensuales promedio</p>
            """, unsafe_allow_html=True)
            
            if 'ingresos_values' not in st.session_state:
                st.session_state['ingresos_values'] = {
                    "Sueldo/Negocio": {"valor": 0.0, "desc": "Ingresos por salario o negocio principal"},
                    "Otros Ingresos": {"valor": 0.0, "desc": "Ingresos adicionales como arriendos, inversiones, etc."}
                }
            
            if 'gastos_values' not in st.session_state:
                st.session_state['gastos_values'] = {
                    "Vivienda": {"valor": 0.0, "desc": "Hipoteca/arriendo, servicios, mantenimiento"},
                    "Alimentación": {"valor": 0.0, "desc": "Supermercado, restaurantes, comida"},
                    "Transporte": {"valor": 0.0, "desc": "Gasolina, transporte público, mantenimiento"},
                    "Otros Gastos": {"valor": 0.0, "desc": "Entretenimiento, educación, salud, etc."}
                }
            
            st.markdown("<h5>Ingresos Mensuales</h5>", unsafe_allow_html=True)
            ingresos_total = 0.0
            for item, data in st.session_state['ingresos_values'].items():
                st.markdown(f"**{item}**")
                st.markdown(f'<div class="field-description">{data["desc"]}</div>', unsafe_allow_html=True)
                valor = st.text_input(
                    f"Ingreso {item}",
                    value=format_currency(data['valor']),
                    key=f"ing_{item}",
                    label_visibility="collapsed"
                )
                valor_num = parse_currency(valor)
                st.session_state['ingresos_values'][item]['valor'] = valor_num
                ingresos_total += valor_num
            
            st.markdown("<h5>Gastos Mensuales</h5>", unsafe_allow_html=True)
            gastos_total = 0.0
            for item, data in st.session_state['gastos_values'].items():
                st.markdown(f"**{item}**")
                st.markdown(f'<div class="field-description">{data["desc"]}</div>', unsafe_allow_html=True)
                valor = st.text_input(
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
                <h4>Resumen Mensual</h4>
                <p><strong>Total Ingresos:</strong> {format_currency(ingresos_total)}</p>
                <p><strong>Total Gastos:</strong> {format_currency(gastos_total)}</p>
                <p><strong>Flujo de Caja:</strong> <span style="color: {'var(--verde)' if flujo_caja >=0 else 'var(--rojo)'}">
                    {format_currency(flujo_caja)}
                </span></p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Analizar mi situación financiera"):
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
                st.markdown(analisis['resumen'])
    
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
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="reporte_bienes_raices.pdf">Descargar Reporte Completo</a>'
            st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    crear_base_datos()
    main()