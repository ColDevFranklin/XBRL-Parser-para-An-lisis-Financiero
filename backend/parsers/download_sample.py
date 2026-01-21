import urllib.request
import os

# Crear carpeta data si no existe
os.makedirs('data', exist_ok=True)

# URL directa del archivo XBRL de Apple
url = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930_htm.xml"

print("Descargando archivo XBRL de Apple 2023...")

try:
    # Crear request con headers (SEC requiere User-Agent)
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; FinancialAnalyzer/1.0)'}
    )
    
    with urllib.request.urlopen(req) as response:
        data = response.read()
        
    with open("data/apple_10k.xml", "wb") as f:
        f.write(data)
    
    # Verificar tamaño
    size_mb = os.path.getsize("data/apple_10k.xml") / (1024 * 1024)
    print(f"✓ Archivo descargado: {size_mb:.2f} MB")
    print("✓ Guardado en: data/apple_10k.xml")
    
except Exception as e:
    print(f"✗ Error: {e}")
