import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys

# 1. Configuración
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BASE_URL = "https://www.cnmv.es/portal/"
ARCHIVO_DB = 'registro_entidades.csv'

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID:
        print("❌ ERROR: Faltan TOKEN o CHAT_ID en los Secrets de GitHub.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': mensaje, 'parse_mode': 'HTML'}
    try:
        r = requests.post(url, data=payload)
        print(f"📡 Respuesta Telegram: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Error de conexión con Telegram: {e}")

def obtener_datos():
    entidades = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    urls = {
        "SGIIC": "https://www.cnmv.es/portal/consultas/listadoentidad?id=2&tipoent=0&lang=es",
        "SGEIC": "https://www.cnmv.es/portal/consultas/listadoentidad?id=4&tipoent=0&lang=es"
    }
    for tipo, url in urls.items():
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                if "consultas/instancia" in link['href']:
                    nombre = link.get_text(strip=True)
                    if nombre:
                        entidades.append({'Nombre': nombre, 'Tipo': tipo, 'Enlace': BASE_URL + link['href']})
        except:
            print(f"⚠️ Error leyendo {tipo}")
    
    # IMPORTANTE: Forzamos las columnas para evitar el error de 'EmptyDataError'
    return pd.DataFrame(entidades, columns=['Nombre', 'Tipo', 'Enlace'])

# --- EJECUCIÓN ---
try:
    df_nuevo = obtener_datos()
    
    if not os.path.exists(ARCHIVO_DB):
        df_nuevo.to_csv(ARCHIVO_DB, index=False)
        enviar_telegram("🚀 <b>¡Monitor Activado!</b>\nHe guardado el primer registro correctamente.")
    else:
        # Si el archivo existe pero está vacío, lo manejamos sin crash
        try:
            df_antiguo = pd.read_csv(ARCHIVO_DB)
        except:
            df_antiguo = pd.DataFrame(columns=['Nombre', 'Tipo', 'Enlace'])

        novedades = df_nuevo[~df_nuevo['Nombre'].isin(df_antiguo['Nombre'])]
        
        if not novedades.empty:
            for _, fila in novedades.iterrows():
                enviar_telegram(f"🔔 <b>NUEVA GESTORA:</b>\n🏢 {fila['Nombre']}\n🔗 <a href='{fila['Enlace']}'>Ver ficha</a>")
            df_nuevo.to_csv(ARCHIVO_DB, index=False)
        else:
            print("Sin novedades.")
            enviar_telegram("🤖 <b>Monitor CNMV:</b> Sigo vigilando, hoy no hay cambios.")

except Exception as e:
    print(f"❌ ERROR CRITICAL: {e}")
    sys.exit(1)
