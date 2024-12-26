from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task, dag
import chromedriver_autoinstaller
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, Tag
import os
from tasks.merge_all_xml import merge_all_xml
from tasks.push_all_in_one import push_all_in_one
from utils.xmltv import xmltv
from utils.push_to_github import push_to_github
import pendulum

# Definición del DAG utilizando el decorador de contexto
default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=15),
    'start_date' : pendulum.datetime(2024, 12, 6, tz="Europe/Madrid"),  # Fecha de inicio con zona horaria
}

@dag(
    'rtve_schedule_scraper',
    default_args=default_args,
    description='DAG para scrapeo de horarios de TV desde RTVE',
    schedule_interval='30 00,06,12,18 * * *',
    catchup=False,  # Esto evita que el DAG se ejecute para fechas pasadas si el inicio es reciente
    tags=["RTVE"],
)
# Función que se ejecutará en el DAG
def rtve_schedule_scraper():

    @task()
    def scrape_rtve_task():
        script_directory = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_directory)
        # Configuración de opciones de Chrome
        # chromedriver_autoinstaller.install() 
        # locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument("--headless")  # Si deseas ejecutar sin interfaz gráfica, puedes usar esta opción
        chrome_options.add_argument("--disable-gpu")  # Desactiva la aceleración de gráficos
        # Inicializar el navegador con el servicio y las opciones
        remote_webdriver = 'remote_chromedriver'
        driver = webdriver.Remote(f'{remote_webdriver}:4444/wd/hub', options=chrome_options)
        # driver = webdriver.Chrome(options=chrome_options)
        # Abrir la página
        driver.get(f'https://www.rtve.es/play/guia-tve/')
        driver.implicitly_wait(5)
        
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))
            ).click()
        except:
            pass

        driver.implicitly_wait(5)
        soup = BeautifulSoup(driver.page_source, features="lxml")
        channels_schedules: list[Tag] = soup.find_all('div', class_='tvSchedule')
        
        current_year = datetime.now().year
        meses = {
        'ENE': 1,
        'FEB': 2,
        'MAR': 3,
        'ABR': 4,
        'MAY': 5,
        'JUN': 6,
        'JUL': 7,
        'AGO': 8,
        'SEP': 9,
        'OCT': 10,
        'NOV': 11,
        'DIC': 12
        }

        for channel in channels_schedules:
            channel_name = channel.find('span', class_='rtve-icons').text
            channel_programmes: list[Tag] = channel.find_all('div', class_='content')
            channel_xmltv = xmltv()
            channel_xmltv.add_channel(channel_name)
            
            for programme in channel_programmes[0:-1]:
                programme_name = programme.find('span', class_='maintitle').text
                programme_prename = programme.find('span', class_='pretitle').text
                programme_description = programme.find('p').text
                programme_description = f'{programme_prename}: {programme_description}' if programme_description else programme_prename
                programme_icon = programme.find('img',class_='i_prvw').get('src')
                programme_day = programme.find('span', class_='datemi').text.split(' ')[0]
                programme_month = meses[programme.find('span', class_='datemi').text.split(' ')[1]]
                programme_hours = programme.find('span', class_='horemi').text
                programme_hour_start = programme_hours.split('-')[0] 
                programme_hour_end = programme_hours.split('-')[1]
                
                programme_start_datetime = datetime.strptime(f'{programme_day} {programme_month} {current_year} {programme_hour_start}', "%d %m %Y %H:%M")
                programme_end_datetime = datetime.strptime(f'{programme_day} {programme_month} {current_year} {programme_hour_end}', "%d %m %Y %H:%M")
                
                if programme_end_datetime < programme_start_datetime:
                    programme_end_datetime += timedelta(days=1)
                    if programme_start_datetime.year != programme_end_datetime.year:
                        current_year = programme_end_datetime.year

                programme_start_str = programme_start_datetime.strftime("%Y%m%d%H%M%S") + ' +0100'
                programme_end_str = programme_end_datetime.strftime("%Y%m%d%H%M%S") + ' +0100'
                
                channel_xmltv.add_programme(channel_name=channel_name,
                                            start_time=programme_start_str, 
                                            end_time=programme_end_str,
                                            programe_name=programme_name,
                                            icon=programme_icon,
                                            description=programme_description)
            
            epgs_path = '/opt/airflow/dags/epgs' # Ruta completa hacia la carpeta 'epgs'
            if not os.path.exists(epgs_path):
                os.makedirs(epgs_path)
            # Definir la ruta completa del archivo que se quiere guardar
            xmltv_local_path = os.path.join(epgs_path, f'{channel_name}.xml')
            xmltv_repo_path = f'channels/{channel_name}.xml'
            channel_xmltv.write_xmltv(xmltv_local_path)
            push_to_github(xmltv_local_path, xmltv_repo_path)
            print(f'Escrito el xmltv del canal "{channel_name}"')

        
        driver.quit()

    flow = scrape_rtve_task() >> merge_all_xml() >> push_all_in_one()

rtve_dag = rtve_schedule_scraper()