import os, time, random, json, traceback
from functools import wraps
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ---------- CONFIGURACIÓN ----------
PROFILE_URL  = "https://www.linkedin.com/in/julianavasqueza/"
LI_AT        = os.getenv("LINKEDIN_COOKIE")   # solo valor de li_at
JSID         = os.getenv("JSID_COOKIE")       # opcional
SCROLL_TIME  = 30     # seg. para la lista de publicaciones
PAUSE_RANGE  = (0.8, 1.8)
# ------------------------------------

if not LI_AT or len(LI_AT) < 50:
    raise ValueError("LINKEDIN_COOKIE vacío o demasiado corto")

def human():
    """Pequeña pausa aleatoria para simular comportamiento humano."""
    time.sleep(random.uniform(*PAUSE_RANGE))

# ------------------------------------------------------------------
# 🛠  UTILIDADES
# ------------------------------------------------------------------

def wait_for(locator: str, by: By = By.CSS_SELECTOR, timeout: int = 15,
            clickable: bool = True):
    """Espera a que un elemento esté presente (y opcionalmente *clickable*).

    Además hace *scrollIntoView* para asegurarse de que el nodo existe en el
    viewport, algo imprescindible en LinkedIn porque mucha parte del DOM se
    monta sólo cuando el usuario hace scroll.
    """
    # 1) Esperamos presencia
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, locator))
    )
    # 2) Lo traemos al centro de la pantalla
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", el
        )
    except Exception:
        # si falla, seguimos adelante
        pass
    # 3) Esperamos que sea clickable si procede
    if clickable:
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, locator))
        )
    return el

def safe(paso):
    """Decorador para envolver los pasos y loguear la excepción
    sin abortar el scraping completo."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                print(f"❌  Error en «{paso}»: {e}")
                traceback.print_exc()
                return None
        return wrapper
    return decorator

# ---- Chrome “menos detectable” ----
opts = webdriver.ChromeOptions()
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_argument("--disable-gpu")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=opts
)

perfil = {}          # dict donde guardaremos cada sección

try:
    # 1) Sesión ----------------------------------------------------------------
    driver.get("https://www.linkedin.com")
    driver.delete_all_cookies()
    driver.add_cookie({"name": "li_at", "value": LI_AT,
                       "domain": ".linkedin.com", "path": "/"})
    if JSID:
        driver.add_cookie({"name": "JSESSIONID", "value": JSID,
                           "domain": ".linkedin.com", "path": "/"})
    driver.get(PROFILE_URL)
    wait_for("body", By.TAG_NAME, clickable=False)  # página cargada

    # 2) Información de contacto ----------------------------------------------
    @safe("Información de contacto")
    def contacto():
        wait_for("top-card-text-details-contact-info", By.ID).click()
        wait_for("div.artdeco-modal__content", clickable=False)
        human()
        perfil["contacto_html"] = driver.page_source
        # Cerrar modal
        driver.find_element(By.CSS_SELECTOR,
                            "button.artdeco-modal__dismiss").click()
    contacto()

    # 3) Acerca de -------------------------------------------------------------
    @safe("Acerca de")
    def acerca():
        try:
            btn = wait_for("//section[contains(@class,'about')]//button"\
                           "[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"\
                           " 'abcdefghijklmnopqrstuvwxyz'),'ver más')]", By.XPATH,
                           timeout=6)
            btn.click()
            human()
        except TimeoutException:
            # puede que el botón no exista
            pass
        sec = driver.execute_script(
            """return document.evaluate(
                     "//section[contains(@class,'about')]", document, null,
                     XPathResult.FIRST_ORDERED_NODE_TYPE, null).\
                     singleNodeValue;""")
        perfil["acerca_html"] = (sec.get_attribute("outerHTML")
                                   if sec else "<!-- no about -->")
    acerca()

    # 4) Publicaciones ---------------------------------------------------------
    @safe("Publicaciones")
    def publicaciones():
        """Obtiene todas las publicaciones.

        1. Intenta navegar directamente a /recent-activity/posts/.
        2. Si falla (p.e. LinkedIn redirige a 'all'), intenta hacer clic en la
           pestaña de Actividad.
        """
        reached = False
        try:
            driver.get(PROFILE_URL + "recent-activity/posts/")
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body")))
            reached = True
        except TimeoutException:
            # volvemos atrás y probamos mediante clic
            driver.back()

        if not reached:
            wait_for("//a[contains(@href,'recent-activity')]",
                     By.XPATH).click()

        end = time.time() + SCROLL_TIME
        while time.time() < end:
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            human()
        perfil["publicaciones_html"] = driver.page_source
        driver.back()
        human()
    publicaciones()

    # 5) Aptitudes -------------------------------------------------------------
    @safe("Aptitudes")
    def aptitudes():
        sec_xpath = "//section[@id='skills']"
        wait_for(sec_xpath, By.XPATH, clickable=False)

        # Botón «Mostrar todas» (puede variar su texto o no existir)
        btns = driver.find_elements(
            By.XPATH,
            "//section[@id='skills']//button["\
            "contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mostrar')"\
            "]")

        if btns:
            driver.execute_script("arguments[0].click();", btns[0])
            wait_for("div.artdeco-modal__content", clickable=False)
            human()
            perfil["aptitudes_html"] = driver.page_source
            driver.find_element(By.CSS_SELECTOR,
                                "button.artdeco-modal__dismiss").click()
        else:
            # sin botón => pocas aptitudes listadas inline
            perfil["aptitudes_html"] = driver.page_source
    aptitudes()

    # 6) Copia completa del perfil tal como quedó ------------------------------
    perfil["perfil_html"] = driver.page_source

    # 7) Guardar ---------------------------------------------------------------
    with open("perfil_completo.json", "w", encoding="utf-8") as f:
        json.dump(perfil, f, ensure_ascii=False, indent=2)
    print("✅ Terminado; datos en perfil_completo.json")

except Exception as e:
    print("🚨 Excepción general:", e)
    traceback.print_exc()
finally:
    driver.quit()
