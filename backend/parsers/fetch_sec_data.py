from sec_edgar_downloader import Downloader
import os

# Configurar downloader (requiere user agent válido por regulación SEC)
dl = Downloader("MyCompany", "contact@mycompany.com")

# Descargar 10-K más reciente de Apple
print("Descargando 10-K de Apple desde SEC EDGAR...")
dl.get("10-K", "AAPL", limit=1, download_details=True)

print("\n✓ Descarga completada")
print("Archivos en: sec-edgar-filings/AAPL/10-K/")

# Listar archivos descargados
for root, dirs, files in os.walk("sec-edgar-filings"):
    for file in files:
        if file.endswith('.xml'):
            filepath = os.path.join(root, file)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  {file}: {size_mb:.2f} MB")
