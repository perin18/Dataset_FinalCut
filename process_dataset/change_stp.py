import os
import h5py
import numpy as np
from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
import win32com.client

from macro_new import *

input_path = 'D:/Dataset/Random_Argu_old/PFDataset_vec'
output_path = 'D:/Dataset/Random_Argu_old/PFDataset_stp'

bug_list = []

trunk_list = os.listdir(input_path)
count = 0
for trunk in trunk_list:
    if int(trunk) <= 72:
        continue

    file_list = os.listdir(os.path.join(input_path, trunk))
    if not os.path.exists(os.path.join(output_path, trunk)):
        os.makedirs(os.path.join(output_path, trunk))
    for file in file_list:
        count += 1
        # 2602
        if count <= 698:
            continue
        doc = None
        catia = win32com.client.Dispatch('catia.application')
        catia.visible = 1

        file_path = os.path.join(input_path, trunk, file)
        output_file_path = os.path.join(output_path, trunk, file)
        macro_vec = h5py.File(file_path, 'r')['vec'][:]

        try:
            cad = Macro_Seq.from_vector(macro_vec, is_numerical=True, n=256)

            doc = catia.documents.add('Part')
            part = doc.part
            create_CAD_CATIA(cad, catia, doc, part)

            doc.ExportData(os.path.join(output_path, trunk, file[:-3] + '.stp'), "stp")
            doc.close()
            print(count, file_path, 'OK')
        except:
            doc.close()
            bug_list.append(trunk + '/' + file)
            print(count, ': ', file, ' Failed')
            print('bug:', len(bug_list), bug_list)




