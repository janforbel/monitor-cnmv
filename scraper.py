import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# Configuración de Telegram
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BASE_URL = "https://www.cnmv.es/portal/"

def enviar_telegram(mensaje):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID, 
            'text': mensaje,
            'parse_mode': 'HTML' # Esto permite poner negritas y enlaces bonitos
        }
        requests.post(url, data=payload)

def obtener_datos():
    nuevas_entidades = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    urls = {
        "SGIIC (Fondos)": "https://www.cnmv.es/portal/consultas/listadoentidad?id=2&tipoent=0&lang=es",
        "SGEIC (Capital Riesgo)": "https://www.cnmv.es/portal/consultas/listadoentidad?id=4&tipoent=0&lang=es"
    }
    
    for tipo, url in urls.items():
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos los enlaces que contienen la ficha de la entidad
        for link in soup.find_all('a', href=True):
            if "consultas/instancia" in link['href']:
                nombre = link.get_text(strip=True)
                # Construimos la URL completa
                enlace_completo = BASE_URL + link['href']
                if nombre:
                    nuevas_entidades.append({
                        'Nombre': nombre, 
                        'Tipo': tipo, 
                        'Enlace': enlace_completo
                    })
    
    return pd.DataFrame(nuevas_entidades)

# --- Ejecución principal ---
archivo_db = 'registro_entidades.csv'
df_nuevo = obtener_datos()

if not os.path.exists(archivo_db):
    df_nuevo.to_csv(archivo_db, index=False)
    enviar_telegram("✅ <b>Monitor CNMV Activado</b>\nEl sistema ya está vigilando los registros de SGIIC y SGEIC.")
else:
    df_antiguo = pd.read_csv(archivo_db)
    # Comparamos para ver si hay nombres nuevos que no estaban en nuestra lista
    novedades = df_nuevo[~df_nuevo['Nombre'].isin(df_antiguo['Nombre'])]
    
    if not novedades.empty:
        for _, fila in novedades.iterrows():
            mensaje = (
                f"🔔 <b>¡NUEVA GESTORA DETECTADA!</b>\n\n"
                f"🏢 <b>Nombre:</b> {fila['Nombre']}\n"
                f"📂 <b>Tipo:</b> {fila['Tipo']}\n"
                f"🔗 <a href='{fila['Enlace']}'>Ver ficha oficial en CNMV</a>"
            )
            enviar_telegram(mensaje)
        # Guardamos la lista actualizada
        df_nuevo.to_csv(archivo_db, index=False)
    else:
        print("Sin novedades en el registro.")
