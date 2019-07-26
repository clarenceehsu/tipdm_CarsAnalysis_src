# -*- encoding: utf-8 -*-

import os
import pandas as pd
from folium import plugins
import folium


class data_io:

    @staticmethod
    def get_csv_list(_dir):  # 获取_dataset中csv文件目录

        csv_list = []
        _dir = _dir + '\\_dataset'
        for dir_path, dirname, filenames in os.walk(_dir):
            for filename in filenames:
                if '.csv' in os.path.split(filename)[-1]:
                    csv_list.append(os.path.join(filename))

        return csv_list
    
    @staticmethod
    def data_input(_dir, n):  # 输入数据，并用pandas读取csv文件

        _data = pd.read_csv(_dir + '\\_dataset\\' + n, low_memory=False)
            
        return _data

    @staticmethod
    def save(processed_location, n, filepath, name):  # 把获得的数据存储到csv中

        try:
            with open(filepath + '\\' + n.split('.')[0] + name + '.csv', 'w') as dict_file:
                while processed_location:
                    m = processed_location.pop()
                    dict_file.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12]))
        except IOError as ioerr:
            print("文件 %s 无法创建，请检查数据文件位置。" % filepath)

    @staticmethod
    def save_weather(filepath, final, _data, n):
        try:
            with open(filepath + '\\weather_dataset.csv', 'w') as dict_file:
                dict_file.write('文件名,车牌号,设备号,小雨,中雨,大雨,暴雨,大暴雨,雾,超速次数')
                for m in final:
                    dict_file.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (n.split('.')[0], _data[0][0], _data[0][1], m[0][3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12]))
        except IOError as ioerr:
            print("文件 %s 无法创建，请检查数据文件位置。" % filepath)

    @staticmethod
    def map_g(_dir, location, n, name, color):  # 生成运行轨迹地图

        m = folium.Map([28, 115], zoom_start=10)
        folium.PolyLine(
            location,
            weight=3,
            color=color,
            opacity=0.8
        ).add_to(m)
        m.save(os.path.join(_dir + '\\map', n + name + '.html'))

    @staticmethod
    def save_data(processed_location, n, filepath, name):  # 把获得的数据存储到csv中

        try:
            with open(filepath + '\\' + n.split('.')[0] + name + '.csv', 'w') as dict_file:
                while processed_location:
                    m = processed_location.pop()
                    dict_file.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12]))
        except IOError as ioerr:
            print("文件 %s 无法创建，请检查数据文件位置。" % filepath)

    @staticmethod
    def save_distance(distance, filepath, name):  # 把获得的数据存储到csv中

        try:
            with open(filepath + '\\' + name + '.csv', 'w') as dict_file:
                for m in distance:
                    dict_file.write('%s\n' % m)
        except IOError as ioerr:
            print("文件 %s 无法创建，请检查数据文件位置。" % filepath)

    @staticmethod
    def save_csv(processed_location, n, filepath, name):  # 把获得的数据存储到csv中

        try:
            with open(filepath + '\\' + name + '.csv', 'w', encoding='utf-8') as dict_file:
                for m in processed_location:
                    if n in m:
                        dict_file.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10]))
        except IOError as ioerr:
            print("文件 %s 无法创建，请检查数据文件位置。%s" % (filepath, n))