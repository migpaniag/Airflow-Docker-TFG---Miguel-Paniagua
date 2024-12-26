from datetime import datetime, timedelta
import os
import requests
from bs4 import BeautifulSoup
from utils.xmltv import xmltv
from pytz import timezone
from airflow import DAG
from airflow.decorators import task, dag
from utils.push_to_github import push_to_github
from tasks.merge_all_xml import merge_all_xml
from tasks.push_all_in_one import push_all_in_one
from airflow.operators.python import PythonOperator
from datetime import datetime
from zoneinfo import ZoneInfo
import pendulum


# Definición del DAG utilizando el decorador de contexto
default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=15),
    'start_date' : pendulum.datetime(2024, 12, 6, tz="Europe/Madrid"),  # Fecha de inicio con zona horaria
}

@dag(
    'la_otra_schedule_scraper',
    default_args=default_args,
    description='DAG para scrapeo de horarios de TV de La Otra',
    schedule_interval='30 00,06,12,18 * * *',
    catchup=False,  # Evitar que se ejecute para fechas pasadas
    tags=["Telemadrid","La Otra"],
)
def la_otra_schedule_scraper():
    
    # Función para scrapear la programación de Telemadrid
    @task()
    def scrape_la_otra_schedule():
        channel_title = 'La Otra'
        channel_url = 'https://www.telemadrid.es/programacion-laotra/'
        current_year = datetime.now().year
        meses = {
            "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5,
            "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10,
            "Noviembre": 11, "Diciembre": 12
        }

        # Realizar la petición HTTP y parsear el HTML
        response = requests.get(channel_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        daily_schedules = soup.find_all('div', class_='tv-schedule__list')

        channel_xmltv = xmltv()
        channel_xmltv.add_channel(channel_title)

        for day_schedule in daily_schedules:
            sum_day = False
            schedule_date = day_schedule.find('h2').text.split()
            schedule_day = schedule_date[1]
            schedule_month = meses[schedule_date[2]]
            programmes = day_schedule.find_all('article', class_='tv-schedule__item')

            for programme in programmes:
                programme_title = programme.find('a', class_='lnk').text
                programme_icon = programme.find('img', class_='photo').get('data-src') if programme.find('img', class_='photo') else ''
                programme_description = programme.find('small').text
                programme_hours = programme.find('p').text
                programme_start_hour = programme_hours.split(' - ')[0].strip()
                programme_end_hour = programme_hours.split(' - ')[1].strip()

                programme_start_datetime = datetime.strptime(f'{schedule_day} {schedule_month} {current_year} {programme_start_hour}', "%d %m %Y %H.%M")
                programme_end_datetime = datetime.strptime(f'{schedule_day} {schedule_month} {current_year} {programme_end_hour}', "%d %m %Y %H.%M")

                # Control de año y día si pasa las 00:00
                if programme_end_datetime < programme_start_datetime and not sum_day:
                    programme_end_datetime += timedelta(days=1)
                    sum_day = True
                    if programme_start_datetime.year != programme_end_datetime.year:
                        current_year = programme_end_datetime.year
                elif sum_day:
                    programme_start_datetime += timedelta(days=1)
                    programme_end_datetime += timedelta(days=1)

                programme_start_formated = programme_start_datetime.strftime("%Y%m%d%H%M%S") + ' +0100'
                programme_end_formated = programme_end_datetime.strftime("%Y%m%d%H%M%S") + ' +0100'

                channel_xmltv.add_programme(channel_name=channel_title,
                                            start_time=programme_start_formated,
                                            end_time=programme_end_formated,
                                            programe_name=programme_title,
                                            icon=programme_icon,
                                            description=programme_description)

        # Guardar el archivo XMLTV
        epgs_path = '/opt/airflow/dags/epgs'
        if not os.path.exists(epgs_path):
            os.makedirs(epgs_path)

        xmltv_local_path = os.path.join(epgs_path, f'{channel_title}.xml')
        xmltv_repo_path = f'channels/{channel_title}.xml'
        channel_xmltv.write_xmltv(xmltv_local_path)
        print(f'Escrito el xmltv del canal "{channel_title}"')
        
        # Subir el archivo a GitHub
        push_to_github(xmltv_local_path, xmltv_repo_path)
    
    # Definición de la secuencia de ejecución
    flow = scrape_la_otra_schedule() >> merge_all_xml() >> push_all_in_one()

# Para crear el DAG solo tienes que invocar la función `telemadrid_schedule_scraper`
dag_la_otra = la_otra_schedule_scraper()
