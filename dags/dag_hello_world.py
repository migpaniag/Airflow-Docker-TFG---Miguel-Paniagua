import pendulum
from airflow.models.dag import DAG
from airflow.operators.empty import EmptyOperator
from airflow.decorators import task, dag
from airflow.operators.python_operator import PythonOperator

with DAG(
    dag_id="example",
    schedule_interval='12 18 * * *',  # Se ejecuta todos los días a las 17:30 hora local
    start_date=pendulum.datetime(2024, 12, 6, 17, 20, tz="Europe/Madrid"),  # Hora actual como start_date
    catchup=False,  # No intentar recuperar ejecuciones pasadas
    tags=["example3"],
) as dag:

    def print_hello():
        print(pendulum.now('Europe/Madrid'))

    task1 = EmptyOperator(task_id="task1")
    task2 = EmptyOperator(task_id="task2")
    python_task = PythonOperator(
        task_id='my_python_task',
        python_callable=print_hello,
        op_kwargs={'key': 'value'}
    )
    task1 >> task2 >> python_task 
