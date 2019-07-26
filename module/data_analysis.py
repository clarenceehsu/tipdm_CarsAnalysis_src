# -*- encoding: utf-8 -*-

import math
import numpy as np
import requests
import json

from module.data_preprocess import data_process
from module.data_convert import data_convert


class data_analysis:

    @staticmethod
    def distance(location, location2):
        # 0纬度 1经度ln
        radLat1 = math.radians(location[0])
        radLat2 = math.radians(location2[0])
        a = radLat1 - radLat2
        b = math.radians(location[1]) - math.radians(location2[1])
        s = 2 * math.asin(math.sqrt(math.pow(math.sin(a / 2), 2) + math.cos(radLat1) * math.cos(radLat2) * math.pow(math.sin(b/2), 2)))
        d = s * 6371.004  # 单位km
        return d

    @staticmethod
    def fatigue_driving(_data):

        driving_state = []
        drive_count = 0
        rest_count = 0
        fatigue_count = 0
        fatigue_time = 0
        all_long = 0

        for n in _data:
            if n[5] == 1 or n[11] != 0:
                if rest_count != 0:
                    driving_state.append(['rest', rest_count])
                    rest_count = 0
                drive_count += 1
            if n[5] == 0 and n[11] == 0:
                if drive_count != 0:
                    driving_state.append(['drive', drive_count])
                    drive_count = 0
                rest_count += 1

        # 确保所有的数据写入到了driving_state列表中
        if drive_count != 0:
            driving_state.append(['drive', drive_count])
        if rest_count != 0:
            driving_state.append(['rest', rest_count])

        for m in driving_state:
            if m[0] == 'drive' or (m[0] == 'rest' and m[1] <= 5):  # 5秒内算误差
                fatigue_time += m[1]
                if fatigue_time >= 14400:  # 大于4个小时记一次疲劳驾驶
                    fatigue_count += 1
                    all_long += fatigue_time
                    fatigue_time = 0
            if m[0] == 'rest' and m[1] >= 1200:  # 如果rest大于20分钟则记录次数归零
                fatigue_time = 0

        return all_long, fatigue_count

    @staticmethod
    def speed_change_analysis(_data):  # 急加速急减速分析

        L1 = []
        L2 = []
        times_acc = 1
        times_dec = 1

        for n in range(1, len(_data) - 1):
            a = (_data[n + 1][11] - _data[n - 1][11]) / 2
            if a >= 3:
                L1.append([a, _data[n][10]])
            elif a <= -3:
                L2.append([a, _data[n][10]])

        time_last_acc = len(L1)
        time_last_dec = len(L2)

        for m in range(len(L1) - 1):
            pre = data_process.date_to_sec(L1[m][1])
            cur = data_process.date_to_sec(L1[m + 1][1])

            if cur - pre == 1:
                continue
            else:
                times_acc += 1

        for i in range(len(L2) - 1):
            pre = data_process.date_to_sec(L2[i][1])
            cur = data_process.date_to_sec(L2[i + 1][1])

            if cur - pre == 1:
                continue
            else:
                times_dec += 1

        return time_last_acc, time_last_dec, times_acc, times_dec

    @staticmethod
    def static_analysis(_data):  # 状态分析（怠速预热、超长怠速、熄火滑行、超速）

        date_set = []
        static_set2 = []
        static_set3 = []

        count = 1
        count2 = 1
        count3 = 1

        idle_heating = 0
        idle_count = 0

        long_tickover = 0
        long_count = 0

        flameout = 0
        flameout_count = 0

        speed = 0
        speed_count = 0

        for n in range(len(_data) - 1):  # 将怠速的数据日期写入date_set列表

            if _data[n][11] == 0 and _data[n][5] == 1:
                if data_process.date_to_sec(_data[n + 1][10]) - data_process.date_to_sec(_data[n][10]) == 1:
                    count += 1
                else:
                    date_set.append([_data[n][10].split(' ')[0], _data[n][10].split(' ')[1], count])
                    # 日期（年月日），最后时间（时分秒），经历秒数
                    count = 1

            if 0 <= _data[n][11] * 3.6 <= 5 and _data[n][5] == 0:
                if data_process.date_to_sec(_data[n + 1][10]) - data_process.date_to_sec(_data[n][10]) == 1:
                    count2 += 1
                elif count2 >= 3:
                    static_set2.append([_data[n][10].split(' ')[0], _data[n][10].split(' ')[1], count2])
                    count2 = 1

            if _data[n][11] >= 27.778:  # 秒速度大于27.778m/s（100km/h）
                if data_process.date_to_sec(_data[n + 1][10]) - data_process.date_to_sec(_data[n][10]) == 1:  #判断两个数据连续
                    count3 += 1  # 秒数累积
                elif count3 >= 3:  # 大于3秒记为超速
                    static_set3.append([_data[n][10].split(' ')[0], _data[n][10].split(' ')[1], count3])  # 写入超速数据
                    count3 = 1

        for m in range(len(date_set) - 1):
            if date_set[m][2] >= 3:
                idle_heating += date_set[m][2]
                idle_count += 1
            else:
                long_tickover += date_set[m][2]
                long_count += 1

        for i in range(len(static_set2) - 1):
            if static_set2[i][2] >= 3:
                flameout += static_set2[i][2]
                flameout_count += 1

        for j in range(len(static_set3) - 1):
            if static_set3[j][2] >= 3:
                speed += static_set3[j][2]
                speed_count += 1

        return idle_heating, idle_count, long_tickover, long_count, flameout, flameout_count, speed, speed_count

    @staticmethod
    def stable_analysis(_data):  # 标准差（所有的速度、运行状态下的速度）

        speed = []

        for n in _data:
            if n[5] == 1:  # or n[11] != 0:
                speed.append(n[11])

        return np.std(speed, ddof=1)

    @staticmethod
    def road_swift(_data):

        angle_shift = []
        count = 0
        time_sum = 0
        times = 0

        for n in range(len(_data) - 1):
            temp = _data[n + 1][2] - _data[n][2]
            if temp > 180: temp -= 360
            elif temp < -180: temp += 360  # 保持变化角度在+-180度内
            angle_shift.append(temp)  # 把每秒变化的值存入列表

        for n in angle_shift:
            if 20 <= abs(n) <= 70:  # 发现大角度的变化，开始记数
                count += 1  # 记秒数
                time_sum += n  # 记录角度的变化
            if abs(time_sum) <= 5 and count <= 4 and n == 0: # 开始到结束的角度变化在5度内，且下一秒的变化为0，变化持续时间小于4秒记为急变道
                times += 1
                count = 0
                time_sum = 0

        return times

    @staticmethod
    def get_location_bd(location):
        r = requests.get(url='http://api.map.baidu.com/geocoder/v2/',
                         params={'location': '%s,%s' % (location[1], location[0]), 'ak': 'qpiImN8ticG8lI0rFtN3HCRGXjCL2sha', 'output': 'json'})

        result = r.json()
        city = result['result']['addressComponent']['city']
        district = result['result']['addressComponent']['district']

        return city, district

    @staticmethod
    def get_location(location):
        r = requests.get(url='https://restapi.amap.com/v3/geocode/regeo?parameters',
                         params={'location': '%s,%s' % (location[0], location[1]), 'key': 'dce22a61e9b7f25763ea2b24c206cd15', 'output': 'json'})

        result = r.json()
        city = result['regeocode']['addressComponent']['city']
        district = result['regeocode']['addressComponent']['district']

        return city, district

    @staticmethod
    def speed_analysis(_data, spd_set, weather_data):

        # 预处理出一个最低速度阈值
        spd_lmt = 100
        for m in spd_set:
            spd_lmt = min(spd_lmt, m[1])
        spd_lmt = spd_lmt / 3.6  # 转化为秒速度

        static_set3 = []

        count3 = 1
        static = 'Null'

        speed_count = 0

        # 各种条件
        xy = 0
        zy = 0
        dy = 0
        by = 0
        dby = 0
        w = 0
        q = 0

        for n in range(len(_data) - 1):

            if _data[n][11] >= spd_lmt:  # 秒速度大于阈值
                if data_process.date_to_sec(_data[n + 1][10]) - data_process.date_to_sec(_data[n][10]) == 1:  # 判断两个数据连续
                    count3 += 1  # 秒数累积
                elif count3 >= 3:  # 大于3秒记为超速
                    # 判断超速是否符合要求
                    city, district = data_analysis.get_location(data_convert.wgs84_to_gcj02(_data[n][3], _data[n][4]))
                    city = str(city).replace('市', '')
                    district = str(district).replace('区', '').replace('县', '')
                    time = str(int(_data[n][10].split(' ')[0].split('-')[2])) + '/' + str(int(_data[n][10].split(' ')[0].split('-')[1])) + '/' + str(int(_data[n][10].split(' ')[0].split('-')[0]))
                    for m in spd_set:
                        if city == m[2] and district == m[3] and time == m[0]:  # 匹配市、区、时间
                            if spd_lmt >= m[1] / 3.6:
                                for i in weather_data:
                                    if city == i[0] and district == i[1] and time == m[0]:  # 匹配市、区、时间
                                        static = i[2]
                                static_set3.append([_data[n][10].split(' ')[0], count3, static])  # 写入超速数据
                                count3 = 1
                                speed_count += 1

        for j in static_set3:
            if '大暴雨' in j[2]:
                dby += j[1]
            elif '暴雨' in j[2]:
                by += j[1]
            elif '大雨' in j[2]:
                dy += j[1]
            elif '中雨' in j[2] or '阵雨' in j[2]:
                zy += j[1]
            elif '小雨' in j[2] or '雨夹雪' in j[2]:
                xy += j[1]
            elif '雾' in j[2]:
                w += j[1]
            else:
                q += j[1]

        print([q, xy, zy, dy, by, dby, w])

        return [[q, xy, zy, dy, by, dby, w], speed_count]

