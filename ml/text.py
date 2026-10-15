import re
import unicodedata

def normalize(text: str) -> str:
    return ' '.join(unicodedata.normalize('NFC', str(text)).split())

def anonymize(text: str) -> str:
    """Redacción preliminar; nombres/domicilios necesitan revisión humana."""
    text = normalize(text)
    patterns = [
        (r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b', '[CORREO]'),
        (r'(?<!\w)(?:\+51[ -]?)?9(?:[ -]?\d){8}(?!\w)', '[TELEFONO]'),
        (r'\b(?:DNI\s*[:#]?\s*)?\d{8}\b', '[DNI]'),
        (r'\b(?:me llamo|mi nombre es|soy el señor|soy la señora)\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+){0,3}', '[NOMBRE]'),
        (r'\b(?:calle|jirón|jr\.?|avenida|av\.?)\s+[\wáéíóúñ .-]{1,60}\s+(?:n[°º.]?\s*)?\d{1,5}\b', '[DOMICILIO]'),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE if replacement != '[NOMBRE]' else 0)
    return text
