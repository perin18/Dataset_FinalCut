import glob

from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
import win32com.client
import h5py
import os
import glob
import trimesh
from trimesh.sample import sample_surface
import numpy as np
from plyfile import PlyData, PlyElement

def write_ply(points, filename, text=False):
    """ input: Nx3, write points to filename as PLY format. """
    points = [(points[i,0], points[i,1], points[i,2]) for i in range(points.shape[0])]
    vertex = np.array(points, dtype=[('x', 'f4'), ('y', 'f4'),('z', 'f4')])
    el = PlyElement.describe(vertex, 'vertex', comments=['vertices'])
    with open(filename, mode='wb') as f:
        PlyData([el], text=text).write(f)

# 给定向量，存储其点云形式
def process(catia, vec, save_path, file_count):
    catia.visible = 1

    cad = Macro_Seq.from_vector(vec, is_numerical=True, n=256)
    doc = catia.documents.add('Part')
    specsAndGeomWindow1 = catia.ActiveWindow
    part = doc.part
    try:
        create_CAD_CATIA(cad, catia, doc, part)
    except:
        specsAndGeomWindow1.close()
        doc.close()
        print(file_count, ' ', save_path, ": Failed")
        return
    partDocument1 = catia.ActiveDocument
    partDocument1.ExportData(save_path + ".stl", "stl")
    specsAndGeomWindow1.close()
    doc.close()
    out_mesh = trimesh.load(save_path + ".stl")
    os.system("rm " + save_path + ".stl")
    # 采样点原来为8096
    out_pc, _ = sample_surface(out_mesh, 8096)
    write_ply(out_pc, save_path + ".ply")
    os.remove(save_path + ".stl")
    print(file_count, ' ', save_path, ": OK")

file_count = 0
input_path = './valid_data/vec_data_100'
# 必须为绝对路径
output_path = 'C:/Users/45088/Desktop/WHU_dataset/pc'
input_trunks = os.listdir(input_path)
catia = win32com.client.Dispatch('catia.application')
for trunk in input_trunks:
    if not os.path.exists(output_path + '/' + trunk):
        os.makedirs(output_path + '/' + trunk)
    file_paths = os.listdir(input_path + '/' + trunk)
    for file_path in file_paths:
        file_count = file_count + 1
        vec = h5py.File(input_path + '/' + trunk + '/' + file_path, 'r')['vec'][:]
        file_name = file_path[:-3]
        process(catia, vec, output_path + '/' + trunk + '/' + file_name, file_count)
        print()