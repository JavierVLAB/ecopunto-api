import streamlit as st
import time
import datetime
import pytz

import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

import asyncio

import pandas as pd
import numpy as np


def initialize_firebase_app():
    # Verificar si Firebase ya está inicializado
    try:
        firebase_app = firebase_admin.get_app()
    except:
        # Verificar si el archivo de credenciales existe en local
        firebase_creds_path = None
        try:
            firebase_creds_path = "secrets/ecopunto.json"
        except:
            pass
        
        if os.path.exists(firebase_creds_path):
            # En local: usa el archivo JSON
            cred = credentials.Certificate(firebase_creds_path)
        else:
            # En la nube: usa los secretos de Streamlit
            firebase_creds_dict = json.loads(st.secrets["firebase_service_account"])
            print(firebase_creds_dict)
            cred = credentials.Certificate(firebase_creds_dict)

        # Inicializar Firebase con las credenciales adecuadas
        firebase_app = firebase_admin.initialize_app(cred)

    return firebase_app



# Inicializa la app Firebase
firebase_app = initialize_firebase_app()

# Inicializa Firestore
db = firestore.client(firebase_app)



###################

async def get_metrics():

    # Aquí NO necesitas inicializar Firestore de nuevo, solo usar `db`
    events_ref = db.collection('events')

    # Número total de conexiones
    total_connections_query = events_ref.where('event_name', '==', 'App Start')
    total_connections = len([doc for doc in total_connections_query.stream()])

    # Conexiones en "Contenedor" y "Local"
    init_page_connections_query = events_ref.where('event_name', '==', 'App Start')
    init_page_connections = {}
    for doc in init_page_connections_query.stream():
        data = doc.to_dict()
        init_page = data.get('init_page')
        if init_page in init_page_connections:
            init_page_connections[init_page] += 1
        else:
            init_page_connections[init_page] = 1

    # Número total de incidencias reportadas
    total_incidents_query = events_ref.where('event_name', '==', 'Success')
    total_incidents = len([doc for doc in total_incidents_query.stream()])

    # Incidencias reportadas y su conteoStar
    incident_reports_query = events_ref.where('event_name', '==', 'Success')
    incident_reports = {}
    for doc in incident_reports_query.stream():
        data = doc.to_dict()
        incidencia = data.get('incidencia')
        print(incidencia)
        if incidencia in incident_reports:
            incident_reports[incidencia] += 1
        else:
            incident_reports[incidencia] = 1

    # Abandonos y en qué página ocurrieron
    abandonments_query = events_ref.where('event_name', '==', 'Quit')
    abandonments = {}
    for doc in abandonments_query.stream():
        data = doc.to_dict()
        actual_page = data.get('actual_page')
        if actual_page in abandonments:
            abandonments[actual_page] += 1
        else:
            abandonments[actual_page] = 1

    # Número total de abandonos
    total_quits = len([doc for doc in abandonments_query.stream()])

    return {
        "total_connections": total_connections,
        "init_page_connections": init_page_connections,
        "total_incidents": total_incidents,
        "incident_reports": incident_reports,
        "abandonments": abandonments,
        "total_quits": total_quits
    }


###################

st.markdown("# Estadistica de uso de APP Ecopunto")

huso_horario_utc_2 = pytz.timezone('Europe/Madrid')
time_now = datetime.datetime.now().astimezone(huso_horario_utc_2)
#st.markdown("### " + time_now.strftime("%H:%M:%S - %d/%m/%Y"))

print("ssss")
results = asyncio.run(get_metrics())
print(results)

col1, col2 = st.columns([1, 3])

col1.markdown("### Conexiones")
col1.metric(label="Conexiones totales", 
            value=results["total_connections"], 
            delta="OK" ,
            delta_color="normal",
            help="Porcentaje de la batería LiPo")


# Convertir los datos en un DataFrame
df1 = pd.DataFrame(list(results["init_page_connections"].items()), columns=['Categoría', 'Cantidad'])
df1.set_index('Categoría', inplace=True)

col2.markdown("### Número de conexiones por entrada (Contenedor o Local)")
col2.bar_chart(df1, horizontal=True)


###########
col3, col4 = st.columns([1, 3])

col3.markdown("### Incidencias")
col3.metric(label="Incidencias", 
            value=results["total_incidents"], 
            delta="OK" ,
            delta_color="normal",
            help="Porcentaje de la batería LiPo")

df2 = pd.DataFrame(list(results["incident_reports"].items()), columns=['Categoría', 'Cantidad'])
df2.set_index('Categoría', inplace=True)

col4.markdown("### Número de incidencias por tipo")
col4.bar_chart(df2, horizontal=True)



###########
col5, col6 = st.columns([1, 3])

col5.markdown("### Abandonos")
col5.metric(label="Abandonos", 
            value=results["total_quits"], 
            delta="OK" ,
            delta_color="normal",
            help="Número total de abandonos en la app")

df3 = pd.DataFrame(list(results["incident_reports"].items()), columns=['Categoría', 'Cantidad'])
df3.set_index('Categoría', inplace=True)

col6.markdown("### Abandonos por página")
col6.bar_chart(df3, horizontal=True)


