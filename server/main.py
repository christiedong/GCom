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


@app.route('/command', methods=['GET'])
def command():
    try:
        # parse command request
        devId = request.args.get('devId')
        cmdType = request.args.get('cmdType')
        address = request.args.get('address')
        params = []
        p = {}
        cmd = None

        if devId is None or cmdType is None or address is None:
            raise Exception('devId and cmdType and address are required!')
        address = int(address)

        if cmdType == 'GIMBOMOVE':
            p['address'] = address
            p['direction'] = request.args.get('direction') if request.args.get('direction') is not None else ''
            p['speed'] = int(request.args.get('speed')) if request.args.get('speed') is not None else -1
            params.append(p)
            cmd = GimboMoveCommand(params)
        elif cmdType == 'GIMBOSTOP':
            p['address'] = address
            params.append(p)
            cmd = GimboStopCommand(params)
        elif cmdType == 'GIMBODELAY':
            p['address'] = address
            p['delayms'] = int(request.args.get('delayms')) if request.args.get('delayms') is not None else -1
            params.append(p)
            cmd = GimboDelayCommand(params)
        elif cmdType == 'GIMBOSTEPMOVE':
            p1={'address': address}
            p1['direction'] = request.args.get('direction') if request.args.get('direction') is not None else ''
            p1['speed'] = int(request.args.get('speed')) if request.args.get('speed') is not None else -1
            params.append(p1)
            p2 = {'address': address}
            p2['delayms'] = int(request.args.get('delayms')) if request.args.get('delayms') is not None else -1
            params.append(p2)
            p3 = {'address': address}
            params.append(p3)
            cmd = GimboStepMoveCommand(params)
        else:
            raise Exception('Unknown command!')

        # insert command
        # r = Redis(host='140.143.87.154', port=6379, db=1, decode_responses=True)
        rcmd.lpush(devId, cmd._toString())
        return MyReturn('202', 'Command sent: ' + cmd.toString()).toJson()
    except Exception as e:
        return MyReturn('100', 'Error:'+str(traceback.format_exc())).toJson()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889)
