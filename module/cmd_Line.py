# -*- encoding: utf-8 -*-

import sys

from module.data_io import data_io
from module.data_analysis import data_analysis
from module.data_preprocess import data_process
from module.data_convert import data_convert

_dir = sys.path[0]


class cmd_Line:

    @staticmethod
    def building():

        print("Building list...")
        L = data_io.get_csv_list(_dir)
        print(L)
        print("List is built.\nLoading data from list.")
        
        return L

    @staticmethod
    def analysis_line(L):

        choice = input('是否需要将数据处理结果输出至控制台？[Y/N]')
        if choice == 'Y' or choice == 'y':
            index = 1
        elif choice == 'N' or choice == 'n':
            index = 0

        try:
            with open(_dir + '\\' + 'dataset.csv', 'w', encoding='utf-8-sig') as dict_file:
                # csv 头名
                dict_file.write(u'文件名,车牌号,设备号,疲劳驾驶时间,疲劳驾驶次数,急加速累计时长,急加速累计次数,急减速累计时长,急减速累计次数,怠速预热累计时长,怠速预热累计次数,超长怠速累计时长,超长怠速累计次数,熄火滑行累计时长,熄火滑行累计次数,超速累计时长,超速累计次数,标准差,急变道次数\n')
                num = len(L)
                cur_num = 0
                for n in L:
                    cur_num += 1

                    _data = data_io.data_input(_dir, n).values.tolist()
                    if index == 1:
                        print('\n' + n + ':')
                        print('\t车牌号：%s\n\t设备号：%s\n' % (_data[0][0], _data[0][1]))
                    fixed_data = list(reversed(data_process.check(_data)))

                    # 分模块来进行处理，这可以使各个部分的数据处理独立，后期便于调整和方法复用
                    # 这一块因为时间紧，所以没有做多进程
                    swift_times = data_analysis.road_swift(fixed_data)
                    fatigue_driving, fatigue_times = data_analysis.fatigue_driving(fixed_data)
                    time_last_acc, time_last_dec, times_acc, times_dec = data_analysis.speed_change_analysis(fixed_data)
                    idle_heating, idle_count, long_tickover, long_count, flameout, flameout_count, speed, speed_count = data_analysis.static_analysis(fixed_data)
                    variance = data_analysis.stable_analysis(fixed_data)

                    if index == 1:
                        print('\t疲劳驾驶时间：%d秒\n\t疲劳驾驶次数：%d次' % (fatigue_driving, fatigue_times))
                        print('\n\t急加速累计时长：%d秒\n\t急加速累计次数：%d次\n\t急减速累计时长：%d秒\n\t急减速累计次数：%d次' % (time_last_acc, times_acc, time_last_dec, times_dec))
                        print('\n\t怠速预热累计时长：%d秒\n\t怠速预热累计次数：%d次\n\t超长怠速累计时长：%d秒\n\t超长怠速累计次数：%d次'% (idle_heating, idle_count, long_tickover, long_count))
                        print('\n\t熄火滑行累计时长：%d秒\n\t熄火滑行累计次数：%d次\n\t超速累计时长：%d秒\n\t超速累计次数：%d次' % (flameout, flameout_count, speed, speed_count))
                        print('\n\t标准差：%d\n\t急变道次数：%d' % (variance, swift_times))

                    # 数据写入 csv
                    dict_file.write('%s,%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n' % (n.split('.')[0], fixed_data[0][0], fixed_data[0][1], fatigue_driving, fatigue_times, time_last_acc, times_acc, time_last_dec, times_dec, idle_heating, idle_count, long_tickover, long_count, flameout, flameout_count, speed, speed_count, variance, swift_times))
                    print('The data of %s has been written.(%d/%d)' % (n, cur_num, num))
        except IOError as ioerr:
            print("文件 %s 无法创建，请检查数据文件位置。" % (_dir))

        print("\nDone.")

    @staticmethod
    def analysis_with_weather_line(L):

        all_num = len(L)
        cur_num = 0
        weather_data = []
        didian = []
        weather = []
        spd_lim = {'大雨': 90, '暴雨': 70, '浮尘': 0, '扬沙': 0, '大暴雨': 40, '雾': 100}
        spd_set = []
        default_spd = 100

        final = []

        for n in L:
            cur_num += 1
            print('%s started.' % n)

            _data = data_io.data_input(_dir, n).values.tolist()
            _data = list(reversed(data_process.check(_data)))  # 修正漂移经纬度
            for m in range(len(_data) - 1):
                _data[m + 1][4], _data[m + 1][3] = data_process.location_fix([_data[m][4], _data[m][3], _data[m][11], _data[m][2]])

            temp_data = data_io.data_input(_dir, 'climate.csv').values.tolist()

            for m in temp_data:  # 预处理天气数据
                weather_data.append([m[1], m[2], m[7], m[10]])

            # 以10分钟为间隔获取地点
            for m in range(len(_data)//600):
                loc = data_convert.wgs84_to_gcj02(_data[m * 600][3], _data[m * 600][4])
                city, district = data_analysis.get_location(loc)
                if [city, district] not in didian:

                    didian.append([str(city).replace('市', ''), str(district).replace('区', '').replace('县', '')])

            # 找出符合地理条件的天气和时间
            for m in weather_data:  # ['绍兴', '诸暨', '多云', '24/9/2018']
                for i in didian:
                    if i[0] == m[0] and i[1] == m[1]:
                            if [m[2], m[3], m[0], m[1]] not in weather:
                                weather.append([m[2], m[3], m[0], m[1]])  # ['晴', '30/7/2018', '抚州', '崇仁']

            # 检查找出每个日期对应的最小的速度值
            for m in range(len(weather) - 1):
                for i in spd_lim:
                    if i in weather[m][0]:
                        default_spd = min(default_spd, spd_lim.get(i))
                if weather[m][1] == weather[m + 1][1] and weather[m][2] == weather[m + 1][2] and weather[m][3] == weather[m + 1][3]:
                    continue
                else:
                    spd_set.append([weather[m][1], default_spd, weather[m][2], weather[m][3]])  # ['30/7/2018', 100, '南昌', '新建']
            export = [n.split('.')[0], _data[0][0], _data[0][1], data_analysis.speed_analysis(_data, spd_set, weather_data)]
            final.append(export)
            print(export)
            print('The data of %s was generated. (%d/%d)' % (n, cur_num, all_num))

        try:
            with open(_dir + '\\weather_dataset.csv', 'w') as dict_file:
                dict_file.write('文件名,车牌号,设备号,晴,小雨,中雨,大雨,暴雨,大暴雨,雾,超速次数')
                for m in final:
                    dict_file.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (
                    m[0], m[1], m[2], m[1][0], m[1][1], m[1][2], m[1][3], m[1][4], m[1][5], m[1][6], m[2],
                    m[11], m[12]))
        except IOError as ioerr:
            print("文件 %s 无法创建，请检查数据文件位置。" % _dir)

    print("\nDone.")

    @staticmethod
    def preprocess_line(L):

        for n in L:
            loc = []
            location = []

            _data = data_io.data_input(_dir, n).values.tolist()

            fixed_data = list(reversed(data_process.check(_data)))

            for m in range(len(fixed_data) - 1):
                location.append([fixed_data[m][4], fixed_data[m][3], fixed_data[m][11], fixed_data[m][2]])
                dis = data_analysis.distance([fixed_data[m][4], fixed_data[m][3]], [fixed_data[m + 1][4], fixed_data[m + 1][3]])
                if dis >= 0.3:  # 两点间距离大于定为差异大点，即错误点的开始或结束点
                    loc.append(m)

            block = data_process.block_g(loc)
            print(block)
            for i in block:
                data_process.block_fix(location, i[0], i[1])
            data_process.block_fix(location, 0, len(fixed_data))
            distance = []

            for k in location:
                distance.append([k[0], k[1]])
            data_io.map_g(_dir, distance, n, 'test', 'black')

    def info_extract_line(self):

        climate = []
        wind_direction = []
        level = []

        _data = data_io.data_input(_dir, 'climate.csv').values.tolist()
        for n in _data:
            if n[7] not in climate:
                climate.append(n[7])
            if n[3] not in wind_direction:
                wind_direction.append(n[3])
            if n[4] not in level:
                level.append(n[4])

        for m in climate:
            data_io.save_csv(_data, m, _dir + '\\weather', m)
        for i in wind_direction:
            data_io.save_csv(_data, i, _dir + '\\wind_direction', i)
        for j in level:
            k = j.replace('<', '小于').replace('～', '到')
            print(k)

            data_io.save_csv(_data, j, _dir, k)

    @staticmethod
    def means(L):

        speed = []
        means = []
        all_num = len(L)
        cur = 0

        for n in L:

            cur += 1
            _data = data_io.data_input(_dir, n).values.tolist()
            fixed_data = list(reversed(data_process.check(_data)))

            for m in fixed_data:
                if m[5] == 1:  # or n[11] != 0:
                    speed.append(m[11])
            means.append([n.split('.')[0], sum(speed) / len(speed)])
            speed = []
            print('%s is OK. (%d/%d)' % (n, cur, all_num))

        for n in means:
            print(n)

        print("\nDone.")
