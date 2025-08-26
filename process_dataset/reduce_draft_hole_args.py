import os
import h5py
import numpy as np

from macro_new import *
input_path = 'D:/Dataset/Random_Argument_Final'
output_path = 'D:/Dataset/Random_Argument_Process/reduce_draft_hole_args'

trunk_list = os.listdir(input_path)

for trunk in trunk_list:
    file_list = os.listdir(os.path.join(input_path, trunk))
    if not os.path.exists(os.path.join(output_path, trunk)):
        os.makedirs(os.path.join(output_path, trunk))
    for file in file_list:
        file_path = os.path.join(input_path, trunk, file)
        output_file_path = os.path.join(output_path, trunk, file)
        macro_vec = h5py.File(file_path, 'r')['vec'][:]

        i = 0
        while i < len(macro_vec):
            if macro_vec[i][0] == DRAFT_IDX:
                range = round((macro_vec[i][25] - 128) / 64 * 35.5)
                if range > 0:
                    macro_vec[i][25] = 128 + 7 + range
                else:
                    macro_vec[i][25] = 128 - 7 + range
            elif macro_vec[i][0] == HOLE_IDX:
                macro_vec[i][1] = round((macro_vec[i][1] + 128) / 2)
                macro_vec[i][2] = round((macro_vec[i][2] + 128) / 2)
            i += 1
        with h5py.File(output_file_path) as f:
            f['vec'] = macro_vec
        print(file_path, 'OK')



