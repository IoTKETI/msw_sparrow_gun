#!/usr/bin/python3
import serial, sys, json, os, signal, psutil
import paho.mqtt.client as mqtt
from time import sleep

################################
i_pid = os.getpid()
argv = sys.argv

broker_ip = 'localhost'
port = 1883

def missionPortOpening(missionPortNum, missionBaudrate):
    global missionPort

    print('Connect to serial...')
    try:
        missionPort = serial.Serial(missionPortNum, missionBaudrate, timeout=2)
        if missionPort.isOpen():
            print('missionPort Open. ', missionPortNum, 'Data rate: ', missionBaudrate)

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
    data_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0]
    lib_mqtt_client.publish(data_topic, obj_data)


def missionPortData():
    global status
    status = 'alive'
    send_data_to_msw(status)
    sleep(1)

def msw_mqtt_connect(broker_ip, port):
    global lib
    global lib_mqtt_client

    lib_mqtt_client = mqtt.Client()
    lib_mqtt_client.on_connect = on_connect
    lib_mqtt_client.on_disconnect = on_disconnect
    lib_mqtt_client.on_subscribe = on_subscribe
    lib_mqtt_client.on_message = on_message
    lib_mqtt_client.connect(broker_ip, port)
    control_topic = '/MUV/control/' + lib["name"] + '/' + lib["control"][0]
    lib_mqtt_client.subscribe(control_topic, 0)

    lib_mqtt_client.loop_start()
    return lib_mqtt_client


def on_connect(client, userdata, flags, rc):
    print('[msg_mqtt_connect] connect to ', broker_ip)


def on_disconnect(client, userdata, flags, rc=0):
    print(str(rc))


def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    request_to_mission(payload)


def request_to_mission(con):
    try:
        if missionPort != None:
            if missionPort.isOpen():
                con_arr = con.split(',')
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
        pass

def main():
    global lib
    global missionPort

    my_lib_name = 'lib_sparrow_gun'
    my_msw_name = 'msw'+ my_lib_name[3:] + '_' + 'msw'+ my_lib_name[3:]
    for p in psutil.process_iter():
        if (p.cmdline() == ['python3', './' + my_msw_name + '/' + my_lib_name + '.py', argv[1], argv[2]]):
            print(p.pid)
            os.kill(p.pid, signal.SIGKILL)
#     processWatch = [p.cmdline() for p in psutil.process_iter()].count(['./' + my_msw_name + '/' + my_lib_name, argv[1], argv[2]])

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
    
    
    lib_mqtt_client = msw_mqtt_connect(broker_ip, port)
    missionPort = missionPortOpening(lib['serialPortNum'], lib['serialBaudrate'])

    while True:
        missionPortData()


if __name__ == "__main__":
    main()
