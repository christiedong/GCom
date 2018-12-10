from flask import Flask
from flask import request
from redis import Redis

import traceback
import json
import time



app = Flask(__name__)

class MyReturn():
    code = -1
    message = ""
    def __init__(self,code,message):
        self.code = code
        self.message = message

    def toJson(self):
        ret = {'code': self.code, 'message': self.message}
        return json.dumps(ret)

def myHexStr(indata):
    tmphex = hex(int(indata))[2:]
    if len(tmphex)%2 !=0:
        tmphex='0'+tmphex
    return tmphex

class BaseCommand():
    devId = ''
    devCommandType = ''
    def __init__(self,devId, devCommandType):
        self.devId = devId
        self.devCommandType = devCommandType

class GimboMoveCommand(BaseCommand):
    def __init__(self,devId,cmd1,cmd2,data1,data2):
        super.__init__(devId,'GIMBOMOVE')
        self.start = 0xFF
        self.address = 0x01
        self.cmd1 = cmd1
        self.cmd2 = cmd2
        self.data1 = data1
        self.data2 = data2
        self.checksum = (self.address + self.cmd1 + self.cmd2 + self.data1 + self.data2) & 0xFF

    def toCmdHexString(self):
        ret = '0x%s%s%s%s%s%s%s' % (myHexStr(self.start),myHexStr(self.address),myHexStr(self.cmd1),myHexStr(self.cmd2),myHexStr(self.data1),myHexStr(self.data2),myHexStr(self.checksum))
        return ret

    def toCmdBytes(self):






def save2redis(devId, devStat):
    """
    Save device status to redis
    :param devId: device ID
    :param devStat: device Status in json
    :return:
    """
    if devId is None or devId=='':
        raise Exception('Invalid Device ID.')
    r = Redis('localhost',6379)
    r.set(devId,devStat)
    return

def debugRedis(devId):
    """
    print redis value
    :param devId:
    :return:
    """
    if devId is None or devId=='':
        raise Exception('Invalid Device ID.')
    r = Redis('localhost',6379,decode_responses=True)
    ret = r.get(devId)
    print(ret)
    return ret

@app.route('/upload', methods=['POST'])
def upload():
    timein=time.time()
    try:
        # Get device status params
        devId = request.form.get('devId')
        devStat = request.form.get('devStat')
        # Save status to redis
        save2redis(devId,devStat)
        # Get command from queue

        # Return
        ret = MyReturn('200','Data saved. '+debugRedis(devId))# debugRedis(devId)
    except Exception as e:
        return MyReturn(100,'Error:'+str(traceback.format_exc())).toJson()
    elapsed = time.time()-timein
    print('Elapsed:' + str(round(elapsed)))
    return ret.toJson()







if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889)