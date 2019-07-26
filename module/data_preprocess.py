# -*- encoding: utf-8 -*-

import math


class data_process:

    @staticmethod
    def date_to_sec(time):  # 把时间转化为相对秒数

        mon = int(time.split(' ')[0].split('-')[1]) * 2678400
        date = int(time.split(' ')[0].split('-')[2]) * 86400
        cur = time.split(' ')[1]

        sec = mon + date + int(cur.split(':')[0]) * 3600 + int(cur.split(':')[1]) * 60 + int(cur.split(':')[2])

        return sec

    @staticmethod
    def sec_to_date(time):  # 把相对秒数转化为时间

        mon = 0
        day = 0
        hor = 0
        minute = 0
        sec = 0

        if time // 2678400:
            mon += time // 2678400
            time -= (time // 2678400) * 2678400
        if time // 86400:
            day += time // 86400
            time -= (time // 86400) * 86400
        if time // 3600:
            hor += time // 3600
            time -= (time // 3600) * 3600
        if time // 60:
            minute += time // 60
            time -= (time // 60) * 60
        sec += time

        date = '2018-%02d-%02d %02d:%02d:%02d' % (mon, day, hor, minute, sec)
        return date

    @staticmethod
    def check(_data):  # 填充数据，对空缺数据进行填充（直接插值拟合）

        cur = _data.pop()
        L = [cur]
        while True:
            if _data == []:
                break
            pre = _data.pop()
            space = data_process.date_to_sec(cur[10]) - data_process.date_to_sec(pre[10])
            if 1 < space <= 3:
                gen = []
                for n in range(space - 1):
                    fix_lat, fix_lng = data_process.location_fix([pre[4], pre[3], pre[11], pre[2]])
                    gen.append([pre[0], pre[1], pre[2], fix_lng, fix_lat, pre[5], pre[6], pre[7], pre[8], pre[9], data_process.sec_to_date(data_process.date_to_sec(pre[10]) + 1), pre[11], pre[12]])
                while gen:
                    L.append(gen.pop())
            L.append(pre)
            cur = pre

        return L

    @staticmethod
    def location_fix(location_list):  # 根据该时间的经纬度和速度、方向角来计算下一个位置的经纬度

        lat = location_list[0]
        lng = location_list[1]
        spd = location_list[2]
        ang = location_list[3]

        distance = spd / 3.6
        radius = 6371004
        delta = distance / radius
        theta = math.radians(ang)
        phi1 = math.radians(lat)
        lambda1 = math.radians(lng)

        sin_phi1 = math.sin(phi1)
        cos_phi1 = math.cos(phi1)
        sin_delta = math.sin(delta)
        cos_delta = math.cos(delta)
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)

        sin_phi2 = sin_phi1 * cos_delta + cos_phi1 * sin_delta * cos_theta
        phi2 = math.asin(sin_phi2)
        y = sin_theta * sin_delta * cos_phi1
        x = cos_delta - sin_phi1 * sin_phi2
        lambda2 = lambda1 + math.atan2(y, x)

        return math.degrees(phi2), (math.degrees(lambda2) + 540) % 360 - 180  # 返回纬度、经度

    @staticmethod
    def block_g(loc):  # 找出错误的区块

        temp = [0, 0]
        block = []

        for i in range(len(loc) - 1):
            if temp == [0, 0]:
                temp[0] = loc[i]  # 给block定义最左值
            if loc[i + 1] - loc[i] < 1000:  # 异常值之间时间差值小于1000时，定义为错误块内的数据
                temp[1] = loc[i + 1]  # 始终保持范围内最后的一个异常值为一个错误块的最右值
            else:
                if temp[1] == 0:
                    block.append([temp[0] - 600, temp[0] + 600])  # 如果出现一个值的情况，为避免偶然取其附近+-200的一个区间
                else:
                    block.append(temp)  # 两个值直接写入block列表
                temp = [0, 0]  # 归零

        return block

    @staticmethod
    def block_fix(location, index_1, index_2):  # 按照错误的区块进行处理

        for i in range(len(location) - 2):
            if index_1 <= i <= index_2:
                location[i + 1][0], location[i + 1][1] = data_process.location_fix(location[i])

        return location
