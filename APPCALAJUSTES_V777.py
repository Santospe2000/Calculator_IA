import streamlit as st
from openai import OpenAI
import sqlite3
from fpdf import FPDF
import base64
from io import BytesIO
import re
import os
import pandas as pd

# Configuración inicial de la página DEBE SER LO PRIMERO
st.set_page_config(
    page_title="Taller de Bienes Raíces",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Configuración del cliente de OpenAI (versión segura)
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
        
        .tooltip {
            position: relative;
            display: inline-block;
            cursor: help;
        }
        
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 200px;
            background-color: #1E3A8A;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
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
    pdf.cell(200, 10, txt="Informe Financiero - Taller de Bienes Raíces", ln=1, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Análisis para Inversiones Inmobiliarias", ln=1, align='C')
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
    pdf.cell(200, 10, txt=f"Perfil de Inversión: {analisis_data.get('perfil_inversion', 'No determinado')}", ln=1)
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
        pdf.cell(200, 10, txt="Plan de Trabajo para Bienes Raíces:", ln=1)
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
            perfil_inversion TEXT,
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

# Función para crear la tabla de activos/pasivos con tooltips
def create_asset_table():
    # Definir tooltips para cada campo
    tooltips = {
        "Inmueble 1": "Valor de mercado de tu primera propiedad inmobiliaria",
        "Inmueble 2": "Valor de mercado de tu segunda propiedad inmobiliaria",
        "Automóvil 1": "Valor actual de tu vehículo principal",
        "Automóvil 2": "Valor actual de tu vehículo secundario",
        "Muebles": "Valor estimado de tus muebles y enseres",
        "Joyas": "Valor aproximado de tus joyas y artículos de valor",
        "Arte": "Valor de tus obras de arte o colecciones",
        "Efectivo cuenta 1": "Saldo disponible en tu cuenta bancaria principal",
        "Efectivo cuenta 2": "Saldo disponible en tu cuenta bancaria secundaria",
        "Deudas por cobrar": "Dinero que otras personas/empresas te deben",
        "Bonos o títulos valores": "Valor de tus inversiones en bonos o títulos",
        "Fondo de retiro": "Saldo acumulado en tus fondos de pensiones",
        "Bonos o derechos laborales": "Derechos laborales acumulados"
    }

    # Crear DataFrame inicial
    data = {
        "Descripción": list(tooltips.keys()),
        "Valor ($)": [0.0] * len(tooltips),
        "Deuda ($)": [0.0] * len(tooltips),
        "Activos ($)": [0.0] * len(tooltips)
    }
    
    # Agregar fila de totales
    data["Descripción"].append("Total")
    data["Valor ($)"].append(0.0)
    data["Deuda ($)"].append(0.0)
    data["Activos ($)"].append(0.0)
    
    df = pd.DataFrame(data)

    # Configuración de columnas para el editor
    column_config = {
        "Descripción": st.column_config.Column(
            "Descripción",
            help="Descripción del activo",
            width="medium"
        ),
        "Valor ($)": st.column_config.NumberColumn(
            "Valor ($)",
            help="Valor total del activo",
            format="$%.2f",
            width="small"
        ),
        "Deuda ($)": st.column_config.NumberColumn(
            "Deuda ($)",
            help="Deuda asociada al activo",
            format="$%.2f",
            width="small"
        ),
        "Activos ($)": st.column_config.NumberColumn(
            "Activos ($)",
            help="Valor neto del activo (Valor - Deuda)",
            format="$%.2f",
            width="small",
            disabled=True
        )
    }

    # Mostrar tooltips como marcas de agua en los inputs
    for i, desc in enumerate(df["Descripción"][:-1]):
        if desc in tooltips:
            column_config["Descripción"].help = tooltips[desc]

    # Crear editor de tabla
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        num_rows="fixed",
        key="asset_table"
    )

    # Calcular activos netos y totales
    for i in range(len(edited_df) - 1):
        edited_df.at[i, "Activos ($)"] = edited_df.at[i, "Valor ($)"] - edited_df.at[i, "Deuda ($)"]

    # Calcular totales
    edited_df.at[len(edited_df)-1, "Valor ($)"] = edited_df["Valor ($)"][:-1].sum()
    edited_df.at[len(edited_df)-1, "Deuda ($)"] = edited_df["Deuda ($)"][:-1].sum()
    edited_df.at[len(edited_df)-1, "Activos ($)"] = edited_df["Activos ($)"][:-1].sum()

    return edited_df

# Función para crear la sección de flujo de caja
def create_cashflow_section():
    st.subheader("💸 Flujo de Caja Mensual")
    
    with st.expander("❓ ¿Qué es el flujo de caja?", expanded=False):
        st.markdown("""
        El flujo de caja es la diferencia entre tus ingresos y gastos mensuales.  
        **Positivo:** Generas más de lo que gastas (oportunidad para invertir).  
        **Negativo:** Gastas más de lo que generas (necesitas ajustar finanzas).  
        Para inversiones en bienes raíces, se recomienda un flujo positivo mínimo del 20% de tus ingresos.
        """)
    
    # Ingresos con tooltips
    st.markdown("#### Ingresos")
    col1, col2 = st.columns(2)
    
    ingresos = {
        "Sueldo principal": {"value": 0.0, "tooltip": "Ingresos fijos por trabajo principal", "col": col1},
        "Ingresos adicionales": {"value": 0.0, "tooltip": "Otros ingresos (freelance, alquileres, etc.)", "col": col1},
        "Ingresos pasivos": {"value": 0.0, "tooltip": "Ingresos que no requieren tu tiempo activo", "col": col2},
        "Otros ingresos": {"value": 0.0, "tooltip": "Cualquier otro ingreso no categorizado", "col": col2}
    }
    
    for key, item in ingresos.items():
        item["value"] = item["col"].number_input(
            f"{key} ❓",
            value=item["value"],
            format="%.2f",
            help=item["tooltip"],
            key=f"ingreso_{key}"
        )
    
    total_ingresos = sum(item["value"] for item in ingresos.values())
    
    # Gastos con tooltips
    st.markdown("#### Gastos")
    cols = st.columns(2)
    
    gastos = {
        "Vivienda": {"value": 0.0, "tooltip": "Hipoteca/alquiler, servicios, mantenimiento", "col": cols[0]},
        "Alimentación": {"value": 0.0, "tooltip": "Supermercado, restaurantes", "col": cols[0]},
        "Transporte": {"value": 0.0, "tooltip": "Auto, combustible, transporte público", "col": cols[0]},
        "Entretenimiento": {"value": 0.0, "tooltip": "Salidas, suscripciones, hobbies", "col": cols[0]},
        "Deudas": {"value": 0.0, "tooltip": "Pagos de tarjetas, préstamos", "col": cols[1]},
        "Educación": {"value": 0.0, "tooltip": "Cursos, libros, capacitaciones", "col": cols[1]},
        "Seguros": {"value": 0.0, "tooltip": "Seguros médicos, de vida, de propiedad", "col": cols[1]},
        "Otros gastos": {"value": 0.0, "tooltip": "Cualquier otro gasto no categorizado", "col": cols[1]}
    }
    
    for key, item in gastos.items():
        item["value"] = item["col"].number_input(
            f"{key} ❓",
            value=item["value"],
            format="%.2f",
            help=item["tooltip"],
            key=f"gasto_{key}"
        )
    
    total_gastos = sum(item["value"] for item in gastos.values())
    flujo_caja = total_ingresos - total_gastos
    
    # Análisis de capacidad de inversión
    capacidad_inversion = (flujo_caja / total_ingresos * 100) if total_ingresos > 0 else 0
    
    st.markdown(f"""
    <div class="calculator-container">
        <h4>Resumen Flujo de Caja</h4>
        <p><strong>Total Ingresos:</strong> <span class="positive-value">${total_ingresos:,.2f}</span></p>
        <p><strong>Total Gastos:</strong> <span class="negative-value">${total_gastos:,.2f}</span></p>
        <p><strong>Flujo de Caja:</strong> <span class="{'positive-value' if flujo_caja >= 0 else 'negative-value'}">${flujo_caja:,.2f}</span></p>
        <p><strong>Capacidad de Inversión:</strong> {capacidad_inversion:.1f}% de tus ingresos</p>
    </div>
    """, unsafe_allow_html=True)
    
    return total_ingresos, total_gastos, flujo_caja, capacidad_inversion

# Generar plan de trabajo con enfoque en bienes raíces
def generar_plan_trabajo_bienes_raices(ingresos, gastos, activos, pasivos, capacidad_inversion):
    if not st.session_state.get('openai_configured', False):
        return "Servicio de IA no disponible. Configura tu clave de OpenAI API.", "Desconocido"
    
    prompt = f"""
    Como experto en finanzas personales y bienes raíces (siguiendo la metodología de Carlos Devis), analiza esta situación:
    - Ingresos: ${ingresos:,.2f}/mes
    - Gastos: ${gastos:,.2f}/mes
    - Activos: ${activos:,.2f}
    - Pasivos: ${pasivos:,.2f}
    - Capacidad de inversión: {capacidad_inversion:.1f}% de ingresos
    
    Genera un plan detallado con:
    1. Diagnóstico de situación actual según estándares de inversión en bienes raíces
    2. Perfil de inversor (Baja 0-39%, Media 40-69%, Alta 70-100%)
    3. Estrategias para mejorar flujo de caja para inversiones
    4. Plan de reducción de deudas priorizando libertad financiera
    5. Recomendaciones específicas de inversión en bienes raíces
    6. Metas a corto (3-6 meses), mediano (1-2 años) y largo plazo (3-5+ años)
    7. Cursos específicos de Carlos Devis que debería tomar según su perfil
    
    Base tu análisis en los conceptos de:
    - Efecto apalancamiento
    - Flujo de caja positivo
    - Valoración de propiedades
    - Estrategias de adquisición con poco capital
    - Generación de ingresos pasivos
    
    Referencia estos recursos de Carlos Devis:
    - YouTube: https://www.youtube.com/@carlosdevis
    - Ciclo Educativo: https://landing.tallerdebienesraices.com/registro-ciclo-educativo/
    - Playlist Estrategias: https://www.youtube.com/playlist?list=PL2qGhDf0PEjSF5zxLMa6SlVUxPd4273tl
    - Playlist Análisis: https://www.youtube.com/playlist?list=PL2qGhDf0PEjT9Jy7ULNGfFQvTsruUAyCe
    
    Usa lenguaje claro y motivador, con ejemplos prácticos de bienes raíces.
    Respuesta en español con formato Markdown.
    """
    
    try:
        with st.spinner('Generando tu plan personalizado para inversiones en bienes raíces...'):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un asesor experto en inversiones en bienes raíces, siguiendo la metodología de Carlos Devis. Responde en español con formato Markdown, usando lenguaje claro y motivador."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
        
        # Procesar respuesta para extraer perfil de inversor
        contenido = response.choices[0].message.content
        perfil = "Media"
        if "Perfil de inversor: Alta" in contenido or "70%" in contenido or "100%" in contenido:
            perfil = "Alta"
        elif "Perfil de inversor: Baja" in contenido or "0%" in contenido or "39%" in contenido:
            perfil = "Baja"
        
        # Agregar sección de cursos recomendados
        cursos_recomendados = """
        ### 📚 Cursos Recomendados de Carlos Devis:
        - [Ciclo Educativo de Bienes Raíces](https://landing.tallerdebienesraices.com/registro-ciclo-educativo/) - Ideal para comenzar
        - [Estrategias de Inversión con Poco Dinero](https://www.youtube.com/playlist?list=PL2qGhDf0PEjSF5zxLMa6SlVUxPd4273tl) - Para maximizar recursos limitados
        - [Análisis de Propiedades Rentables](https://www.youtube.com/playlist?list=PL2qGhDf0PEjT9Jy7ULNGfFQvTsruUAyCe) - Para identificar buenas oportunidades
        """
        
        return f"{contenido}\n\n{cursos_recomendados}", perfil
    
    except Exception as e:
        st.error(f"Error al generar el plan: {str(e)}")
        return "No se pudo generar el plan en este momento.", "Desconocido"

# Función para analizar plan de retiro con bienes raíces
def analizar_retiro_bienes_raices(edad_actual, edad_retiro, ingresos_retiro, gastos_retiro, ahorros_retiro, perfil_inversion):
    años_ahorro = edad_retiro - edad_actual
    necesidad_total = (gastos_retiro * 12) * (100 - edad_retiro)  # Estimación conservadora
    ahorro_necesario_anual = (necesidad_total - ahorros_retiro) / años_ahorro if años_ahorro > 0 else 0
    
    # Análisis de bienes raíces para retiro
    propiedades_necesarias = max(necesidad_total / (ingresos_retiro * 12), 1)  # Simplificación
    
    recomendaciones = f"""
    ## 🏘️ Estrategias de Bienes Raíces para tu Retiro:
    
    1. **Inversión en Propiedades Rentables**: 
       - Cada propiedad que genere ${ingresos_retiro/12:,.2f}/mes reduce en 1 el número de propiedades necesarias.
       - Considera propiedades multifamiliares para mayor estabilidad.
    
    2. **Apalancamiento Inteligente**:
       - Usa financiamiento para adquirir más propiedades mientras trabajas.
       - El pago de hipotecas debe ser cubierto por los ingresos de alquiler.
    
    3. **Fondo de Emergencia**:
       - Mantén 6-12 meses de gastos en liquidez para cubrir vacancias o reparaciones.
    
    4. **Educación Continua**:
       - Según tu perfil ({perfil_inversion}), considera estos enfoques:
         { "Alta: Enfoque en adquisición agresiva con apalancamiento" if perfil_inversion == "Alta" else 
          "Media: Combinación de crecimiento y seguridad" if perfil_inversion == "Media" else 
          "Baja: Enfoque en educación primero, luego inversión" }
    """
    
    cursos_recomendados = f"""
    ## 📖 Cursos para Preparar tu Retiro con Bienes Raíces:
    
    - [Planificación Financiera para el Retiro](https://landing.tallerdebienesraices.com/) - Fundamentos esenciales
    - [Construyendo Ingresos Pasivos con Bienes Raíces](https://www.youtube.com/@carlosdevis) - Estrategias prácticas
    - [Estrategias de Inversión a Largo Plazo](https://www.youtube.com/playlist?list=PL2qGhDf0PEjT9Jy7ULNGfFQvTsruUAyCe) - Para tu horizonte de {años_ahorro} años
    """
    
    return {
        "años_ahorro": años_ahorro,
        "necesidad_total": necesidad_total,
        "ahorro_necesario_anual": ahorro_necesario_anual,
        "propiedades_necesarias": propiedades_necesarias,
        "analisis": f"""
        ## 📊 Proyección de Retiro con Bienes Raíces:
        
        - **Años hasta el retiro**: {años_ahorro}
        - **Necesidad total estimada**: ${necesidad_total:,.2f}
        - **Ahorros actuales**: ${ahorros_retiro:,.2f}
        - **Necesitas ahorrar aproximadamente**: ${ahorro_necesario_anual:,.2f} anuales
        - **Propiedades equivalentes necesarias**: {propiedades_necesarias:.1f} (generando ${ingresos_retiro/12:,.2f}/mes cada una)
        
        {recomendaciones}
        
        {cursos_recomendados}
        """
    }

# Interfaz principal de Streamlit
def main():
    load_css()  # Cargar estilos CSS personalizados
    
    # Encabezado con logo
    st.markdown("""
    <div class="header-container">
        <img src="https://via.placeholder.com/60" class="logo" alt="Logo Financiero">
        <div>
            <h1 style="margin:0;color:#1E3A8A;">Taller de Bienes Raíces</h1>
            <h3 style="margin:0;color:#6B7280;">Herramienta de Análisis Financiero para Inversiones</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="calculator-container">
        Esta herramienta te ayudará a analizar tu situación financiera actual con enfoque en inversiones inmobiliarias, 
        crear un plan de acción y establecer metas claras para tu futuro económico siguiendo la metodología de Carlos Devis.
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
            Revisa extractos bancarios y anota todo lo que gastas en efectivo. Identifica oportunidades 
            para mejorar tu flujo de caja y poder invertir en bienes raíces.
            """)
            
            st.markdown("### 🏠 Tabla de Activos y Pasivos")
            asset_table = create_asset_table()
            activos_total = asset_table.at[len(asset_table)-1, "Activos ($)"]
            pasivos_total = asset_table.at[len(asset_table)-1, "Deuda ($)"]
            
            # Flujo de caja mejorado
            ingresos_total, gastos_total, flujo_caja, capacidad_inversion = create_cashflow_section()
            
            if st.button("Analizar mi situación para inversiones en bienes raíces"):
                analisis, perfil = generar_plan_trabajo_bienes_raices(
                    ingresos_total, gastos_total, 
                    activos_total, pasivos_total,
                    capacidad_inversion
                )
                
                st.session_state['perfil_inversion'] = perfil
                st.session_state['reporte_data']['finanzas'] = {
                    'ingresos': ingresos_total,
                    'gastos': gastos_total,
                    'activos': activos_total,
                    'pasivos': pasivos_total
                }
                st.session_state['reporte_data']['analisis']['resumen'] = f"Perfil de Inversión: {perfil}\n\n{analisis}"
                st.session_state['reporte_data']['analisis']['plan_trabajo'] = analisis
                st.session_state['reporte_data']['analisis']['perfil_inversion'] = perfil
                
                st.subheader(f"📝 Plan de Trabajo - Perfil de Inversión: {perfil}")
                st.markdown(analisis, unsafe_allow_html=True)
    
    # Paso 3: Plan de retiro mejorado
    if 'usuario_id' in st.session_state and 'perfil_inversion' in st.session_state:
        with st.container():
            st.subheader("👴 Plan de Retiro con Bienes Raíces")
            
            col1, col2 = st.columns(2)
            edad_actual = col1.number_input("Tu edad actual", min_value=18, max_value=100, value=30)
            edad_retiro = col2.number_input("Edad de retiro deseada", min_value=edad_actual+1, max_value=100, value=65)
            
            ingresos_retiro = st.number_input(
                "Ingresos mensuales esperados durante el retiro ($)", 
                min_value=0.0, 
                value=3000.0,
                help="Ingresos pasivos que deseas tener mensualmente durante el retiro"
            )
            
            gastos_retiro = st.number_input(
                "Gastos mensuales esperados durante el retiro ($)", 
                min_value=0.0, 
                value=2000.0,
                help="Gastos estimados que tendrás mensualmente durante el retiro"
            )
            
            ahorros_retiro = st.number_input(
                "Ahorros actuales para el retiro ($)", 
                min_value=0.0, 
                value=10000.0,
                help="Total acumulado actualmente en fondos de retiro e inversiones"
            )
            
            if st.button("Calcular proyección de retiro con bienes raíces"):
                analisis_retiro = analizar_retiro_bienes_raices(
                    edad_actual, edad_retiro,
                    ingresos_retiro, gastos_retiro,
                    ahorros_retiro, st.session_state['perfil_inversion']
                )
                
                st.session_state['reporte_data']['analisis']['proyeccion_retiro'] = analisis_retiro['analisis']
                st.markdown(analisis_retiro['analisis'], unsafe_allow_html=True)
    
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
            <li>Considera los cursos de Carlos Devis para profundizar en bienes raíces</li>
            <li>Comienza con inversiones pequeñas y escala progresivamente</li>
        </ul>
        
        <h3>🔗 Recursos Recomendados</h3>
        <ul>
            <li><a href="https://www.youtube.com/@carlosdevis" target="_blank">Canal de YouTube de Carlos Devis</a></li>
            <li><a href="https://landing.tallerdebienesraices.com/registro-ciclo-educativo/" target="_blank">Ciclo Educativo de Bienes Raíces</a></li>
            <li><a href="https://www.youtube.com/playlist?list=PL2qGhDf0PEjSF5zxLMa6SlVUxPd4273tl" target="_blank">Estrategias de Inversión con Poco Dinero</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    crear_base_datos()
    main()