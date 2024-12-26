import os
import xml.etree.ElementTree as ET
from airflow.decorators import task, dag

@task()
def merge_all_xml():
    input_files_path = '/opt/airflow/dags/epgs'
    output_path = '/opt/airflow/dags/all_in_one/all_in_one.xml'
    # Crear el elemento raíz <tv>
    tv_element = ET.Element("tv")

    # Listas para almacenar los canales y programas
    channels = []
    programmes = []

    # Iterar sobre los archivos XML en la ruta proporcionada
    for file in os.listdir(input_files_path):
        if file.endswith(".xml"):
            file_path = os.path.join(input_files_path, file)
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Extraer los canales
            for channel in root.findall('channel'):
                channels.append(channel)

            # Extraer los programas
            for programme in root.findall('programme'):
                programmes.append(programme)

    # Crear el nuevo XML con los canales y programas
    # Primero añadimos todos los canales
    for channel in channels:
        tv_element.append(channel)

    # Luego añadimos todos los programas
    for programme in programmes:
        tv_element.append(programme)

    # Crear el nuevo árbol XML y escribirlo en un archivo
    new_tree = ET.ElementTree(tv_element)
    new_tree.write(output_path, encoding="UTF-8", xml_declaration=True)
    print('[INFO] Generado el archivo "all_in_one.xml"')