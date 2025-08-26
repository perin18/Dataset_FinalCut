import h5py
import os
from copy import deepcopy
import numpy as np
from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
import win32com.client

import macro_21
import macro_new

input_paths = 'C:\\Users\\45088\\Desktop\\WHU_dataset\\random_argu'
output_paths = 'C:\\Users\\45088\\Desktop\\WHU_dataset\\random_32\\new'

input_trunks = os.listdir(input_paths)

file_count = 0

for trunk in input_trunks:
    if not os.path.exists(output_paths + '\\' + trunk):
        os.makedirs(output_paths + '\\' + trunk)
    files = os.listdir(input_paths + '\\' + trunk)
    for file in files:
        file_count = file_count + 1
        if file_count >= 79:
            continue
        macro_vec = h5py.File(input_paths + '\\' + trunk + '\\' + file, 'r')['vec'][:]
        new_vec = -np.ones([len(macro_vec), 33])

        for v in range(len(macro_vec)):
            if macro_vec[v][0] == macro_21.LINE_IDX or macro_vec[v][0] == macro_21.ARC_IDX or macro_vec[v][0] == macro_21.CIRCLE_IDX:
                new_vec[v][:1 + macro_21.N_ARGS_SKETCH] = macro_vec[v][:1 + macro_21.N_ARGS_SKETCH]
            elif macro_vec[v][0] == macro_21.EXT_IDX:
                new_vec[v][0] = macro_new.EXT_IDX
                new_vec[v][1 + macro_21.N_ARGS_SKETCH:1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS] = macro_vec[v][1 + macro_21.N_ARGS_SKETCH:1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS]
                length1 = macro_vec[v][1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS]
                length2 = macro_vec[v][1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS + 1]
                extent_type = macro_vec[v][1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS + 3]
                if extent_type == 0:
                    length2 = 128
                elif extent_type == 1:
                    length2 = length1
                if length1 == 128 and length2 == 128:
                    continue
                boolean_type = macro_vec[v][1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS + 2]
                if boolean_type > 0:
                    boolean_type = boolean_type - 1
                new_vec[v][13] = length1
                new_vec[v][14] = length2
                new_vec[v][15] = 0
                new_vec[v][16] = 0
                new_vec[v][19] = boolean_type
            elif macro_vec[v][0] == macro_21.REV_IDX:
                new_vec[v][0] = macro_new.REV_IDX
                new_vec[v][1 + macro_21.N_ARGS_SKETCH:1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS] = macro_vec[v][1 + macro_21.N_ARGS_SKETCH:1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS]
                angle1 = macro_vec[v][1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS]
                angle2 = macro_vec[v][1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS + 1]
                revolve_type = macro_vec[v][1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS + 3]
                boolean_type = macro_vec[v][1 + macro_21.N_ARGS_SKETCH + macro_21.N_ARGS_PLANE + macro_21.N_ARGS_TRANS + 2]
                if boolean_type > 0:
                    boolean_type = boolean_type - 1
                if revolve_type == 0:
                    angle1 = 255
                    angle2 = 128
                elif revolve_type == 1:
                    angle1 = round(angle1 / 256.0 * 255.0)
                    angle2 = round(angle2 / 256.0 * 255.0)
                if angle1 == 128 and angle2 == 128:
                    continue
                new_vec[v][16] = angle1
                new_vec[v][17] = angle2
                new_vec[v][18] = boolean_type
            elif macro_vec[v][0] == macro_21.CHAMFER_IDX:
                new_vec[v][0] = macro_new.CHAMFER_IDX
                new_vec[v][22] = macro_vec[v][13]
                new_vec[v][23] = macro_vec[v][14]
            elif macro_vec[v][0] == macro_21.SHELL_IDX:
                new_vec[v][0] = macro_new.SHELL_IDX
                new_vec[v][20] = macro_vec[v][13]
                new_vec[v][21] = macro_vec[v][14]
                if np.random.random() < 0.5:
                    new_vec[v][21] = 128
            elif macro_vec[v][0] == macro_21.FILLET_IDX:
                new_vec[v][0] = macro_new.FILLET_IDX
                new_vec[v][24] = macro_vec[v][5]
            elif macro_vec[v][0] == macro_21.SELECT_IDX:
                new_vec[v][0] = macro_new.SELECT_IDX
                new_vec[v][-2:] = macro_vec[v][-2:]
                new_vec[v][-4] = macro_new.SELECT_TYPE.index(macro_21.SELECT_TYPE[macro_vec[v][-4]])
                new_vec[v][-3] = macro_new.BODY_TYPE.index(macro_21.BODY_TYPE[macro_vec[v][-3]])
            elif macro_vec[v][0] == macro_21.TOPO_IDX:
                new_vec[v][0] = macro_new.TOPO_IDX
            elif macro_vec[v][0] == macro_21.MIRROR_IDX:
                new_vec[v][0] = macro_new.MIRROR_IDX
            elif macro_vec[v][0] == macro_21.SOL_IDX:
                new_vec[v][0] = macro_new.SOL_IDX
            elif macro_vec[v][0] == macro_21.EOS_IDX:
                new_vec[v][0] = macro_new.EOS_IDX

        # 删除所有TOPO上面的SOL
        final_vec = []
        for i in range(len(new_vec)):
            if new_vec[i][0] == macro_new.SOL_IDX and new_vec[i+1][0] == macro_new.TOPO_IDX:
                continue
            else:
                final_vec.append(new_vec[i])
        final_vec = np.array(final_vec)
        with h5py.File(output_paths + '\\' + trunk + '\\' + file) as f:
            f['vec'] = final_vec
        print(file_count, ': ', file, ' OK')
        # try:
        #     catia = win32com.client.Dispatch('catia.application')
        #     catia.visible = 1
        #     doc = catia.documents.add('Part')
        #
        #     cad = Macro_Seq.from_vector(final_vec, is_numerical=True, n=ARGS_N)
        #     part = doc.part
        #     create_CAD_CATIA(cad, catia, doc, part, remove_bug=False)
        #     doc.close()
        #     with h5py.File(output_paths + '\\' + trunk + '\\' + file) as f:
        #         f['vec'] = final_vec
        #     print(file_count, ': ', file, ' OK')
        # except:
        #     print(file_count, ': ', file, ' Failed!')
        #     doc.close()
