import h5py
import os
from macro_new import *
input_paths = 'D:\\Dataset\\Random_Argument_Process\\DeepSketch'

input_trunks = os.listdir(input_paths)
commands_map = {'Line': 0, 'Arc': 0, 'Circle': 0, 'Spline': 0, 'SCP': 0, 'SOL': 0, 'Extrude': 0, 'Revolve': 0, 'Pocket': 0, 'Groove': 0, 'Chamfer': 0, 'Fillet': 0, 'Shell': 0, 'Mirror': 0, 'Draft': 0, 'Hole': 0}

for trunk in input_trunks:
    # if not os.path.exists('C:\\Users\\45088\\Desktop\\WHU_dataset\\extrude21_100\\' + trunk):
    #     os.makedirs('C:\\Users\\45088\\Desktop\\WHU_dataset\\extrude21_100\\' + trunk)
    files = os.listdir(input_paths + '\\' + trunk)
    for file in files:
        macro_vec = h5py.File(input_paths + '\\' + trunk + '\\' + file, 'r')['vec'][:]
        for i in range(macro_vec.__len__()):
            if macro_vec[i][0] == LINE_IDX:
                commands_map['Line'] = commands_map['Line'] + 1
            elif macro_vec[i][0] == ARC_IDX:
                commands_map['Arc'] = commands_map['Arc'] + 1
            elif macro_vec[i][0] == CIRCLE_IDX:
                commands_map['Circle'] = commands_map['Circle'] + 1
            elif macro_vec[i][0] == SCP_IDX:
                commands_map['SCP'] = commands_map['SCP'] + 1
            elif macro_vec[i][0] == SPLINE_IDX:
                commands_map['Spline'] = commands_map['Spline'] + 1
            elif macro_vec[i][0] == EXT_IDX:
                commands_map['Extrude'] = commands_map['Extrude'] + 1
            elif macro_vec[i][0] == REV_IDX:
                commands_map['Revolve'] = commands_map['Revolve'] + 1
            elif macro_vec[i][0] == POCKET_IDX:
                commands_map['Pocket'] = commands_map['Pocket'] + 1
            # elif macro_vec[i][0] == GROOVE_IDX:
            #     commands_map['Groove'] = commands_map['Groove'] + 1
            elif macro_vec[i][0] == CHAMFER_IDX:
                commands_map['Chamfer'] = commands_map['Chamfer'] + 1
            elif macro_vec[i][0] == FILLET_IDX:
                commands_map['Fillet'] = commands_map['Fillet'] + 1
            elif macro_vec[i][0] == SHELL_IDX:
                commands_map['Shell'] = commands_map['Shell'] + 1
            elif macro_vec[i][0] == DRAFT_IDX:
                commands_map['Draft'] = commands_map['Draft'] + 1
            elif macro_vec[i][0] == MIRROR_IDX:
                commands_map['Mirror'] = commands_map['Mirror'] + 1
            elif macro_vec[i][0] == HOLE_IDX:
                commands_map['Hole'] = commands_map['Hole'] + 1
            elif macro_vec[i][0] == SOL_IDX:
                commands_map['SOL'] = commands_map['SOL'] + 1
        print(file, ': OK')
print(commands_map)

        # save_flag = True
        # for i in range(vec.shape[0]):
        #     for j in range(vec[i].shape[0]):
        #         if vec[i][j] > 256 or vec[i][j] < -1:
        #             save_flag = False
        #         if vec[i][j] == 256:
        #             vec[i][j] = 255
        # if not save_flag:
        #     continue
        # if vec.shape[0] <= 100:
        #     with h5py.File("C:\\Users\\45088\\Desktop\\WHU_dataset\\extrude21_100\\" + trunk + '\\' + file) as f:
        #         f['vec'] = vec
