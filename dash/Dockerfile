FROM python:3.10

# Crear usuario que ejecuta la app
RUN adduser --disabled-password --gecos '' dash-user

# Definir directorio de trabajo 
WORKDIR /opt/dash/tablero

# Instalar dependencias
ADD ./tablero /opt/dash/tablero


RUN pip install --upgrade pip
RUN pip install -r /opt/dash/tablero/requirements.txt

# Hacer el directorio de trabajo ejecutable 
RUN chmod +x /opt/dash/tablero/run.sh

# Cambiar propiedad de la carpeta a dash-user 
RUN chown -R dash-user:dash-user /opt/dash

USER dash-user
# Puerto a exponer para la api 
EXPOSE 8050

# Comandos a ejecutar al correr el contenedor 
CMD ["bash", "./run.sh"]
