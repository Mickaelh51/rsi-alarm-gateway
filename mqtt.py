import logging
import paho.mqtt.client as mqtt



def mqtt_start_server(cfg):
  logging.info("Trying MQTT connection to %s:%s" % (cfg["mqtt_host"], cfg["mqtt_port"]))
  client = mqtt.Client()
  try:
    if cfg["mqtt_user"] and cfg["mqtt_pwd"]:
      logging.info("Connection with User and Password")
      client.username_pw_set(cfg["mqtt_user"], cfg["mqtt_pwd"])
  except:
    logging.info("No User and Password configured")
    
  client.connect(cfg["mqtt_host"], cfg["mqtt_port"])
  client.loop_start()
  logging.info("Connected to MQTT broker")
  return client


def mqtt_ha_config(client, cfg):
  for k, v in cfg["home_assistant_sensors"].items():
    logging.info("Send configuration to MQTT broker for %s" % k)
    if(v["device_class"] == "None"):
      config_data = ('{"name": "%s", "state_topic": "%s/%s/%s/state"}' % (k, cfg["mqtt_prefix"], v["sensor_type"], k) )
    else:
      config_data = ('{"name": "%s", "device_class": "%s", "state_topic": "%s/%s/%s/state"}' % (k, v["device_class"], cfg["mqtt_prefix"], v["sensor_type"], k) )
    config_topic = ('%s/%s/%s/config' % (cfg["mqtt_prefix"], v["sensor_type"], k))
    client.publish(config_topic, config_data, 0, True)
    logging.info("Send default state (%s) to MQTT broker for %s" % (v["default_state"], k))
    default_state = ("%s/%s/%s/state" % (cfg["mqtt_prefix"], v["sensor_type"], k))
    client.publish(default_state, v["default_state"], 0, True)

