from fastapi import FastAPI, HTTPException, Body
import pyodbc
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="API de Control de Temperatura",
    description="API para comunicación con Arduino y registro de datos",
    version="1.0"
)


# Conexión a SQL Server
def get_db_connection():
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={os.getenv('SQL_SERVER')};DATABASE={os.getenv('SQL_DATABASE')};UID={os.getenv('SQL_USERNAME')};PWD={os.getenv('SQL_PASSWORD')}"
    return pyodbc.connect(conn_str)


@app.post("/api/sensor-data")
async def receive_sensor_data(data: dict = Body(...)):
    """
    Recibe datos JSON del sensor DHT11 desde Arduino.
    Ejemplo de entrada:
    {
        "sensor": "DHT11",
        "temperature": 25.5,
        "humidity": 60.0
    }
    """
    try:
        # Validar datos recibidos
        if not all(key in data for key in ["sensor", "temperature", "humidity"]):
            raise HTTPException(status_code=400, detail="Formato JSON incorrecto")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO temperature_log (temperature_value, humidity_value) VALUES (?, ?)",
            (data["temperature"], data["humidity"])
        )
        conn.commit()

        return {
            "status": "success",
            "message": "Datos registrados",
            "received_data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/api/current-config")
async def get_current_config():
    """
    Devuelve la configuración actual en formato JSON para Arduino.
    Ejemplo de respuesta:
    {
        "min_temperature": 40.0,
        "last_update": "2023-05-20T12:00:00"
    }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT TOP 1 min_temperature, set_time 
        FROM temperature_config 
        ORDER BY set_time DESC
        """)
        row = cursor.fetchone()

        if not row:
            return {
                "min_temperature": 40.0,  # Valor por defecto
                "last_update": datetime.now().isoformat()
            }

        return {
            "min_temperature": float(row.min_temperature),
            "last_update": row.set_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/api/update-config")
async def update_config(config: dict = Body(...)):
    """
    Actualiza la configuración desde la interfaz.
    Ejemplo de entrada:
    {
        "min_temperature": 35.5
    }
    """
    try:
        if "min_temperature" not in config:
            raise HTTPException(status_code=400, detail="Se requiere min_temperature")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO temperature_config (min_temperature) VALUES (?)",
            (float(config["min_temperature"]),)
        )
        conn.commit()

        return {
            "status": "success",
            "message": "Configuración actualizada",
            "new_config": {
                "min_temperature": float(config["min_temperature"]),
                "update_time": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/api/latest-data")
async def get_latest_data():
    """
    Obtiene el último registro de sensores para la interfaz.
    Ejemplo de respuesta:
    {
        "sensor_data": {
            "temperature": 25.5,
            "humidity": 60.0,
            "timestamp": "2023-05-20T12:00:00"
        },
        "current_config": {
            "min_temperature": 40.0
        }
    }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener últimos datos del sensor
        cursor.execute("""
        SELECT TOP 1 temperature_value, humidity_value, reading_time 
        FROM temperature_log 
        ORDER BY reading_time DESC
        """)
        sensor_row = cursor.fetchone()

        # Obtener configuración actual
        cursor.execute("""
        SELECT TOP 1 min_temperature 
        FROM temperature_config 
        ORDER BY set_time DESC
        """)
        config_row = cursor.fetchone()

        response = {
            "sensor_data": {
                "temperature": float(sensor_row.temperature_value),
                "humidity": float(sensor_row.humidity_value),
                "timestamp": sensor_row.reading_time.isoformat()
            } if sensor_row else None,
            "current_config": {
                "min_temperature": float(config_row.min_temperature) if config_row else 40.0
            }
        }

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()