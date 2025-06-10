import streamlit as st
from openai import OpenAI
import sqlite3
from fpdf import FPDF
import base64
from io import BytesIO
import re
import os
from datetime import datetime

# Configuración inicial de la página
st.set_page_config(
    page_title="Taller de Bienes Raíces",
    page_icon="🏠",
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
            --primary: #1E3A8A;
            --secondary: #6B7280;
            --success: #10B981;
            --danger: #EF4444;
            --light: #F9FAFB;
            --dark: #111827;
            --white: #FFFFFF;
        }
        
        .stApp {
            max-width: 1000px;
            margin: auto;
            font-family: 'Arial', sans-serif;
            background-color: var(--light);
        }
        
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding: 1rem 0;
            border-bottom: 2px solid var(--primary);
        }
        
        .logo {
            height: 90px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .card {
            background-color: var(--white);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
            border: 1px solid #E5E7EB;
        }
        
        .stButton>button {
            background-color: var(--primary);
            color: var(--white);
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
            border: none;
        }
        
        .stButton>button:hover {
            background-color: #1E40AF;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(30, 58, 138, 0.2);
        }
        
        .stTextInput>div>div>input, 
        .stNumberInput>div>div>input,
        .stSelectbox>div>div>select,
        .stMultiselect>div>div>div {
            border-radius: 8px;
            border: 1px solid var(--secondary);
            padding: 0.75rem;
        }
        
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: var(--primary);
        }
        
        .positive {
            color: var(--success);
            font-weight: 600;
        }
        
        .negative {
            color: var(--danger);
            font-weight: 600;
        }
        
        .help-icon {
            display: inline-flex;
            align-items: center;
            cursor: pointer;
            margin-left: 0.5rem;
            color: var(--primary);
        }
        
        .help-text {
            display: none;
            position: absolute;
            background-color: var(--white);
            border: 1px solid var(--secondary);
            padding: 0.75rem;
            border-radius: 8px;
            z-index: 100;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            width: 300px;
            left: 2rem;
            top: 0;
            font-size: 0.9rem;
        }
        
        .help-icon:hover .help-text {
            display: block;
        }
        
        .table-responsive {
            width: 100%;
            overflow-x: auto;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            font-size: 0.95rem;
        }
        
        .data-table th {
            background-color: var(--primary);
            color: var(--white);
            padding: 0.75rem;
            text-align: left;
        }
        
        .data-table td {
            border: 1px solid #E5E7EB;
            padding: 0.75rem;
            text-align: left;
        }
        
        .data-table tr:nth-child(even) {
            background-color: #F9FAFB;
        }
        
        .data-table tr:hover {
            background-color: #F3F4F6;
        }
        
        .total-row {
            background-color: #EFF6FF !important;
            font-weight: 600;
        }
        
        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .badge-primary {
            background-color: #DBEAFE;
            color: var(--primary);
        }
        
        .badge-success {
            background-color: #D1FAE5;
            color: var(--success);
        }
        
        .badge-warning {
            background-color: #FEF3C7;
            color: #92400E;
        }
        
        .badge-danger {
            background-color: #FEE2E2;
            color: var(--danger);
        }
        
        .progress-container {
            width: 100%;
            background-color: #E5E7EB;
            border-radius: 50px;
            margin: 0.5rem 0;
        }
        
        .progress-bar {
            height: 10px;
            border-radius: 50px;
            background-color: var(--primary);
        }
        
        @media (max-width: 768px) {
            .header-container {
                flex-direction: column;
                text-align: center;
            }
            
            .logo {
                margin: 1rem 0;
            }
            
            .help-text {
                width: 250px;
                left: 0;
                top: 1.5rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# Funciones utilitarias
def format_currency(value):
    """Formatea un valor numérico como moneda"""
    return f"${value:,.2f}" if isinstance(value, (int, float)) else "$0.00"

def parse_currency(currency_str):
    """Convierte un string de moneda a valor numérico"""
    if not currency_str:
        return 0.0
    try:
        num_str = re.sub(r'[^\d.]', '', str(currency_str))
        return float(num_str) if num_str else 0.0
    except:
        return 0.0

def emoji_help_tooltip(text, emoji="ℹ️"):
    """Muestra un tooltip de ayuda con emoji"""
    st.markdown(f"""
    <span class="help-icon">
        {emoji}
        <span class="help-text">{text}</span>
    </span>
    """, unsafe_allow_html=True)

def validate_email(email):
    """Valida el formato de un email"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Funciones de base de datos
def init_database():
    """Inicializa la base de datos SQLite"""
    conn = sqlite3.connect('real_estate_workshop.db')
    cursor = conn.cursor()
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de finanzas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            monthly_income REAL NOT NULL,
            monthly_expenses REAL NOT NULL,
            total_assets REAL NOT NULL,
            total_liabilities REAL NOT NULL,
            net_worth REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Tabla de objetivos de inversión
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investment_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            objectives TEXT NOT NULL,
            time_horizon TEXT NOT NULL,
            strategies TEXT NOT NULL,
            risk_tolerance TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_user_data(name, age, email, phone):
    """Guarda los datos del usuario en la base de datos"""
    if age < 18:
        st.warning("Debes ser mayor de 18 años para usar este programa.")
        return None
    
    if not validate_email(email):
        st.warning("Por favor ingresa un email válido.")
        return None
    
    try:
        conn = sqlite3.connect('real_estate_workshop.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (name, age, email, phone)
            VALUES (?, ?, ?, ?)
        ''', (name, age, email, phone))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        st.error("Este email ya está registrado. Por favor usa otro.")
        return None
    except Exception as e:
        st.error(f"Error al guardar los datos: {str(e)}")
        return None

def save_financial_data(user_id, income, expenses, assets, liabilities, net_worth):
    """Guarda los datos financieros del usuario"""
    try:
        conn = sqlite3.connect('real_estate_workshop.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO finances (user_id, monthly_income, monthly_expenses, 
                                total_assets, total_liabilities, net_worth)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, income, expenses, assets, liabilities, net_worth))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error al guardar los datos financieros: {str(e)}")
        return False

def save_investment_goals(user_id, objectives, horizon, strategies, risk=None, notes=None):
    """Guarda los objetivos de inversión del usuario"""
    try:
        conn = sqlite3.connect('real_estate_workshop.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO investment_goals (user_id, objectives, time_horizon, 
                                        strategies, risk_tolerance, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, objectives, horizon, strategies, risk, notes))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error al guardar los objetivos de inversión: {str(e)}")
        return False

# Funciones de análisis financiero
def calculate_net_worth(assets, liabilities):
    """Calcula el patrimonio neto"""
    return assets - liabilities

def calculate_cash_flow(income, expenses):
    """Calcula el flujo de caja mensual"""
    return income - expenses

def analyze_financial_profile(income, expenses, assets, liabilities):
    """Analiza el perfil financiero para inversión en bienes raíces"""
    cash_flow = calculate_cash_flow(income, expenses)
    net_worth = calculate_net_worth(assets, liabilities)
    
    # Análisis de capacidad de inversión
    if net_worth > 100000 and cash_flow > 2000:
        profile = {
            "level": "Avanzado",
            "description": "Excelente capacidad para inversión en bienes raíces. Puedes considerar propiedades de alto valor y diversificar tu portafolio.",
            "recommendations": [
                "Propiedades multifamiliares o comerciales",
                "Fondos de inversión inmobiliaria (REITs)",
                "Desarrollos de vivienda"
            ],
            "risk": "Moderado-Alto"
        }
    elif net_worth > 50000 and cash_flow > 1000:
        profile = {
            "level": "Intermedio",
            "description": "Buena capacidad para inversión. Considera comenzar con propiedades pequeñas o medianas.",
            "recommendations": [
                "Viviendas unifamiliares en alquiler",
                "Propiedades en remodelación",
                "Co-inversiones con otros socios"
            ],
            "risk": "Moderado"
        }
    elif net_worth > 0 and cash_flow > 500:
        profile = {
            "level": "Principiante",
            "description": "Puedes comenzar con inversiones pequeñas en bienes raíces mientras mejoras tu situación financiera.",
            "recommendations": [
                "Alquiler de habitaciones",
                "Propiedades en remate bancario",
                "Terrenos con potencial"
            ],
            "risk": "Bajo-Moderado"
        }
    else:
        profile = {
            "level": "Preparación",
            "description": "Enfócate en mejorar tu flujo de caja y reducir deudas antes de invertir en propiedades.",
            "recommendations": [
                "Educación financiera",
                "Ahorro sistemático",
                "Reducción de deudas"
            ],
            "risk": "Bajo"
        }
    
    return {
        "cash_flow": cash_flow,
        "net_worth": net_worth,
        "profile": profile,
        "summary": f"""
        **Resumen Financiero:**
        - Ingresos Mensuales: {format_currency(income)}
        - Gastos Mensuales: {format_currency(expenses)}
        - Flujo de Caja: {format_currency(cash_flow)} ({'Positivo' if cash_flow >= 0 else 'Negativo'})
        - Activos Totales: {format_currency(assets)}
        - Pasivos Totales: {format_currency(liabilities)}
        - Patrimonio Neto: {format_currency(net_worth)}
        
        **Perfil de Inversión:** {profile['level']}
        {profile['description']}
        """
    }

def generate_retirement_plan(current_age, retirement_age, retirement_income, retirement_expenses, current_savings, net_worth, cash_flow):
    """Genera un plan de retiro con enfoque en bienes raíces"""
    years_to_retirement = retirement_age - current_age
    annual_need = retirement_income - retirement_expenses
    total_need = annual_need * (100 - retirement_age)  # Estimación simplificada
    required_annual_savings = (total_need - current_savings) / years_to_retirement if years_to_retirement > 0 else 0
    
    # Recomendaciones basadas en el perfil
    if net_worth > 500000 and cash_flow > 3000:
        strategy = "Portafolio diversificado de propiedades generadoras de ingresos pasivos"
        properties_needed = max(1, round(total_need / 30000))  # Estimación de $30k anual por propiedad
    elif net_worth > 200000 and cash_flow > 1500:
        strategy = "Combinación de propiedades en alquiler y fondos inmobiliarios"
        properties_needed = max(1, round(total_need / 40000))
    else:
        strategy = "Enfoque en ahorro sistemático y pequeñas inversiones inmobiliarias"
        properties_needed = 0
    
    return {
        "years_to_retirement": years_to_retirement,
        "annual_need": annual_need,
        "total_need": total_need,
        "required_annual_savings": required_annual_savings,
        "strategy": strategy,
        "properties_needed": properties_needed,
        "analysis": f"""
        **Proyección de Retiro con Bienes Raíces**
        
        - **Años hasta el retiro:** {years_to_retirement}
        - **Necesidad anual en retiro:** {format_currency(annual_need)}
        - **Necesidad total estimada:** {format_currency(total_need)}
        - **Ahorros actuales:** {format_currency(current_savings)}
        - **Ahorro anual requerido:** {format_currency(required_annual_savings)}
        
        **Estrategia Recomendada:**
        {strategy}
        
        **Propiedades estimadas necesarias:** {properties_needed}
        
        **Acciones clave:**
        1. Establece un plan de ahorro sistemático
        2. Educarte sobre inversión en bienes raíces
        3. Comenzar con pequeñas inversiones y escalar
        4. Diversificar tu portafolio inmobiliario
        """
    }

def generate_investment_plan(income, expenses, assets, liabilities, objectives, horizon, strategies):
    """Genera un plan de inversión personalizado usando IA"""
    if not st.session_state.get('openai_configured', False):
        return {
            "plan": "Servicio de IA no disponible. Configura tu clave de OpenAI API para habilitar esta función.",
            "courses": []
        }
    
    prompt = f"""
    Como experto en inversión en bienes raíces, analiza esta situación financiera:
    - Ingresos mensuales: {format_currency(income)}
    - Gastos mensuales: {format_currency(expenses)}
    - Activos totales: {format_currency(assets)}
    - Pasivos totales: {format_currency(liabilities)}
    - Patrimonio neto: {format_currency(assets - liabilities)}
    
    Objetivos del cliente: {objectives}
    Horizonte de tiempo: {horizon}
    Estrategias de interés: {strategies}
    
    Genera un plan detallado que incluya:
    1. Diagnóstico de la situación actual
    2. Estrategias personalizadas para alcanzar los objetivos
    3. Plan de acción con hitos a 3, 6 y 12 meses
    4. Recomendaciones de cursos y recursos educativos
    5. Análisis de riesgos y mitigaciones
    
    Usa un lenguaje claro y motivador, con ejemplos concretos.
    Respuesta en español.
    """
    
    try:
        with st.spinner('Generando tu plan personalizado...'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asesor financiero especializado en bienes raíces. Proporciona recomendaciones prácticas y personalizadas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
        plan = response.choices[0].message.content
        
        # Extraer recomendaciones de cursos (simulado)
        courses = [
            "Curso Básico de Inversión en Bienes Raíces",
            "Estrategias de Financiamiento Inmobiliario",
            "Gestión de Propiedades en Alquiler"
        ]
        
        return {
            "plan": plan,
            "courses": courses
        }
    except Exception as e:
        st.error(f"Error al generar el plan: {str(e)}")
        return {
            "plan": "No se pudo generar el plan en este momento.",
            "courses": []
        }

# Funciones de generación de reportes
def generate_pdf_report(user_data, financial_data, analysis_data):
    """Genera un reporte PDF con los resultados"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Taller de Bienes Raíces - Reporte Personalizado", ln=1, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Análisis Financiero y Plan de Inversión", ln=1, align='C')
    pdf.ln(10)
    
    # Información del usuario
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Información Personal", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Nombre: {user_data.get('name', '')}", ln=1)
    pdf.cell(200, 10, txt=f"Edad: {user_data.get('age', '')}", ln=1)
    pdf.cell(200, 10, txt=f"Email: {user_data.get('email', '')}", ln=1)
    pdf.cell(200, 10, txt=f"Teléfono: {user_data.get('phone', '')}", ln=1)
    pdf.ln(5)
    
    # Situación financiera
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Situación Financiera Actual", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Ingresos Mensuales: {format_currency(financial_data.get('income', 0))}", ln=1)
    pdf.cell(200, 10, txt=f"Gastos Mensuales: {format_currency(financial_data.get('expenses', 0))}", ln=1)
    pdf.cell(200, 10, txt=f"Activos Totales: {format_currency(financial_data.get('assets', 0))}", ln=1)
    pdf.cell(200, 10, txt=f"Pasivos Totales: {format_currency(financial_data.get('liabilities', 0))}", ln=1)
    pdf.cell(200, 10, txt=f"Patrimonio Neto: {format_currency(financial_data.get('net_worth', 0))}", ln=1)
    pdf.ln(5)
    
    # Análisis y recomendaciones
    if 'profile' in analysis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Perfil de Inversión: {analysis_data['profile']['level']}", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analysis_data['profile']['description'])
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Recomendaciones Específicas:", ln=1)
        pdf.set_font("Arial", size=12)
        for rec in analysis_data['profile']['recommendations']:
            pdf.cell(200, 10, txt=f"- {rec}", ln=1)
        pdf.ln(5)
    
    # Plan de inversión
    if 'investment_plan' in analysis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Plan de Inversión Personalizado:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analysis_data['investment_plan']['plan'])
        pdf.ln(5)
        
        if analysis_data['investment_plan']['courses']:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Cursos Recomendados:", ln=1)
            pdf.set_font("Arial", size=12)
            for course in analysis_data['investment_plan']['courses']:
                pdf.cell(200, 10, txt=f"- {course}", ln=1)
            pdf.ln(5)
    
    # Plan de retiro
    if 'retirement_plan' in analysis_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Plan de Retiro con Bienes Raíces:", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=analysis_data['retirement_plan']['analysis'])
        pdf.ln(5)
    
    # Pie de página
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt=f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align='C')
    
    # Guardar PDF en memoria
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_bytes = pdf_output.getvalue()
    pdf_output.close()
    
    return pdf_bytes

# Interfaz principal
def main():
    # Inicializar CSS y base de datos
    load_css()
    init_database()
    
    # Encabezado
    st.markdown("""
    <div class="header-container">
        <div>
            <h1 style="margin:0;">Taller de Bienes Raíces</h1>
            <h3 style="margin:0;color:#6B7280;">Calculadora Financiera para Inversión Inmobiliaria</h3>
        </div>
        <img src="https://raw.githubusercontent.com/Santospe2000/Calculator_IA/main/WhatsApp%20Image%202025-05-19%20at%2012.57.14%20PM.jpeg" class="logo" alt="Logo">
    </div>
    
    <div class="card">
        <p>Esta herramienta te ayudará a analizar tu capacidad para invertir en bienes raíces, 
        crear un plan de acción personalizado y establecer metas claras para construir 
        patrimonio inmobiliario de manera inteligente.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar variables de sesión
    if 'user_data' not in st.session_state:
        st.session_state['user_data'] = {}
    if 'financial_data' not in st.session_state:
        st.session_state['financial_data'] = {}
    if 'analysis_data' not in st.session_state:
        st.session_state['analysis_data'] = {}
    
    # Paso 1: Información personal
    with st.expander("📝 Información Personal", expanded=True):
        st.markdown("### Completa tus datos básicos")
        
        col1, col2 = st.columns(2)
        name = col1.text_input("Nombre completo*")
        age = col2.number_input("Edad*", min_value=18, max_value=100, value=30)
        
        email = st.text_input("Email*")
        phone = st.text_input("Teléfono")
        
        if st.button("Guardar información personal"):
            if name and email and age:
                user_id = save_user_data(name, age, email, phone)
                if user_id:
                    st.session_state['user_id'] = user_id
                    st.session_state['user_data'] = {
                        'name': name,
                        'age': age,
                        'email': email,
                        'phone': phone
                    }
                    st.success("Información guardada correctamente")
            else:
                st.warning("Por favor completa los campos obligatorios (*)")
    
    # Paso 2: Datos financieros (solo si usuario está registrado)
    if 'user_id' in st.session_state:
        with st.expander("💰 Situación Financiera", expanded=True):
            st.markdown("### Ingresa tus datos financieros")
            
            # Activos
            st.markdown("#### Activos")
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.markdown("**Descripción**")
            col2.markdown("**Valor ($)**")
            col3.markdown("**Deuda ($)**")
            
            assets_items = [
                {"name": "Efectivo y cuentas bancarias", "help": "Saldo total en cuentas de ahorro y corriente"},
                {"name": "Inversiones financieras", "help": "Acciones, bonos, fondos de inversión, etc."},
                {"name": "Propiedades inmobiliarias", "help": "Valor de mercado de tus propiedades"},
                {"name": "Vehículos", "help": "Valor actual de tus vehículos"},
                {"name": "Otros activos", "help": "Joyas, arte, equipos, etc."}
            ]
            
            assets_values = {}
            for item in assets_items:
                cols = st.columns([3, 1, 1])
                cols[0].markdown(item['name'])
                emoji_help_tooltip(item['help'])
                
                value = cols[1].number_input(
                    f"Valor {item['name']}",
                    min_value=0.0,
                    value=0.0,
                    key=f"asset_{item['name']}_value",
                    label_visibility="collapsed"
                )
                
                debt = cols[2].number_input(
                    f"Deuda {item['name']}",
                    min_value=0.0,
                    value=0.0,
                    key=f"asset_{item['name']}_debt",
                    label_visibility="collapsed"
                )
                
                assets_values[item['name']] = {
                    "value": value,
                    "debt": debt,
                    "net": value - debt
                }
            
            # Calcular totales de activos
            total_assets = sum(item['value'] for item in assets_values.values())
            total_assets_debt = sum(item['debt'] for item in assets_values.values())
            net_assets = total_assets - total_assets_debt
            
            st.markdown(f"""
            **Total Activos:** {format_currency(total_assets)}  
            **Total Deuda Activos:** {format_currency(total_assets_debt)}  
            **Activos Netos:** {format_currency(net_assets)}
            """)
            
            # Pasivos
            st.markdown("#### Pasivos")
            liabilities_items = [
                {"name": "Tarjetas de crédito", "help": "Saldo total adeudado en tarjetas"},
                {"name": "Préstamos personales", "help": "Préstamos de consumo, estudiantiles, etc."},
                {"name": "Hipotecas", "help": "Saldo pendiente de préstamos hipotecarios"},
                {"name": "Otros pasivos", "help": "Cualquier otra deuda no clasificada"}
            ]
            
            liabilities_values = {}
            for item in liabilities_items:
                cols = st.columns([3, 1])
                cols[0].markdown(item['name'])
                emoji_help_tooltip(item['help'])
                
                value = cols[1].number_input(
                    f"Valor {item['name']}",
                    min_value=0.0,
                    value=0.0,
                    key=f"liability_{item['name']}_value",
                    label_visibility="collapsed"
                )
                
                liabilities_values[item['name']] = value
            
            total_liabilities = sum(liabilities_values.values())
            
            st.markdown(f"**Total Pasivos:** {format_currency(total_liabilities)}")
            
            # Patrimonio neto
            net_worth = net_assets - total_liabilities
            st.markdown(f"**Patrimonio Neto:** {format_currency(net_worth)}")
            
            # Flujo de caja mensual
            st.markdown("#### Flujo de Caja Mensual")
            
            st.markdown("##### Ingresos Mensuales")
            col1, col2 = st.columns(2)
            salary = col1.number_input("Salario/sueldo", min_value=0.0, value=0.0)
            other_income = col2.number_input("Otros ingresos", min_value=0.0, value=0.0)
            total_income = salary + other_income
            
            st.markdown("##### Gastos Mensuales")
            col1, col2 = st.columns(2)
            housing = col1.number_input("Vivienda (arriendo/hipoteca)", min_value=0.0, value=0.0)
            utilities = col2.number_input("Servicios públicos", min_value=0.0, value=0.0)
            
            col1, col2 = st.columns(2)
            food = col1.number_input("Alimentación", min_value=0.0, value=0.0)
            transportation = col2.number_input("Transporte", min_value=0.0, value=0.0)
            
            col1, col2 = st.columns(2)
            health = col1.number_input("Salud", min_value=0.0, value=0.0)
            entertainment = col2.number_input("Entretenimiento", min_value=0.0, value=0.0)
            
            other_expenses = st.number_input("Otros gastos", min_value=0.0, value=0.0)
            total_expenses = housing + utilities + food + transportation + health + entertainment + other_expenses
            
            cash_flow = total_income - total_expenses
            
            st.markdown(f"""
            **Resumen Flujo de Caja:**
            - **Total Ingresos:** {format_currency(total_income)}
            - **Total Gastos:** {format_currency(total_expenses)}
            - **Flujo de Caja Mensual:** {format_currency(cash_flow)}  
            """)
            
            if st.button("Analizar mi situación financiera"):
                analysis = analyze_financial_profile(
                    total_income, total_expenses, 
                    net_assets, total_liabilities
                )
                
                # Guardar datos financieros
                save_financial_data(
                    st.session_state['user_id'],
                    total_income, total_expenses,
                    net_assets, total_liabilities, net_worth
                )
                
                st.session_state['financial_data'] = {
                    'income': total_income,
                    'expenses': total_expenses,
                    'assets': net_assets,
                    'liabilities': total_liabilities,
                    'net_worth': net_worth,
                    'cash_flow': cash_flow
                }
                
                st.session_state['analysis_data']['profile'] = analysis['profile']
                st.session_state['analysis_data']['summary'] = analysis['summary']
                
                st.success("Análisis completado correctamente")
                st.markdown(analysis['summary'])
    
    # Paso 3: Plan de inversión (solo si hay datos financieros)
    if 'financial_data' in st.session_state and st.session_state['financial_data']:
        with st.expander("📈 Plan de Inversión", expanded=True):
            st.markdown("### Define tus objetivos de inversión")
            
            objectives = st.text_area(
                "¿Cuáles son tus objetivos con la inversión en bienes raíces?",
                "Generar ingresos pasivos a través de propiedades en alquiler, diversificar mis inversiones y construir patrimonio a largo plazo."
            )
            
            horizon = st.selectbox(
                "Horizonte de tiempo para tus inversiones",
                ["Corto plazo (1-3 años)", "Mediano plazo (3-5 años)", "Largo plazo (5+ años)"]
            )
            
            strategies = st.multiselect(
                "Estrategias de interés",
                [
                    "Alquiler residencial", "Alquiler comercial", "Rehabilitación y venta",
                    "Terrenos", "Remates bancarios", "Rentas vacacionales", "Co-inversiones",
                    "Fondos inmobiliarios (REITs)", "Desarrollo de propiedades"
                ],
                default=["Alquiler residencial", "Rehabilitación y venta"]
            )
            
            risk_tolerance = st.select_slider(
                "Tolerancia al riesgo",
                options=["Muy baja", "Baja", "Moderada", "Alta", "Muy alta"],
                value="Moderada"
            )
            
            if st.button("Generar plan de inversión personalizado"):
                with st.spinner("Creando tu plan de inversión..."):
                    financial_data = st.session_state['financial_data']
                    investment_plan = generate_investment_plan(
                        financial_data['income'],
                        financial_data['expenses'],
                        financial_data['assets'],
                        financial_data['liabilities'],
                        objectives,
                        horizon,
                        ", ".join(strategies)
                    )
                    
                    # Guardar objetivos de inversión
                    save_investment_goals(
                        st.session_state['user_id'],
                        objectives,
                        horizon,
                        ", ".join(strategies),
                        risk_tolerance
                    )
                    
                    st.session_state['analysis_data']['investment_plan'] = investment_plan
                    
                    st.success("Plan de inversión generado")
                    st.markdown(investment_plan['plan'])
                    
                    if investment_plan['courses']:
                        st.markdown("### Cursos Recomendados")
                        for course in investment_plan['courses']:
                            st.markdown(f"- {course}")
    
    # Paso 4: Plan de retiro (solo si hay datos financieros)
    if 'financial_data' in st.session_state and st.session_state['financial_data']:
        with st.expander("👴 Plan de Retiro", expanded=True):
            st.markdown("### Planificación de Retiro con Bienes Raíces")
            
            col1, col2 = st.columns(2)
            current_age = col1.number_input(
                "Tu edad actual",
                min_value=18,
                max_value=100,
                value=st.session_state['user_data'].get('age', 30)
            )
            retirement_age = col2.number_input(
                "Edad de retiro deseada",
                min_value=current_age + 1,
                max_value=100,
                value=65
            )
            
            retirement_income = st.number_input(
                "Ingresos anuales deseados durante el retiro ($)",
                min_value=0,
                value=40000
            )
            retirement_expenses = st.number_input(
                "Gastos anuales estimados durante el retiro ($)",
                min_value=0,
                value=30000
            )
            current_savings = st.number_input(
                "Ahorros actuales para el retiro ($)",
                min_value=0,
                value=10000
            )
            
            if st.button("Calcular proyección de retiro"):
                financial_data = st.session_state['financial_data']
                retirement_plan = generate_retirement_plan(
                    current_age,
                    retirement_age,
                    retirement_income,
                    retirement_expenses,
                    current_savings,
                    financial_data['net_worth'],
                    financial_data['cash_flow']
                )
                
                st.session_state['analysis_data']['retirement_plan'] = retirement_plan
                
                st.success("Proyección de retiro calculada")
                st.markdown(retirement_plan['analysis'])
    
    # Generar reporte PDF (solo si hay datos completos)
    if all(key in st.session_state for key in ['user_data', 'financial_data', 'analysis_data']):
        with st.expander("📄 Generar Reporte", expanded=True):
            st.markdown("### Descarga tu reporte personalizado")
            
            if st.button("Generar Reporte Completo en PDF"):
                pdf_bytes = generate_pdf_report(
                    st.session_state['user_data'],
                    st.session_state['financial_data'],
                    st.session_state['analysis_data']
                )
                
                st.success("Reporte generado con éxito")
                
                # Crear enlace de descarga
                b64 = base64.b64encode(pdf_bytes).decode()
                href = f"""
                <a href="data:application/octet-stream;base64,{b64}" 
                   download="reporte_bienes_raices_{st.session_state['user_data']['name'].replace(' ', '_')}.pdf"
                   style="display: inline-block; padding: 0.5rem 1rem; background-color: #1E3A8A; color: white; border-radius: 8px; text-decoration: none;">
                   Descargar Reporte PDF
                </a>
                """
                st.markdown(href, unsafe_allow_html=True)
    
    # Pie de página
    st.markdown("---")
    st.markdown("""
    <div class="card">
        <h3>📌 Próximos Pasos</h3>
        <ul>
            <li>Revisa nuestro <a href="https://www.youtube.com/@carlosdevis" target="_blank">canal de YouTube</a> para más estrategias</li>
            <li>Inscríbete en nuestro <a href="https://landing.tallerdebienesraices.com/registro-ciclo-educativo/" target="_blank">ciclo educativo</a></li>
            <li>Asiste a nuestros eventos presenciales y online</li>
            <li>Comienza con una propiedad pequeña y escala progresivamente</li>
        </ul>
        
        <p style="text-align: center; margin-top: 1rem; color: #6B7280; font-size: 0.9rem;">
            © 2023 Taller de Bienes Raíces - Todos los derechos reservados
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()