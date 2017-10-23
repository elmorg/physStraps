from __future__ import print_function
import serial
import time
import numpy as np
from xbee import XBee,ZigBee

numBelts = 0
addr = {}

serial_port1 = serial.Serial('/dev/cu.usbserial-A900N785',9600)
# serial_port2 = serial.Serial('/dev/cu.usbserial-A900N785',9600)
xbee = ZigBee(serial_port1)

nAvg = 5
xTime = [time.time(), time.time()]
hRates = [[0 for j in range(nAvg)] for i in range(2)]
hrIx = [0,0]
hRate = [0, 0]
resp = [ 0, 0]
pulse = [False, False]
ex_pulse = [False, False]

def getHR(belt):
        global xTime, hRates, hrIx
        tVal = time.time()
        hRate = 60.0/(tVal - xTime[belt])
        if (hRate > 30.0) and (hRate < 190.0):
            hRates[belt][hrIx[belt]] = int(hRate)
            hrIx[belt] += 1
            if hrIx[belt] >= nAvg:
                hrIx[belt] = 0

        xTime[belt] = tVal
        return int(np.mean(hRates[belt]))

while True:
    try:
        frame = xbee.wait_read_frame()
        if frame['source_addr'] not in addr and numBelts < 2:
            addr[frame['source_addr']] = numBelts
            numBelts += 1
        belt = addr[frame['source_addr']]
        resp[belt] = frame['samples'][0]['adc-0']
        pulse[belt] = frame['samples'][0]['dio-1']
        if pulse[belt] and not ex_pulse[belt]:
            hRate[belt] = getHR(belt)
        elif time.time() - xTime[belt] > 3:
            hRate[belt] = 0
        ex_pulse[belt] = pulse[belt]
        print('respA: '+str(resp[0])+'   pulseA: '+str(pulse[0])+str(hRates[0])+'  HR_A: '+str(hRate[0])+'bpm'+
              '     respB: '+str(resp[1])+'   pulseB: '+str(pulse[1])+'  HR_B: ' +str(hRate[1])+'bpm')
    except KeyboardInterrupt:
        print('error')
        break

serial_port.close()
