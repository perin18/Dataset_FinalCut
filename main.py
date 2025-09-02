import copy
import glob
import json
import os

import numpy as np

from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
import win32com.client

flag_test = True

if flag_test:
    input_path = 'C:\\Users\\lenovo\\Desktop\\CG\\macro\\cat'
else:
    input_path = 'D:\\Dataset\\PFDataset\\Whu_0088_MAC_v00\\00883106'

catia = win32com.client.Dispatch('catia.application')
catia.visible = 1
doc = catia.documents.add('Part')
process_on(input_path, catia, doc, remove_bug=False, just_test=True, macro_test=True)
