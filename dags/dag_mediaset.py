from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task, dag
import requests
from bs4 import BeautifulSoup, Tag
from utils.xmltv import xmltv
import os
from itertools import groupby
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
    'start_date' : pendulum.now(tz="Europe/Madrid")-timedelta(days=1),  # Fecha de inicio con zona horaria
}

@dag(
    'mediaset_schedule_scraper',
    default_args=default_args,
    description='DAG para scrapeo de horarios de TV de Mediaset',
    schedule_interval='30 00,06,12,18 * * *',
    catchup=False,  # Esto evita que el DAG se ejecute para fechas pasadas si el inicio es reciente
    tags=["Mediaset","Mitele"],
)
def mediaset_schedule_scraper():

    @task()
    def scrape_mediaset_schedule():
        script_directory = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_directory)
        current_datetime = datetime.now()
        days_for_requests = 3
        epgs_path = '/opt/airflow/dags/epgs'
        channels_data = {}
        scraper = requests.Session()
        canales = [
            "telecinco",
            "cuatro",
            "gh-24h-plus",
            "gh-24h",
            "mitele-en-la-calle",
            "mitele-viajes",
            "mitele-plus-lqsa",
            "mitele-comedia",
            "mitele-top-series",
            "divinity",
            "fdf",
            "energy",
            "bemad",
            "boing",
            "acontraplus",
            "fight-sports",
            "mtmad-24h"
        ]

        for day in range(0, days_for_requests):
            current_date_str = current_datetime.strftime("%Y-%m-%d")
            global_schedule = scraper.get(f'https://mab.mediaset.es/1.0.0/get?oid=bitban_live&eid=/epg?date={current_date_str}').json()
            schedule_grouped_by_channel = {key: list(group) for key, group in groupby(global_schedule, key=lambda x: x['channel'])}
            filtered_schedule = {key: group for key, group in schedule_grouped_by_channel.items() if key in canales}

            for channel_title, channel_schedule in filtered_schedule.items():
                channel_title = channel_title.capitalize().replace('-',' ')
                if channel_title not in channels_data:
                    channels_data[channel_title] = []

                # Añadir la programación de este día al canal correspondiente
                for programme in channel_schedule:
                    programme_title = programme['name']
                    programme_start_time = programme['init']
                    programme_end_time = programme['end']
                    programme_start_datetime = datetime.fromtimestamp(programme_start_time / 1000)
                    programme_end_datetime = datetime.fromtimestamp(programme_end_time / 1000)
                    programme_start_format = programme_start_datetime.strftime("%Y%m%d%H%M%S") + ' +0100'
                    programme_end_format = programme_end_datetime.strftime("%Y%m%d%H%M%S") + ' +0100'
                    programme_icon = programme['image_url']
                    programme_description = programme['description']
                    
                    # Guardar la programación del programa en la lista del canal
                    channels_data[channel_title].append({
                        'start_time': programme_start_format,
                        'end_time': programme_end_format,
                        'title': programme_title,
                        'icon': programme_icon,
                        'description': programme_description
                    })

            # Avanzar al siguiente día
            current_datetime += timedelta(days=1)

        # Ahora generamos un archivo XML para cada canal con toda su programación acumulada
        for channel_title, programmes in channels_data.items():
            print(f"Generando XML para el canal {channel_title}")

            # Crear el objeto XMLTV para este canal
            channel_xmltv = xmltv()
            channel_xmltv.add_channel(channel_title)
            
            for programme in programmes:
                # Añadir cada programa al XMLTV del canal
                channel_xmltv.add_programme(
                    channel_name=channel_title,
                    start_time=programme['start_time'],
                    end_time=programme['end_time'],
                    programe_name=programme['title'],
                    icon=programme['icon'],
                    description=programme['description']
                )

            xmltv_local_path = os.path.join(epgs_path, f'{channel_title}.xml')
            xmltv_repo_path = f'channels/{channel_title}.xml'
            channel_xmltv.write_xmltv(xmltv_local_path)
            print(f'Escrito el xml del canal "{channel_title}"')
            push_to_github(xmltv_local_path, xmltv_repo_path)

    # Definición de la secuencia de ejecución
    flow = scrape_mediaset_schedule() >> merge_all_xml() >> push_all_in_one()

# Para crear el DAG solo tienes que invocar la función `telemadrid_schedule_scraper`
dag_mediaset = mediaset_schedule_scraper()