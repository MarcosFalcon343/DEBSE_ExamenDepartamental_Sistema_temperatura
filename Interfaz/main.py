import sys
import serial
import serial.tools.list_ports
import threading
import time
import requests
import json
from PyQt5 import uic, QtWidgets, QtCore

qtCreatorFile = "ui.ui"  # Tu archivo .ui
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class SerialThread(QtCore.QThread):
    def __init__(self, serial_port, parent=None):
        super().__init__(parent)
        self.serial_port = serial_port
        self.running = True

    def run(self):
        while self.running:
            if self.serial_port.in_waiting:
                try:
                    line = self.serial_port.readline().decode().strip()
                    data = json.loads(line)

                    # Enviar a la API
                    requests.post("http://localhost:8000/api/sensor-data", json=data)

                    # Obtener temperatura mínima
                    response = requests.get("http://localhost:8000/api/current-config")
                    config = response.json()
                    min_temp = config.get("min_temperature", 40.0)

                    # Enviar al Arduino
                    self.serial_port.write(
                        (json.dumps({"min_temperature": min_temp}) + "\n").encode()
                    )
                except Exception as e:
                    print("Error en hilo serial:", e)
            time.sleep(1)

    def stop(self):
        self.running = False


class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.serial_port = None
        self.serial_thread = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.actualizar_valores_ui)

        self.Btn_Buscar.clicked.connect(self.buscar_puertos)
        self.Btn_Conectar.clicked.connect(self.conectar_puerto)
        self.Btn_Enviar.clicked.connect(self.enviar_temperatura)

        # Al inicio, desactivar funciones dependientes de la conexión
        self.Btn_Enviar.setEnabled(False)
        self.DSB_TemperaturaMinima.setEnabled(False)

    def buscar_puertos(self):
        self.CB_PuertoCOM.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.CB_PuertoCOM.addItem(port.device)

    def conectar_puerto(self):
        port_name = self.CB_PuertoCOM.currentText()
        if port_name:
            try:
                self.serial_port = serial.Serial(port_name, 9600, timeout=1)
                time.sleep(2)  # Esperar que se estabilice la conexión

                # Iniciar hilo de lectura serial
                self.serial_thread = SerialThread(self.serial_port)
                self.serial_thread.start()

                # Iniciar timer de consulta a FastAPI cada 5 segundos
                self.timer.start(5000)

                # Activar controles dependientes de la conexión
                self.Btn_Enviar.setEnabled(True)
                self.DSB_TemperaturaMinima.setEnabled(True)

                QtWidgets.QMessageBox.information(self, "Conectado", f"Conectado a {port_name}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo conectar:\n{e}")

    def actualizar_valores_ui(self):
        try:
            response = requests.get("http://localhost:8000/api/latest-data")
            if response.status_code == 200:
                data = response.json()
                if data["sensor_data"]:
                    self.LE_Temperatura.setText(str(data["sensor_data"]["temperature"]))
                    self.LE_Humedad.setText(str(data["sensor_data"]["humidity"]))
        except Exception as e:
            print("Error al consultar datos:", e)

    def enviar_temperatura(self):
        if self.serial_port and self.serial_port.is_open:
            nueva_temp = self.DSB_TemperaturaMinima.value()
            try:
                response = requests.post(
                    "http://localhost:8000/api/update-config",
                    json={"min_temperature": nueva_temp},
                )
                if response.status_code == 200:
                    QtWidgets.QMessageBox.information(self, "Éxito", "Configuración actualizada")
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "No se pudo actualizar la configuración")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, event):
        # Detener el hilo si se cierra la ventana
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
