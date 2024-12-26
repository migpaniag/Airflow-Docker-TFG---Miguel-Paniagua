from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task, dag
import locale
import requests
from bs4 import BeautifulSoup, Tag
import xml.etree.ElementTree as ET
from utils.xmltv import xmltv
import os
from tasks.merge_all_xml import merge_all_xml
from tasks.push_all_in_one import push_all_in_one
from utils.xmltv import xmltv
from utils.push_to_github import push_to_github
import pendulum

# Definición del DAG utilizando el decorador de contexto
default_args = {
    'owner': 'airflow',
    'retries': 4,
    'retry_delay': timedelta(minutes=30),
    'start_date' : pendulum.datetime(2024, 12, 6, tz="Europe/Madrid"),  # Fecha de inicio con zona horaria
}

@dag(
    'a3media_schedule_scraper',
    default_args=default_args,
    description='DAG para scrapeo de horarios de TV de A3Media',
    schedule_interval='30 00,06,12,18 * * *',
    catchup=False,  # Esto evita que el DAG se ejecute para fechas pasadas si el inicio es reciente
    tags=["A3media"],
)
# Función que se ejecutará en el DAG
def a3media_schedule_scraper():

    @task()
    def scrape_a3media_task():
        # script_directory = os.path.dirname(os.path.abspath(__file__))
        # os.chdir(script_directory)
        base_url = 'https://api.atresplayer.com/client/v1/page/programming'
        scraper = requests.Session()
        days_to_request = 3
        response = scraper.get(base_url)
        response_json = response.json()
        channels_data = [channel for channel in response_json['rows'] if not 'eventChannel' in channel.keys()]

        for channel in channels_data:
            channel_title = channel['title'].replace('Directo ','')
            channel_schedule_url = channel['href']
            datetime_to_request = datetime.now() - timedelta(days=1)
            channel_xmltv = xmltv()
            channel_xmltv.add_channel(channel_title)

            for day in range(0, days_to_request):
                # Formatear la URL correctamente para cada fecha
                url = channel_schedule_url + '{dt.day}-{dt.month}-{dt.year}'.format(dt=datetime_to_request)
                print(url)

                # Obtener los datos
                channel_data = scraper.get(url).json()
                channel_programmes = channel_data['itemRows']

                # Procesar los programas
                for programme in channel_programmes:
                    programme_title = programme['title']
                    programme_description = programme['description'] if 'description' in programme else ''
                    programme_icon = programme['image']['pathHorizontal'] + '1280x720.jpg'
                    programme_start_time = programme['startTime']
                    programme_end_time = programme['endTime']
                    programme_start_datetime = datetime.fromtimestamp(programme_start_time / 1000) + timedelta(hours=1)
                    programme_end_datetime = datetime.fromtimestamp(programme_end_time / 1000) + timedelta(hours=1)
                    programme_start_format = programme_start_datetime.strftime("%Y%m%d%H%M%S") + ' +0100'
                    programme_end_format = programme_end_datetime.strftime("%Y%m%d%H%M%S") + ' +0100'
                    
                    # Añadir la programación al XMLTV
                    channel_xmltv.add_programme(
                        channel_name=channel_title,
                        start_time=programme_start_format,
                        end_time=programme_end_format,
                        programe_name=programme_title,
                        icon=programme_icon,
                        description=programme_description
                    )

                # Asegúrate de sumar un día a la fecha de la próxima iteración
                datetime_to_request += timedelta(days=1)

            epgs_path = '/opt/airflow/dags/epgs'  # Ruta completa hacia la carpeta 'epgs'
            
            # Verificar si la carpeta 'epgs' existe, si no, crearla
            if not os.path.exists(epgs_path):
                os.makedirs(epgs_path)

            # Definir la ruta completa del archivo que se quiere guardar
            xmltv_local_path = os.path.join(epgs_path, f'{channel_title}.xml')
            xmltv_repo_path = f'channels/{channel_title}.xml'
            channel_xmltv.write_xmltv(xmltv_local_path)
            print(f'Escrito el xmltv del canal "{channel_title}"')
            push_to_github(xmltv_local_path, xmltv_repo_path)
        
    flow = scrape_a3media_task() >> merge_all_xml() >> push_all_in_one()

dag_a3media = a3media_schedule_scraper()
