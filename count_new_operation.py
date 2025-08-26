import h5py
import os
from macro_new import *
from Catia_utils import *
input_paths = 'D:\\Dataset\\Random_Argument_Final'

input_trunks = os.listdir(input_paths)
new_count_map = {}

for trunk in input_trunks:
    files = os.listdir(input_paths + '\\' + trunk)
    for file in files:
        print(file)
        macro_vec = h5py.File(input_paths + '\\' + trunk + '\\' + file, 'r')['vec'][:]

        try:
            cad = Macro_Seq.from_vector(macro_vec, is_numerical=True, n=256)
        except:
            continue

        new_count = 0
        for i in cad.extrude_operation:
            if not isinstance(i, Extrude):
                new_count += 1

        if new_count not in new_count_map.keys():
            new_count_map[new_count] = 1
        else:
            new_count_map[new_count] += 1

print(new_count_map)

