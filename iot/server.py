import socket
import pickle
import logging
import asyncio
from time import sleep

import psycopg2

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', filename='mp_wn_server.log',
                    encoding='utf-8',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


def connect_to_db():
    conn = psycopg2.connect(
        database="gisdb",
        host="localhost",
        user="django",
        password="root",
        port="5432"
    )
    conn.autocommit = True
    return conn


db_cursor = connect_to_db().cursor()


async def data_handler(reader, writer):
    data = await reader.read(4096)

    rec_data = pickle.loads(data)
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr} Data :{rec_data}")

    writer.close()
    await writer.wait_closed()

    upload_data(rec_data)


async def server_async():
    server = await asyncio.start_server(
        data_handler, '0.0.0.0', 1234)

    addr = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


def server():
    HOST = '0.0.0.0'
    PORT = 1234

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            logging.debug(f"Server listening on port {PORT}...")

            while True:
                conn, addr = s.accept()
                print(f"Connected by {addr}")
                data = conn.recv(4096)
                rec_data = pickle.loads(data)
                print(f"Data by {rec_data}")
                upload_data(rec_data)

    except socket.error as e:
        logging.error(f"{e}")
    except Exception as e:
        logging.critical(f"{e}")


def upload_data(data):
    global db_cursor
    for item in data:
        sensor_name = str(item)
        sensor_data = data[f'{sensor_name}']['soil_moisture_data']
        sensor_date_time = data[f'{sensor_name}']['timestamp']

        print(f"Processing sensor: {sensor_name}")
        print(f"Sensor data: {sensor_data}")
        print(f"Sensor date/time: {sensor_date_time}")

        try:
            db_cursor.execute("""INSERT INTO public.sensor_collected_data(sensor_name, sensor_data, sensor_date_time, sensor_group_name_id)
                    VALUES(%s, %s, %s, %s);""",
                              (sensor_name, sensor_data , sensor_date_time, 'University of Technology'))
            print("\nData Inserted")

        except psycopg2.Error as e:
            print(f"Error: {e}")
            db_cursor.rollback()
        except Exception as e:
            print(f"Error {e}")


def main():
    asyncio.run(server_async())
    # server()


if __name__ == '__main__':
    main()
