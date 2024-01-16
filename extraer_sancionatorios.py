import logging
from helium import *
import pandas as pd
import time
import os
import shutil
from datetime import datetime
import re
from selenium.common.exceptions import NoSuchElementException
from navegacionSancionatorios import crear_driver
from unidecode import unidecode

fecha_actual = datetime.now().strftime('%d-%m-%Y')
ruta_archivo = '/home/ubuntu/Sancionatorios/Reportes'

def descargar_archivo_sancionatorio():
    driver = crear_driver()
    time.sleep(1)
    sancionatorios = '/html/body/div[6]/div/div/div[2]/div/div[1]/div[1]/div[3]/div/a'
    click(driver.find_element_by_xpath(sancionatorios))
    time.sleep(1)
    click(driver.find_element_by_xpath('//*[@id=":1"]/div/c-wiz/div[2]/c-wiz/div[1]/c-wiz/div[2]/c-wiz/div[1]/c-wiz/c-wiz/div/c-wiz[3]/div/div/div/div[6]/div/span'))
    time.sleep(10)
    kill_browser()
    
    nuevo_nombre = f'Sancionatorios_{fecha_actual}.xlsx'
    archivo_descargado = os.path.join(ruta_archivo, 'Sancionatorios.xlsx')
    os.rename(archivo_descargado, os.path.join(ruta_archivo, nuevo_nombre))

def leer_y_buscar_registros():
    logging.info("Abriendo Excel")
    hechos_sancionatorios = []
    nombre_archivo = f'Sancionatorios_{fecha_actual}.xlsx'
    archivo = os.path.join(ruta_archivo, nombre_archivo)
    try: 
        df = pd.read_excel(archivo)
        df_sin_duplicados = df.drop_duplicates(subset=['Expediente'])
    except FileNotFoundError:
        logging.warning("El archivo no se encuentra, intentando descargar denuevo")
        descargar_archivo_sancionatorio()

    driver = crear_driver()
    for row in df_sin_duplicados.itertuples(index=False):
        link = row.LinkSNIFA_UF
        num_expediente = row.Expediente
        nombre = row.Nombre
        proceso_sancion = row.ProcesoSancionTipoNombre
        proceso_sancion_id = row.ProcesoSancionId
        estado = row.ProcesoSancionEstado
        fecha_inicio = row.FechaInicio
        fecha_termino = row.FechaTermino
        confirmacion_pdc = row.ConfirmaPdC
        multa = row.MultaTotalUTA
        unidad_fiscalizada = row.UnidadFiscalizableId
        nombre = row.Nombre
        latitud = row.Latitud
        longitud = row.Longitud
        categoria = row.CategoriaEconomicaNombre
        subcategoria = row.SubCategoriaEconomicaNombre
        link_uf = row.LinkSNIFA_UF
        actualizacion = row.FechaActualizacion
        comuna = row.ComunaNombre
        region = row.RegionNombre
        logging.info(f"Buscando num expediente: {num_expediente} con nombre {nombre}")
        driver.get(link)
        try:
            wait_until(lambda: not S('//*[@id="cargandoInformacion"]/div/div/div/div/b').exists(), timeout_secs=10)
        except TimeoutError:
            logging.error("El tiempo de espera para la página fue excedido")
            leer_y_buscar_registros()

        try:
            tabla_titular = driver.find_element_by_xpath('//*[@id="tResultado1"]').get_attribute('outerHTML')
            tabla_titulares = pd.read_html(tabla_titular)[0]
            if len(tabla_titulares) > 1:
                index_tr = 0 
                for _, row in tabla_titulares.iterrows():
                    index_tr += 1
                    if unidecode(row[1].lower()) in unidecode(nombre.lower()):
                        rut = row[0]
                        break
                else:
                    index_tr = 0
                    for _, row in tabla_titulares.iterrows():
                        index_tr += 1
                        if row[0] != 'Información Reservada':
                            rut = row[0]
                            break
                    else:
                        rut = driver.find_element_by_xpath('//*[@id="tResultado1"]/tbody/tr/td[1]').text
            else:
                rut = driver.find_element_by_xpath('//*[@id="tResultado1"]/tbody/tr/td[1]').text
        except NoSuchElementException:
            logging.warning(f'El expediente buscado: {num_expediente}, no contiene un rut')
            rut = ''
        
        logging.info(f"Buscando hechos para expediente {num_expediente}")
        driver.get('https://snifa.sma.gob.cl/DatosAbiertos')
        click(driver.find_element_by_xpath('//*[@id="dos"]/a'))

        logging.info(f"Escribiendo num expediente")
        click(driver.find_element_by_xpath('//*[@id="expediente"]'))
        write(num_expediente)

        click(driver.find_element_by_xpath('//*[@id="formularioBuscarSancionatorio"]/button[2]'))
        time.sleep(1)
        try:
            wait_until(lambda: not S('//*[@id="cargandoInformacion"]/div/div/div/div/div/div').exists(), timeout_secs=10)
        except:
            logging.error("El tiempo de espera para la página fue excedido")
            leer_y_buscar_registros()

        logging.info("Comprobando si la tabla tiene datos")
        sin_datos = 'No hay datos en la tabla' in S('//*[@id="myTable"]').web_element.text

        if not sin_datos:
            logging.info("La tabla contiene registros procediendo a extraer registros")
            click(driver.find_element_by_xpath('//*[@id="myTable"]/tbody/tr/td[8]'))
            try:
                click(driver.find_element_by_xpath('//*[@id="tabs-0"]/li[2]/a'))
                url_actual = driver.current_url
                tabla = driver.find_element_by_xpath('//*[@id="instrumentos-considerados"]/table').get_attribute('outerHTML')
                tabla_hechos = pd.read_html(tabla)[0]
                if len(tabla_hechos) > 0:
                    patron = r'\b\d+\.\d+\.\d|\b\d+\.\d+\.|\b\d+\.\d+\b|\b\d+\.|[A-Z]\d+\.|[A-Z]+\.\d+\:|[A-Z]+\.\d+\.\d|[A-Z]+\.\d+\.|\b[A-Za-z]\.\d+\b|[A-Z]+\.|[A-Z]+\:|[A-Z]\d+\:|[A-H]+\d|\b\d+\)'
                    for _, row in tabla_hechos.iterrows():
                        correlativo = row['#']
                        hecho = row['Hecho']
                        hecho = row['Hecho'].replace('"""', '').replace('"', '')
                        hecho = re.sub(patron, '', hecho)
                        hecho = hecho.replace(':', '').strip()
                        texto = row['Clasificación(Art. 36 LOSMA)']

                        patron_clasificacion = re.compile(r'(Leves|Graves|Gravísimas)', re.IGNORECASE)
                        try:
                            clacificacion = [match.group(1) for match in patron_clasificacion.finditer(texto) if match.group(1)]
                            clasificaciones_str = ', '.join(clacificacion)
                        except TypeError:
                            logging.warning('La columna clasificacion de la tabla de hecho, esta vacia')
                            clasificaciones_str= ''
                        clasificaciones_str= clasificaciones_str.split(',')[0]        
                        
                        nuevo_registro = {'Data_field': correlativo, 'Original_URL': url_actual, 'Hecho': hecho, 
                                'Clasificacion_Art_36_LOSM': clasificaciones_str, 'ProcesoSancionId': proceso_sancion_id, 'Expediente': num_expediente,
                                'ProcesoSancionTipoNombre': proceso_sancion, 'ProcesoSancionEstado': estado, 'FechaInicio': fecha_inicio,
                                'FechaTermino': fecha_termino, 'ConfirmaPdC': confirmacion_pdc, 'MultaTotalUTA': multa,
                                'UnidadFiscalizableId': unidad_fiscalizada, 'Nombre': nombre, 'RegionNombre': region, 'ComunaNombre': comuna,
                                'Latitud': latitud, 'Longitud': longitud, 'CategoriaEconomicaNombre': categoria, 'SubCategoriaEconomicaNombre':
                                subcategoria, 'LinkSNIFA_UF': link_uf, 'FechaActualizacion': actualizacion, 'RUT': rut
                            }
                        hechos_sancionatorios.append(nuevo_registro)
                else:
                    logging.warning("La tabla hechos esta vacia, omitiendo")
                    pass

            except NoSuchElementException:
                logging.warning(f"No se encontro el registro para la empresa {nombre} y rut: {rut} omitiendo")
                pass     
        else:
            logging.warning(f"No se encontraron procedimientos sancionatoris para la empresa {nombre} y rut: {rut} omitiendo")
            pass

    df_hechos_sancionatorios = pd.DataFrame(hechos_sancionatorios)
    archivo_xlsx = f'/home/ubuntu/Sancionatorios/Reportes/Sancionatorios_Act_{fecha_actual}.xlsx'
    df_hechos_sancionatorios.to_excel(archivo_xlsx, index=False)
    kill_browser()

def descargar_y_generar_reportes():
    logging.info("Descargando Sancionatorios")
    descargar_archivo_sancionatorio()
    logging.info("Abriendo Excel")
    leer_y_buscar_registros()

if __name__ == "__main__":
    descargar_y_generar_reportes()
