from flask import Flask
from flask import request
from redis import Redis
from gimbocontrol import *

import traceback
import json
import time


app = Flask(__name__)
rstat = Redis('localhost', 6379, db=0, decode_responses=True)
rcmd = Redis('localhost', 6379, db=1, decode_responses=True)


class MyReturn:
    code = -1
    message = ""

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def toJson(self):
        ret = {'code': self.code, 'message': self.message}
        return json.dumps(ret)





def getCmdFromQ(devId):
    """
    get cmd from redis queue
    :param devId:
    :return:
    """
    # command Q db
    # r = Redis('localhost', 6379, db=1, decode_responses=True)
    if rcmd.exists(devId) == 0:
        return None
    else:
        if rcmd.type(devId) != 'list':
            raise Exception('Wrong command key type!')
        newcmd = rcmd.rpop(devId)
        return newcmd





def save2redis(devId, devStat):
    """
    Save device status to redis
    :param devId: device ID
    :param devStat: device Status in json
    :return:
    """
    if devId is None or devId=='':
        raise Exception('Invalid Device ID.')
    # r = Redis('localhost', 6379, db=0, decode_responses=True)
    rstat.set(devId, devStat)
    return


def debugRedis(devId):
    """
    print redis value
    :param devId:
    :return:
    """
    if devId is None or devId=='':
        raise Exception('Invalid Device ID.')
    # r = Redis('localhost', 6379, db=0, decode_responses=True)
    ret = rstat.get(devId)
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
        save2redis(devId, devStat)
        # Get command from queue
        gimboCmd = getCmdFromQ(devId)
        # Return
        if gimboCmd is not None:
            ret = MyReturn('201', gimboCmd)
        else:
            ret = MyReturn('200', 'Data saved. ' + debugRedis(devId))
    except Exception as e:
        return MyReturn('100', 'Error:'+str(traceback.format_exc())).toJson()
    elapsed = time.time()-timein
    print('Elapsed:' + str(round(elapsed)))
    return ret.toJson()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889)
