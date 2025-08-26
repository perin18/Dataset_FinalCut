import os
import json
import h5py
import numpy as np
import win32com.client
from Catia_utils import *

input_path = 'D:\\Dataset\\Fusion 360\\r1.0.1\\fusion360_json'
out_path = 'D:\\Dataset\\Fusion 360\\r1.0.1\\fusion360_vec'
out_path_100 = 'D:\\Dataset\\Fusion 360\\r1.0.1\\fusion360_vec\\100'
curve_type_map = {}


# 处理草图
def parse_sketch(op, profile_dic, entity_dic):
    # 因为草图curve不考虑z坐标，但有时候z坐标未必是0，但一定所有curve的z相同，此时记录该offset添加到origin中
    # 但添加时一定注意，添加方向是基于草图的z轴，也就是在normal方向上的z_offset
    z_offset = 0
    # 可能存在多个草图，逐个解析
    loop_list_final = []
    sketch_no = profile_dic['sketch']
    profile_no = profile_dic['profile']
    sketch = entity_dic[sketch_no]
    profile = sketch['profiles'][profile_no]
    # 此处将多个loop的curve_list分开保存了，但针对macro时是将其混合然后集中处理
    # 如何处理取决于start和end是否严格对应
    loop_list = []
    for loop in profile['loops']:
        curve_list = []
        for curve in loop['profile_curves']:
            if curve['type'] == 'Line3D':
                curve_list.append(Line(np.array([curve['start_point']['x'], curve['start_point']['y']]),
                                       np.array([curve['end_point']['x'], curve['end_point']['y']])))
                z_offset = curve['start_point']['z']
                if curve['start_point']['z'] != curve['end_point']['z']:
                    print('z不相同！')
            elif curve['type'] == 'Circle3D':
                curve_list.append(
                    Circle(np.array([curve['center_point']['x'], curve['center_point']['y']]), curve['radius']))
                z_offset = curve['center_point']['z']
            elif curve['type'] == 'Arc3D':
                center = np.array([curve['center_point']['x'], curve['center_point']['y']])
                radius = curve['radius']
                start_point = np.array([curve['start_point']['x'], curve['start_point']['y']])
                end_point = np.array([curve['end_point']['x'], curve['end_point']['y']])
                start_arc = vec2arc(start_point, center)
                end_arc = vec2arc(end_point, center)
                # 暂时默认逆时针
                if start_arc < end_arc:
                    mid_arc = (start_arc + end_arc) / 2
                else:
                    mid_arc = (start_arc + end_arc + 2 * np.pi) / 2
                curve_list.append(Arc(center, radius, start_arc, end_arc, mid_arc))
                z_offset = curve['start_point']['z']
                if curve['start_point']['z'] != curve['end_point']['z']:
                    print('z不相同！')
            # 如果有其他类型，跳过该loop
            else:
                print(curve['type'], 'not supported')
                return None
        loop_list.append(deepcopy(curve_list))

    # 解析草图，暂时默认start和end相对应
    # 首先将所有圆剔除出来，因为圆不需要组成loop

    for curves in loop_list:
        curve_list_final = []
        for loop_curve in curves:
            if isinstance(loop_curve, Circle):
                loop_list_final.append(Loop([loop_curve]))
            else:
                curve_list_final.append(loop_curve)
        if len(curve_list_final) > 0:
            loop_list_final.append(Loop(deepcopy(curve_list_final)))

    # 草图平面信息
    origin = np.array([sketch['transform']['origin']['x'], sketch['transform']['origin']['y'],
                       sketch['transform']['origin']['z']])
    x_axis = np.array([sketch['transform']['x_axis']['x'], sketch['transform']['x_axis']['y'],
                       sketch['transform']['x_axis']['z']])
    y_axis = np.array([sketch['transform']['y_axis']['x'], sketch['transform']['y_axis']['y'],
                       sketch['transform']['y_axis']['z']])
    z_axis = np.array([sketch['transform']['z_axis']['x'], sketch['transform']['z_axis']['y'],
                       sketch['transform']['z_axis']['z']])
    # 处理normal方向上的偏移
    origin = origin + z_offset * z_axis / np.linalg.norm(z_axis)
    theta, phi, gamma = polar_parameterization(z_axis, x_axis)
    sketch_plane = CoordSystem(origin, theta, phi, gamma, y_axis=cartesian2polar(y_axis))

    sketch_profile = Profile(loop_list_final)
    point = sketch_profile.start_point
    sketch_pos = point[0] * sketch_plane.x_axis + point[1] * sketch_plane.y_axis + sketch_plane.origin
    sketch_size = sketch_profile.bbox_size
    sketch_profile.normalize(size=ARGS_N)
    op.sketch_plane = sketch_plane
    op.sketch_pos = sketch_pos
    op.sketch_size = sketch_size
    op.sketch_profile = sketch_profile
    return deepcopy(op)

file_count = 0
input_paths = os.listdir(input_path)
for file_path in input_paths:
    file_count = file_count + 1
    # if file_count <= 94:
    #     continue
    # if file_path != '100229_aa33a237_0002.json':
    #     continue
    operation_list = []
    with open(os.path.join(input_path, file_path), 'r', encoding='utf-8') as fp:
        data_json = json.load(fp)
    bounding_box = {
        'X_max': data_json['properties']['bounding_box']['max_point']['x'],
        'Y_max': data_json['properties']['bounding_box']['max_point']['y'],
        'Z_max': data_json['properties']['bounding_box']['max_point']['z'],
        'X_min': data_json['properties']['bounding_box']['min_point']['x'],
        'Y_min': data_json['properties']['bounding_box']['min_point']['y'],
        'Z_min': data_json['properties']['bounding_box']['min_point']['z']
    }
    x_size = float(bounding_box['X_max']) - float(bounding_box['X_min'])
    y_size = float(bounding_box['Y_max']) - float(bounding_box['Y_min'])
    z_size = float(bounding_box['Z_max']) - float(bounding_box['Z_min'])

    bounding_size = max(max(x_size, y_size), z_size)

    # 记录timeline中的每个实体，并一一去entities中寻找
    timeline_dic = data_json['timeline']
    entity_dic = data_json['entities']
    for oper in timeline_dic:
        entity_no = oper['entity']
        entity = entity_dic[entity_no]
        # 先寻找extrude，对于extrude中有的草图才去解析，有可能存在没有拉伸的草图，直接舍弃
        if entity['type'] == 'ExtrudeFeature':
            profile_list = entity['profiles']
            boolean_type = entity['operation']
            if boolean_type != "CutFeatureOperation" and boolean_type != "IntersectFeatureOperation":
                boolean_type = "AddFeatureOperation"
            extent_type = entity['extent_type']
            extent_one = entity['extent_one']['distance']['value']
            extent_two = 0
            if extent_type == 'SymmetricFeatureExtentType':
                extent_two = extent_one
            elif extent_type == 'OneSideFeatureExtentType':
                extent_two = 0
            else:
                extent_two = entity['extent_two']['distance']['value']
            for profile in profile_list:
                extrude = None
                extrude = Extrude(extent_one, extent_two, False, False, boolean_type, "OffsetLimit", "OffsetLimit", '')
                extrude = parse_sketch(extrude, profile, entity_dic)
                if extrude is None:
                    print(file_count, ':', file_path, ' Skip')
                    continue
                else:
                    operation_list.append(deepcopy(extrude))
    if len(operation_list) == 0:
        continue
    macro_seq = Macro_Seq(operation_list, bounding_size)
    macro_seq.normalize()
    macro_seq.numericalize(n=ARGS_N)
    macro_vec = macro_seq.to_vector(MAX_N_EXT, MAX_N_LOOPS, MAX_N_CURVES, MAX_TOTAL_LEN, pad=False)
    ##################################################################################################
    cad = Macro_Seq.from_vector(macro_vec, is_numerical=True, n=ARGS_N)

    catia = win32com.client.Dispatch('catia.application')
    catia.visible = 1
    doc = catia.documents.add('Part')

    part = doc.part
    try:
        create_CAD_CATIA(cad, catia, doc, part, remove_bug=False)
        print(file_count, ':', file_path, ' OK')
        doc.close()
        with h5py.File(out_path + '\\' + file_path[:-5] + '.h5') as f:
            f['vec'] = macro_vec
            # 若长度低于100，再单独保存一次
            if macro_vec.shape[0] <= 100:
                with h5py.File(out_path_100 + '\\' + file_path[:-5] + '.h5') as f:
                    f['vec'] = macro_vec
    except:
        print(file_count, ':', file_path, ' Error')
        doc.close()