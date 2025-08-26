import os
import h5py
from macro_new import ARC_IDX, CIRCLE_IDX
input_path = 'D:/Dataset/Random_Argument_Final'
output_path = 'D:/Dataset/Random_Argument_Process/exchange_arc_circle'

trunk_list = os.listdir(input_path)

for trunk in trunk_list:
    file_list = os.listdir(os.path.join(input_path, trunk))
    if not os.path.exists(os.path.join(output_path, trunk)):
        os.makedirs(os.path.join(output_path, trunk))
    for file in file_list:
        file_path = os.path.join(input_path, trunk, file)
        output_file_path = os.path.join(output_path, trunk, file)
        macro_vec = h5py.File(file_path, 'r')['vec'][:]
        for i in range(len(macro_vec)):
            if macro_vec[i][0] == ARC_IDX:
                macro_vec[i][0] = CIRCLE_IDX
            elif macro_vec[i][0] == CIRCLE_IDX:
                macro_vec[i][0] = ARC_IDX

        with h5py.File(output_file_path) as f:
            f['vec'] = macro_vec
        print(file_path, 'OK')
