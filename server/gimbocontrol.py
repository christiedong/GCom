from redis import Redis




def myHexStr(indata):
    tmphex = hex(int(indata))[2:]
    if len(tmphex ) %2 != 0: tmphex='0'+ tmphex
    return tmphex


class BaseCommand:
    # command type: GIMBOMOVE, FOCUSMOVE, etc
    cmdType = ''
    # params of command
    cmdParams = []
    cmdPriority = 10

    def __init__(self, cmdType, cmdParams, cmdPriority=10):
        self.cmdType = cmdType
        self.cmdParams = cmdParams
        self.cmdPriority = cmdPriority

    def validateParams(self):
        pass

    def toString(self):
        pass

    def _toString(self):
        return '(%d)%s' % (self.cmdPriority, self.toString())

class GimboMoveCommand(BaseCommand):
    """
    Implementation of gimbo move command
    """
    def __init__(self, params):
        super().__init__('GIMBOMOVE', params)
        if not self.validateParams(params):
            raise Exception('Invalid command params: ' + str(params))
        # construct command bytes
        self.start = 0xFF
        self.address = params[0]['address']
        direction = params[0]['direction']
        if direction == 'left':
            self.cmd1 = 0x00
            self.cmd2 = 0x04
            self.data1 = params[0]['speed']
            self.data2 = 0x00
        elif direction == 'right':
            self.cmd1 = 0x00
            self.cmd2 = 0x02
            self.data1 = params[0]['speed']
            self.data2 = 0x00
        elif direction == 'up':
            self.cmd1 = 0x00
            self.cmd2 = 0x08
            self.data1 = 0x00
            self.data2 = params[0]['speed']
        elif direction == 'down':
            self.cmd1 = 0x00
            self.cmd2 = 0x10
            self.data1 = 0x00
            self.data2 = params[0]['speed']
        else:
            raise Exception('Invalid direction param')

        self.checksum = (self.address + self.cmd1 + self.cmd2 + self.data1 + self.data2) & 0xFF

    def validateParams(self, params):
        if type(params).__name__ == 'list' \
                and len(params) == 1 \
                and type(params[0]).__name__ == 'dict' \
                and 'address' in params[0] \
                and (params[0]['address'] >= 0x00 and params[0]['address'] <= 0xFF) \
                and 'direction' in params[0] \
                and params[0]['direction'] in ['left','right','up','down'] \
                and 'speed' in params[0] \
                and (params[0]['speed'] >= 0x00 and params[0]['speed'] <= 0x3F):
            return True
        return False

    def toString(self):
        ret = '%s%s%s%s%s%s%s' % (myHexStr(self.start),
                                  myHexStr(self.address),
                                  myHexStr(self.cmd1),
                                  myHexStr(self.cmd2),
                                  myHexStr(self.data1),
                                  myHexStr(self.data2),
                                  myHexStr(self.checksum))
        return ret


class GimboStopCommand(BaseCommand):
    """
    Implementation of stop command
    """
    def __init__(self, params):
        super().__init__('GIMBOSTOP', params, 1)
        if not self.validateParams(params):
            raise Exception('Invalid command params: ' + str(params))
        self.start = 0xFF
        self.address =params[0]['address']
        self.cmd1 = 0
        self.cmd2 = 0
        self.data1 = 0
        self.data2 = 0
        self.checksum = 1

    def validateParams(self, params):
        if type(params).__name__ == 'list' \
                and len(params) == 1 \
                and type(params[0]).__name__ == 'dict' \
                and 'address' in params[0] \
                and (params[0]['address'] >=0x00 and params[0]['address'] <= 0xFF):
            return True
        return False

    def toString(self):
        ret = '%s%s%s%s%s%s%s' % (myHexStr(self.start),
                                  myHexStr(self.address),
                                  myHexStr(self.cmd1),
                                  myHexStr(self.cmd2),
                                  myHexStr(self.data1),
                                  myHexStr(self.data2),
                                  myHexStr(self.checksum))
        return ret


class GimboDelayCommand(BaseCommand):
    """
    Delay
    """
    def __init__(self, params):
        super().__init__('GIMBODELAY', params)
        if not self.validateParams(params):
            raise Exception('Invalid command params: ' + str(params))
        self.delayms = int(params[0]['delayms'])

    def validateParams(self, params):
        if type(params).__name__ == 'list' \
                and len(params) == 1 \
                and type(params[0]).__name__ == 'dict' \
                and 'delayms' in params[0] \
                and int(params[0]['delayms'])>0 \
                and 'address' in params[0] \
                and (params[0]['address'] >=0x00 and params[0]['address'] <= 0xFF):
            return True
        return False

    def toString(self):
        return 'DELAY'+ str(self.delayms)


class GimboStepMoveCommand(BaseCommand):
    """
    Implementation of gimbo step move command
    step command = Gimbomove + Gimbostop
    """
    def __init__(self, params):
        super().__init__('GIMBOSTEPMOVE', params)
        if not self.validateParams(params):
            raise Exception('Invalid command params: ' + str(params))
        self.move = GimboMoveCommand([params[0]])
        self.delay = GimboDelayCommand([params[1]])
        self.stop = GimboStopCommand([params[2]])

    def validateParams(self, params):
        if type(params).__name__ == 'list' \
                and len(params) >= 3:
            return True
        return False

    def toString(self):
        """
        step move fromat: movecmd + duration + stop
        :return:
        """
        ret = '%s-%s-%s' % (self.move.toString(), self.delay.toString(), self.stop.toString())
        return ret


if __name__ == '__main__':
    leftmoveparam = [{'address': 0x01, 'direction': 'left', 'speed': 0x3F}]
    rightmoveparam = [{'address': 0x01, 'direction': 'right', 'speed': 0x3F}]
    upmoveparam = [{'address': 0x01, 'direction': 'up', 'speed': 0x3F}]
    downmoveparam = [{'address': 0x01, 'direction': 'down', 'speed': 0x3F}]

    stopparam = [{'address':0x01}]

    delayparam = [{'address':0x01,'delayms':1000}]

    stepmoveparam = [leftmoveparam[0], delayparam[0], stopparam[0]]

    leftmovecmd = GimboMoveCommand(leftmoveparam)
    rightmovecmd = GimboMoveCommand(rightmoveparam)
    upmovecmd = GimboMoveCommand(upmoveparam)
    downmovecmd = GimboMoveCommand(downmoveparam)

    stepmovecmd = GimboStepMoveCommand(stepmoveparam)

    stopcmd = GimboStopCommand(stopparam)


    r = Redis(host='140.143.87.154', port=6379, db=1, decode_responses=True)
    r.lpush('001',stepmovecmd._toString())
    r.lpush('001', leftmovecmd._toString())
    r.lpush('001', rightmovecmd._toString())
    r.lpush('001', stopcmd._toString())

    print('LEFT: ' + stopcmd._toString())
    # print('Right: ' + rightmovecmd.toString())
    # print('UP: ' + upmovecmd.toString())
    # print('down: ' + downmovecmd.toString())
    #
    # print('step: '+ stepmovecmd.toString() )


