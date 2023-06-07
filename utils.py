import logging
from Crypto.Cipher import AES
from Crypto import Random
import codecs
import json
import traceback

decode_hex = codecs.getdecoder("hex_codec")


def generate_preshared_key (serial):
  return serial[4] + '0' + serial[15] + serial[11] + '0' + serial[5] + serial[13] + serial[6] + serial[8] + serial[12] + serial[7] + serial[14] + '1' + '0' \
    + serial[10] + serial[9] + serial[7] + serial[10] + serial [4] + serial[15] + serial[13] + serial[6] + serial[12] + '0' + serial[8] + '0' + serial[14] + \
    '1' + serial[11] + serial[11] + '0' + serial[5]

def delete_x1a (string):
  if '\x1a' in string[-1]:
    return string[:-1]


def client_auth(conn):
  if(conn.send(b"IDENT,1000\x1a")):
    serial = conn.recv(1024)
    if serial: # b'IDENT,E760491513080214,2\x1a'
      serial = serial.decode().split(',')[1]
      logging.info("serial: %s" % serial)
      key = generate_preshared_key(serial)
      logging.info("key: %s" % key)

      if (serial and key): 
        logging.info("Setting preshared key")
        # panels may require the key to be set
        msg = 'SETKEY,' + key + '\x1a'
        if(conn.send(msg.encode())):
          if(conn.send(b"VERSION,2,0\x1a")):
            #generate Random server challenge
              challenge = Random.new().read(16).hex().upper()
              logging.info("Generate new challenge: %s" % challenge)
              msg = 'AUTH1,' + challenge + '\x1a'
              if(conn.send(msg.encode())):
                cipher = AES.new(decode_hex(key)[0])
                challenge_and_key = conn.recv(1024) # b'AUTH2,E228231BBC986CA9016700499E1C8AE7,B08AE8A308821AC6292811545A15BF59\x1a'
                alarm_challenge = challenge_and_key.decode().split(',')[2]
                alarm_challenge = delete_x1a(alarm_challenge)
                response = cipher.encrypt(decode_hex(alarm_challenge)[0]).hex().upper()
                logging.info("Key response to alarm: %s" % response )
                msg = 'AUTH3,' + response + "\x1a"
                if(conn.send(msg.encode())):
                  answer = conn.recv(1024)
                  logging.info("Answer: %s" % answer.decode())
                  if('AUTH_SUCCESS' in answer.decode()):
                    logging.info("Logging successful !!")
                    return True
  return False

def read_config(config):
  with open(config, 'r') as file:
    return json.load(file)

def find_event_type(event, cfg):
  try:
    event_array = event.split(',')
    # EVENT,3,62,0
    # 3 = mapping_events key
    # 62 = source of event
    # 0 = ??
    # find data of this type of event in json conf file with key (event_array[1])
    event_type = cfg["mapping_events"][event_array[1]]
    source_of_event = None
    zone_of_event = None
    try:
      if("device_index" in event_type.keys()):
        source_of_event = cfg["device_index"][event_array[2]].get("name")
        if("zone" in cfg["device_index"][event_array[2]].keys()):
          zone_id = cfg["device_index"][event_array[2]].get("zone")
          zone_of_event = cfg["zones"][str(zone_id)].get("name")
      elif("mapping_users" in event_type.keys()):
        source_of_event = cfg["mapping_users"][event_array[3]]
      # Ex: {'type': 'alarm_autoprotection', 'state': 'on', 'comment': 'autoprotection alert', 'name': 'Panel'}
    except:
      logging.error("unable to find source of event (%s)" % event)
      traceback.print_exc()
    # Ex: {'type': 'alarm_autoprotection', 'state': 'off', 'comment': 'autoprotection recovery'}
    event_type["source_event"] = source_of_event
    event_type["zone_event"] = zone_of_event
    return event_type
  except:
    logging.error("unable to find event type (%s)" % event)
    traceback.print_exc()
    return None
