# Guardar como: debug_revenue.py
import lxml.etree as ET

# Cargar archivo
tree = ET.parse('data/apple_10k_xbrl.xml')
root = tree.getroot()

# Extraer namespaces
ns = {k if k else 'default': v for k, v in root.nsmap.items()}

# Buscar TODOS los tags que contengan "Revenue"
print("\n🔍 Tags que contienen 'Revenue':")
print("-" * 50)

for elem in root.iter():
    tag_name = elem.tag.split('}')[-1]  # Eliminar namespace
    if 'Revenue' in tag_name and elem.text and elem.text.strip():
        # Mostrar tag completo + valor
        full_tag = elem.tag
        value = elem.text.strip()
        
        print(f"\nTag: {full_tag}")
        print(f"Valor: {value}")
        print(f"Contexto: {elem.get('contextRef', 'N/A')}")

print("\n" + "="*50)
print("✅ Copia el tag COMPLETO que tenga el revenue anual")
