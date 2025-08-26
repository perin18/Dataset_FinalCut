import h5py
import os
from copy import deepcopy
import numpy as np
from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
import win32com.client

import macro
import macro_new

input_paths = 'D:\\Dataset\\cad_vec'
output_paths = 'D:\\Dataset\\DeepCAD_data_32'

input_trunks = os.listdir(input_paths)

file_count = 0

for trunk in input_trunks:
    if not os.path.exists(output_paths + '\\' + trunk):
        os.makedirs(output_paths + '\\' + trunk)
    files = os.listdir(input_paths + '\\' + trunk)
    for file in files:
        file_count = file_count + 1
        # if file_count >= 79:
        #     continue
        macro_vec = h5py.File(input_paths + '\\' + trunk + '\\' + file, 'r')['vec'][:]
        new_vec = -np.ones([len(macro_vec), 33])

        for v in range(len(macro_vec)):
            if macro_vec[v][0] == macro.LINE_IDX or macro_vec[v][0] == macro.ARC_IDX or macro_vec[v][0] == macro.CIRCLE_IDX:
                new_vec[v][:1 + macro.N_ARGS_SKETCH] = macro_vec[v][:1 + macro.N_ARGS_SKETCH]
            elif macro_vec[v][0] == macro.EXT_IDX:
                new_vec[v][0] = macro_new.EXT_IDX
                new_vec[v][1 + macro.N_ARGS_SKETCH:1 + macro.N_ARGS_SKETCH + macro.N_ARGS_PLANE + macro.N_ARGS_TRANS] = macro_vec[v][1 + macro.N_ARGS_SKETCH:1 + macro.N_ARGS_SKETCH + macro.N_ARGS_PLANE + macro.N_ARGS_TRANS]
                length1 = macro_vec[v][1 + macro.N_ARGS_SKETCH + macro.N_ARGS_PLANE + macro.N_ARGS_TRANS]
                length2 = macro_vec[v][1 + macro.N_ARGS_SKETCH + macro.N_ARGS_PLANE + macro.N_ARGS_TRANS + 1]
                extent_type = macro_vec[v][1 + macro.N_ARGS_SKETCH + macro.N_ARGS_PLANE + macro.N_ARGS_TRANS + 3]
                if extent_type == 0:
                    length2 = 128
                elif extent_type == 1:
                    length2 = length1
                if length1 == 128 and length2 == 128:
                    continue
                boolean_type = macro_vec[v][1 + macro.N_ARGS_SKETCH + macro.N_ARGS_PLANE + macro.N_ARGS_TRANS + 2]
                if boolean_type > 0:
                    boolean_type = boolean_type - 1
                new_vec[v][13] = length1
                new_vec[v][14] = length2
                new_vec[v][15] = 0
                new_vec[v][16] = 0
                new_vec[v][19] = boolean_type
            elif macro_vec[v][0] == macro.SOL_IDX:
                new_vec[v][0] = macro_new.SOL_IDX
            elif macro_vec[v][0] == macro.EOS_IDX:
                new_vec[v][0] = macro_new.EOS_IDX


        new_vec = np.array(new_vec)
        with h5py.File(output_paths + '\\' + trunk + '\\' + file) as f:
            f['vec'] = new_vec
        print(file_count, ': ', file, ' OK')
        # try:
        #     catia = win32com.client.Dispatch('catia.application')
        #     catia.visible = 1
        #     doc = catia.documents.add('Part')
        #
        #     cad = Macro_Seq.from_vector(new_vec, is_numerical=True, n=ARGS_N)
        #     part = doc.part
        #     create_CAD_CATIA(cad, catia, doc, part, remove_bug=False)
        #     doc.close()
        #     # with h5py.File(output_paths + '\\' + trunk + '\\' + file) as f:
        #     #     f['vec'] = new_vec
        #     print(file_count, ': ', file, ' OK')
        # except:
        #     print(file_count, ': ', file, ' Failed!')
        #     doc.close()
