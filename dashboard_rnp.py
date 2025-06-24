import streamlit as st
import pandas as pd
import plotly.express as px

# ======================
# CONFIGURACIÓN INICIAL
# ======================
st.set_page_config(layout="wide")

# ======================
# CARGA Y LIMPIEZA DE DATOS
# ======================
st.title("📊 Tablero académico personalizado")

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
# SIDEBAR – FILTRO DE ESTUDIANTE
# ======================
st.sidebar.title("🔎 Filtro de estudiante")
matricula_select = st.sidebar.selectbox("Selecciona una matrícula", df['Matricula'].unique())
resultado = df[df['Matricula'] == matricula_select]

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
    col5.metric("✅ Completadas", filtro['Completadas'])
    col6.metric("📝 Nota final", round(filtro['Final'], 2))

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

    # Comentario automático
    # Comentario automático comparado con promedio del grupo
    st.subheader("💬 Comentario sugerido")
    
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

else:
    st.warning("⚠️ No se encontró información para esta matrícula. Revisa el archivo CSV.")
