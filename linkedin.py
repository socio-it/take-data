from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import os                                             # <-- nuevo

# ----------------- CONFIG -----------------
url_de_la_pagina = "https://www.linkedin.com/feed/"   # Puedes cambiar la URL
# Pega tu cookie o guárdala en una variable de entorno llamada LI_AT_COOKIE
LI_AT_COOKIE = os.getenv("LINKEDIN_COKIE")
# ------------------------------------------

try:
    print(f"Intentando abrir la página: {url_de_la_pagina}")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    # 1) Ir primero al dominio base para que Selenium permita agregar la cookie
    driver.get("https://www.linkedin.com")            # <-- nuevo
    time.sleep(2)                                     # <-- nuevo

    # 2) Añadir la cookie de sesión
    driver.add_cookie({                               # <-- nuevo
        "name": "li_at",
        "value": LI_AT_COOKIE,
        "domain": ".linkedin.com",
        "path": "/"
    })

    # 3) Ahora sí, ir a la página deseada (feed)
    driver.get(url_de_la_pagina)                      # <-- (antes ya estaba driver.get)
    print(f"Título de la página: {driver.title}")

    selector_css_del_boton = ".alternate-signin__btn--google.margin-top-12"
    print(f"Esperando a que el botón con el selector '{selector_css_del_boton}' sea clickeable...")

    # IMPORTANTE: Espera explícita para asegurar que el elemento esté listo
    boton_google = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector_css_del_boton))
    )
    print("Botón encontrado. Haciendo clic.")
    boton_google.click()

    # Espera un momento para ver el resultado
    time.sleep(5)
    print("La página permanecerá abierta por 10 segundos...")
    time.sleep(10)

except Exception as e:
    print(f"Ocurrió un error: {e}")

finally:
    if 'driver' in locals() and driver is not None:
        print("Cerrando el navegador.")
        driver.quit()
