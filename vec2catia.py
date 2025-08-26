from Catia_utils import *
from CAD_Class import *
import win32com.client
import h5py

doc = None

input_path = 'D:\\Dataset\\DeepCAD_data_32\\0000\\00000061.h5'

f = h5py.File(input_path, 'r')
if len(f.keys()) > 1:
    macro_vec = f['out_vec'][:]
else:
    macro_vec = f['vec'][:]
try:
    cad = Macro_Seq.from_vector(macro_vec, is_numerical=True, n=256)
    catia = win32com.client.Dispatch('catia.application')
    catia.visible = 1
    doc = catia.documents.add('Part')
    part = doc.part
    create_CAD_CATIA(cad, catia, doc, part)
    print(input_path, ' OK')
except:
    print(input_path, ' Error')

