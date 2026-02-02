import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BASE_URL = "https://www.cnmv.es/portal/"

def enviar_telegram(mensaje):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {'chat_id': CHAT_ID, 'text': mensaje, 'parse_mode': 'HTML'}
        requests.post(url, data=payload)

def extraer_detalle_gestora(url_ficha):
    """Entra en la ficha de la gestora y saca dirección, teléfono y cargos."""
    try:
        res = requests.get(url_ficha, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Buscamos los campos de texto en la ficha (Dirección y Teléfono)
        datos = soup.get_text()
        
        # Lógica simple para extraer datos (la CNMV usa etiquetas variadas)
        direccion = "No disponible"
        telefono = "No disponible"
        
        for span in soup.find_all('span'):
            texto = span.get_text().strip()
            if "Domicilio" in texto:
                direccion = span.find_next_sibling().get_text().strip() if span.find_next_sibling() else "Consultar ficha"
            if "Teléfono" in texto:
                telefono = span.find_next_sibling().get_text().strip() if span.find_next_sibling() else "Consultar ficha"

        return direccion, telefono
    except:
        return "Error al extraer", "Error al extraer"

def obtener_datos():
    entidades = []
    urls = {
        "SGIIC": "https://www.cnmv.es/portal/consultas/listadoentidad?id=2&tipoent=0&lang=es",
        "SGEIC": "https://www.cnmv.es/portal/consultas/listadoentidad?id=4&tipoent=0&lang=es"
    }
    for tipo, url in urls.items():
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            if "consultas/instancia" in link['href']:
                nombre = link.get_text(strip=True)
                enlace = BASE_URL + link['href']
                if nombre:
                    entidades.append({'Nombre': nombre, 'Tipo': tipo, 'Enlace': enlace})
    return pd.DataFrame(entidades)

# --- EJECUCIÓN ---
archivo_db = 'registro_entidades.csv'
df_nuevo = obtener_datos()

if not os.path.exists(archivo_db):
    df_nuevo.to_csv(archivo_db, index=False)
    enviar_telegram("✅ <b>Monitor Detallado Activado</b>")
else:
    df_antiguo = pd.read_csv(archivo_db)
    novedades = df_nuevo[~df_nuevo['Nombre'].isin(df_antiguo['Nombre'])]
    
    if not novedades.empty:
        for _, fila in novedades.iterrows():
            # PASO EXTRA: Entramos a la ficha para más info
            dir_social, tlf = extraer_detalle_gestora(fila['Enlace'])
            
            mensaje = (
                f"🔔 <b>NUEVA GESTORA DETECTADA</b>\n\n"
                f"🏢 <b>Nombre:</b> {fila['Nombre']}\n"
                f"📍 <b>Dirección:</b> {dir_social}\n"
                f"📞 <b>Teléfono:</b> {tlf}\n"
                f"📂 <b>Tipo:</b> {fila['Tipo']}\n"
                f"🔗 <a href='{fila['Enlace']}'>Ver Ficha y Directivos</a>"
            )
            enviar_telegram(mensaje)
        df_nuevo.to_csv(archivo_db, index=False)
