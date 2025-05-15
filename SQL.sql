-- Verificar y crear la base de datos si no existe
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'DBSE_Examen_Departamental')
BEGIN
    CREATE DATABASE DBSE_Examen_Departamental;
    PRINT 'Base de datos creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'La base de datos ya existe.';
END
GO
USE DBSE_Examen_Departamental;
GO
-- Tabla para registro de temperatura
CREATE TABLE temperature_log (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    temperature_value DECIMAL(5,2) NOT NULL,
    humidity_value DECIMAL(5,2) NOT NULL,
    reading_time DATETIME DEFAULT GETDATE()
);

-- Tabla para configuración de temperatura mínima
CREATE TABLE temperature_config (
    config_id INT IDENTITY(1,1) PRIMARY KEY,
    min_temperature DECIMAL(5,2) NOT NULL,
    set_time DATETIME DEFAULT GETDATE()
);

-- Insertar valor inicial
INSERT INTO temperature_config (min_temperature) VALUES (40.0);