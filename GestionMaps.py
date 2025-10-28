# -*- coding: utf-8 -*-
"""
Created on Mon Oct 27 16:11:00 2025

@author: acer
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import folium
from folium import plugins
from streamlit_folium import st_folium
import time

# Configuración de la página
st.set_page_config(
    page_title="Gestión Territorial",
    page_icon="🗺️",
    layout="wide"
)

# Inicializar datos en session_state
if 'casas' not in st.session_state:
    st.session_state.casas = []
if 'territorios' not in st.session_state:
    st.session_state.territorios = []

# Título principal
st.title("🗺️ Sistema de Gestión Territorial")
st.markdown("---")

# Sidebar para navegación
menu = st.sidebar.selectbox(
    "📋 Menú Principal",
    ["🗺️ Gestionar Territorios", "🏠 Registrar Casa", "📍 Ver Mapa", "📊 Estadísticas", "📋 Lista de Casas"]
)

# Función para guardar datos
def guardar_casa(datos):
    st.session_state.casas.append(datos)
    st.success("✅ Casa registrada exitosamente!")

def guardar_territorio(datos):
    st.session_state.territorios.append(datos)
    st.success("✅ Territorio creado exitosamente!")

# Función para obtener color según estado
def get_color(estado):
    colores = {
        "Atendido": "green",
        "No atendió": "red",
        "No tocar": "black",
        "Solo fines de semana": "blue",
        "Pendiente": "orange"
    }
    return colores.get(estado, "gray")

# Función para obtener icono según estado
def get_icon(estado):
    iconos = {
        "Atendido": "check",
        "No atendió": "remove",
        "No tocar": "ban",
        "Solo fines de semana": "calendar",
        "Pendiente": "time"
    }
    return iconos.get(estado, "home")

# Función para verificar si un punto está dentro de un polígono
def punto_en_poligono(lat, lng, poligono):
    x, y = lat, lng
    n = len(poligono)
    inside = False
    p1x, p1y = poligono[0]
    for i in range(n + 1):
        p2x, p2y = poligono[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

# SECCIÓN: GESTIONAR TERRITORIOS
if menu == "🗺️ Gestionar Territorios":
    st.header("Gestionar Territorios")

    tab1, tab2 = st.tabs(["➕ Crear Territorio", "📋 Ver Territorios"])

    with tab1:
        st.subheader("Crear Nuevo Territorio")

    # --- Inicializar coordenadas base en session_state ---
    if "latitud_base" not in st.session_state:
        st.session_state.latitud_base = 31.7619
    if "longitud_base" not in st.session_state:
        st.session_state.longitud_base = -106.4850

    col1, col2 = st.columns([2, 1])

    # --- Columna derecha: formulario de datos ---
    with col2:
        st.subheader("📋 Datos del Territorio")

        nombre_territorio = st.text_input("📝 Nombre del territorio", placeholder="Ej: Zona Norte")
        descripcion_territorio = st.text_area("📄 Descripción", placeholder="Detalles del territorio...")
        color_territorio = st.color_picker("🎨 Color del territorio", "#FF6B6B")
        responsable = st.text_input("👤 Responsable", placeholder="Nombre del encargado")

        st.markdown("---")
        st.markdown("### 🌎 Coordenadas base (centro del mapa)")

        lat_input = st.number_input(
            "Latitud inicial", value=st.session_state.latitud_base,
            format="%.6f", step=0.0001, key="input_lat"
        )
        lng_input = st.number_input(
            "Longitud inicial", value=st.session_state.longitud_base,
            format="%.6f", step=0.0001, key="input_lng"
        )

        # Botón para centrar mapa
        if st.button("📍 Centrar mapa"):
            st.session_state.latitud_base = float(lat_input)
            st.session_state.longitud_base = float(lng_input)
            st.rerun()

        st.markdown("---")
        st.markdown("**💡 Cómo crear:**")
        st.markdown("""
        1. Usa las herramientas de dibujo en el mapa
        2. Dibuja un polígono o rectángulo
        3. Completa los datos del formulario
        4. Haz clic en 'Guardar Territorio'
        """)

        # --- Botón para guardar territorio ---
        if st.button("💾 Guardar Territorio", type="primary", use_container_width=True):
            if map_data and map_data.get("all_drawings"):
                geometria = map_data["all_drawings"][-1]["geometry"]
                coordenadas = [(y, x) for x, y in geometria["coordinates"][0]]

                nuevo_territorio = {
                    "id": str(uuid.uuid4()),
                    "nombre": nombre_territorio or "Territorio sin nombre",
                    "descripcion": descripcion_territorio,
                    "color": color_territorio,
                    "responsable": responsable or "Sin responsable",
                    "coordenadas": coordenadas,
                    "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }

                st.session_state.territorios.append(nuevo_territorio)
                st.success(f"✅ Territorio '{nuevo_territorio['nombre']}' guardado correctamente.")
                st.rerun()
            else:
                st.warning("⚠️ Dibuja un polígono en el mapa antes de guardar el territorio.")

    # --- Columna izquierda: mapa interactivo ---
    with col1:
        # Crear mapa centrado en coordenadas base
        m = folium.Map(
            location=[st.session_state.latitud_base, st.session_state.longitud_base],
            zoom_start=13,
            tiles="OpenStreetMap"
        )

        # Mostrar territorios ya creados
        for territorio in st.session_state.territorios:
            folium.Polygon(
                locations=territorio["coordenadas"],
                color=territorio["color"],
                fill=True,
                fillColor=territorio["color"],
                fillOpacity=0.3,
                popup=f"<b>{territorio['nombre']}</b><br>{territorio['descripcion']}",
                tooltip=territorio["nombre"]
            ).add_to(m)

        # Habilitar herramientas de dibujo
        draw = plugins.Draw(
            export=True,
            draw_options={
                'polyline': False,
                'rectangle': True,
                'polygon': True,
                'circle': False,
                'marker': False,
                'circlemarker': False,
            }
        )
        draw.add_to(m)

        map_data = st_folium(m, width=800, height=500, key="territorio_map")



    with tab2:
        st.subheader("Lista de Territorios")

        if len(st.session_state.territorios) == 0:
            st.info("No hay territorios creados. Ve a 'Crear Territorio' para empezar.")
        else:
            for i, territorio in enumerate(st.session_state.territorios):
                with st.expander(f"🗺️ {territorio['nombre']}"):
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"**Responsable:** {territorio['responsable']}")
                    col2.write(f"**Creado:** {territorio['fecha_creacion']}")
                    col3.write(f"**Color:** {territorio['color']}")

                    st.write(f"**Descripción:** {territorio['descripcion']}")

                    # Contar casas en este territorio
                    casas_en_territorio = [
                        casa for casa in st.session_state.casas
                        if casa.get("territorio_id") == territorio["id"]
                    ]
                    st.metric("Casas registradas", len(casas_en_territorio))

                    # Botón para eliminar territorio
                    if st.button(f"🗑️ Eliminar territorio '{territorio['nombre']}'", key=f"delete_{territorio['id']}"):
                        # Eliminar casas asociadas
                        st.session_state.casas = [
                            casa for casa in st.session_state.casas
                            if casa.get("territorio_id") != territorio["id"]
                        ]
                        # Eliminar territorio
                        del st.session_state.territorios[i]
                        st.success(f"✅ Territorio '{territorio['nombre']}' eliminado junto con sus casas asociadas.")
                        st.rerun()


# SECCIÓN: REGISTRAR CASA
elif menu == "🏠 Registrar Casa":
    st.header("Registrar Nueva Casa")

    if len(st.session_state.territorios) == 0:
        st.warning("⚠️ No hay territorios creados. Por favor crea un territorio primero en 'Gestionar Territorios'")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🗺️ Territorio")
        if len(st.session_state.territorios) > 0:
            territorio_seleccionado = st.selectbox(
                "Selecciona el territorio",
                options=[t["id"] for t in st.session_state.territorios],
                format_func=lambda x: next(t["nombre"] for t in st.session_state.territorios if t["id"] == x)
            )
        else:
            territorio_seleccionado = None

        st.subheader("📍 Ubicación")
        direccion = st.text_input("Dirección completa", placeholder="Ej: Calle Principal #123")

        # Ayuda para obtener coordenadas
        with st.expander("💡 ¿Cómo obtener coordenadas de Google Maps?"):
            st.markdown("""
            1. Abre [Google Maps](https://www.google.com/maps)
            2. Busca la dirección o haz clic derecho en el mapa
            3. Haz clic en las coordenadas que aparecen
            4. Se copiarán automáticamente (formato: latitud, longitud)
            5. Pégalas aquí abajo

            **Ejemplo de Ciudad Juárez:** 31.7619, -106.4850
            """)

        coordenadas_texto = st.text_input(
            "Pega las coordenadas aquí (lat, lng)",
            placeholder="Ej: 31.7619, -106.4850"
        )

        # Parsear coordenadas si se pegaron
        if coordenadas_texto and "," in coordenadas_texto:
            try:
                lat_str, lng_str = coordenadas_texto.split(",")
                latitud = float(lat_str.strip())
                longitud = float(lng_str.strip())
                st.success(f"✅ Coordenadas detectadas: {latitud}, {longitud}")

                # Verificar si está dentro del territorio seleccionado
                if territorio_seleccionado:
                    territorio = next(t for t in st.session_state.territorios if t["id"] == territorio_seleccionado)
                    if punto_en_poligono(latitud, longitud, territorio["coordenadas"]):
                        st.success(f"✅ La ubicación está dentro del territorio '{territorio['nombre']}'")
                    else:
                        st.warning(f"⚠️ La ubicación NO está dentro del territorio '{territorio['nombre']}'")
            except:
                latitud = 0.0
                longitud = 0.0
                st.error("⚠️ Formato de coordenadas incorrecto")
        else:
            latitud = st.number_input("Latitud", format="%.6f", value=31.7619)
            longitud = st.number_input("Longitud", format="%.6f", value=-106.4850)

        st.subheader("🚪 Estado de Visita")
        estado = st.selectbox(
            "Estado",
            ["Pendiente", "Atendido", "No atendió", "No tocar", "Solo fines de semana"]
        )

        if estado == "Atendido":
            fecha_visita = st.date_input("Fecha de visita")
            hora_visita = st.time_input("Hora de visita")
        else:
            fecha_visita = None
            hora_visita = None

    with col2:
        st.subheader("👥 Información de Residentes")
        nombre_contacto = st.text_input("Nombre del contacto", placeholder="Opcional")
        telefono = st.text_input("Teléfono", placeholder="Opcional")

        st.subheader("⚠️ Casos Especiales")
        tiene_caso_especial = st.checkbox("Marcar como caso especial")

        if tiene_caso_especial:
            tipo_caso = st.multiselect(
                "Tipo de caso",
                ["Expulsado", "Censurado", "Disciplinado", "Otro"]
            )
            detalles_caso = st.text_area("Detalles del caso", placeholder="Información adicional...")
        else:
            tipo_caso = []
            detalles_caso = ""

        st.subheader("📝 Notas")
        notas = st.text_area("Observaciones generales", placeholder="Cualquier información relevante...")

    # Vista previa en mapa
    if latitud != 0.0 and longitud != 0.0:
        st.subheader("📍 Vista previa de ubicación")
        m_preview = folium.Map(
            location=[latitud, longitud],
            zoom_start=15
        )

        # Agregar territorios
        if territorio_seleccionado:
            territorio = next(t for t in st.session_state.territorios if t["id"] == territorio_seleccionado)
            folium.Polygon(
                locations=territorio["coordenadas"],
                color=territorio["color"],
                fill=True,
                fillColor=territorio["color"],
                fillOpacity=0.2,
                popup=territorio["nombre"]
            ).add_to(m_preview)

        # Agregar marcador
        folium.Marker(
            location=[latitud, longitud],
            popup=direccion,
            icon=folium.Icon(color="red", icon="home", prefix='glyphicon')
        ).add_to(m_preview)

        st_folium(m_preview, width=700, height=300, key="preview_map")

    if st.button("💾 Guardar Casa", type="primary", use_container_width=True):
        if direccion and latitud != 0.0 and longitud != 0.0 and territorio_seleccionado:
            nueva_casa = {
                "id": len(st.session_state.casas) + 1,
                "territorio_id": territorio_seleccionado,
                "territorio_nombre": next(t["nombre"] for t in st.session_state.territorios if t["id"] == territorio_seleccionado),
                "direccion": direccion,
                "latitud": latitud,
                "longitud": longitud,
                "estado": estado,
                "fecha_visita": str(fecha_visita) if fecha_visita else None,
                "hora_visita": str(hora_visita) if hora_visita else None,
                "nombre_contacto": nombre_contacto,
                "telefono": telefono,
                "tiene_caso_especial": tiene_caso_especial,
                "tipo_caso": tipo_caso,
                "detalles_caso": detalles_caso,
                "notas": notas,
                "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            guardar_casa(nueva_casa)
        else:
            st.error("⚠️ Por favor completa todos los campos requeridos (dirección, coordenadas y territorio)")

# SECCIÓN: VER MAPA
elif menu == "📍 Ver Mapa":
    st.header("Mapa del Territorio")

    # Filtros
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if len(st.session_state.territorios) > 0:
            territorios_filtro = st.multiselect(
                "Filtrar por territorio",
                options=[t["id"] for t in st.session_state.territorios],
                format_func=lambda x: next(t["nombre"] for t in st.session_state.territorios if t["id"] == x),
                default=[t["id"] for t in st.session_state.territorios]
            )
        else:
            territorios_filtro = []
            st.info("No hay territorios")

    with col2:
        filtro_estado = st.multiselect(
            "Filtrar por estado",
            ["Pendiente", "Atendido", "No atendió", "No tocar", "Solo fines de semana"],
            default=["Pendiente", "Atendido", "No atendió", "No tocar", "Solo fines de semana"]
        )

    with col3:
        filtro_caso = st.checkbox("Solo casos especiales")

    with col4:
        st.metric("Total de casas", len(st.session_state.casas))

    # Filtrar casas
    casas_filtradas = [
        casa for casa in st.session_state.casas
        if casa.get("territorio_id") in territorios_filtro
        and casa["estado"] in filtro_estado
        and (not filtro_caso or casa["tiene_caso_especial"])
    ]

    # Crear mapa
    if len(st.session_state.territorios) == 0:
        st.warning("No hay territorios creados. Por favor crea territorios primero.")
        m = folium.Map(
            location=[31.7619, -106.4850],
            zoom_start=13,
            tiles="OpenStreetMap"
        )
    else:
        # Calcular centro del mapa basado en territorios
        todas_coords = []
        for territorio in st.session_state.territorios:
            if territorio["id"] in territorios_filtro:
                todas_coords.extend(territorio["coordenadas"])

        if todas_coords:
            lat_centro = sum(coord[0] for coord in todas_coords) / len(todas_coords)
            lng_centro = sum(coord[1] for coord in todas_coords) / len(todas_coords)
        else:
            lat_centro, lng_centro = 31.7619, -106.4850

        m = folium.Map(
            location=[lat_centro, lng_centro],
            zoom_start=13,
            tiles="OpenStreetMap"
        )

        # Agregar territorios al mapa
        for territorio in st.session_state.territorios:
            if territorio["id"] in territorios_filtro:
                # Contar casas en este territorio
                casas_en_territorio = [c for c in casas_filtradas if c.get("territorio_id") == territorio["id"]]
                atendidas = len([c for c in casas_en_territorio if c["estado"] == "Atendido"])

                popup_html = f"""
                <div style="font-family: Arial; min-width: 200px;">
                    <h4 style="margin: 0 0 10px 0;">{territorio['nombre']}</h4>
                    <b>Responsable:</b> {territorio['responsable']}<br>
                    <b>Total casas:</b> {len(casas_en_territorio)}<br>
                    <b>Atendidas:</b> {atendidas}<br>
                    <b>Descripción:</b> {territorio['descripcion']}<br>
                </div>
                """

                folium.Polygon(
                    locations=territorio["coordenadas"],
                    color=territorio["color"],
                    fill=True,
                    fillColor=territorio["color"],
                    fillOpacity=0.2,
                    weight=3,
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{territorio['nombre']} ({len(casas_en_territorio)} casas)"
                ).add_to(m)

        # Agregar marcadores de casas
        for casa in casas_filtradas:
            color = get_color(casa["estado"])
            icono = get_icon(casa["estado"])

            # Crear contenido del popup
            caso_badge = ""
            if casa["tiene_caso_especial"]:
                tipos = ", ".join(casa["tipo_caso"])
                caso_badge = f'<span style="background-color: #ff4444; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">⚠️ {tipos}</span><br>'

            contacto_info = ""
            if casa["nombre_contacto"]:
                contacto_info += f"<b>👤 Contacto:</b> {casa['nombre_contacto']}<br>"
            if casa["telefono"]:
                contacto_info += f"<b>📞 Teléfono:</b> {casa['telefono']}<br>"

            fecha_info = ""
            if casa["fecha_visita"]:
                fecha_info = f"<b>📅 Fecha visita:</b> {casa['fecha_visita']} {casa['hora_visita'] or ''}<br>"

            popup_html = f"""
            <div style='font-family: Arial; min-width: 200px;'>
                <h4 style='margin: 0 0 10px 0; color: {color};'>📍 {casa['direccion']}</h4>
                <span style='background-color: {color}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;'>
                    {casa['territorio_nombre']}
                </span><br><br>
                {caso_badge}
                <b>Estado:</b> <span style='color: {color}; font-weight: bold;'>{casa['estado']}</span><br>
                {contacto_info}
                {fecha_info}
                <b>📝 Notas:</b> {casa['notas'][:100] if casa['notas'] else 'Sin notas'}<br>
                <small style='color: #666;'>Registrado: {casa['fecha_registro']}</small>
            </div>
            """

            # Agregar marcador
            folium.Marker(
                location=[casa["latitud"], casa["longitud"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{casa['direccion']} - {casa['territorio_nombre']}",
                icon=folium.Icon(color=color, icon=icono, prefix='glyphicon')
            ).add_to(m)

    # Mostrar mapa
    st_folium(m, width=1400, height=600)

    # Leyenda
    st.markdown("### 🎨 Leyenda de colores:")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.markdown("🟢 **Atendido**")
    col2.markdown("🔴 **No atendió**")
    col3.markdown("⚫ **No tocar**")
    col4.markdown("🔵 **Solo fines de semana**")
    col5.markdown("🟠 **Pendiente**")

# SECCIÓN: ESTADÍSTICAS
elif menu == "📊 Estadísticas":
    st.header("Estadísticas del Territorio")

    # Selector de territorio
    if len(st.session_state.territorios) > 0:
        territorio_stats = st.selectbox(
            "Selecciona un territorio para ver estadísticas",
            options=["Todos"] + [t["id"] for t in st.session_state.territorios],
            format_func=lambda x: "Todos los territorios" if x == "Todos" else next(t["nombre"] for t in st.session_state.territorios if t["id"] == x)
        )

        # Filtrar casas según territorio seleccionado
        if territorio_stats == "Todos":
            casas_stats = st.session_state.casas
        else:
            casas_stats = [c for c in st.session_state.casas if c.get("territorio_id") == territorio_stats]
    else:
        st.warning("No hay territorios creados.")
        casas_stats = []

    if len(casas_stats) == 0:
        st.warning("No hay datos para mostrar estadísticas.")
    else:
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)

        total = len(casas_stats)
        atendidos = sum(1 for c in casas_stats if c["estado"] == "Atendido")
        no_atendio = sum(1 for c in casas_stats if c["estado"] == "No atendió")
        casos_especiales = sum(1 for c in casas_stats if c["tiene_caso_especial"])

        col1.metric("Total de Casas", total)
        col2.metric("Atendidos", atendidos, f"{atendidos/total*100:.1f}%" if total > 0 else "0%")
        col3.metric("No Atendieron", no_atendio)
        col4.metric("Casos Especiales", casos_especiales)

        st.markdown("---")

        # Estadísticas por territorio
        if territorio_stats == "Todos":
            st.subheader("📊 Estadísticas por Territorio")

            for territorio in st.session_state.territorios:
                casas_territorio = [c for c in st.session_state.casas if c.get("territorio_id") == territorio["id"]]
                if len(casas_territorio) > 0:
                    with st.expander(f"🗺️ {territorio['nombre']} ({len(casas_territorio)} casas)"):
                        col1, col2, col3 = st.columns(3)

                        atendidos_t = sum(1 for c in casas_territorio if c["estado"] == "Atendido")
                        pendientes_t = sum(1 for c in casas_territorio if c["estado"] == "Pendiente")
                        casos_t = sum(1 for c in casas_territorio if c["tiene_caso_especial"])

                        col1.metric("Atendidos", atendidos_t, f"{atendidos_t/len(casas_territorio)*100:.1f}%")
                        col2.metric("Pendientes", pendientes_t)
                        col3.metric("Casos Especiales", casos_t)

        st.markdown("---")

        # Gráficos
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Distribución por Estado")
            estados_count = {}
            for casa in casas_stats:
                estados_count[casa["estado"]] = estados_count.get(casa["estado"], 0) + 1

            for estado, count in estados_count.items():
                porcentaje = count/total*100
                color_emoji = {"Atendido": "🟢", "No atendió": "🔴", "No tocar": "⚫",
                              "Solo fines de semana": "🔵", "Pendiente": "🟠"}
                emoji = color_emoji.get(estado, "⚪")
                st.write(f"{emoji} **{estado}:** {count} casas ({porcentaje:.1f}%)")
                st.progress(porcentaje/100)

        with col2:
            st.subheader("⚠️ Casos Especiales")
            tipos_casos = {}
            for casa in casas_stats:
                if casa["tiene_caso_especial"]:
                    for tipo in casa["tipo_caso"]:
                        tipos_casos[tipo] = tipos_casos.get(tipo, 0) + 1

            if tipos_casos:
                for tipo, count in tipos_casos.items():
                    st.write(f"**{tipo}:** {count} casos")
                    st.progress(count/casos_especiales if casos_especiales > 0 else 0)
            else:
                st.info("No hay casos especiales registrados")

# SECCIÓN: LISTA DE CASAS
elif menu == "📋 Lista de Casas":
    st.header("Lista de Todas las Casas")

    if len(st.session_state.casas) == 0:
        st.warning("No hay casas registradas.")
    else:
        # Filtros
        col1, col2 = st.columns(2)

        with col1:
            busqueda = st.text_input("🔍 Buscar por dirección o contacto", placeholder="Escribe para buscar...")

        with col2:
            if len(st.session_state.territorios) > 0:
                territorio_filtro = st.selectbox(
                    "Filtrar por territorio",
                    options=["Todos"] + [t["id"] for t in st.session_state.territorios],
                    format_func=lambda x: "Todos" if x == "Todos" else next(t["nombre"] for t in st.session_state.territorios if t["id"] == x)
                )
            else:
                territorio_filtro = "Todos"

        # Filtrar por búsqueda y territorio
        casas_mostrar = st.session_state.casas

        if territorio_filtro != "Todos":
            casas_mostrar = [c for c in casas_mostrar if c.get("territorio_id") == territorio_filtro]

        if busqueda:
            casas_mostrar = [
                casa for casa in casas_mostrar
                if busqueda.lower() in casa["direccion"].lower()
                or (casa["nombre_contacto"] and busqueda.lower() in casa["nombre_contacto"].lower())
            ]

        st.write(f"Mostrando {len(casas_mostrar)} de {len(st.session_state.casas)} casas")

        # Crear DataFrame
        if len(casas_mostrar) > 0:
            df = pd.DataFrame(casas_mostrar)

            # Mostrar tabla
            st.dataframe(
                df[["territorio_nombre", "direccion", "estado", "nombre_contacto", "tiene_caso_especial", "fecha_registro"]],
                use_container_width=True,
                hide_index=True
            )

            # Detalles de casa seleccionada
            st.markdown("---")
            st.subheader("Ver detalles de una casa")
            casa_seleccionada = st.selectbox(
                "Selecciona una casa",
                options=range(len(casas_mostrar)),
                format_func=lambda i: f"{casas_mostrar[i]['direccion']} - {casas_mostrar[i]['territorio_nombre']}"
            )

            if casa_seleccionada is not None:
                casa = casas_mostrar[casa_seleccionada]

                # Mostrar en dos columnas
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"### 📍 {casa['direccion']}")
                    st.markdown(f"**🗺️ Territorio:** {casa['territorio_nombre']}")
                    st.write(f"**🚪 Estado:** {casa['estado']}")
                    st.write(f"**👤 Contacto:** {casa['nombre_contacto'] or 'N/A'}")
                    st.write(f"**📞 Teléfono:** {casa['telefono'] or 'N/A'}")
                    if casa['fecha_visita']:
                        st.write(f"**📅 Fecha visita:** {casa['fecha_visita']} {casa['hora_visita'] or ''}")

                with col2:
                    st.write(f"**⚠️ Caso especial:** {'Sí' if casa['tiene_caso_especial'] else 'No'}")
                    if casa['tiene_caso_especial']:
                        st.write(f"**Tipo:** {', '.join(casa['tipo_caso'])}")
                        st.write(f"**Detalles:** {casa['detalles_caso']}")
                    st.write(f"**📝 Notas:** {casa['notas'] or 'Sin notas'}")
                    st.write(f"**🕐 Registrado:** {casa['fecha_registro']}")

                st.markdown("---")

                # Botones de acción para la casa
                col_action1, col_action2, col_action3 = st.columns([1, 1, 2])

                with col_action1:
                    if st.button("✏️ Editar casa", key=f"edit_casa_{casa['id']}", use_container_width=True):
                        st.session_state[f"editing_casa_{casa['id']}"] = True
                        st.rerun()

                with col_action2:
                    if st.button("🗑️ Eliminar casa", key=f"delete_casa_{casa['id']}", type="secondary", use_container_width=True):
                        st.session_state[f"confirm_delete_casa_{casa['id']}"] = True
                        st.rerun()

                # Confirmación de eliminación de casa
                if st.session_state.get(f"confirm_delete_casa_{casa['id']}", False):
                    st.warning(f"⚠️ ¿Estás seguro de eliminar la casa en '{casa['direccion']}'?")
                    col_confirm1, col_confirm2 = st.columns(2)

                    with col_confirm1:
                        if st.button("✅ Sí, eliminar casa", key=f"confirm_yes_casa_{casa['id']}", type="primary"):
                            # Eliminar la casa
                            st.session_state.casas = [
                                c for c in st.session_state.casas
                                if c["id"] != casa["id"]
                            ]
                            # Limpiar estados relacionados
                            st.session_state[f"confirm_delete_casa_{casa['id']}"] = False
                            if f"editing_casa_{casa['id']}" in st.session_state:
                                del st.session_state[f"editing_casa_{casa['id']}"]
                            st.success("✅ Casa eliminada exitosamente")
                            # Usar time.sleep para dar tiempo a mostrar el mensaje
                            time.sleep(1)
                            st.rerun()

                    with col_confirm2:
                        if st.button("❌ Cancelar", key=f"confirm_no_casa_{casa['id']}"):
                            st.session_state[f"confirm_delete_casa_{casa['id']}"] = False
                            st.rerun()

                # Formulario de edición de casa
                if st.session_state.get(f"editing_casa_{casa['id']}", False):
                    st.markdown("### ✏️ Editar Casa")

                    edit_col1, edit_col2 = st.columns(2)

                    with edit_col1:
                        nueva_direccion = st.text_input("Dirección", value=casa['direccion'], key=f"edit_dir_{casa['id']}")
                        nuevo_estado = st.selectbox(
                            "Estado",
                            ["Pendiente", "Atendido", "No atendió", "No tocar", "Solo fines de semana"],
                            index=["Pendiente", "Atendido", "No atendió", "No tocar", "Solo fines de semana"].index(casa['estado']),
                            key=f"edit_estado_{casa['id']}"
                        )
                        nuevo_contacto = st.text_input("Contacto", value=casa['nombre_contacto'] or "", key=f"edit_cont_{casa['id']}")
                        nuevo_telefono = st.text_input("Teléfono", value=casa['telefono'] or "", key=f"edit_tel_{casa['id']}")

                    with edit_col2:
                        nuevas_notas = st.text_area("Notas", value=casa['notas'] or "", key=f"edit_notas_{casa['id']}")
                        nuevo_caso_especial = st.checkbox("Caso especial", value=casa['tiene_caso_especial'], key=f"edit_caso_{casa['id']}")

                        if nuevo_caso_especial:
                            nuevos_tipos = st.multiselect(
                                "Tipo de caso",
                                ["Expulsado", "Censurado", "Disciplinado", "Otro"],
                                default=casa['tipo_caso'],
                                key=f"edit_tipos_{casa['id']}"
                            )
                            nuevos_detalles = st.text_area("Detalles caso", value=casa['detalles_caso'] or "", key=f"edit_det_{casa['id']}")
                        else:
                            nuevos_tipos = []
                            nuevos_detalles = ""

                    col_save_casa1, col_save_casa2 = st.columns(2)

                    with col_save_casa1:
                        if st.button("💾 Guardar cambios", key=f"save_casa_{casa['id']}", type="primary"):
                            for c in st.session_state.casas:
                                if c["id"] == casa["id"]:
                                    c["direccion"] = nueva_direccion
                                    c["estado"] = nuevo_estado
                                    c["nombre_contacto"] = nuevo_contacto
                                    c["telefono"] = nuevo_telefono
                                    c["notas"] = nuevas_notas
                                    c["tiene_caso_especial"] = nuevo_caso_especial
                                    c["tipo_caso"] = nuevos_tipos
                                    c["detalles_caso"] = nuevos_detalles
                                    break

                            st.session_state[f"editing_casa_{casa['id']}"] = False
                            st.success("✅ Casa actualizada exitosamente")
                            st.rerun()

                    with col_save_casa2:
                        if st.button("❌ Cancelar edición", key=f"cancel_casa_{casa['id']}"):
                            st.session_state[f"editing_casa_{casa['id']}"] = False
                            st.rerun()

                # Mini mapa de ubicación
                st.subheader("📍 Ubicación en el mapa")
                m_mini = folium.Map(
                    location=[casa["latitud"], casa["longitud"]],
                    zoom_start=16
                )

                # Agregar territorio
                territorio = next(t for t in st.session_state.territorios if t["id"] == casa["territorio_id"])
                folium.Polygon(
                    locations=territorio["coordenadas"],
                    color=territorio["color"],
                    fill=True,
                    fillColor=territorio["color"],
                    fillOpacity=0.2,
                    popup=territorio["nombre"]
                ).add_to(m_mini)

                # Agregar marcador
                folium.Marker(
                    location=[casa["latitud"], casa["longitud"]],
                    popup=casa["direccion"],
                    icon=folium.Icon(color=get_color(casa["estado"]), icon=get_icon(casa["estado"]), prefix='glyphicon')
                ).add_to(m_mini)

                st_folium(m_mini, width=700, height=300, key="mini_map")

        # Opción de exportar
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="📥 Descargar datos (JSON)",
                data=json.dumps(st.session_state.casas, indent=2, ensure_ascii=False),
                file_name=f"territorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        with col2:
            # Convertir a CSV
            if len(casas_mostrar) > 0:
                df_export = pd.DataFrame(st.session_state.casas)
                csv = df_export.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Descargar datos (CSV)",
                    data=csv,
                    file_name=f"territorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Resumen General")
st.sidebar.metric("Territorios", len(st.session_state.territorios))
st.sidebar.metric("Casas Totales", len(st.session_state.casas))

if len(st.session_state.casas) > 0:
    atendidos_total = sum(1 for c in st.session_state.casas if c["estado"] == "Atendido")
    porcentaje_atendidos = (atendidos_total / len(st.session_state.casas)) * 100
    st.sidebar.metric("Atendidos", f"{atendidos_total} ({porcentaje_atendidos:.1f}%)")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Usa Google Maps para obtener coordenadas precisas haciendo clic derecho en cualquier ubicación.")
st.sidebar.markdown("🗺️ **Gestión Territorial v2.0**")
st.sidebar.markdown("Developed by M.E Erik Armenta 🗺️")