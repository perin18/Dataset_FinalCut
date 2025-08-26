import h5py
import os

import numpy

from macro_new import *
input_paths = 'D:\\Dataset\\Ours'
# input_paths = 'C:\\Users\\45088\\Desktop\\WHU_dataset\\random_32\\fuse'
input_trunks = os.listdir(input_paths)
count_map = {}

count = 0
for trunk in input_trunks:
    # if not os.path.exists('C:\\Users\\45088\\Desktop\\WHU_dataset\\extrude21_100\\' + trunk):
    #     os.makedirs('C:\\Users\\45088\\Desktop\\WHU_dataset\\extrude21_100\\' + trunk)
    files = os.listdir(input_paths + '\\' + trunk)
    for file in files:
        count = count + 1
        macro_vec = h5py.File(input_paths + '\\' + trunk + '\\' + file, 'r')['vec'][:]
        vec_length = len(macro_vec)
        if (vec_length - (vec_length % 10)) / 10 not in count_map.keys():
            count_map[(vec_length - (vec_length % 10)) / 10] = 1
        else:
            count_map[(vec_length - (vec_length % 10)) / 10] += 1
        if vec_length >= 100:
            print()


        print(file, ': ', count_map)
for key in count_map.keys():
    count_map[key] = round(count_map[key] / count, 4)
print(file, ': ', count_map)

# 绘制直方图
