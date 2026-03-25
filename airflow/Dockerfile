FROM apache/airflow:2.11.2-python3.11

USER airflow

RUN pip install --no-cache-dir \
    google-cloud-storage==2.18.2 \
    google-cloud-bigquery==3.25.0 \
    pandas==2.2.3 \
    pyarrow==17.0.0
