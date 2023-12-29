from sys import stdout
import logging
from dotenv import load_dotenv
load_dotenv()


def main():

    file_handler = logging.FileHandler(filename='tmp.log', encoding='utf-8', mode='a')
    stdout_handler = logging.StreamHandler(stream=stdout)
    handlers = [file_handler]

    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                        handlers=handlers)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("requests").setLevel(logging.ERROR)
    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.ERROR)

    logging.info(f"Iniciando proceso para sancionatorios")
    from extraer_sancionatorios import descargar_y_generar_reportes
    descargar_y_generar_reportes()
    logging.info("Finalizando proceso.")


if __name__ == "__main__":
    main()
