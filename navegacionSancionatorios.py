import logging
from helium import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
import os
from dotenv import load_dotenv
load_dotenv()

def crear_driver():
    logging.debug(f"Abriendo chrome")
    PATH_CHROME_DRIVER = os.path.join(os.path.dirname(__file__), os.environ.get('CHROME_DRIVER'))

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 " \
                 "Safari/537.36 "
    options = ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-logging')
    options.add_argument('--log-level=3')
    options.add_argument(f'--user-agent={user_agent}')
    Config.implicit_wait_secs = 120

    nombre = 'Descargas'
    carpeta_descarga = os.path.join(os.getcwd(), nombre)
    if not os.path.exists(carpeta_descarga):
        os.makedirs(carpeta_descarga)
    prefs = {"download.default_directory": carpeta_descarga
             }
    options.add_experimental_option("prefs", prefs)
    carpeta_base =  '/home/ubuntu/Sancionatorios/'
    carpeta_csv = os.path.join(carpeta_base, 'Reportes')
    carpeta_descarga = os.path.join(os.getcwd(), carpeta_csv)
    if not os.path.exists(carpeta_descarga):
        os.makedirs(carpeta_descarga)
    prefs = {"download.default_directory": carpeta_descarga
             }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(PATH_CHROME_DRIVER, options=options)
    set_driver(driver)
    logging.debug(f"Cargando página Sancionatorios")
    driver.get('https://snifa.sma.gob.cl/DatosAbiertos')
    return driver
