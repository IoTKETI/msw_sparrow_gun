import serial
import paho.mqtt.client as mqtt
import sys
import threading
from time import sleep
import json

################################
# lib_topic = []
# mqtt param
# global lib_mqtt_client
global lib
global lib_topic
#lib_topic = ['/keti']
broker_ip = 'localhost'
port = 1883

#missionPortNum = '/dev/ttyUSB3'
#missionBaudrate = 9600

global lib_mqtt_client
lib={}
#missionPortNum = lib.serialPortNum
#missionBaudrate = lib.serialBaudrate
lteQ = {}
sleep_sec = 1


def missionPortOpen(missionPortNum, missionBaudrate):
    # Connect serial
    global missionPort
    print('Connect to serial...')
    try:
        missionPort = serial.Serial(missionPortNum, missionBaudrate, timeout=2)
        if missionPort.isOpen():
            print('missionPort Open. ', missionPortNum, 'Data rate: ', missionBaudrate)
            mission_thread = threading.Thread(
                target=missionPortData, args=(missionPort,)
            )
            mission_thread.start()

            return missionPort
    except serial.SerialException as e:
        missionPortError(e)
    except TypeError as e:
        missionPortClose()
        missionPort.close()


def missionPortClose():
    print('missionPort closed!')


def missionPortError(err):
    print('[missionPort error]: ', err)


def lteReqGetRssi(missionPort):
    if missionPort is not None:
        if missionPort.isOpen():
            atcmd = b'AT@DBG\r'
            missionPort.write(atcmd)


def send_data_to_msw (data_topic, obj_data):
    lib_mqtt_client.publish(data_topic, obj_data)


def missionPortData(missionPort):
    while True:
        arrRssi = missionPort.read()
#        send_data_to_msw(data_topic,lteQ)


def msw_mqtt_connect(broker_ip, port):
    lib_mqtt_client = mqtt.Client()
    lib_mqtt_client.on_connect = on_connect
    lib_mqtt_client.on_disconnect = on_disconnect
    lib_mqtt_client.on_subscribe = on_subscribe
    lib_mqtt_client.on_message = on_message
    lib_mqtt_client.connect(broker_ip, port)
    lib_muv_topic = '/MUV/control/'+ lib['name'] + '/MICRO'
    lib_mqtt_client.subscribe(lib_muv_topic, 0)
    print(lib_muv_topic)
#    for idx in lib['topic']:
#        if idx in lib['topic']:
#            idx = lib['topic'].index(idx)
#            lib_mqtt_client.subscribe(str(lib['topic'][idx]))
#    print('[lib_mqtt_connect] lib_topic[' ,'+', idx ,'+' ']: ', lib['topic'][idx]);
    lib_mqtt_client.loop_start()
    # lib_mqtt_client.loop_forever()
    return lib_mqtt_client


def on_connect(client, userdata, flags, rc):
    print('[msg_mqtt_connect] connect to ', broker_ip)


def on_disconnect(client, userdata, flags, rc=0):
    print(str(rc))


def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, msg):
#    for idx in lib['topic']:
#        if idx in lib['topic']:
#            idx = lib['topic'].index(idx)
#            if msg.topic == lib['topic'][idx]:
                payload = msg.payload.decode('utf-8')
                on_receive_from_msw(msg.topic, str(payload))


def on_receive_from_msw(topic, str_message):
    print('[' + topic + '] ' + str_message)
#    str_message = {"con":str_message}
    cinObj = json.loads(str_message)
#    print(cinObj)
    request_to_mission(cinObj)


def request_to_mission(cinObj):
    if missionPort != None:
        if missionPort.isOpen():
            con = cinObj['con']
            con_arr = con.split(',')
            if (int(con_arr[0]) < 8) and (int(con_arr[1]) < 8):
                stx = 'A2'
                command = '030' + con_arr[0] + '0' + con_arr[1] + '000000000000'
                crc = 0
                print(command)
                for i in range(0,len(command),2):
                    crc ^= int(command[i+1],16)
                if crc < 16:
                    command += ('0' + str(crc))
                else :
                    command += str(crc)

                etx = 'A3'
                command = stx + command + etx
                print('command: ', command)
                
                msdata = bytes.fromhex(command)
                print('msdata: ', msdata)
                missionPort.write(msdata)

#lib={}
def main():
    global lib
    argv = sys.argv[1:]  # argv 가져오기
    if argv != None:
        lib = {'name': argv[0], 'serialPortNum': argv[1], 'serialBaudrate': argv[2]}  # argv값 셋팅
        print(lib)
        # sys argv input
        lib_mqtt_client = msw_mqtt_connect(broker_ip, port)
        missionPort = missionPortOpen(lib['serialPortNum'], lib['serialBaudrate'])
#        missionPort = missionPortOpen(missionPortNum, missionBaudrate)
    else :
        print("Input the argv!")

#    lib_mqtt_client = msw_mqtt_connect(broker_ip, port)
#    missionPort = missionPortOpen(missionPortNum, missionBaudrate)
#    print(missionPort)
    
if __name__ == "__main__":
    main()
