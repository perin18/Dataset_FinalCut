import glob
import json
import os

from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
import win32com.client
import h5py

check_point = 0
input_paths = 'D:\\Dataset\\PFDataset'
out_path = 'C:\\Users\\45088\\Desktop\\WHU_dataset\\vec_data'
input_trunks = os.listdir(input_paths)

for input_trunk in input_trunks:
    files_path = os.listdir(input_paths + '\\' + input_trunk)
    output_path = out_path + '\\' + input_trunk
    output_path_100 = out_path + '\\vec_data_100\\' + input_trunk
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if not os.path.exists(output_path_100):
        os.makedirs(output_path_100)
    for cur_file in files_path:
        catia = win32com.client.Dispatch('catia.application')
        catia.visible = 1
        doc = catia.documents.add('Part')
        try:
            save_flag = True
            macro_vec = process_on(input_paths + '\\' + input_trunk + '\\' + cur_file, catia, doc, remove_bug=True,
                                   just_test=False)
            if macro_vec is None:
                print(cur_file, ":None")
                continue
            print(cur_file, ":OK")

            # 判断向量值是否越界
            for i in range(macro_vec.__len__()):
                for j in range(macro_vec[i].__len__()):
                    if macro_vec[i][j] > ARGS_N or macro_vec[i][j] < -1:
                        save_flag = False
                    if macro_vec[i][j] == ARGS_N:
                        macro_vec[i][j] = ARGS_N - 1

            # 保存向量
            if save_flag:
                with h5py.File(output_path + '\\' + cur_file + '.h5') as f:
                    f['vec'] = macro_vec
                # 若长度低于100，再单独保存一次
                if macro_vec.shape[0] <= 100:
                    with h5py.File(output_path_100 + '\\' + cur_file + '.h5') as f:
                        f['vec'] = macro_vec
        except:
            print(cur_file, ":Failed")
            doc.close()