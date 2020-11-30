#!/usr/bin/python3
import serial, sys, json, os, signal, psutil
import paho.mqtt.client as mqtt
from time import sleep
import threading

################################
argv = sys.argv

broker_ip = 'localhost'
port = 1883

gun_event = 0x00

CONTROL_E = 0x01
DATA_E = 0x02

def missionPortOpening(missionPortNum, missionBaudrate):
    global missionPort

    print('Connect to serial...')
    try:
        missionPort = serial.Serial(missionPortNum, missionBaudrate, timeout=2)
        if missionPort.isOpen():
            print('missionPort Open. ', missionPortNum, 'Data rate: ', missionBaudrate)
#             mission_thread = threading.Thread(
#                 target=missionPortData
#             )
#             mission_thread.start()

    except serial.SerialException as e:
        missionPortError(e)
    except TypeError as e:
        missionPortClose()


def missionPortOpen():
    global missionPort
    global status
    status = 'open'
    send_data_to_msw(status)

    print('missionPort open!')
    missionPort.open()


def missionPortClose():
    global missionPort
    global status
    status = 'close'
    send_data_to_msw(status)

    print('missionPort closed!')
    missionPort.close()


def missionPortError(err):
    print('[missionPort error]: ', err)
    global status
    status = 'error'
    send_data_to_msw(status)

    os.kill(i_pid, signal.SIGKILL)


def send_data_to_msw (obj_data):
    global lib_mqtt_client
    global data_topic
    data_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0]
    lib_mqtt_client.publish(data_topic, obj_data)


def missionPortData():
    global status
    global req

    if req == "1":
#     while True:
        status = 'alive'
        send_data_to_msw(status)
    #     sleep(1)

def msw_mqtt_connect(broker_ip, port):
    global lib
    global lib_mqtt_client
    global control_topic
    global data_topic
    global req_topic

    lib_mqtt_client = mqtt.Client()
    lib_mqtt_client.on_connect = on_connect
    lib_mqtt_client.on_disconnect = on_disconnect
    lib_mqtt_client.on_subscribe = on_subscribe
    lib_mqtt_client.on_message = on_message
    lib_mqtt_client.connect(broker_ip, port)
    control_topic = '/MUV/control/' + lib["name"] + '/' + lib["control"][0]
    lib_mqtt_client.subscribe(control_topic, 0)
    lib_mqtt_client.subscribe(req_topic, 0)

    lib_mqtt_client.loop_start()
    return lib_mqtt_client


def on_connect(client, userdata, flags, rc):
    print('[msg_mqtt_connect] connect to ', broker_ip)


def on_disconnect(client, userdata, flags, rc=0):
    print(str(rc))


def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, msg):
    cmd = msg.payload.decode('utf-8')
    print('on_message: ', cmd)
    request_to_mission(cmd)
    global gun_event
    global data_topic
    global control_topic
    global req_topic
    global con
    global req

    print(msg.topic)

    if msg.topic == control_topic:
        print('control')
        con = msg.payload.decode('utf-8')
        gun_event |= CONTROL_E
    elif msg.topic == req_topic:
        print('req status')
        req = msg.payload.decode('utf-8')
        gun_event |= DATA_E



def request_to_mission(con):
    global missionPort

    try:
        if missionPort != None:
            if missionPort.isOpen():
                con_arr = con.split(',')
                print(con_arr)
                if (int(con_arr[0]) < 8) and (int(con_arr[1]) < 8):
                    stx = 'A2'
                    command = '030' + con_arr[0] + '0' + con_arr[1] + '000000000000'
                    crc = 0
                    print(command)
                    for i in range(0,len(command),2):
                        print('crc: ', crc)
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

    except (ValueError, IndexError, TypeError):
        print ('except Error')
        pass

def main():
    global lib
    global lib_mqtt_client
    global missionPort
    global control_topic
    global data_topic
    global req_topic

    global gun_event
    global con
    global req

    my_lib_name = 'lib_sparrow_gun'
    my_msw_name = 'msw'+ my_lib_name[3:] + '_' + 'msw'+ my_lib_name[3:]

#     cmd = ['python3', './' + my_msw_name + '/' + my_lib_name + '.py', argv[1], argv[2]]
    cmd = ['./' + my_msw_name + '/' + my_lib_name, argv[1], argv[2]]
    pid_arr = []
    processWatch = [p.cmdline() for p in psutil.process_iter()].count(cmd)
    if processWatch > 2:
        for p in psutil.process_iter():
            if (p.cmdline() == cmd):
                print(p.pid)
                pid_arr.append(p.pid)
        os.kill(pid_arr[0], signal.SIGKILL)
        os.kill(pid_arr[0]+1, signal.SIGKILL)

    try:
        lib = dict()
        with open(my_lib_name + '.json', 'r') as f:
            lib = json.load(f)
            lib = json.loads(lib)

    except:
        lib = dict()
        lib["name"] = my_lib_name
        lib["target"] = 'armv6'
        lib["description"] = "[name] [portnum] [baudrate]"
        lib["scripts"] = './' + my_lib_name + ' /dev/ttyUSB3 9600'
        lib["data"] = ['GUN']
        lib["control"] = ['MICRO']
        lib = json.dumps(lib, indent=4)
        lib = json.loads(lib)

        with open('./' + my_lib_name + '.json', 'w', encoding='utf-8') as json_file:
            json.dump(lib, json_file, indent=4)


    lib['serialPortNum'] = argv[1]
    lib['serialBaudrate'] = argv[2]
    
    control_topic = '/MUV/control/' + lib["name"] + '/' + lib["control"][0]
    data_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0]
    req_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0] + 'req'

    msw_mqtt_connect(broker_ip, port)
    missionPortOpening(lib['serialPortNum'], lib['serialBaudrate'])

    while True:
        if gun_event & CONTROL_E:
            gun_event &= (~CONTROL_E)
            request_to_mission(con)
        elif gun_event & DATA_E:
            gun_event &= (~DATA_E)
            print('req status 2')
            missionPortData()


if __name__ == "__main__":
    main()
