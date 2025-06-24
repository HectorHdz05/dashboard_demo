from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
import streamlit as st
import pandas as pd
import plotly.express as px

def generar_pdf(fila_estudiante, notas_actividades, comentario):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setTitle("Reporte académico")

    # Encabezado
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 1 * inch, f"Reporte académico – {fila_estudiante['Matricula']}")

    c.setFont("Helvetica", 11)
    c.drawString(1 * inch, height - 1.3 * inch, f"Participaciones: {fila_estudiante['Participaciones']}")
    c.drawString(1 * inch, height - 1.5 * inch, f"Vistas: {fila_estudiante['Vistas']}")
    c.drawString(1 * inch, height - 1.7 * inch, f"Minutos activos: {round(fila_estudiante['Minutos en plataforma'], 1)}")
    c.drawString(1 * inch, height - 1.9 * inch, f"% Avance del curso: {fila_estudiante['%Avance del curso']}%")
    c.drawString(1 * inch, height - 2.1 * inch, f"Completadas: {fila_estudiante['Completadas']}")
    c.drawString(1 * inch, height - 2.3 * inch, f"Faltantes: {fila_estudiante['Faltantes']}")
    c.drawString(1 * inch, height - 2.5 * inch, f"Nota final: {round(fila_estudiante['Final'], 2)}")

    # Actividades
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, height - 3.0 * inch, "Calificaciones por actividad:")

    c.setFont("Helvetica", 10)
    y_pos = height - 3.3 * inch
    for actividad, nota in notas_actividades.items():
        c.drawString(1.2 * inch, y_pos, f"{actividad}: {nota}")
        y_pos -= 0.2 * inch
        if y_pos < 1 * inch:
            c.showPage()
            y_pos = height - 1 * inch

    # Comentario
    c.setFont("Helvetica-Bold", 12)
    y_pos -= 0.3 * inch
    c.drawString(1 * inch, y_pos, "Comentario del sistema:")

    c.setFont("Helvetica", 10)
    y_pos -= 0.2 * inch
    for line in comentario.splitlines():
        c.drawString(1.2 * inch, y_pos, line)
        y_pos -= 0.2 * inch

    c.save()
    buffer.seek(0)
    return buffer

# ======================
# CONFIGURACIÓN INICIAL
# ======================
st.set_page_config(layout="wide")

# ======================
# CARGA Y LIMPIEZA DE DATOS
# ======================
st.title("📊 MA1042 - Tablero académico Periodo 1")

# Cargar CSV
df = pd.read_csv("seguimiento_alumnos.csv", encoding="utf-8")

# Limpieza básica
df['Matricula'] = df['Matricula'].astype(str).str.strip()
if 'Nombre alumno' in df.columns:
    df['Nombre alumno'] = df['Nombre alumno'].astype(str).str.strip()

# Conversión segura de 'Horas' a minutos
def time_to_minutes(t):
    try:
        if isinstance(t, str) and ":" in t:
            h, m, s = map(int, t.split(':'))
            return h * 60 + m + s / 60
        elif isinstance(t, float) or isinstance(t, int):
            return t * 24 * 60  # formato decimal de Excel
        else:
            return None
    except:
        return None

df['Minutos en plataforma'] = df['Horas'].apply(time_to_minutes)

# Asegurarse que columnas clave sean numéricas
columnas_numericas = [
    'Participaciones', 'Vistas', 'Minutos en plataforma',
    '%Avance del curso', 'Completadas', 'Faltantes', 'Final'
]
for col in columnas_numericas:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# ======================
# FILTRO DE ESTUDIANTE
# ======================
st.subheader("🔎 Buscar matrícula")
matricula_input = st.text_input("Ingresa tu matrícula exacta (ej. A00012345):").strip()
resultado = df[df['Matricula'].astype(str).str.strip() == matricula_input]

# ======================
# MOSTRAR DASHBOARD
# ======================
if not resultado.empty:
    filtro = resultado.iloc[0]
    nombre = filtro['Nombre alumno'] if 'Nombre alumno' in df.columns else 'Estudiante sin nombre'
    
    st.header(f"Desempeño académico de: {filtro['Matricula']}")

    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    col1.metric("📚 Participaciones", filtro['Participaciones'])
    col2.metric("👁️ Vistas", filtro['Vistas'])
    col3.metric("⏱️ Minutos activos", round(filtro['Minutos en plataforma'], 1))

    col4, col5, col6 = st.columns(3)
    col4.metric("📈 Avance del curso", f"{filtro['%Avance del curso']}%")
    col5.metric("✅ Actividades completadas", filtro['Completadas'])
    col6.metric("📝 Calificación final", round(filtro['Final'], 2))

    # Comparativo vs promedio del grupo
    st.subheader("📊 Comparativo con promedio del grupo")
    df_comp = pd.DataFrame({
        "Indicador": columnas_numericas,
        "Estudiante": [filtro[col] for col in columnas_numericas],
        "Promedio grupo": df[columnas_numericas].mean().values
    })

    fig = px.bar(df_comp, x="Indicador", y=["Estudiante", "Promedio grupo"],
                 barmode="group", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    # ========================
    # Comparativo dividido
    # ========================
    st.subheader("📊 Comparativo con el grupo")
    
    # Gráfico 1 – Vistas y tiempo
    comparacion_1 = pd.DataFrame({
        "Indicador": ['Vistas', 'Minutos en plataforma'],
        "Estudiante": [filtro['Vistas'], filtro['Minutos en plataforma']],
        "Promedio grupo": [
            df['Vistas'].mean(), df['Minutos en plataforma'].mean()
        ]
    })
    
    # Gráfico 2 – Participaciones y calificaciones
    comparacion_2 = pd.DataFrame({
        "Indicador": ['Participaciones', 'Completadas', 'Faltantes', 'Final'],
        "Estudiante": [filtro['Participaciones'], filtro['Completadas'], filtro['Faltantes'], filtro['Final']],
        "Promedio grupo": [
            df['Participaciones'].mean(),
            df['Completadas'].mean(),
            df['Faltantes'].mean(),
            df['Final'].mean()
        ]
    })
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("**🟦 Actividad en plataforma**")
        fig_g1 = px.bar(comparacion_1, x="Indicador", y=["Estudiante", "Promedio grupo"],
                        barmode="group", text_auto=True)
        st.plotly_chart(fig_g1, use_container_width=True)
    
    with col_g2:
        st.markdown("**🟩 Desempeño académico**")
        fig_g2 = px.bar(comparacion_2, x="Indicador", y=["Estudiante", "Promedio grupo"],
                        barmode="group", text_auto=True)
        st.plotly_chart(fig_g2, use_container_width=True)

    # Calificaciones por actividad
    st.subheader("🧾 Desempeño por actividad")
    actividades = [col for col in df.columns if any(x in col for x in ['Actividad', 'Quiz', 'Fase', 'Evidencia'])]
    notas = filtro[actividades]
    df_notas = pd.DataFrame({
        "Actividad": notas.index,
        "Calificación": notas.values
    }).dropna()

    fig2 = px.bar(df_notas, x="Actividad", y="Calificación",
                  color="Calificación", text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

    # Comentario automático comparado con promedio del grupo
    st.subheader("💬 Feedback sugerido")
    
    nota_final = filtro['Final']
    prom_grupo = df['Final'].mean()
    
    if pd.isna(nota_final):
        st.warning("Este estudiante no tiene una nota final registrada aún.")
    elif nota_final < prom_grupo - 1:
        st.warning("Tu nota está por debajo del promedio del grupo. Revisa actividades pendientes y solicita retroalimentación.")
    elif prom_grupo - 1 <= nota_final <= prom_grupo + 1:
        st.info("Estás en el promedio del grupo. ¡Sigue así y busca pequeñas mejoras!")
    elif nota_final > prom_grupo + 1:
        st.success("¡Vas por encima del promedio del grupo! Excelente desempeño.")

    # Descarga en PDF
    st.subheader("⬇️ Descargar reporte en PDF")
    
    comentario_final = ""
    if pd.isna(nota_final):
        comentario_final = "Este estudiante no tiene una nota final registrada aún."
    elif nota_final < prom_grupo - 1:
        comentario_final = "Tu nota está por debajo del promedio del grupo. Revisa actividades pendientes y solicita retroalimentación."
    elif prom_grupo - 1 <= nota_final <= prom_grupo + 1:
        comentario_final = "Estás en el promedio del grupo. ¡Sigue así y busca pequeñas mejoras!"
    elif nota_final > prom_grupo + 1:
        comentario_final = "¡Vas por encima del promedio del grupo! Excelente desempeño."
    
    pdf_bytes = generar_pdf(filtro, df_notas.set_index("Actividad")["Calificación"].to_dict(), comentario_final)
    
    st.download_button(
        label="Descargar reporte PDF",
        data=pdf_bytes,
        file_name=f"reporte_{filtro['Matricula']}.pdf",
        mime="application/pdf"
    )

else:
    st.warning("⚠️ No se encontró información para esta matrícula. Revisa el archivo CSV.")
