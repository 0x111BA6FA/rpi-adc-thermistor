import math
import time
import smbus
import bisect
import MCP342x
import datetime

R25 = 10**4			# 10 кОм при 25C на термисторе, для B57861S0103

# R/T 8016
rt_list = list(range(155, -60, -5))
rr25_list = [0.01653, 0.01853, 0.02083, 0.02348, 0.02654, 0.03009, 0.03417, 0.03893, 0.04454, 0.05112, 0.05886, 0.068, 0.07885, 0.09177, 0.1072, 0.1258, 0.1481, 0.1752, 0.2083, 0.2488, 0.2986, 0.3603, 0.4369, 0.5327, 0.6531, 0.8057, 1.0, 1.249, 1.571, 1.99, 2.539, 3.265, 4.232, 5.533, 7.293, 9.707, 13.04, 17.7, 24.26, 33.65, 47.17, 67.01, 96.3]

# проверки корректности внесенных таблиц
if rt_list != sorted(rt_list, reverse=True): raise ValueError('rt_list is not sorted')
if rr25_list != sorted(rr25_list): raise ValueError('rr25_list is not sorted')
if len(rt_list) != len(rr25_list) or len(rt_list) < 2: raise ValueError('rtlist rr25_list len fail')


addr68_ch0 = MCP342x.MCP342x(smbus.SMBus(1), 0x68, channel=0, resolution=18)
outfile = open(f'./{datetime.datetime.now().strftime("thermistor_%Y%m%d_%H%M%S")}.log', 'w')


secs_left = 0
while True:
	
	# получаем вольтаж с АЦП
	#v_adc = addr68_ch0.convert_and_read(sleep=True)
	v_adc = addr68_ch0.convert_and_read()
	
	sv = 3.3			# напряжение питания
	r2 = 1000			# 1 кОм R2 резистор делителя

	# вычисления по схеме А - R2 термистор R1 резистор
	'''
	dur1 = sv - v_adc	# падение напряжения на резисторе R1
	i = dur1/r1			# ток в делителе, вычислен по резистору R1
	rt = v_adc/i		# искомое сопротивление термистора R2
	'''

	# вычисления по схеме C - R1 термистор R2 резистор
	i = v_adc/r2		# ток в делителе через резистор R2
	dur1 = sv - v_adc	# падение напряжения на термисторе R1	
	rt = dur1/i			# искомое сопротивление термистора R1

	# ищем диапазон
	rt25 = rt/R25		# текущее Rt/R25
	max_index = bisect.bisect(rr25_list, rt25, lo=1, hi=len(rr25_list)-1)	# конец диапазона с контролем выхода за пределы
	min_index = max_index - 1	# начало дипазона
	# считаем B для диапазона
	#B = 3988	# B25/100
	B = (math.log(R25*rr25_list[min_index]) - math.log(R25*rr25_list[max_index])) / (1/(rt_list[min_index]+273.15) - 1/(rt_list[max_index]+273.15))
	
	# считаем температуру от одной из границ диапазона, разницы нет
	t1 = 1 / ((math.log(rt) - math.log(R25*rr25_list[max_index])) / B + 1 / (rt_list[max_index]+273.15)) - 273.15

	print(f'{secs_left}\tU: {v_adc:.3f} V\tR: {rt/1000:.1f} kOhms\tB: {int(B)} K\tT: {t1:.1f} C')

	# выводим в результат файл
	outfile.write('\t'.join([str(secs_left),	# время
							 f'{v_adc:.3f}',	# U
							 f'{rt25:.3f}',		# Rt/R25
							 f'{t1:.1f}'		# T
							])+'\n')
	outfile.flush()
	
	tts = 5
	secs_left += tts
	time.sleep(tts)