import threading
import queue
import logging
from dynamixel_sdk import PortHandler

class PortHandlerQueue:
    def __init__(self, device_name, baud_rate):
        """
        Initialisiert den PortHandler mit einer Warteschlange für Anfragen.
        :param device_name: Gerätename des Ports (z.B. '/dev/ttyUSB0')
        :param baud_rate: Baudrate des Ports
        """
        self.device_name = device_name
        self.baud_rate = baud_rate
        self.port_handler = PortHandler(device_name)
        self.lock = threading.Lock()
        self.request_queue = queue.Queue()
        self.running = True

        # Initialisiere den Port
        if not self.port_handler.openPort():
            raise RuntimeError(f"Port {device_name} konnte nicht geöffnet werden.")
        if not self.port_handler.setBaudRate(baud_rate):
            raise RuntimeError(f"Baudrate {baud_rate} konnte nicht gesetzt werden.")

        logging.info(f"Port {device_name} mit Baudrate {baud_rate} geöffnet.")

        # Starte den Thread für die Warteschlange
        self.thread = threading.Thread(target=self._process_requests, daemon=True)
        self.thread.start()

    def _process_requests(self):
        """
        Verarbeitet Anfragen aus der Warteschlange sequenziell.
        """
        while self.running:
            try:
                func, args, kwargs, result_queue = self.request_queue.get(timeout=0.1)
                with self.lock:
                    try:
                        result = func(*args, **kwargs)
                        result_queue.put((True, result))
                    except Exception as e:
                        result_queue.put((False, e))
                self.request_queue.task_done()
            except queue.Empty:
                continue

    def add_request(self, func, *args, **kwargs):
        """
        Fügt eine Anfrage zur Warteschlange hinzu und wartet auf das Ergebnis.
        :param func: Funktion, die aufgerufen werden soll
        :param args: Argumente für die Funktion
        :param kwargs: Keyword-Argumente für die Funktion
        :return: Ergebnis der Funktion
        """
        result_queue = queue.Queue()
        self.request_queue.put((func, args, kwargs, result_queue))
        success, result = result_queue.get()
        if success:
            return result
        else:
            raise result

    def close(self):
        """
        Schließt den Port und stoppt den Warteschlangen-Thread.
        """
        self.running = False
        self.thread.join()
        with self.lock:
            if self.port_handler.is_using:
                self.port_handler.closePort()
                logging.info("Port wurde geschlossen.")

# Beispiel zur Nutzung des PortHandlerQueue
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        port_handler_queue = PortHandlerQueue('/dev/ttyUSB0', 57600)

        # Beispielanfrage: Prüfen, ob der Port geöffnet ist
        def is_port_open():
            return port_handler_queue.port_handler.is_using

        result = port_handler_queue.add_request(is_port_open)
        logging.info(f"Port geöffnet: {result}")

    finally:
        port_handler_queue.close()
