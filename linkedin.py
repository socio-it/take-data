from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeManager
import time

# URL de la página que quieres abrir
url_de_la_pagina = "https://www.linkedin.com/feed/"  # Puedes cambiar esto a la URL que desees

# Inicializar el WebDriver de Chrome usando webdriver-manager
# Esto descargará y configurará automáticamente el ChromeDriver si es necesario
try:
    print(f"Intentando abrir la página: {url_de_la_pagina}")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    # Abrir la página web especificada
    driver.get(url_de_la_pagina) # [1, 2, 3, 4, 5, 6]

    # Opcional: Imprimir el título de la página para confirmar que se cargó
    print(f"Título de la página: {driver.title}") # [2, 6]

    selector_css_del_boton = ".alternate-signin__btn--google.margin-top-12"

    print(f"Esperando a que el botón con el selector '{selector_css_del_boton}' sea clickeable...")

    # IMPORTANTE: Espera explícita para asegurar que el elemento esté listo
    # Espera hasta 10 segundos antes de lanzar una excepción de Timeout
    boton_google = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector_css_del_boton))
    )

    print("Botón encontrado. Haciendo clic.")
    boton_google.click()

    # Espera un momento para ver el resultado
    time.sleep(5)
    # Opcional: Mantener la ventana del navegador abierta por unos segundos
    # para que puedas verla antes de que se cierre.
    # En un script de scraping real, aquí iría la lógica para interactuar con la página.
    print("La página permanecerá abierta por 10 segundos...")
    time.sleep(10) # [7]

except Exception as e:
    print(f"Ocurrió un error: {e}")

finally:
    # Asegurarse de cerrar el navegador al final
    if 'driver' in locals() and driver is not None:
        print("Cerrando el navegador.")
        driver.quit() # [2, 3, 8, 6]li


"""

"""