import requests
import os

# URL base del filing más reciente de Apple
accession = "0000320193-25-000079"
base_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik=320193&accession_number={accession}&xbrl_type=v"

print(f"Descargando XBRL de Apple (accession: {accession})...")

headers = {
    'User-Agent': 'MyCompany contact@mycompany.com',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.sec.gov'
}

response = requests.get(base_url, headers=headers)

# Guardar en data/
os.makedirs('data', exist_ok=True)
output_path = 'data/apple_10k_xbrl.xml'

with open(output_path, 'wb') as f:
    f.write(response.content)

size_mb = os.path.getsize(output_path) / (1024 * 1024)
print(f"✓ Archivo guardado: {output_path}")
print(f"  Tamaño: {size_mb:.2f} MB")

# Verificar que es XML válido
with open(output_path, 'r', encoding='utf-8', errors='ignore') as f:
    first_line = f.readline()
    print(f"  Primera línea: {first_line[:100]}")
