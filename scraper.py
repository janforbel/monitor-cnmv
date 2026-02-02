import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# Configuración de Telegram
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def enviar_telegram(mensaje):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {'chat_id': CHAT_ID, 'text': mensaje}
        requests.post(url, data=payload)

def obtener_datos():
    nuevas_entidades = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    urls = {
        "SGIIC": "https://www.cnmv.es/portal/consultas/listadoentidad?id=2&tipoent=0&lang=es",
        "SGEIC": "https://www.cnmv.es/portal/consultas/listadoentidad?id=4&tipoent=0&lang=es"
    }
    
    for tipo, url in urls.items():
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            if "consultas/instancia" in link['href']:
                nombre = link.get_text(strip=True)
                if nombre:
                    nuevas_entidades.append({'Nombre': nombre, 'Tipo': tipo})
    return pd.DataFrame(nuevas_entidades)

# Ejecución principal
archivo_db = 'registro_entidades.csv'
df_nuevo = obtener_datos()

if not os.path.exists(archivo_db):
    df_nuevo.to_csv(archivo_db, index=False)
    enviar_telegram("✅ Monitor CNMV activado. Primer registro completado.")
else:
    df_antiguo = pd.read_csv(archivo_db)
    novedades = df_nuevo[~df_nuevo['Nombre'].isin(df_antiguo['Nombre'])]
    
    if not novedades.empty:
        for _, fila in novedades.iterrows():
            mensaje = f"🔔 ¡NUEVA GESTORA REGISTRADA!\n\n🏢 Nombre: {fila['Nombre']}\n📂 Tipo: {fila['Tipo']}"
            enviar_telegram(mensaje)
        df_nuevo.to_csv(archivo_db, index=False)
    else:
        print("Sin novedades.")
