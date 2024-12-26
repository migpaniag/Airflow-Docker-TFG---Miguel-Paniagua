import os
import xml.etree.ElementTree as ET
import sys
sys.path.append('/opt/airflow/dags/utils')
from push_to_github import push_to_github
from airflow.decorators import task, dag

@task()
def push_all_in_one():
    output_path = '/opt/airflow/dags/all_in_one/all_in_one.xml'
    push_to_github(output_path,'all_in_one/all_in_one.xml')