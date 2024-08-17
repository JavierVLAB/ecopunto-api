import streamlit as st
import time
import datetime
import pytz

###################


###################

st.markdown("# Estado de los contenedores - Ecovidrio 2023")

huso_horario_utc_2 = pytz.timezone('Europe/Madrid')
time_now = datetime.datetime.now().astimezone(huso_horario_utc_2)
st.markdown("### " + time_now.strftime("%H:%M:%S - %d/%m/%Y"))

