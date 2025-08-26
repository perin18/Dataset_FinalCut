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

in_path = 'D:\\Dataset\\Random_Argument_Process\\only_sketch_macro\\0010_macro'
out_path = 'C:\\Users\\45088\\Desktop\\Fusion_generation'

input_paths = os.listdir(in_path)
for input_path in input_paths:
    file_count = file_count + 1
    # if file_count < 100:
    #     continue
    # if input_path != '00000071.h5':
    #     continue
    doc = None
    catia = win32com.client.Dispatch('catia.application')
    catia.visible = 1

    f = h5py.File(in_path + '\\' + input_path, 'r')
    try:
        if 'out_vec' in f.keys():
            macro_vec = f['out_vec'][:]
        else:
            macro_vec = f['vec'][:]

        cad = Macro_Seq.from_vector(macro_vec, is_numerical=True, n=256)

        doc = catia.documents.add('Part')
        part = doc.part
        create_CAD_CATIA(cad, catia, doc, part, only_sketch=True)
        # 没有问题则记录名字
        print(file_count, ': ', input_path, 'OK')
        partDocument1 = catia.ActiveDocument
        file_name = out_path + '\\' + input_path[:-3] + '.CATPart'
        # partDocument1.SaveAs(file_name)
        doc.close()
    except:
        print(file_count, ': ', input_path, 'Error')
        if not doc is None:
            doc.close()
