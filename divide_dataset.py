import glob
import os
import random
import numpy as np
import json
import h5py

input_path = 'D:\\Dataset\\Random_Argument_Final'

file_list = []
file_list_for_train = []
file_list_for_test = []
file_list_for_val = []

count_map = {}

trucks = sorted(os.listdir(input_path))
for truck in trucks:
    file_list = file_list + sorted(glob.glob(os.path.join(input_path + '/' + truck, "*.h5")))

# 过滤长度大于300的数据
for file in file_list:
    print(file)
    f_vec = h5py.File(file, 'r')
    f_vec = f_vec['vec'][:]
    if f_vec.shape[0] > 100:
        file_list.remove(file)

# # 统计数据长度
# for file in file_list:
#     f_vec = h5py.File(file, 'r')
#     f_vec = f_vec['vec'][:]
#     if not f_vec.shape[0] in count_map.keys():
#         count_map[f_vec.shape[0]] = 1
#     else:
#         count_map[f_vec.shape[0]] = count_map[f_vec.shape[0]] + 1
#
# tmp_count = 0
# for key in count_map.keys():
#     if key > 100:
#         tmp_count = tmp_count + count_map[key]
# 按0.9概率加入train
for i in file_list:
    chance = np.random.uniform(0, 1)
    if chance < 0.9:
        file_list_for_train.append(i)
file_list = list(set(file_list) - set(file_list_for_train))
# 将剩余按0.5概率加入test
for i in file_list:
    chance = np.random.uniform(0, 1)
    if chance < 0.5:
        file_list_for_test.append(i)
file_list_for_val = list(set(file_list) - set(file_list_for_test))

# 打乱顺序
random.shuffle(file_list_for_train)
random.shuffle(file_list_for_test)
random.shuffle(file_list_for_val)

train_val_test_split = {
    'train': file_list_for_train,
    'test': file_list_for_test,
    'validation': file_list_for_val
}

with open('./vec_data/train_val_test_split.json', 'w') as fp:
    json.dump(train_val_test_split, fp, indent=1)