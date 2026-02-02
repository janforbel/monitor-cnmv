import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# 1. URLs de la CNMV
urls = {
    "SGIIC": "https://www.cnmv.es/portal/consultas/listadoentidad?id=2&tipoent=0&lang=es",
    "SGEIC": "https://www.cnmv.es/portal/consultas/listadoentidad?id=4&tipoent=0&lang=es"
}

def obtener_datos():
    nuevas_entidades = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for tipo, url in urls.items():
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos los enlaces de las entidades
        for link in soup.find_all('a', href=True):
            if "consultas/instancia" in link['href']:
                nombre = link.get_text(strip=True)
                if nombre:
                    nuevas_entidades.append({'Nombre': nombre, 'Tipo': tipo})
    
    return pd.DataFrame(nuevas_entidades)

# 2. Lógica de comparación
archivo_db = 'registro_entidades.csv'
df_nuevo = obtener_datos()

if not os.path.exists(archivo_db):
    # Si es la primera vez, guardamos todo
    df_nuevo.to_csv(archivo_db, index=False)
    print("Primer registro creado.")
else:
    # Comparamos con lo que ya teníamos
    df_antiguo = pd.read_csv(archivo_db)
    # Buscamos entidades en el nuevo que no estén en el antiguo
    novedades = df_nuevo[~df_nuevo['Nombre'].isin(df_antiguo['Nombre'])]
    
    if not novedades.empty:
        print(f"¡ALERTA! Nuevas entidades detectadas:\n{novedades}")
        # Actualizamos la base de datos
        df_nuevo.to_csv(archivo_db, index=False)
    else:
        print("No hay novedades hoy.")
