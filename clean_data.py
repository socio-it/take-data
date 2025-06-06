"""
clean_data.py  —  Limpia el JSON crudo exportado por tu scraper de LinkedIn
Requisitos: beautifulsoup4 (pip install beautifulsoup4)
"""

import json, re, unicodedata, sys
from pathlib import Path
from bs4 import BeautifulSoup

# ────────────────────────── CONFIGURA AQUÍ ───────────────────────────────
RAW_FILE = Path("take-data\perfil_completo.json")   # JSON de entrada (crudo)
OUT_FILE = Path("perfil_limpio.json")     # JSON limpio de salida
# ─────────────────────────────────────────────────────────────────────────

if not RAW_FILE.exists():
    sys.exit(f"❌  No se encontró «{RAW_FILE.resolve()}»")

###########################################################################
# ---------------------------  HELPERS  -----------------------------------
###########################################################################

RE_EMOJI  = re.compile(
    r"[\U0001F300-\U0001F64F\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF]+",
    flags=re.UNICODE
)
RE_EMAIL  = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
RE_PHONE  = re.compile(r"\+?\d[\d\s.-]{7,}\d")
RE_URL    = re.compile(r"https?://[^\s]+")

def html2text(html: str | None) -> str:
    """Convierte HTML a texto plano compacto, sin emojis ni dobles espacios."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    txt  = soup.get_text(" ", strip=True)
    txt  = RE_EMOJI.sub("", txt)
    txt  = unicodedata.normalize("NFKC", txt)
    txt  = re.sub(r"\s{2,}", " ", txt)
    return txt.strip()

def split_posts(posts_html: str | None) -> list[str]:
    """Devuelve lista deduplicada de textos (≥30 car.) de cada publicación."""
    if not posts_html:
        return []
    soup  = BeautifulSoup(posts_html, "html.parser")
    cards = soup.select("div.feed-shared-update-v2")
    posts = {html2text(str(c)) for c in cards}
    return [p for p in posts if len(p) >= 30]

def contact_details(text: str) -> dict:
    """Agrupa mails, teléfonos y URLs extraídos del texto."""
    return {
        "texto":     text,
        "emails":    sorted(set(RE_EMAIL.findall(text))),
        "telefonos": sorted(set(RE_PHONE.findall(text))),
        "urls":      sorted(set(RE_URL.findall(text)))
    }

###########################################################################
# -------------------------  LIMPIEZA  ------------------------------------
###########################################################################

raw = json.loads(RAW_FILE.read_text(encoding="utf-8"))

perfil_text   = html2text(raw.get("perfil_html"))
contacto_text = html2text(raw.get("contacto_html"))
acerca_text   = html2text(raw.get("acerca_de_html"))
posts_list    = split_posts(raw.get("publicaciones_html"))
skills_text   = html2text(raw.get("aptitudes_html"))

# Nombre, titular y ubicación
nombre, titular = "", ""
parts = re.split(r"\s[·│|]\s", perfil_text, maxsplit=2)
if parts:
    nombre  = parts[0].strip()
    titular = parts[1].strip() if len(parts) > 1 else ""

ubic_match = re.search(r"(Área [^·│|]+|Colombia[^·│|]*|[A-Z][a-z]+,\s?[A-Z]{2})", perfil_text)
ubicacion  = ubic_match.group(1).strip() if ubic_match else ""

# Aptitudes deduplicadas y capitalizadas
aptitudes = sorted({w.strip().title()
                    for w in re.findall(r"[A-ZÁÉÍÓÚÑ][\w\+#\- ]{2,}", skills_text)
                    if len(w.strip()) > 2})

###########################################################################
# -------------------------  OBJETO FINAL  --------------------------------
###########################################################################

clean = {
    "perfil": {
        "nombre":     nombre,
        "titular":    titular,
        "resumen":    acerca_text,
        "ubicacion":  ubicacion
    },
    "contacto": contact_details(contacto_text),
    "publicaciones": [{"texto": t} for t in posts_list],
    "aptitudes": aptitudes
}

OUT_FILE.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✓ JSON limpio guardado en →  {OUT_FILE.resolve()}")
