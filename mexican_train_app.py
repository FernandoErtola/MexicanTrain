import streamlit as st
import pandas as pd

# ------------------------ Lógica del Juego ------------------------

class MexicanTrainApp:
    def __init__(self):
        if 'grupos' not in st.session_state:
            st.session_state.grupos = {}
        if 'auto_sumar' not in st.session_state:
            st.session_state.auto_sumar = True
        if 'ronda_actual' not in st.session_state:
            st.session_state.ronda_actual = 12

    def toggle_auto_sumar(self):
        st.session_state.auto_sumar = not st.session_state.auto_sumar

    def crear_grupo(self, nombre_grupo):
        if nombre_grupo and nombre_grupo not in st.session_state.grupos:
            st.session_state.grupos[nombre_grupo] = {'jugadores': [], 'partidas': [], 'ranking': {}}

    def agregar_jugadores(self, nombre_grupo, jugadores):
        if nombre_grupo in st.session_state.grupos:
            st.session_state.grupos[nombre_grupo]['jugadores'].extend(jugadores)
            for jugador in jugadores:
                st.session_state.grupos[nombre_grupo]['ranking'].setdefault(jugador, 0)

    def nueva_partida(self, nombre_grupo):
        partida = {'rondas': [], 'puntajes_totales': {j: 0 for j in st.session_state.grupos[nombre_grupo]['jugadores']}}
        st.session_state.grupos[nombre_grupo]['partidas'].append(partida)
        st.session_state.ronda_actual = 12

    def reiniciar_partida(self, nombre_grupo, partida_numero):
        if nombre_grupo in st.session_state.grupos and len(st.session_state.grupos[nombre_grupo]['partidas']) >= partida_numero:
            st.session_state.grupos[nombre_grupo]['partidas'][partida_numero - 1] = {'rondas': [], 'puntajes_totales': {j: 0 for j in st.session_state.grupos[nombre_grupo]['jugadores']}}
            st.session_state.ronda_actual = 12

    def cargar_resultados(self, nombre_grupo, partida_numero, ronda, resultados):
        partida = st.session_state.grupos[nombre_grupo]['partidas'][partida_numero - 1]

        # Si la ronda ya existe, actualizamos
        rondas_existentes = [r['ronda'] for r in partida['rondas']]
        if ronda in rondas_existentes:
            idx = rondas_existentes.index(ronda)
            ronda_anterior = partida['rondas'][idx]['resultados']
            for jugador, puntaje_ant in ronda_anterior.items():
                partida['puntajes_totales'][jugador] -= puntaje_ant
            partida['rondas'][idx]['resultados'] = resultados
            for jugador, puntaje_nuevo in resultados.items():
                partida['puntajes_totales'][jugador] += puntaje_nuevo
        else:
            # Nueva ronda
            partida['rondas'].append({'ronda': ronda, 'resultados': resultados})
            for jugador, puntaje in resultados.items():
                partida['puntajes_totales'][jugador] += puntaje

        if ronda == 0:
            min_puntaje = min(partida['puntajes_totales'].values())
            for jugador, puntaje in partida['puntajes_totales'].items():
                if puntaje == min_puntaje:
                    st.session_state.grupos[nombre_grupo]['ranking'][jugador] += 1
                    partida['rondas'].append({'ronda': 'Ganador', 'resultados': {j: (str(puntaje) + ' 🏆' if j == jugador else str(puntaje)) for j, puntaje in partida['puntajes_totales'].items()}})

    def ver_tabla_partida(self, nombre_grupo, partida_numero, mostrar_totales):
        partida = st.session_state.grupos[nombre_grupo]['partidas'][partida_numero - 1]
        filas = []
        for ronda_data in sorted(
            partida['rondas'],
            key=lambda x: x['ronda'] if isinstance(x['ronda'], int) else -1,
            reverse=True
        ):
            ronda_label = ronda_data['ronda']
            if isinstance(ronda_label, int):
                ronda_label = f"🁢 {ronda_label}"  # Emoji ficha dominó al lado
            fila = {'Ronda': ronda_label}
            fila.update(ronda_data['resultados'])
            filas.append(fila)

        df = pd.DataFrame(filas)

        for i, row in df.iterrows():
            if row['Ronda'] != 'Total':
                puntajes = []
                for col in df.columns:
                    if col != 'Ronda':
                        val = str(row[col]).replace(" ✅", "").replace("🏆", "").strip()
                        if val.isdigit():
                            puntajes.append(int(val))
                if puntajes:
                    min_puntaje = min(puntajes)
                    for col in df.columns:
                        if col != 'Ronda':
                            val = str(row[col]).replace(" ✅", "").replace("🏆", "").strip()
                            if val.isdigit() and int(val) == min_puntaje:
                                df.at[i, col] = f"{row[col]} ✅"

        if mostrar_totales and st.session_state.auto_sumar:
            totales = {j: partida['puntajes_totales'][j] for j in st.session_state.grupos[nombre_grupo]['jugadores']}
            totales['Ronda'] = 'Total'
            df = pd.concat([df, pd.DataFrame([totales])], ignore_index=True)

        return df

    def ver_ranking(self, nombre_grupo):
        ranking = st.session_state.grupos[nombre_grupo]['ranking']
        df_ranking = pd.DataFrame(sorted(ranking.items(), key=lambda item: item[1], reverse=True), columns=['Jugador', 'Partidas Ganadas'])
        df_ranking['Trofeo'] = df_ranking['Partidas Ganadas'].apply(lambda x: "🏆" if x > 0 else "")
        df_ranking['Partidas Ganadas'] = df_ranking.apply(lambda row: f"{row['Partidas Ganadas']} {row['Trofeo']}", axis=1)
        df_ranking = df_ranking.drop(columns=['Trofeo'])
        return df_ranking


# ------------------------ Interfaz Streamlit ------------------------

st.set_page_config(page_title="Mexican Train - Gestor de Partidas", layout="wide")
st.markdown("""
<style>
    .main {background-color: #f5f5f5;}
    .stTextInput > div > div > input {background-color: #ffffff;}
    .stButton > button {
        background-color: #4CAF50; color: white; border: none; padding: 8px 16px; margin-top: 4px;
    }
    .stDataFrame {background-color: #ffffff;}
</style>
""", unsafe_allow_html=True)

st.markdown("# 🚂 Mexican Train - Gestor de Partidas")

app = MexicanTrainApp()

seccion = st.sidebar.radio("Seleccioná una sección", ["Administración de Grupos", "Partidas", "Ranking"])

if seccion == "Administración de Grupos":
    st.write("## ➕ Crear o administrar grupos")
    grupo = st.text_input("Nombre del nuevo grupo")
    if st.button("Crear Grupo"):
        if grupo:
            app.crear_grupo(grupo)
            st.success(f"✅ Grupo '{grupo}' creado")
            st.rerun()
        else:
            st.warning("⚠️ Por favor, ingresá un nombre de grupo válido.")

    if st.session_state.grupos:
        grupo_seleccionado = st.selectbox("🎯 Seleccioná un grupo", list(st.session_state.grupos.keys()))

        st.write(f"## Grupo: {grupo_seleccionado}")
        st.write("### 👥 Integrantes:")
        for jugador in st.session_state.grupos[grupo_seleccionado]['jugadores']:
            st.write(f"- {jugador}")

        jugador = st.text_input("👤 Agregar jugador", key="add_player")

        if st.button("Agregar Jugador"):
            if jugador.strip():
                app.agregar_jugadores(grupo_seleccionado, [jugador.strip()])
                st.success(f"✅ Jugador '{jugador.strip()}' agregado a '{grupo_seleccionado}'")
                st.rerun()
            else:
                st.warning("⚠️ Por favor, ingresá un nombre válido.")

        st.write("### ⚙️ Administración del grupo")
        nuevo_nombre = st.text_input("✏️ Cambiar nombre del grupo", value=grupo_seleccionado, key="rename_group")
        if st.button("Renombrar Grupo"):
            if nuevo_nombre and nuevo_nombre != grupo_seleccionado:
                st.session_state.grupos[nuevo_nombre] = st.session_state.grupos.pop(grupo_seleccionado)
                st.success(f"Grupo renombrado a '{nuevo_nombre}'")
                st.rerun()

        jugador_a_eliminar = st.selectbox("🗑️ Eliminar jugador", st.session_state.grupos[grupo_seleccionado]['jugadores'], key="delete_player")
        if st.button("Eliminar Jugador"):
            st.session_state.grupos[grupo_seleccionado]['jugadores'].remove(jugador_a_eliminar)
            st.session_state.grupos[grupo_seleccionado]['ranking'].pop(jugador_a_eliminar, None)
            st.success(f"Jugador '{jugador_a_eliminar}' eliminado de '{grupo_seleccionado}'")
            st.rerun()

        if st.button("🗑️ Eliminar Grupo"):
            st.session_state.grupos.pop(grupo_seleccionado, None)
            st.success(f"Grupo '{grupo_seleccionado}' eliminado")
            st.rerun()

elif seccion == "Partidas":
    if st.session_state.grupos:
        grupo_seleccionado = st.selectbox("🎯 Seleccioná un grupo", list(st.session_state.grupos.keys()))

        if st.button("🎲 Crear Nueva Partida"):
            app.nueva_partida(grupo_seleccionado)
            st.success("✅ Nueva partida creada")
            st.session_state.ronda_actual = 12
            st.rerun()

        if st.session_state.grupos[grupo_seleccionado]['partidas']:
            partida_numero = len(st.session_state.grupos[grupo_seleccionado]['partidas'])

            mostrar_totales = st.checkbox("Mostrar total de la partida", value=False)

            st.markdown(f"### 📋 Cargando resultados para la ronda **{st.session_state.ronda_actual}**")

            df_input = pd.DataFrame(
                [[0] for _ in st.session_state.grupos[grupo_seleccionado]['jugadores']],
                index=st.session_state.grupos[grupo_seleccionado]['jugadores'],
                columns=["Puntaje"]
            )
            edited_df = st.data_editor(df_input, num_rows="dynamic")

            ronda = st.number_input("🔢 Ronda", min_value=0, max_value=12, step=1, value=st.session_state.ronda_actual, key="ronda_input")

            if st.button("✅ Cargar Resultados"):
                resultados = {jugador: int(edited_df.loc[jugador, "Puntaje"]) for jugador in edited_df.index}
                try:
                    app.cargar_resultados(grupo_seleccionado, partida_numero, ronda, resultados)
                    st.success("Resultados cargados correctamente")
                    st.session_state.ronda_actual = max(0, ronda - 1)
                    st.rerun()
                except ValueError as e:
                    st.warning(str(e))

            st.write("### 📊 Tabla de resultados")
            df_tabla = app.ver_tabla_partida(grupo_seleccionado, partida_numero, mostrar_totales)
            st.dataframe(df_tabla.style.hide(axis='index'), use_container_width=True)

            if st.button("🔄 Reiniciar partida"):
                app.reiniciar_partida(grupo_seleccionado, partida_numero)
                st.success("✅ Partida reiniciada")
                st.session_state.ronda_actual = 12
                st.rerun()

            st.write("### 🏆 Ranking histórico del grupo")
            df_ranking = app.ver_ranking(grupo_seleccionado)
            st.dataframe(df_ranking, use_container_width=True)

elif seccion == "Ranking":
    if st.session_state.grupos:
        grupo_seleccionado = st.selectbox("Seleccioná grupo para ver ranking histórico", list(st.session_state.grupos.keys()))
        st.write(f"### 🏆 Ranking histórico del grupo '{grupo_seleccionado}'")
        df_ranking = app.ver_ranking(grupo_seleccionado)
        st.dataframe(df_ranking, use_container_width=True)
    else:
        st.info("No hay grupos creados todavía.")
