FROM apache/airflow:2.10.3

# RUN apt-get update && \
#     apt-get install -y locales && \
#     sed -i -e 's/# es_ES.UTF-8 UTF-8/es_ES.UTF-8 UTF-8/' /etc/locale.gen && \
#     dpkg-reconfigure --frontend=noninteractive locales

# ENV LANG ru_RU.UTF-8
# ENV LC_ALL ru_RU.UTF-8
# # Establecer el usuario para todas las operaciones posteriores
# USER airflow
# # Instalar locales y configurarlos
# RUN apt-get update && \
#     apt-get install -y locales && \
#     sed -i -e 's/# es_ES.UTF-8 UTF-8/es_ES.UTF-8 UTF-8/' /etc/locale.gen && \
#     dpkg-reconfigure --frontend=noninteractive locales && \
#     update-locale LANG=es_ES.UTF-8 LC_ALL=es_ES.UTF-8

# # Copiar el script de inicio al contenedor
# COPY start_airflow.sh /usr/local/bin/start_airflow.sh

# # Darle permisos de ejecución
# RUN chmod +x /usr/local/bin/start_airflow.sh

# # Usar el script de inicio como ENTRYPOINT
# ENTRYPOINT ["start_airflow.sh"]

# # Configuración de la zona horaria
# ENV TZ="CET"

# # Entrypoint predeterminado de Airflow (en caso de que no uses "start_airflow.sh")
# CMD ["bash", "-c", "airflow webserver"]