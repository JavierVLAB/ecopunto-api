import streamlit as st
import pytz
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import july
from july.utils import date_range
from datetime import datetime, timedelta

import warnings
import matplotlib
warnings.filterwarnings("ignore", category=matplotlib.MatplotlibDeprecationWarning)

is_local = False
firebase_creds_path = "secrets/ecopunto.json"

def initialize_firebase_app():
    # Verificar si Firebase ya está inicializado
    
    try:
        firebase_app = firebase_admin.get_app()
    except:
        # Verificar si el archivo de credenciales existe en local
        
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

st.markdown("# Estadística de uso de APP Ecopunto")

huso_horario_utc_2 = pytz.timezone('Europe/Madrid')
time_now = datetime.now().astimezone(huso_horario_utc_2)
#st.markdown("### " + time_now.strftime("%H:%M:%S - %d/%m/%Y"))


# Función para obtener y procesar datos de Firestore
def fetch_and_process_track_events(collection_name):
    collection_ref = db.collection(collection_name)
    query = collection_ref.where("event_name", "==", "Track")
    docs = query.stream()

    # Extraer los datos y agrupar por incidencia y actual_page
    data = []
    for doc in docs:
        doc_data = doc.to_dict()

        if 'incidencia' in doc_data and 'actual_page' in doc_data:
            data.append({
                'incidencia': doc_data['incidencia'],
                'actual_page': doc_data['actual_page']
            })

    # Número total de incidencias reportadas
    total_incidents_query = collection_ref.where("event_name", "==", "Success")
    total_incidents = len([doc for doc in total_incidents_query.stream()])

    # Incidencias reportadas y su conteo
    incident_reports_query = collection_ref.where("event_name", "==", "Success")
    incident_reports = {}


    for doc in incident_reports_query.stream():
        data1 = doc.to_dict()
        incidencia = data1.get('incidencia')
        print(data1)
        if incidencia in incident_reports:
            incident_reports[incidencia] += 1
        else:
            incident_reports[incidencia] = 1

    data2 = []
    for doc in incident_reports_query.stream():
        doc_data = doc.to_dict()

        if 'timestamp' in doc_data:
            data2.append({
                'timestamp': doc_data['timestamp']
            })

    
    df_timestamp = pd.DataFrame(data2)

    if not df_timestamp.empty:
        df_timestamp['date'] = pd.to_datetime(df_timestamp['timestamp']).dt.date

    
    df = pd.DataFrame(data)
    #print(df)
    extra = {
        "total_incidents": total_incidents,
        "incident_reports": incident_reports
    }
    return df, extra, df_timestamp


# Obtener los datos
collection_name = "events"
df, results, df_timestap = fetch_and_process_track_events(collection_name)

# Obtener todas las incidencias únicas
incidencias = df['incidencia'].unique()

col1, col2 = st.columns([1, 3])
conexiones = df[df['incidencia'] == '']
#print(conexiones)

# Filtrar para las páginas 'local' y 'contenedor' en conexiones_count
conexiones_count = conexiones['actual_page'].value_counts().reset_index()
conexiones_count.columns = ['actual_page', 'count']
conexiones_filtered = conexiones_count[conexiones_count['actual_page'].isin(['local', 'contenedor'])]

# Calcular el total solo de las páginas 'local' y 'contenedor'
total_conexiones = conexiones_filtered['count'].sum()

col1.markdown("### Conexiones")
col1.metric(label="Conexiones totales", 
            value=total_conexiones, 
            help='Este es el número total de veces que se han abierto las páginas "/contenedor" y "/local"')





col2.markdown("### Número de conexiones por entrada (Contenedor o Local)")
col2.bar_chart(conexiones_filtered.set_index('actual_page'), horizontal=True)

#print(results)

###########
col3, col4 = st.columns([1, 3])

col3.markdown("### Incidencias")
col3.metric(label="Incidencias", 
            value=results["total_incidents"]-results['incident_reports']['whatsapp'], 
            delta="OK" ,
            delta_color="normal",
            help="Este es el número de incidencias que se han enviado exitosamente. Este valor es el valor total de envios sucess menos el número de envios de whatsapp")

df2 = pd.DataFrame(list(results["incident_reports"].items()), columns=['Categoría', 'Cantidad'])
df2.set_index('Categoría', inplace=True)

col4.markdown("### Número de incidencias por tipo")
col4.bar_chart(df2, horizontal=True)



######

st.divider()
st.write('##')


st.write('## Visitas de las páginas por cada incidencia')

for incidencia in incidencias:
        if incidencia == '':
            continue
        st.subheader(f"Incidencia: {incidencia}")
        
        # Filtrar el DataFrame por la incidencia actual
        df_filtered = df[df['incidencia'] == incidencia]
        
        # Contar el número de ocurrencias por actual_page
        df_count = df_filtered['actual_page'].value_counts().reset_index()
        df_count.columns = ['actual_page', 'count']
        
        # Generar el gráfico utilizando st.bar_chart
        
        st.bar_chart(df_count.set_index('actual_page'), horizontal=True)





###############

st.divider()
st.write('##')

dates = date_range("2024-08-01", "2024-12-31")
data3 = np.random.randint(0, 14, len(dates))

start_date = datetime(2024, 8, 1)
end_date = datetime(2024, 12, 31)

# Generar todas las fechas dentro del rango deseado
all_dates = pd.date_range(start=start_date, end=end_date).date

# Crear un DataFrame con todas las fechas
all_dates_df = pd.DataFrame({'date': all_dates})

df_new = df_timestap.groupby('date').size().reset_index(name='count')

print(df_new)
# Combinar con los datos existentes

df_new = pd.merge(all_dates_df, df_new, on='date', how='left')

df_new['count'] = df_new.apply(lambda row: 0 if pd.isna(row['count']) else row['count'], axis=1)

dates = df_new['date'].tolist()
counts = df_new['count'].tolist()


fig, ax = plt.subplots()

# Define el mapa de colores personalizado
custom_cmap = mcolors.LinearSegmentedColormap.from_list(
    "custom_github", ["white", "#c6e48b", "#239a3b", "#196127"], N=256
)

july.heatmap(
    dates=dates,
    data=counts,
    #cmap='github',
    cmap=custom_cmap,
    month_grid=True,
    horizontal=True,
    value_label=False,
    date_label=True,
    weekday_label=True,
    month_label=True,
    colorbar=True,
    fontsize=6,
    ax=ax   ## <- Tell July to put the heatmap in that Axes
)
st.markdown("## Número de conexiones por día")
st.pyplot(fig)
#st.pyplot(july)

#########
def delete_documents():
    collection_ref = db.collection("events")

    #query_hola = collection_ref.where("event_name", "==", "Success")
    #docs_hola = query_hola.stream()
    
    #for doc in docs_hola:
    #    doc.reference.delete()

    #query_chao = collection_ref.where("actual_page", "==", "local")
    #docs_chao = query_chao.stream()
    
    #counter = 0
    #for doc in docs_chao:
    #    if counter < 40:
    #        doc.reference.delete()
    #        counter = counter + 1

if os.path.exists(firebase_creds_path):
    if st.button("Delete Documents"):
        delete_documents()
        st.success(f"Listo")

