import streamlit as st
import boto3
import pandas as pd


# Configurar las credenciales de AWS
s3 = boto3.client(
    "s3",
    aws_access_key_id="AKIA4JPLITO7VQCH5Z4Z",
    aws_secret_access_key="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"
)

bucket_name= 'chile-usa-japon'
file_name= 'combined_earthquake_data.csv'

def download_csv_from_s3(bucket_name, file_name):
    # Descargar el archivo CSV desde S3
    s3.download_file(bucket_name, file_name, file_name)

    # Leer el archivo CSV en un DataFrame de Pandas
    df = pd.read_csv(file_name, encoding='latin-1')

    # Mostrar el DataFrame en Streamlit
    st.write(df)

    # Agregar un enlace para descargar el archivo CSV
    st.download_button(
        label="Descargar CSV",
        data=df.to_csv(index=False),
        file_name=file_name,
        mime="text/csv"
    )

def main():
    st.title("Descargar archivo CSV desde S3")

    # Nombre del bucket de S3 y el archivo CSV
    bucket_name= 'chile-usa-japon'
    file_name= 'combined_earthquake_data.csv'

    # Descargar y mostrar el archivo CSV
    download_csv_from_s3(bucket_name, file_name)

if __name__ == "__main__":
    main()