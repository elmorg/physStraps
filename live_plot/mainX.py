from __future__ import print_function
import serial
import time
import numpy as np
from datetime import datetime, date, timedelta
import time
import pandas as pd
from bokeh.io import curdoc, show
from bokeh.models import ColumnDataSource, Range1d
from bokeh.layouts import column
from bokeh.plotting import figure
from bokeh.client import push_session
from bokeh.palettes import Category10
from pandas import DataFrame
import os
from xbee import XBee,ZigBee

session = push_session(curdoc(),session_id = "straps")
numBelts = 0
addr = {}
tspan = 30
tspan2 = 120
width = 1200
height = 300
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

readings = pd.DataFrame({'time': [],
                         'hr1': [],
                         'hr2': [],
                         'resp1': [],
                         'resp2': []})
readings.set_index('time',inplace=True)
readings_plot = ColumnDataSource(readings)

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

p = figure(plot_width=width, plot_height=height,x_axis_type="datetime",title = 'Respiration',logo = None,
           x_range=Range1d((time.time()-tspan)*1000, time.time()*1000),y_range=Range1d(0,1023),tools=[],min_border_top=10)
p2 = figure(plot_width=width, plot_height=height,x_axis_type="datetime", title = "Heart Rate",logo = None,
            x_range=Range1d((time.time()-tspan2)*1000, time.time()*1000),y_range=Range1d(0,150),tools=[],min_border_top=10)

resp1 = p.line(x='time', y= 'resp1', source = readings_plot, line_width=2,line_color = Category10[10][2])
resp2 = p.line(x='time', y= 'resp2', source = readings_plot, line_width=2,line_color = Category10[10][4])
hr1 = p2.line(x='time', y= 'hr1', source = readings_plot, line_width=2,line_color = Category10[10][2])
hr2 = p2.line(x='time', y= 'hr2', source = readings_plot, line_width=2,line_color = Category10[10][4])

p.xaxis.axis_label = 'Time'
p2.xaxis.axis_label= 'Time'
p.yaxis.axis_label = 'Chest Expansion'
p2.yaxis.axis_label = 'Heart Rate (bmp)'


def data_update():
    global readings_plot, addr, numBelts,resp,pulse,hrIx,hRate,hRates,ex_pulse
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
    temp = {'time': [time.time()*1000],
                             'hr1': [hRate[0]],
                             'hr2': [hRate[1]],
                             'resp1': [resp[0]],
                             'resp2': [resp[1]]}
    # temp.set_index('time',inplace=True)
    p.x_range.start = (time.time()-tspan)*1000
    p.x_range.end =  time.time()*1000
    p2.x_range.start = (time.time()-tspan2)*1000
    p2.x_range.end =  time.time()*1000
    readings_plot.stream(temp)
    # print('here')

curdoc().add_periodic_callback(data_update, 1)
session.show(column(p,p2)) # open the document in a browser
session.loop_until_closed() # run forever

serial_port1.close()
