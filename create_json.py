import json
import os
import numpy as np
input_path = './vec_data/vec_data_100'
out_path = 'train_val_test_split.json'

# 统计所有数据路径
files_paths = []

trunks = os.listdir(input_path)
for trunk in trunks:
    files = os.listdir(input_path + '/' + trunk)
    for file in files:
        files_paths.append(trunk + '/' + file)

train_paths = []
test_paths = []
validation_paths = []

# 随机划分，按照训练：测试：验证 = 18：1：1的比例
for path in files_paths:
    ran = np.random.rand()
    if ran < 0.9:
        train_paths.append(path)
rest_paths = list(set(files_paths) - set(train_paths))
for path in rest_paths:
    ran = np.random.rand()
    if ran < 0.5:
        test_paths.append(path)
validation_paths = list(set(rest_paths) - set(test_paths))

json_dict = {
    'train': train_paths,
    'test': test_paths,
    'validation': validation_paths
}

# 写入json
with open(out_path, 'w') as json_file:
    json_file.write(json.dumps(json_dict))
