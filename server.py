# coding: utf-8

from socket import socket, AF_INET, SOCK_STREAM, timeout, SOL_SOCKET, SO_REUSEADDR
import logging
import sys
import traceback
import time
import threading
import atexit
import os

from utils import generate_preshared_key, delete_x1a, client_auth, read_config, find_event_type
from mqtt import mqtt_start_server, mqtt_ha_config


# Get env var
try:  
   os.environ["LOGLEVEL"]
except KeyError: 
   print("Please set the environment variable LOGLEVEL")
   sys.exit(1)

log = logging.getLogger()
out_hdlr = logging.StreamHandler()
out_hdlr.setFormatter(logging.Formatter('[%(asctime)s] - %(module)s - %(levelname)s - %(message)s'))
out_hdlr.setLevel(logging.os.environ["LOGLEVEL"])
log.addHandler(out_hdlr)
log.setLevel(logging.os.environ["LOGLEVEL"])

def main():
  try:
    cfg = read_config("config.json")
    start_alarm_server(cfg)
  except KeyError: 
   print("Please add config.json")
   sys.exit(1)
  
def start_alarm_server(cfg):
    host = cfg["socket_bind"]
    port = cfg["socket_listen_port"]

    soc = socket(AF_INET, SOCK_STREAM)
    soc.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)   # SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state, without waiting for its natural timeout to expire
    logging.info("Socket created")

    #start socket bind
    try:
      soc.bind((host, port))
    except:
      logging.error(str(sys.exc_info()))
      sys.exit()

    # mqtt connection
    try:
      mqtt_client = mqtt_start_server(cfg)
      # If we want to connect to HA with default values
      if (cfg["home_assistant_integration"]):
        mqtt_ha_config(mqtt_client, cfg)
    except:
      raise
      logging.error(str(sys.exc_info()))
      sys.exit()

    soc.listen(5)       # queue up to 5 requests
    logging.info("Socket now listening")

    # infinite loop- do not reset for every requests
    while True:
      connection, address = soc.accept()

      ip, port = str(address[0]), str(address[1])
      logging.info("### Connected with %s:%s ###" % (ip, port))

      try:
        e = threading.Event()
        t = threading.Thread(target=client_thread, args=(connection, ip, port, mqtt_client, cfg))
        t.setDaemon = True
        t.start()
      except:
        logging.error("Thread did not start.")
        traceback.print_exc()
    soc.close()

def client_thread(connection, ip, port, mqtt_client, cfg, max_buffer_size = 5120):
    logging.info("Start new thread: %s" % threading.get_ident())
    logging.info("Number of threads: %s" % threading.active_count())
    is_active = True
    is_authenticated = False

    connection.settimeout(cfg["socket_timeout"])

    while is_active:
      # force AUTH
      if(is_authenticated == False):
        if (client_auth(connection)):
          is_authenticated = True
        else:
          logging.info("Authentication failed")
          connection.close()
          logging.info("### Connection %s:%s closed ###" % (ip, port))
          is_active = False
          break

      try:
        received = connection.recv(max_buffer_size)
      except:
        logging.info("No data from client")
        connection.close()
        logging.info("### Connection %s:%s closed ###" % (ip, port))
        is_active = False
        break
      
      if (received):
        logging.debug(str(received))

      if("EVENT" in str(received)):
        logging.info("We received EVENT: %s" % delete_x1a(received.decode()))
        event = delete_x1a(received.decode())
        event_data = find_event_type(event, cfg)
        if not event_data:
          continue
        try:
          topic = ("%s/%s/%s/state" % (cfg["mqtt_prefix"], cfg["home_assistant_sensors"][event_data["type"]]["sensor_type"], event_data["type"]))
        except:
          logging.error("We can send MQTT data")
          traceback.print_exc()
          continue
        if(mqtt_client.publish(topic, event_data["state"], 0)):
          if(event_data["type"] + "_source" in cfg["home_assistant_sensors"].keys() and event_data["source_event"] and event_data["source_event"] != "None"):
            topic_source = ("%s/%s/%s/state" % (cfg["mqtt_prefix"], cfg["home_assistant_sensors"][event_data["type"] + "_source"]["sensor_type"], event_data["type"] + "_source"))
            mqtt_client.publish(topic_source, event_data["source_event"], 0)
          logging.info("Received update from alarm (%s) update MQTT / source of event (%s) / zone of event (%s)" % (event_data["comment"], event_data["source_event"], event_data["zone_event"]))
        continue

      if('FILE' in str(received)):
        logging.info("We received FILE")
        received = connection.recv(max_buffer_size)
        if('FileVersion' in str(received)):
          logging.debug(str(received))
          logging.info("We received json file, send ACK")
          msg = 'FILE_ACK\x1a'
          connection.send(msg.encode())
        continue

      if('REQACK' in str(received)):
        logging.info("We received REQACK, send simple ACK")
        msg = 'ACK\x1a'
        connection.send(msg.encode())
        continue


if __name__ == "__main__":
    main()