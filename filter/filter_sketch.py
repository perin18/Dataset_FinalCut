import glob

from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
import win32com.client
import h5py
import os
import glob

file_count = 0

doc = None
in_path = 'D:\\Dataset\\Random_Argument_Process\\only_sketch_argu\\0000'
# in_path = 'D:\\Dataset\\Random_Argument_Process\\only_sketch_argu_generation'
out_path = 'D:\\Dataset\\Random_Argument_Process\\only_sketch_argu_filter'

input_paths = os.listdir(in_path)
for input_path in input_paths:
    doc = None
    catia = win32com.client.Dispatch('catia.application')
    catia.visible = 1
    file_count = file_count + 1
    if file_count < 0:
        continue
    f = h5py.File(in_path + '\\' + input_path, 'r')
    try:
        if 'out_vec' in f.keys():
            macro_vec = f['out_vec'][:]
        else:
            macro_vec = f['vec'][:]

        cad = Macro_Seq.from_vector(macro_vec, is_numerical=True, n=256)

        # 计算草图线段总数，并判断是否包含spline
        curve_sum = 0
        spline_flag = False
        for op in cad.extrude_operation:
            for loop in op.sketch_profile.children:
                curve_sum += len(loop.children)
                if not spline_flag:
                    for curve in loop.children:
                        if isinstance(curve, Spline):
                            spline_flag = True
                            break
        # 过滤
        # 长度低于限制的过滤掉
        if spline_flag:
            if curve_sum < 5:
                continue
            elif curve_sum < 10:
                file_name = out_path + '\\with_spline\\' + '5_9\\' + input_path[:-3] + '.h5'
            elif curve_sum < 15:
                file_name = out_path + '\\with_spline\\' + '10_14\\' + input_path[:-3] + '.h5'
            elif curve_sum < 20:
                file_name = out_path + '\\with_spline\\' + '15_19\\' + input_path[:-3] + '.h5'
            else:
                file_name = out_path + '\\with_spline\\' + '20\\' + input_path[:-3] + '.h5'
        else:
            if curve_sum < 5:
                continue
            elif curve_sum < 10:
                file_name = out_path + '\\without_spline\\' + '5_9\\' + input_path[:-3] + '.h5'
            elif curve_sum < 15:
                file_name = out_path + '\\without_spline\\' + '10_14\\' + input_path[:-3] + '.h5'
            elif curve_sum < 20:
                file_name = out_path + '\\without_spline\\' + '15_19\\' + input_path[:-3] + '.h5'
            else:
                file_name = out_path + '\\without_spline\\' + '20\\' + input_path[:-3] + '.h5'

        doc = catia.documents.add('Part')
        part = doc.part
        create_CAD_CATIA(cad, catia, doc, part, only_sketch=True)
        # 没有问题则记录名字
        print(file_count, ': ', input_path, 'OK')
        with h5py.File(file_name) as f:
            f['vec'] = macro_vec
        doc.close()
    except:
        print(file_count, ': ', input_path, 'Error')
        if not doc is None:
            doc.close()
