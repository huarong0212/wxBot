#!/usr/bin/env python
# coding: utf-8
#subprocess.call(['ffmpeg', '-y', '-i', '/var/folders/71/42k8g72x4pq09tfp920d033r0000gn/T/tmpeZTgMy', '-vn', '-f', 'wav', '/var/folders/71/42k8g72x4pq09tfp920d033r0000gn/T/tmpK5aLcZ'])
#ffmpeg -i in.mp3 -acodec pcm_s8 -ac 1 -ar 8000 -vn out.wav

import wave
import urllib2
import base64, requests
import json
import subprocess
## get access token by api key & secret key
def get_token():
    apiKey = "D2m5htQa0F3lqwVKV8Mi38b9"
    secretKey = "5838bcc4eea4becda652816828a71824"

    auth_url = "https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id=" + apiKey + "&client_secret=" + secretKey;

    res = urllib2.urlopen(auth_url)
    json_data = res.read()
    return json.loads(json_data)['access_token']


## post audio to server
def tts(cuid, audioPath):
    token = get_token()
    d = open(audioPath, 'rb').read()
    size = len(d)
    data = {
        "format": "wav",
        "rate": 8000,
        "channel": 1,
        "token":token,
        "cuid": cuid,
        "len": size,
        "speech": base64.encodestring(d).replace('\n', '')
    }
    result = requests.post('http://vop.baidu.com/server_api', json=data, headers={'Content-Type': 'application/json; charset=utf-8', 'Content-Length': str(size) })
    data_result = result.json()
    # print data_result['err_msg']
    if data_result['err_msg']=='success.':
        return data_result['result'][0]
    else:
        return data_result['err_msg']

def mp3topcm(mp3Path):
    subprocess.call(['ffmpeg', '-y', '-i', mp3Path, '-f', 's8',  '-acodec', 'pcm_s8' ,'-ab:a', '8k' , '-ac', '2', '-ar', '8000', mp3Path+'.wav'])
    return mp3Path + ".wav"


# if __name__ == '__main__':
#     print tts('1d2678900f734aa0a23734ace8aec5b1', mp3topcm("1.mp3")).encode('utf-8').replace("，", "")
