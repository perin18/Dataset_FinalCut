import os
import h5py
import numpy as np

from macro_new import *
input_path = 'D:/Dataset/Random_Argument_Final'
output_path = 'D:/Dataset/Random_Argument_Process/Random_Argument_Remove_Draft_Hole'

trunk_list = os.listdir(input_path)

for trunk in trunk_list:
    file_list = os.listdir(os.path.join(input_path, trunk))
    if not os.path.exists(os.path.join(output_path, trunk)):
        os.makedirs(os.path.join(output_path, trunk))
    for file in file_list:
        file_path = os.path.join(input_path, trunk, file)
        output_file_path = os.path.join(output_path, trunk, file)
        macro_vec = h5py.File(file_path, 'r')['vec'][:]
        # 移除Draft和Hole
        i = 0
        while i < len(macro_vec):
            if macro_vec[i][0] == DRAFT_IDX:
                j = i - 1
                count = 0
                while j >= 0:
                    if macro_vec[j][0] == TOPO_IDX:
                        count += 1
                        if count >= 2:
                            break
                        else:
                            j -= 1
                    else:
                        j -= 1
                macro_vec = np.concatenate([macro_vec[:j], macro_vec[i + 1:]])
                i = j - 1
            elif macro_vec[i][0] == HOLE_IDX:
                j = i - 1
                while j >= 0:
                    if macro_vec[j][0] == TOPO_IDX:
                        break
                    j -= 1
                macro_vec = np.concatenate([macro_vec[:j], macro_vec[i + 1:]])
                i = j - 1
            elif macro_vec[i][0] == SELECT_IDX and macro_vec[i][-3] == BODY_TYPE.index('Hole'):
                j = i - 1
                while j >= 0:
                    if macro_vec[j][0] == TOPO_IDX:
                        break
                    j -= 1
                while i < len(macro_vec):
                    if macro_vec[i][0] != SELECT_IDX:
                        break
                    i += 1
                macro_vec = np.concatenate([macro_vec[:j], macro_vec[i + 1:]])
                i = j - 1
            i += 1


        with h5py.File(output_file_path) as f:
            f['vec'] = macro_vec
        print(file_path, 'OK')



