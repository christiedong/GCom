import json
import traceback
import time
from urllib import request,parse
import requests

# interval between upload in ms
interval = 2000
# default device ID
devId = '001'
# url of gcom
# url = 'http://140.143.87.154:8889/upload'
url = 'http://localhost:8889/upload'


class MyReturn():
    code = -1
    message = ""
    def __init__(self,code,message):
        self.code = code
        self.message = message

    def toJson(self):
        ret = {'code': self.code, 'message': self.message}
        return json.dumps(ret)

class DevStatus():

    def __init__(self, devId, longtitude, latitude, altitude, elevation, azimuth):
        self.devId = devId
        self.long = longtitude
        self.lat = latitude
        self.alti = altitude
        self.elev = elevation
        self.azim = azimuth

    def toJson(self):
        ret = {'devId':self.devId, 'devStat':{'long':self.long, 'lat':self.lat, 'alti':self.alti, 'elev':self.elev, 'azim':self.azim}}
        return json.dumps(ret)

    def toDict(self):
        return {'devId':self.devId, 'devStat':{'long':self.long, 'lat':self.lat, 'alti':self.alti, 'elev':self.elev, 'azim':self.azim}}


def debug():
    # devStat = DevStatus(devId,'100','200','300','400','500')
    # print(devStat.toJson())
    req = requests.get('http://140.143.87.154:8889/')
    print(req.text)


def getStatus(devId):
    return DevStatus(devId,'100','200','300','400','500')

def send_req(devStat):
    """
    send request to get response containing control command
    :param devStat:
    :return:
    """
    header_dict={'Content-Type':'application/x-www-form-urlencoded'}
    data = devStat.toDict()
    data = parse.urlencode(data).encode(encoding='utf-8')
    res = requests.post(url,data,headers=header_dict)
    res = res.text.encode('utf-8')
    res_json = json.loads(res)
    # req = request.Request(url, data = data, headers=header_dict)
    # res = request.urlopen(req)
    # res_json = json.loads(res.read())
    ret = MyReturn(res_json['code'],res_json['message'])
    return ret

def find_response(resp):
    code = resp.code
    message = resp.message
    if code == '200':
        print('%s-%s' % ('Upload OK but no command',message))
    elif code == '100':
        print('%s-%s' % ('Error caused by ', message))
    elif code == '201':
        print('%s-%s' % ('Upload OK with new command', message))
    else:
        print('Unknown response')

def run():
    """
    main procedure
    :return:
    """
    if devId is None or devId.strip() == '':
        raise Exception('Invaid device Id')

    while True:
        # get device status
        stat = getStatus(devId)
        # send request
        resp = send_req(stat)
        # find response
        find_response(resp)
        # sleep with interval
        time.sleep(interval/1000)

    return

if __name__ == '__main__':
    try:
        run()
        # debug()
    except Exception as e:
        traceback.print_exc()


