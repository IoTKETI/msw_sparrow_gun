/**
 * Copyright (c) 2018, OCEAN
 * All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/**
 * Created by ryeubi on 2015-08-31.
 */

let http = require('http');

function http_request(origin, path, method, ty, bodyString, callback) {
    var options = {
        hostname: drone_info.host,
        port: '7579',
        path: path,
        method: method,
        headers: {
            "X-M2M-RI": require('shortid').generate(),
            "Accept": 'application/json',
            "X-M2M-Origin": origin,
            "Locale": 'en'
        }
    };

    if(bodyString.length > 0) {
        options.headers['Content-Length'] = bodyString.length;
    }

    if(method === 'post') {
        var a = (ty==='') ? '': ('; ty='+ty);
        options.headers['Content-Type'] = 'application/vnd.onem2m-res+json' + a;
    }
    else if(method === 'put') {
        options.headers['Content-Type'] = 'application/vnd.onem2m-res+json';
    }

    var res_body = '';
    var jsonObj = {};
    var req = http.request(options, function (res) {
        // console.log('[crtae response : ' + res.statusCode);
        //
        // res.setEncoding('utf8');

        res.on('data', function (chunk) {
            res_body += chunk;
        });

        res.on('end', function () {
            try {
                if(res_body == '') {
                    jsonObj = {};
                }
                else {
                    jsonObj = JSON.parse(res_body);
                }
                callback(res.headers['x-m2m-rsc'], jsonObj);
            }
            catch (e) {
                console.log('[http_adn] json parse error');
                jsonObj = {};
                jsonObj.dbg = res_body;
                callback(9999, jsonObj);
            }
        });
    });

    req.on('error', function (e) {
        console.log(e)
        console.log('problem with request: ' + e.message);
        jsonObj = {};
        jsonObj.dbg = e.message;

        callback(9999, jsonObj);
    });

    //console.log(bodyString);

    //console.log(path);

    req.write(bodyString);
    req.end();
}

exports.crtci = function(parent, count, content_obj, socket, callback) {
    var results_ci = {};
    var bodyString = '';

    results_ci['m2m:cin'] = {};
    results_ci['m2m:cin'].con = content_obj;

    bodyString = JSON.stringify(results_ci);

    // console.log(bodyString);

    http_request('S' + drone_info.id, parent, 'post', '4', bodyString, function (rsc, res_body) {
        callback(rsc, res_body, parent, socket);
    });
};


global.getType = function (p) {
    var type = 'string';
    if (Array.isArray(p)) {
        type = 'array';
    } else if (typeof p === 'string') {
        try {
            var _p = JSON.parse(p);
            if (typeof _p === 'object') {
                type = 'string_object';
            } else {
                type = 'string';
            }
        } catch (e) {
            type = 'string';
            return type;
        }
    } else if (p != null && typeof p === 'object') {
        type = 'object';
    } else {
        type = 'other';
    }

    return type;
};
