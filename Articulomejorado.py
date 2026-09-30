import streamlit as st
import pandas as pd
import os

# Configuración de la página
st.set_page_config(page_title="Mi Fichero Académico", layout="wide", page_icon="📚")

CSV_FILE = "mis_articulos.csv"
PDF_DIR = "pdf_articulos"

if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

COLUMNAS_NUEVAS = [
    "ID", "Título", "Autores", "Fecha Publicación", "Tipo Artículo", 
    "Temas", "Resumen", "Utilidad", "Citas Clave", "Ruta PDF"
]

def cargar_datos():
    if os.path.exists(CSV_FILE):
        # Cargar forzando a que todas las columnas salvo ID se lean como texto
        dtypes_dict = {col: str for col in COLUMNAS_NUEVAS if col != "ID"}
        df = pd.read_csv(CSV_FILE, dtype=dtypes_dict)
        
        if "Tema" in df.columns and "Temas" not in df.columns:
            df = df.rename(columns={"Tema": "Temas"})
            
        for col in COLUMNAS_NUEVAS:
            if col not in df.columns:
                if col == "ID":
                    df["ID"] = range(1, len(df) + 1)
                elif col == "Tipo Artículo":
                    df[col] = "Otro"
                elif col in ["Autores", "Fecha Publicación"]:
                    df[col] = "No especificado"
                else:
                    df[col] = ""
                    
        # Asegurar que todas las columnas de texto sean tratadas como string por Pandas
        for col in COLUMNAS_NUEVAS:
            if col == "ID":
                df["ID"] = pd.to_numeric(df["ID"], errors='coerce').fillna(1).astype(int)
            else:
                df[col] = df[col].fillna("").astype(str)
                
        return df[COLUMNAS_NUEVAS]
    else:
        return pd.DataFrame(columns=COLUMNAS_NUEVAS)

def guardar_datos(df):
    df.to_csv(CSV_FILE, index=False)

df = cargar_datos()

# Estado para manejar el modo de edición
if "editando_id" not in st.session_state:
    st.session_state["editando_id"] = None

temas_existentes = set()
if not df.empty:
    for lista_t in df["Temas"].dropna():
        for t in str(lista_t).split(", "):
            if t.strip():
                temas_existentes.add(t.strip())
temas_existentes = sorted(list(temas_existentes))

st.title("📚 Mi Fichero Académico Didáctico")
st.write("Organiza, edita y gestiona fácilmente tus artículos de investigación.")

# --- BARRA LATERAL: FORMULARIO DE INGRESO ---
st.sidebar.header("➕ Agregar Nuevo Artículo")

with st.sidebar.form("nuevo_articulo_form", clear_on_submit=True):
    titulo = st.text_input("1. Título del Artículo *")
    autores = st.text_input("2. Autores", placeholder="Ej. Gómez, A., & Pérez, J.")
    fecha_pub = st.text_input("3. Fecha o Año de Publicación", placeholder="Ej. 2024")
    tipo_articulo = st.selectbox("4. Tipo de Artículo", ["Experimental", "De Revisión", "Otro"])
    
    temas_seleccionados = st.multiselect("5. Seleccionar Temas Existentes", options=temas_existentes)
    nuevos_temas = st.text_input("O escribir nuevos temas (separados por coma)")
    
    resumen = st.text_area("6. ¿De qué trata?")
    utilidad = st.text_area("7. ¿Para qué te sirve?")
    citas = st.text_area("8. Citas o Ideas Importantes")
    archivo_pdf = st.file_uploader("9. Subir archivo PDF del artículo", type=["pdf"])
    
    boton_guardar = st.form_submit_button("💾 Guardar Ficha")

if boton_guardar:
    if not titulo.strip():
        st.sidebar.error("⚠️ El título es obligatorio.")
    else:
        lista_temas_final = list(temas_seleccionados)
        if nuevos_temas.strip():
            lista_temas_final.extend([t.strip() for t in nuevos_temas.split(",") if t.strip()])
        lista_temas_final = list(dict.fromkeys(lista_temas_final))
        str_temas = ", ".join(lista_temas_final) if lista_temas_final else "Sin Categoría"
        
        ruta_pdf_guardada = ""
        if archivo_pdf is not None:
            nombre_limpio = "".join(c for c in titulo[:30] if c.isalnum() or c in (" ", "_")).rstrip()
            pdf_filename = f"{nombre_limpio}_{archivo_pdf.name}"
            ruta_pdf_guardada = os.path.join(PDF_DIR, pdf_filename)
            with open(ruta_pdf_guardada, "wb") as f:
                f.write(archivo_pdf.getbuffer())
        
        nuevo_id = 1 if df.empty else int(df["ID"].max()) + 1
        nueva_fila = pd.DataFrame([{
            "ID": nuevo_id, 
            "Título": str(titulo),
            "Autores": str(autores) if autores else "No especificado",
            "Fecha Publicación": str(fecha_pub) if fecha_pub else "No especificada",
            "Tipo Artículo": str(tipo_articulo), 
            "Temas": str(str_temas),
            "Resumen": str(resumen), 
            "Utilidad": str(utilidad), 
            "Citas Clave": str(citas),
            "Ruta PDF": str(ruta_pdf_guardada)
        }])
        
        df = pd.concat([df, nueva_fila], ignore_index=True)
        guardar_datos(df)
        st.sidebar.success("¡Artículo guardado!")
        st.rerun()

# --- ÁREA PRINCIPAL: CONSULTA Y EDICIÓN ---

if df.empty:
    st.info("👈 Tu fichero está vacío. Agrega tu primer artículo en la barra lateral.")
else:
    opciones_filtro = ["Todos"] + sorted(list(temas_existentes))
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        tema_filtro = st.selectbox("🔎 Filtrar por Tema:", opciones_filtro)
    with col_f2:
        tipo_filtro = st.selectbox("🔬 Filtrar por Tipo:", ["Todos", "Experimental", "De Revisión", "Otro"])

    df_filtrado = df.copy()
    if tema_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Temas"].str.contains(rf"\b{tema_filtro}\b", case=False, na=False)]
    if tipo_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo Artículo"] == tipo_filtro]

    st.markdown("---")
    tab_tarjetas, tab_tabla = st.tabs(["🎴 Fichas Didácticas", "📊 Vista de Tabla"])

    with tab_tarjetas:
        for idx, row in df_filtrado.iterrows():
            badge_tipo = "🧪" if row["Tipo Artículo"] == "Experimental" else "📖"
            
            with st.expander(f"📌 **{row['Título']}**  |  {badge_tipo} *{row['Tipo Artículo']}*  |  🏷️ *[{row['Temas']}]*"):
                
                # --- MODO DE EDICIÓN ---
                if st.session_state["editando_id"] == row["ID"]:
                    st.warning("✏️ Editando información de este artículo:")
                    with st.form(key=f"form_edit_{row['ID']}"):
                        e_titulo = st.text_input("Título", value=str(row["Título"]))
                        e_autores = st.text_input("Autores", value=str(row["Autores"]))
                        e_fecha = st.text_input("Fecha", value=str(row["Fecha Publicación"]))
                        
                        opciones_tipo = ["Experimental", "De Revisión", "Otro"]
                        idx_tipo = opciones_tipo.index(row["Tipo Artículo"]) if row["Tipo Artículo"] in opciones_tipo else 2
                        e_tipo = st.selectbox("Tipo", opciones_tipo, index=idx_tipo)
                        
                        e_temas = st.text_input("Temas (separados por coma)", value=str(row["Temas"]))
                        e_resumen = st.text_area("¿De qué trata?", value=str(row["Resumen"]))
                        e_utilidad = st.text_area("¿Para qué te sirve?", value=str(row["Utilidad"]))
                        e_citas = st.text_area("Citas clave", value=str(row["Citas Clave"]))
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Guardar Cambios"):
                                # Asignación uno a uno asegurando conversión a string
                                df.loc[df["ID"] == row["ID"], "Título"] = str(e_titulo)
                                df.loc[df["ID"] == row["ID"], "Autores"] = str(e_autores)
                                df.loc[df["ID"] == row["ID"], "Fecha Publicación"] = str(e_fecha)
                                df.loc[df["ID"] == row["ID"], "Tipo Artículo"] = str(e_tipo)
                                df.loc[df["ID"] == row["ID"], "Temas"] = str(e_temas)
                                df.loc[df["ID"] == row["ID"], "Resumen"] = str(e_resumen)
                                df.loc[df["ID"] == row["ID"], "Utilidad"] = str(e_utilidad)
                                df.loc[df["ID"] == row["ID"], "Citas Clave"] = str(e_citas)
                                
                                guardar_datos(df)
                                st.session_state["editando_id"] = None
                                st.success("¡Cambios guardados!")
                                st.rerun()
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar"):
                                st.session_state["editando_id"] = None
                                st.rerun()

                # --- MODO LECTURA HABITUAL ---
                else:
                    st.markdown(f"**👨‍🔬 Autores:** {row['Autores']}   |   **📅 Fecha:** {row['Fecha Publicación']}")
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("💡 ¿De qué trata?")
                        st.write(row["Resumen"] if row["Resumen"] else "*(Sin resumen)*")
                        st.subheader("🎯 ¿Para qué sirve?")
                        st.write(row["Utilidad"] if row["Utilidad"] else "*(Sin especificar)*")
                    with col2:
                        st.subheader("💬 Citas / Ideas Clave")
                        st.info(row["Citas Clave"] if row["Citas Clave"] else "*(Sin citas)*")
                    
                    st.markdown("---")
                    c_pdf, c_edit, c_del = st.columns([2, 1, 1])
                    
                    with c_pdf:
                        if row["Ruta PDF"] and os.path.exists(row["Ruta PDF"]):
                            with open(row["Ruta PDF"], "rb") as f_pdf:
                                st.download_button("📄 Descargar PDF", data=f_pdf, file_name=os.path.basename(row["Ruta PDF"]), mime="application/pdf", key=f"pdf_{row['ID']}")
                        else:
                            st.caption("📂 Sin PDF adjunto")
                            
                    with c_edit:
                        if st.button("✏️ Editar", key=f"edit_btn_{row['ID']}"):
                            st.session_state["editando_id"] = row["ID"]
                            st.rerun()
                            
                    with c_del:
                        if st.button("🗑️ Eliminar", key=f"del_card_{row['ID']}"):
                            if row["Ruta PDF"] and os.path.exists(row["Ruta PDF"]):
                                try: os.remove(row["Ruta PDF"])
                                except Exception: pass
                            df = df[df["ID"] != row["ID"]]
                            guardar_datos(df)
                            st.success("Eliminado.")
                            st.rerun()

    with tab_tabla:
        st.dataframe(df_filtrado.drop(columns=["ID", "Ruta PDF"]), use_container_width=True)
        excel_name = "mis_articulos.xlsx"
        df.to_excel(excel_name, index=False)
        with open(excel_name, "rb") as f:
            st.download_button("📥 Descargar Excel", data=f, file_name="fichero_academico.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")