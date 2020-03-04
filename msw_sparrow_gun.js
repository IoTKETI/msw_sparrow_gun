/**
 * Created by Il Yeup, Ahn in KETI on 2019-11-30.
 */

/**
 * Copyright (c) 2019, OCEAN
 * All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

// for TAS of mission


var mqtt = require('mqtt');
var fs = require('fs');
var spawn = require('child_process').spawn;

var fc = {};

var config = {};
try {
    config = JSON.parse(fs.readFileSync('config.json', 'utf8'));
}
catch (e) {
    config.name = 'msw_sparrow_GUN';
    config.gcs = 'KETI_MUV';
    config.drone = 'FC_MUV_01';
    config.lib = [];

    fs.writeFileSync('config.json', JSON.stringify(cse_host, null, 4), 'utf8');
}

var add_lib = {
    name: 'lib_sparrow_gun',
    target: 'arm',
    description: "[name] [portnum] [baudrate]",
//    scripts: 'python3 lib_sparrow_gun.py /MUV/control/lib_sparrow_gun/MICRO /dev/ttyUSB3 9600',
    scripts: './chute lib_sparrow_gun /dev/ttyUSB3 9600',
    data: ['GUN'],
    control: ['MICRO']
};

config.lib.push(add_lib);

function init() {
    if(config.lib.length > 0) {
        for(var idx in config.lib) {
            if(config.lib.hasOwnProperty(idx)) {
                if (msw_mqtt_client != null) {
                    for (var i = 0; i < config.lib[idx].data.length; i++) {
                        var container_name = config.lib[idx].data[i];
                        var _topic = '/MUV/data/' + config.lib[idx].name + '/' + container_name;
                        msw_mqtt_client.subscribe(_topic);
                        lib_topic.push(_topic);
                        console.log('[lib_mqtt] lib_topic[' + i + ']: ' + _topic);
                    }
                }

                var obj_lib = config.lib[idx];
                setTimeout(set_lib_config, parseInt(Math.random()*10), JSON.parse(JSON.stringify(obj_lib)));
            }
        }
    }
}

function set_lib_config(obj_lib) {
    try {
        var scripts_arr = obj_lib.scripts.split(' ');
        var run_lib = spawn(scripts_arr[0], scripts_arr.slice(1));

        run_lib.stdout.on('data', function(data) {
            console.log('stdout: ' + data);
        });

        run_lib.stderr.on('data', function(data) {
            console.log('stderr: ' + data);
        });

        run_lib.on('exit', function(code) {
            console.log('exit: ' + code);
        });

        run_lib.on('error', function(code) {
            console.log('error: ' + code);
        });
    }
    catch (e) {
        console.log(e.message);
    }
}

var msw_mqtt_client = null;
var noti_topic = [];
var fc_topic = [];
var lib_topic = [];
fc_topic.push('/Mobius/' + config.gcs + '/Drone_Data/' + config.drone +'/heartbeat');
fc_topic.push('/Mobius/' + config.gcs + '/Drone_Data/' + config.drone +'/global_position_int');
fc_topic.push('/Mobius/' + config.gcs + '/Drone_Data/' + config.drone +'/attitude');
fc_topic.push('/Mobius/' + config.gcs + '/Drone_Data/' + config.drone +'/battery_status');

//noti_topic.push('/Mobius/KETI_MUV/Mission_Data/MUV_IYAHN_01/sparrow_LTE/control_test');
var test_name = config.lib[0].control[0];
noti_topic.push('/Mobius/' + config.gcs + '/Mission_Data/' + config.drone + '/' + config.name + '/' + test_name);

msw_mqtt_connect('localhost', 1883);

function msw_mqtt_connect(broker_ip, port) {
    if(msw_mqtt_client == null) {
        var connectOptions = {
            host: broker_ip,
            port: port,
//              username: 'keti',
//              password: 'keti123',
            protocol: "mqtt",
            keepalive: 10,
//              clientId: serverUID,
            protocolId: "MQTT",
            protocolVersion: 4,
            clean: true,
            reconnectPeriod: 2000,
            connectTimeout: 2000,
            rejectUnauthorized: false
        };

        msw_mqtt_client = mqtt.connect(connectOptions);
    }

    msw_mqtt_client.on('connect', function () {
        console.log('[msw_mqtt_connect] connected to ' + broker_ip);
        for(var idx in noti_topic) {
            if(noti_topic.hasOwnProperty(idx)) {
                msw_mqtt_client.subscribe(noti_topic[idx]);
                console.log('[msw_mqtt_connect] noti_topic[' + idx + ']: ' + noti_topic[idx]);
            }
        }

        for(idx in fc_topic) {
            if(fc_topic.hasOwnProperty(idx)) {
                msw_mqtt_client.subscribe(fc_topic[idx]);
                console.log('[msw_mqtt_connect] fc_topic[' + idx + ']: ' + fc_topic[idx]);
            }
        }
    });

    msw_mqtt_client.on('message', function (topic, message) {
        for(var idx in noti_topic) {
            if (noti_topic.hasOwnProperty(idx)) {
                if(topic == noti_topic[idx]) {
	            
                    setTimeout(on_receive_from_nCube, parseInt(Math.random() * 5), topic, message.toString());
                    break;
                }
            }
        }

        for(idx in lib_topic) {
            if (lib_topic.hasOwnProperty(idx)) {
                if(topic == lib_topic[idx]) {
                    setTimeout(on_receive_from_lib, parseInt(Math.random() * 5), topic, message.toString());
                    break;
                }
            }
        }

        for(idx in fc_topic) {
            if (fc_topic.hasOwnProperty(idx)) {
                if(topic == fc_topic[idx]) {
                    var topic_arr = topic.split('/');
                    fc[topic_arr[topic_arr.length-1]] = JSON.parse(message.toString());

                    console.log('[' + topic + '] ' + message.toString());
                    break;
                }
            }
        }
    });

    msw_mqtt_client.on('error', function (err) {
        console.log(err.message);
    });
}

function on_receive_from_nCube(topic, str_message) {
    var indata = JSON.parse(str_message);
    
    console.log('[' + topic + '] ' + indata.con);
    console.log('msw message received from nCube');
    //if (stringVal.indexOf(',') !== -1) {
    var container_name = config.lib[0].control[0];
    var control_topic = '/MUV/control/' + config.lib[0].name + '/' + container_name;
    console.log('topic: ' + topic + ' cmd: ' + str_message);
    var msg_con = JSON.stringify(str_message);
    msg_con = msg_con["con"]
    msw_mqtt_client.publish(control_topic, msg_con);
//    msw_mqtt_client.publish(control_topic, JSON.stringify(str_message));
//    msw_mqtt_client.publish(control_topic, str_message);
    //}
}

function on_receive_from_lib(topic, str_message) {
    console.log('[' + topic + '] ' + str_message);

    var obj_lib_data = JSON.parse(str_message);

    if(fc.hasOwnProperty('global_position_int')) {
        Object.assign(obj_lib_data, JSON.parse(JSON.stringify(fc['global_position_int'])));
    }

    var topic_arr = topic.split('/');
    var data_topic = '/Mobius/' + config.gcs + '/Mission_Data/' + config.drone + '/' + config.name + '/' + topic_arr[topic_arr.length-1];
    send_mission_data(data_topic, JSON.stringify(obj_lib_data));
}

function send_mission_data(data_topic, obj_lteQ) {
    msw_mqtt_client.publish(data_topic, JSON.stringify(obj_lteQ));
}

init();
