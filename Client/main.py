import json
import traceback
import time
import re
from urllib import request,parse
import requests, threading

# interval between upload in ms
interval = 1000
# default device ID
devId = '001'
# url of gcom
url = 'http://140.143.87.154:8889/upload'
# url = 'http://localhost:8889/upload'

# command execution que
Q=[]
lock = threading.Lock()
devStatus = []


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
    # req = requests.get('http://140.143.87.154:8889/')
    # print(req.text)
    # Q=[{'p'}]
    pass


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
        print('[%d]%s-%s' % (round(time.time()),'Upload OK but no command ',message))
    elif code == '100':
        print('[%d]%s-%s' % (round(time.time()),'Error caused by ', message))
    elif code == '201':
        # 有新的命令来了后，先取出命令的优先级和命令字，然后放入Q中
        parseCommand(message)
        print('[%d]%s-%s' % (round(time.time()),'Upload OK with new command', message))
    else:
        print('Unknown response')

def parseCommand(cmdString):
    """
    取出命令中的优先级和命令字序列，插入到命令队列中，并确保按照优先级降序排列（数字越小优先级越高）
    :param cmdString: 
    :return: 
    """
    global lock, Q
    # parse cmdString
    exp = r'\((\d*)\)(.*)'
    grp = re.match(exp, cmdString).groups()
    if len(grp)<2:
        raise Exception('Invalid command format')
    cmdPriority = int(grp[0])
    cmdSeris = grp[1].split('-')
    # insert cmd
    lock.acquire()
    Q.append({'priority': cmdPriority, 'seris': cmdSeris})
    Q.sort(key=lambda ele:ele['priority'])
    lock.release()
    return

def cmdSchedule():
    """
    命令调度过程
    :return: 
    """
    global lock, Q
    while True:
        # 0 合法性检测
        if len(Q) == 0:
            # print('No command')
            time.sleep(interval/10000)
            continue
        lock.acquire()
        # 1 从命令队列中取出第一个元素，并删除队列第一个元素
        p = Q[0]['priority']
        s = Q[0]['seris']
        Q = Q[1:] if len(Q) > 1 else []
        lock.release()
        # 2 循环执行seris中的每个命令字
        for ele in s:
            lock.acquire()
            if len(Q) > 0 and Q[0]['priority'] < p:
                print('Quit current cmd...')
                break
            lock.release()
            executecmd(ele)
            # print('Executing ' + ele + '...')
        # 3 获取电机的当前位置，并刷新缓存
        
        time.sleep(interval/10000)

    # 4 在循环结束或delay过程中查询是否有高于当前命令优先级的命令到来，如果有，则退出当前命令执行，去执行高优先级

def executecmd(cmdBytes):
    """
    
    :param cmdBytes: 
    :return: 
    """
    exp = r'DELAY(\d*)'
    grp = re.match(exp, cmdBytes)
    if grp is not None and len(grp.groups())>0:
        delay(int(grp.groups()[0])/1000)
        return
    RS232Send(cmdBytes)
    return

def delay(sec):
    time.sleep(sec)
    print('%d sec. delayed' % sec)
    return

def RS232Send(bytes):
    print('RS232 sending: ' + bytes)
    return


def run():
    """
    main procedure
    :return:
    """
    if devId is None or devId.strip() == '':
        raise Exception('Invaid device Id')

    # start cmd scheduler
    scheduler = threading.Thread(target=cmdSchedule)
    scheduler.start()

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


