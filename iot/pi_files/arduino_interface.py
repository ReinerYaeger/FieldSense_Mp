# Code for the Raspberry pi
import asyncio
import pickle
import random
from time import sleep
import serial
import traceback
from datetime import datetime
import logging
import socket
import threading

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', filename='mp_wn.log', encoding='utf-8',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_serial_data(sleep_sec=0):
    try:
        ser = serial.Serial('COM7', 9600, timeout=1)
        ser.flushInput()
        analog_dict = {
            'A0': {'soil_moisture_data': [], 'timestamp': []},
            'A1': {'soil_moisture_data': [], 'timestamp': []},
            'A2': {'soil_moisture_data': [], 'timestamp': []},
        }

        while True:
            ser_bytes = ser.readline()
            decoded_string = ser_bytes.decode("utf-8").strip()

            if decoded_string and decoded_string != "":
                output_list = decoded_string.split("\t")
                for data_point in output_list:
                    for prefix in ['A0:', 'A1:', 'A2:', ]:
                        if prefix in data_point:
                            data_value = data_point.split(":")[1].strip()
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            data_dict = {
                                'soil_moisture_data': data_value,
                                'timestamp': timestamp
                            }
                            if data_value:
                                analog_dict[prefix[:-1]] = data_dict

            #process_data(analog_dict)
            print(analog_dict)
            logging.info(analog_dict)

            sleep(sleep_sec)

    except KeyboardInterrupt as e:
        logging.error(f"Keyboard Interrupt {e}")
        logging.error(traceback.print_exc())

    except serial.SerialTimeoutException as e:
        logging.error(f"Serial Timeout Exception: {e}")
        logging.error(traceback.print_exc())

    except serial.SerialException as e:
        logging.error(f"SerialException caught: {e}")
        logging.error(traceback.print_exc())

    except PermissionError as pe:
        logging.critical(f"Permission Error: {pe}")
        logging.error(traceback.print_exc())

    except TypeError as e:
        logging.error(f"Possible Sensor Disconnection\tType Error {e}")
        logging.error(traceback.print_exc())

    except Exception as ex:
        logging.error(f"An unexpected error occurred: {ex}")
        logging.error(traceback.print_exc())
    finally:
        fallback()


def fallback():
    analog_dict = {
        'A0': {'soil_moisture_data': [], 'timestamp': []},
        'A1': {'soil_moisture_data': [], 'timestamp': []},
        'A2': {'soil_moisture_data': [], 'timestamp': []},
    }

    while True:

        A0_value = random.uniform(1, 0.202020)
        A1_value = random.uniform(1, 0.202020)
        A2_value = random.uniform(1, 0.202020)

        A0_value

        decoded_string = f"A0:{A0_value:.5f}\tA1:{A1_value:.5f}\tA2:{A2_value:.5f}"
        output_list = decoded_string.split("\t")

        for data_point in output_list:
            for prefix in ['A0:', 'A1:', 'A2:', ]:
                timestamp = None
                if prefix in data_point:
                    data_value = data_point.split(":")[1].strip()
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    data_dict = {
                        'soil_moisture_data': data_value,
                        'timestamp': timestamp
                    }
                    if data_value:
                        analog_dict[prefix[:-1]] = data_dict

        process_data(analog_dict)
        print(analog_dict)
        logging.info(analog_dict)


def process_data(analog_dict):
    try:
        encoded_data = pickle.dumps(analog_dict)

        asyncio.run(send_data_async(encoded_data))
        logging.info(f"Data contents {analog_dict} ")
    except Exception as e:
        logging.error(e)


def send_data(data):
    host = "192.168.0.5"
    port = 1234

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(data)
    except socket.error as e:
        logger.error(f"Socket Error: {e}")
    return


async def send_data_async(data):
    reader, writer = await asyncio.open_connection(
        '192.168.0.5', 1234)

    writer.write(data)
    await writer.drain()
    logging.info(f"Data Sent {data}")
    writer.close()
    await writer.wait_closed()


def main():
    get_serial_data()


if __name__ == '__main__':
    main()
