import numpy as np

from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
import win32com.client
import h5py
import time

INPUT_PATH = 'D:\\Dataset\\DeepCAD_data_32'
SAVE_PATH = 'D:\\Dataset\\Random_Argument_Final'

SPLINE_RESTRICTION = 0.25
REVOLVE_RESTRICTION = 0.4
REVOLVE_FULL_RESTRICTION = 0.7
OPERATION_EXCEPTION = 2
TWICE_EXCEPTION = 1
SHELL_IT_RESTRICTION = 0.7
CHAMFER_EQUAL_RESTRICTION = 0.5
HOLE_RESTRICTION = 0.5
HOLE_TYPE_RESTRICTION = {'Offset': 1.0 / 3, 'UpToNext': 1}
FACE_RANDOM_MAP = {'Shell': 0.25, 'Chamfer': 0.5, 'Fillet': 0.75, 'Mirror': 1}
EDGE_RANDOM_MAP = {'Chamfer': 1.0 / 3, 'Fillet': 2.0 / 3, 'Draft': 1}
NEW_OPERATION_RESTRICTION = 2

REMOVE_BUG = True

def face_equal(a, b):
    if a.shape[0] == b.shape[0] and a.shape[1] == b.shape[1]:
        if np.allclose(a, b):
            return True
    return False

# 判断是否为曲面
def judge_surface(vec, topo, is_extrude):
    # 若为旋转且不为上下面，直接跳过
    if not is_extrude:
        if topo[-1][-1] == 0:
            return True
    # 若为拉伸，记录Line的wire_no，核对topo是否为平面
    line_index_list = []
    wire_no = 0
    for one_vec in vec:
        if one_vec[0] == LINE_IDX or one_vec[0] == ARC_IDX or one_vec[0] == CIRCLE_IDX or one_vec[0] == SPLINE_IDX:
            wire_no += 1
        if one_vec[0] == LINE_IDX:
            line_index_list.append(wire_no)

    # 若出现wire的no不在line list里则说明非平面
    for one_vec in topo:
        if one_vec[-4] == SELECT_TYPE.index('Wire') and one_vec[-1] not in line_index_list:
            return True
    return False

def get_min_sketch_length(vec):
    # 获得草图集合，未必是一个
    # 首先按SOL分组，若不为圆，计算其边长
    min_scale = 256
    last_position = None
    start_position = None
    for i in vec:
        if i[0] == SOL_IDX:
            if start_position is not None and last_position is not None:
                distance = np.sqrt(np.sum(np.power(start_position - last_position, 2)))
                min_scale = min(min_scale, distance)
            start_position = None
            last_position = None
        elif i[0] == CIRCLE_IDX:
            min_scale = min(min_scale, i[5] * 2)
        elif i[0] == LINE_IDX or i[0] == ARC_IDX or i[0] == SCP_IDX:
            if start_position is None:
                start_position = i[1:3]
            if last_position is None:
                last_position = i[1:3]
            else:
                distance = np.sqrt(np.sum(np.power(i[1:3] - last_position, 2)))
                min_scale = min(min_scale, distance)
                last_position = i[1:3]
        elif i[0] == EXT_IDX or i[0] == REV_IDX or i[0] == SPLINE_IDX:
            continue
        else:
            print('get_min_sketch_length: not a curve')
    return min_scale

# 获得body的限制尺寸
def get_max_scale(vec):
    # 计算草图各边边长，替换max_scale
    max_scale = 256
    min_length = get_min_sketch_length(vec)
    if max_scale > min_length:
        max_scale = min_length
    # 计算拉伸长度，替换max_scale
    if max_scale > np.abs((vec[-1][1 + N_ARGS_SKETCH + N_ARGS_PLANE + N_ARGS_TRANS] - 128) + (vec[-1][1 + N_ARGS_SKETCH + N_ARGS_PLANE + N_ARGS_TRANS + 1] - 128)):
        max_scale = np.abs((vec[-1][13] - 128) + (vec[-1][14] - 128))
    return max_scale


def get_probability_flag(limitation):
    return np.random.rand() < limitation

# 获得正态分布的操作参数,最小为1
# 使用标准差×3的方式，让数值尽量在loc±scale以内
def get_scale_n(loc, scale):
    return np.clip(np.round(np.random.normal(loc, scale / 3)), loc - scale + 1, loc + scale)

def get_uniform(begin, end):
    return np.random.randint(begin, end)

def get_topo_vec_list(vec, operation_map):
    # 记录拓扑元素对应的选取数组
    topo_vec_list = []
    # 对于拉伸和旋转分开统计
    if vec[-1][0] == EXT_IDX:
        sketch_count = len(np.where((vec[:, 0] == LINE_IDX) | (vec[:, 0] == SPLINE_IDX) |
                                    (vec[:, 0] == ARC_IDX) | (vec[:, 0] == CIRCLE_IDX))[0].tolist())
        # 统计面
        topo_vec_list.append(np.array([TOPO_VEC, [SELECT_IDX, *[PAD_VAL]*(N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Pad'), operation_map['Extrude'], 1]]))
        topo_vec_list.append(np.array([TOPO_VEC, [SELECT_IDX, *[PAD_VAL]*(N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Pad'), operation_map['Extrude'], 2]]))
        for one_wire in range(1, sketch_count + 1):
            topo_vec_list.append(np.array([TOPO_VEC,
                                           [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), operation_map['Sketch'], one_wire],
                                           [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Pad'), operation_map['Extrude'], 0]]))
        face_num = len(topo_vec_list)
        # 统计上下面的边
        for i in range(2, face_num):
            tmp_vec = [TOPO_VEC]
            for v in topo_vec_list[0][1:]:
                tmp_vec.append(v)
            for v in topo_vec_list[i][1:]:
                tmp_vec.append(v)
            tmp_vec.append([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0])
            topo_vec_list.append(np.array(tmp_vec))

            tmp_vec = [TOPO_VEC]
            for v in topo_vec_list[i][1:]:
                tmp_vec.append(v)
            for v in topo_vec_list[1][1:]:
                tmp_vec.append(v)
            tmp_vec.append([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0])
            topo_vec_list.append(np.array(tmp_vec))
        # 统计侧边，先将圆剔除出来
        circle_list = []
        wire_no = 0
        for i in vec:
            if i[0] == LINE_IDX or i[0] == ARC_IDX or i[0] == CIRCLE_IDX or i[0] == SPLINE_IDX:
                wire_no += 1
            if i[0] == CIRCLE_IDX:
                circle_list.append(wire_no)
        for i in range(3, face_num):
            if (i - 1) in circle_list or (i - 2) in circle_list:
                continue
            tmp_vec = [TOPO_VEC]
            for v in topo_vec_list[i][1:]:
                tmp_vec.append(v)
            for v in topo_vec_list[i - 1][1:]:
                tmp_vec.append(v)
            tmp_vec.append([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0])
            topo_vec_list.append(np.array(tmp_vec))
        tmp_vec = [TOPO_VEC]
        if not(1 in circle_list or (face_num - 2) in circle_list):
            for v in topo_vec_list[2][1:]:
                tmp_vec.append(v)
            for v in topo_vec_list[face_num - 1][1:]:
                tmp_vec.append(v)
            tmp_vec.append([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0])
            topo_vec_list.append(np.array(tmp_vec))
    else:
        sketch_count = len(np.where((vec[:, 0] == LINE_IDX) | (vec[:, 0] == SPLINE_IDX) |
                                    (vec[:, 0] == ARC_IDX) | (vec[:, 0] == CIRCLE_IDX))[0].tolist())
        # 若用草图curve作为旋转轴，该curve不形成面
        if vec[-2][-3] == BODY_TYPE.index('Sketch'):
            # 统计面
            if not (vec[-1][17] == 255 and vec[-1][18] == 0):
                topo_vec_list.append(np.array([TOPO_VEC, [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), operation_map['Revolve'], 1]]))
                topo_vec_list.append(np.array([TOPO_VEC, [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), operation_map['Revolve'], 2]]))
            axis_no = vec[-2][-1]
            for one_wire in range(1, sketch_count + 1):
                if one_wire != axis_no:
                    topo_vec_list.append(np.array([TOPO_VEC,
                                                   [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), operation_map['Sketch'], one_wire],
                                                   [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), operation_map['Revolve'], 0]]))
            # 统计上下面的边
            if not (vec[-1][17] == 255 and vec[-1][18] == 0):
                for one_wire in range(1, sketch_count + 1):
                    if one_wire != axis_no:
                        tmp_vec = [TOPO_VEC]
                        for v in topo_vec_list[0][1:]:
                            tmp_vec.append(v)
                        tmp_vec.append([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), operation_map['Sketch'], one_wire])
                        tmp_vec.append([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), operation_map['Revolve'], 0])
                        tmp_vec.append([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0])
                        topo_vec_list.append(np.array(tmp_vec))

                        tmp_vec = [TOPO_VEC]
                        tmp_vec.append([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), operation_map['Sketch'], one_wire])
                        tmp_vec.append([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), operation_map['Revolve'], 0])
                        for v in topo_vec_list[1][1:]:
                            tmp_vec.append(v)
                        tmp_vec.append([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0])
                        topo_vec_list.append(np.array(tmp_vec))

            # 统计侧面的边
            for one_wire in range(2, sketch_count + 1):
                if one_wire != axis_no and one_wire - 1 != axis_no:
                    topo_vec_list.append(np.array([TOPO_VEC,
                                                   [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), operation_map['Sketch'], one_wire],
                                                   [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), operation_map['Revolve'], 0],
                                                   [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), operation_map['Sketch'], one_wire - 1],
                                                   [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), operation_map['Revolve'], 0],
                                                   [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0]]))
            if axis_no != 1 and axis_no != sketch_count:
                topo_vec_list.append(np.array([TOPO_VEC,
                                              [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), operation_map['Sketch'], 1],
                                              [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), operation_map['Revolve'], 0],
                                              [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), operation_map['Sketch'], sketch_count],
                                              [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), operation_map['Revolve'], 0],
                                              [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0]]))
    return topo_vec_list

def divide_face_in_edge(face_vec):
    end_point = len(face_vec) - 1
    while end_point >= 0:
        if face_vec[end_point][-4] == SELECT_TYPE.index('Wire') or \
                (face_vec[end_point][-4] == SELECT_TYPE.index('Face') and face_vec[end_point][-1] != 0):
            break
        end_point -= 1
    return face_vec[:end_point], face_vec[end_point:]

# 输入为作为body的一组vec
def random_spline(vec):
    # 处理Line，将其按概率转换成Spline
    # 检查草图里是否有连续的Line，记录其起始下标和对应数量
    line_point_count = {}
    tmp_point1 = 0
    while tmp_point1 < len(vec):
        if vec[tmp_point1][0] == LINE_IDX:
            tmp_point2 = tmp_point1
            line_point_count[tmp_point2] = 0
            while tmp_point1 < len(vec) and vec[tmp_point1][0] == LINE_IDX:
                line_point_count[tmp_point2] += 1
                tmp_point1 += 1
        else:
            tmp_point1 += 1
    # 对line_point_count中超过2的按概率改为Spline
    for one_line_point in line_point_count.keys():
        if line_point_count[one_line_point] >= 2:
            if get_probability_flag(SPLINE_RESTRICTION):
                for one_point in range(one_line_point, one_line_point + line_point_count[one_line_point]):
                    vec[one_point][0] = SCP_IDX
                vec = np.concatenate([vec[:one_line_point], np.array([SPLINE_VEC]), vec[one_line_point:]])
    return vec

def random_revolve(vec, operation_map):
    # 记录所有Line的下标，随机挑选一个作为旋转轴
    line_index_list = []
    wire_no = 0
    for i in vec:
        if i[0] == LINE_IDX or i[0] == ARC_IDX or i[0] == CIRCLE_IDX or i[0] == SPLINE_IDX:
            wire_no += 1
        if i[0] == LINE_IDX:
            line_index_list.append(wire_no)
    wire_no = line_index_list[get_uniform(0, len(line_index_list))]
    if get_probability_flag(REVOLVE_FULL_RESTRICTION):
        angle1 = 255
        angle2 = 0
    else:
        angle1 = get_uniform(1, 256)
        angle2 = get_uniform(0, angle1)
    revolve_vec = np.array([TOPO_VEC, [SELECT_IDX, *[PAD_VAL]*(N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), operation_map['Sketch'], wire_no]])
    vec[-1][0] = REV_IDX
    vec[-1][1 + N_ARGS_SKETCH + N_ARGS_TRANS + N_ARGS_PLANE:1 + N_ARGS_SKETCH + N_ARGS_TRANS + N_ARGS_PLANE + 6] = [-1, -1, -1, -1, angle1, angle2]
    vec = np.concatenate([vec[:-1], revolve_vec, [vec[-1]]])
    return vec

def random_shell(vec, topo, max_scale, operation_map, topo_vec_list, topo_twice_list):
    # 设定参数插入向量
    if get_probability_flag(SHELL_IT_RESTRICTION):
        internal_thickness = 128 + get_scale_n(max_scale / 2, max_scale / 2)
        external_thickness = 128
    else:
        internal_thickness = 128 + get_scale_n(max_scale / 2, max_scale / 2)
        external_thickness = 128 + get_scale_n(max_scale / 2, max_scale / 2)
    shell_vec = np.array([SHELL_IDX, *[PAD_VAL] * (N_ARGS_SKETCH + N_ARGS_EXT), internal_thickness, external_thickness, *[PAD_VAL]*(N_ARGS_FINISH_PARAM - 2 + N_ARGS_SELECT_PARAM)])
    vec = np.concatenate([vec, topo, np.array([shell_vec])])

    # 将失效的拓扑对象替换为新的拓扑对象，即在后面加上shell修饰，并将新增的内面加入twice中
    shell_internal_vec = np.array([SELECT_IDX, *[PAD_VAL]*(N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shell'), operation_map['Shell'], 1])
    shell_external_vec = np.array([SELECT_IDX, *[PAD_VAL]*(N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Shell'), operation_map['Shell'], 2])

    face_vec = topo[1:]

    for i in range(len(topo_vec_list)):
        if topo_vec_list[i][-1][-4] == SELECT_TYPE.index('Face'):
            if not face_equal(face_vec, topo_vec_list[i][1:]):
                topo_twice_list.append(np.concatenate([topo_vec_list[i], np.array([shell_internal_vec])], axis=0))
                if external_thickness != 128:
                    topo_vec_list[i] = np.concatenate([topo_vec_list[i], np.array([shell_external_vec])], axis=0)
                    topo_twice_list.append(topo_vec_list.pop(i))
        else:
            first_vec, second_vec = divide_face_in_edge(topo_vec_list[i][1:-1])
            first_it_vec = deepcopy(first_vec)
            second_it_vec = deepcopy(second_vec)
            first_et_vec = deepcopy(first_vec)
            second_et_vec = deepcopy(second_vec)
            if not face_equal(face_vec, first_vec):
                first_it_vec = np.concatenate([first_vec, np.array([shell_internal_vec])])
                if external_thickness != 128:
                    first_et_vec = np.concatenate([first_vec, np.array([shell_external_vec])])
            if not face_equal(face_vec, second_vec):
                second_it_vec = np.concatenate([second_vec, np.array([shell_internal_vec])])
                if external_thickness != 128:
                    second_et_vec = np.concatenate([second_vec, np.array([shell_external_vec])])
            topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), first_it_vec, second_it_vec, np.array([topo_vec_list[i][-1]])]))
            if external_thickness != 128:
                topo_vec_list[i] = np.concatenate([np.array([TOPO_VEC]), first_et_vec, second_et_vec, np.array([topo_vec_list[i][-1]])])
                topo_twice_list.append(topo_vec_list.pop(i))

    return vec, topo_vec_list, topo_twice_list, (internal_thickness - 128 + external_thickness - 128)

def random_chamfer(vec, topo, max_scale, operation_map, topo_vec_list, topo_twice_list):
    # 设定参数插入向量
    length1 = 128 + get_scale_n(max_scale / 2, max_scale / 2)
    if get_probability_flag(CHAMFER_EQUAL_RESTRICTION):
        length2 = length1
    else:
        length2 = 128 + get_scale_n(max_scale / 2, max_scale / 2)
    vec_type = topo[-1][-4]
    chamfer_vec = np.array([CHAMFER_IDX, *[PAD_VAL] * (N_ARGS_SKETCH + N_ARGS_EXT), -1, -1, length1, length2, *[PAD_VAL] * (N_ARGS_FINISH_PARAM - 4 + N_ARGS_SELECT_PARAM)])
    vec = np.concatenate([vec, topo, np.array([chamfer_vec])])
    # 将失效的拓扑对象替换为新的拓扑对象，并将新拓扑面加入twice
    # 失效替换方法是，将边的select_type换为face，body_type换为chamfer，以及其序号即可
    edge_vec = np.array([SELECT_IDX, *[PAD_VAL]*(N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0])
    if vec_type == SELECT_TYPE.index('Edge'):
        face_vec = topo[1:-1]
        for i in range(len(topo_vec_list)):
            if topo_vec_list[i][-1][-4] == SELECT_TYPE.index('Edge'):
                if face_equal(face_vec, topo_vec_list[i][1:-1]):
                    # 将目标边替换为面加入twice，然后删除
                    topo_vec_list[i][-1][-4] = SELECT_TYPE.index('Face')
                    topo_vec_list[i][-1][-3] = BODY_TYPE.index('Chamfer')
                    topo_vec_list[i][-1][-2] = operation_map['Chamfer']
                    # 将新边加入twice，即旧边的两面分别与新面组成边
                    # 将vec中的两面分开，用于构成新的两边，暂时直接视为两普通边，日后depth增加时需要修改
                    first_face, second_face = divide_face_in_edge(face_vec)

                    topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), first_face, topo_vec_list[i][1:], np.array([edge_vec])]))
                    topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), topo_vec_list[i][1:], second_face, np.array([edge_vec])]))
                    topo_twice_list.append(topo_vec_list.pop(i))
                    break
    else:
        face_vec = topo[1:]
        # 分别找出该面周围的所有边，记录并删除
        edge_removed = []
        tmp_point = 0
        while tmp_point < len(topo_vec_list):
            if topo_vec_list[tmp_point][-1][-4] == SELECT_TYPE.index('Edge'):
                first_vec, second_vec = divide_face_in_edge(topo_vec_list[tmp_point][1:-1])
                if face_equal(first_vec, face_vec) or face_equal(second_vec, face_vec):
                    edge_removed.append(topo_vec_list.pop(tmp_point))
                    tmp_point -= 1
            tmp_point += 1
        for one_edge in edge_removed:
            one_edge[-1][-4] = SELECT_TYPE.index('Face')
            one_edge[-1][-3] = BODY_TYPE.index('Chamfer')
            one_edge[-1][-2] = operation_map['Chamfer']
            first_face, second_face = divide_face_in_edge(one_edge[1:-1])
            topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), first_face, one_edge[1:], np.array([edge_vec])]))
            topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), one_edge[1:], second_face, np.array([edge_vec])]))
            topo_twice_list.append(one_edge)
    return vec, topo_vec_list, topo_twice_list, min(length1 - 128, length2 - 128)

def random_fillet(vec, topo, max_scale, operation_map, topo_vec_list, topo_twice_list):
    # 设定参数插入向量
    radius = 128 + get_scale_n(max_scale / 2, max_scale / 2)
    vec_type = topo[-1][-4]
    fillet_vec = np.array([FILLET_IDX, *[PAD_VAL] * (N_ARGS_SKETCH + N_ARGS_EXT), -1, -1, -1, -1, radius, *[PAD_VAL] * (N_ARGS_FINISH_PARAM - 5 + N_ARGS_SELECT_PARAM)])
    vec = np.concatenate([vec, topo, np.array([fillet_vec])])
    # 将失效的拓扑对象替换为新的拓扑对象，并将新拓扑面加入twice
    # 失效替换方法是，将边的select_type换为face，body_type换为chamfer，以及其序号即可
    if vec_type == SELECT_TYPE.index('Edge'):
        face_vec = topo[1:-1]
        for i in range(len(topo_vec_list)):
            if topo_vec_list[i][-1][-4] == SELECT_TYPE.index('Edge'):
                if face_equal(face_vec, topo_vec_list[i][1:-1]):
                    # 将目标边替换为面加入twice，然后删除
                    topo_vec_list[i][-1][-4] = SELECT_TYPE.index('Face')
                    topo_vec_list[i][-1][-3] = BODY_TYPE.index('EdgeFillet')
                    topo_vec_list[i][-1][-2] = operation_map['Fillet']
                    # Fillet产生的边无法二次操作
                    topo_twice_list.append(topo_vec_list.pop(i))
                    break
    else:
        face_vec = topo[1:]
        # 分别找出该面周围的所有边，记录并删除
        edge_removed = []
        tmp_point = 0
        while tmp_point < len(topo_vec_list):
            if topo_vec_list[tmp_point][-1][-4] == SELECT_TYPE.index('Edge'):
                first_vec, second_vec = divide_face_in_edge(topo_vec_list[tmp_point][1:-1])
                if face_equal(first_vec, face_vec) or face_equal(second_vec, face_vec):
                    edge_removed.append(topo_vec_list.pop(tmp_point))
                    tmp_point -= 1
            tmp_point += 1
        for one_edge in edge_removed:
            one_edge[-1][-4] = SELECT_TYPE.index('Face')
            one_edge[-1][-3] = BODY_TYPE.index('EdgeFillet')
            one_edge[-1][-2] = operation_map['Fillet']
            topo_twice_list.append(one_edge)
    return vec, topo_vec_list, topo_twice_list, radius - 128

def random_mirror(vec, topo, operation_map, topo_vec_list, topo_twice_list):
    mirror_vec = np.array([MIRROR_IDX, *[PAD_VAL] * N_ARGS])
    vec = np.concatenate([vec, topo, np.array([mirror_vec])])
    # 删除选作镜面的面，将所有拓扑元素对应的镜像加入twice，若选中面为底面或顶面，删除一切侧面，将和镜像组成的多面加入twice
    face_vec = topo[1:]
    select_face_vec = np.array([SELECT_IDX, *[PAD_VAL]*(N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Mirror'), operation_map['Mirror'], 0])
    sub_select_vec = deepcopy(select_face_vec)
    sub_select_vec[-4] = SELECT_TYPE.index('Sub_Face')
    tmp_point = 0
    edge_vec = np.array([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0])
    if face_vec[-1][-1] == 0:
        while tmp_point < len(topo_vec_list):
            if topo_vec_list[tmp_point][-1][-4] == SELECT_TYPE.index('Face'):
                if face_equal(face_vec, topo_vec_list[tmp_point][1:]):
                    topo_vec_list.pop(tmp_point)
                    tmp_point -= 1
            else:
                first_vec, second_vec = divide_face_in_edge(topo_vec_list[tmp_point][1:-1])
                if face_equal(first_vec, face_vec) or face_equal(second_vec, face_vec):
                    topo_vec_list.pop(tmp_point)
                    tmp_point -= 1
            tmp_point += 1
        # 删除后将现有拓扑面全部镜像加入twice，将所有边的子面添加镜像加入twice
        edge_vec = np.array([SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0])
        for i in topo_vec_list:
            if i[-1][-4] == SELECT_TYPE.index('Face'):
                topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), np.array([MIRROR_START_VEC]), i[1:], np.array([select_face_vec])]))
            else:
                first_vec, second_vec = divide_face_in_edge(i[1:-1])
                topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]),
                                                       np.array([MIRROR_START_VEC]), first_vec, np.array([select_face_vec]),
                                                       np.array([MIRROR_START_VEC]), second_vec, np.array([select_face_vec]),
                                                       np.array([edge_vec])]))
    else:
        Multi_vec = [SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Multiply_Face'), BODY_TYPE.index('None'), 0, 0]
        while tmp_point < len(topo_vec_list):
            if topo_vec_list[tmp_point][-1][-4] == SELECT_TYPE.index('Face'):
                if face_equal(face_vec, topo_vec_list[tmp_point][1:]):
                    topo_vec_list.pop(tmp_point)
                    tmp_point -= 1
                elif topo_vec_list[tmp_point][-1][-1] == 0 and topo_vec_list[tmp_point][-2][-4] == SELECT_TYPE.index('Wire'):
                    sub_topo = deepcopy(topo_vec_list[tmp_point])
                    sub_topo[-1][-4] = SELECT_TYPE.index('Sub_Face')
                    topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), sub_topo[1:],
                                                           np.concatenate([np.array([MIRROR_START_VEC]), topo_vec_list[tmp_point][1:], np.array([sub_select_vec])]),
                                                           np.array([Multi_vec])]))
                    topo_vec_list.pop(tmp_point)
                    tmp_point -= 1
            else:
                first_vec, second_vec = divide_face_in_edge(topo_vec_list[tmp_point][1:-1])
                if face_equal(first_vec, face_vec) or face_equal(second_vec, face_vec):
                    topo_vec_list.pop(tmp_point)
                    tmp_point -= 1
                else:
                    if first_vec[-1][-1] == 0 and first_vec[-2][-4] == SELECT_TYPE.index('Wire'):
                        sub_first = deepcopy(first_vec)
                        sub_first[-1][-4] = SELECT_TYPE.index('Sub_Face')
                        first_vec = np.concatenate([sub_first,
                                                    np.concatenate([np.array([MIRROR_START_VEC]), first_vec,
                                                                    np.array([sub_select_vec])]),
                                                    np.array([Multi_vec])])
                    if second_vec[-1][-1] == 0 and second_vec[-2][-4] == SELECT_TYPE.index('Wire'):
                        sub_second = deepcopy(second_vec)
                        sub_second[-1][-4] = SELECT_TYPE.index('Sub_Face')
                        second_vec = np.concatenate([sub_second,
                                                     np.concatenate([np.array([MIRROR_START_VEC]), second_vec,
                                                                     np.array([sub_select_vec])]),
                                                     np.array([Multi_vec])])
                    topo_vec_list[tmp_point] = np.concatenate([np.array([TOPO_VEC]), first_vec, second_vec, np.array([edge_vec])])
                    topo_twice_list.append(topo_vec_list.pop(tmp_point))
            tmp_point += 1
        # 删除后将现有拓扑面全部镜像加入twice，将所有边的子面添加镜像加入twice
        for i in topo_vec_list:
            if i[-1][-4] == SELECT_TYPE.index('Face'):
                topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), np.array([MIRROR_START_VEC]), i[1:], np.array([select_face_vec])]))
            else:
                first_vec, second_vec = divide_face_in_edge(i[1:-1])
                topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]),
                                                       np.array([MIRROR_START_VEC]), first_vec, np.array([select_face_vec]),
                                                       np.array([MIRROR_START_VEC]), second_vec, np.array([select_face_vec]),
                                                       np.array([edge_vec])]))
    return vec, topo_vec_list, topo_twice_list

def random_draft(vec, neutral_vec, target_topo):
    angle = get_scale_n(128, 64)
    draft_vec = np.array([DRAFT_IDX, *[PAD_VAL] * N_ARGS_SKETCH, 128, 128, 128, *[PAD_VAL] * (N_ARGS_EXT - N_ARGS_PLANE), -1, -1, -1, -1, -1, angle, *[PAD_VAL] * (N_ARGS_FINISH_PARAM - 6 + N_ARGS_SELECT_PARAM)])
    vec = np.concatenate([vec, np.array([TOPO_VEC]), neutral_vec, np.array([TOPO_VEC]), target_topo, np.array([draft_vec])])
    # 没有任何拓扑元素变动，好耶
    return vec

def random_hole(vec, topo, max_scale, operation_map, topo_twice_list):
    is_top = (topo[-1][-1] == 2)
    extent_one, extent_two = 0, 0
    plane_orientation = None
    plane_position = None
    for i in vec:
        if i[0] == EXT_IDX:
            extent_one, extent_two = i[1 + N_ARGS_SKETCH + N_ARGS_TRANS + N_ARGS_PLANE:1 + N_ARGS_SKETCH + N_ARGS_TRANS + N_ARGS_PLANE + 2]
            plane_orientation = i[1 + N_ARGS_SKETCH:1 + N_ARGS_SKETCH + N_ARGS_PLANE]
            plane_position = i[1 + N_ARGS_SKETCH + N_ARGS_PLANE:1 + N_ARGS_SKETCH + N_ARGS_PLANE + 3]
            # # 临时计算平面normal，用于计算偏移
            # sket_plane = CoordSystem.from_vector(i[1 + N_ARGS_SKETCH:1 + N_ARGS_SKETCH + N_ARGS_PLANE + N_ARGS_TRANS - 1])
            # plane_position = np.round(plane_position + sket_plane.normal * (extent_one - 128))
            break
    # 寻找第一个Topo
    topo_point = 0
    while topo_point < len(vec):
        if vec[topo_point][0] == TOPO_IDX or vec[topo_point][0] == EXT_IDX:
            break
        else:
            topo_point = topo_point + 1

    profile_vec = np.concatenate([vec[:topo_point], EOS_VEC[np.newaxis]])

    profile = Profile.from_vector(profile_vec, is_numerical=True)
    mean_x = round((profile.bbox[0][0] + profile.bbox[1][0]) / 2)
    mean_y = round((profile.bbox[0][1] + profile.bbox[1][1]) / 2)
    scale_x = min(mean_x - profile.bbox[0][0], profile.bbox[1][0] - mean_x) * 2
    scale_y = min(mean_y - profile.bbox[0][1], profile.bbox[1][1] - mean_y) * 2
    hole_x = get_scale_n(mean_x, scale_x / 2)
    hole_y = get_scale_n(mean_y, scale_y / 2)
    hole_radius = 128 + get_scale_n(max_scale / 2, max_scale / 4)
    hole_depth = 128
    type_random = np.random.random()
    if type_random < HOLE_TYPE_RESTRICTION['Offset']:
        hole_depth = get_scale_n((extent_one + extent_two) / 2, (extent_one + extent_two - 256) / 2)
        hole_type = EXTENT_TYPE.index('OffsetLimit')
    elif type_random < HOLE_TYPE_RESTRICTION['UpToNext']:
        hole_type = EXTENT_TYPE.index('UpToNextLimit')
    else:
        hole_type = EXTENT_TYPE.index('UpToLastLimit')
    hole_vec = np.array([HOLE_IDX, hole_x, hole_y, -1, -1, -1,
                         plane_orientation[0], plane_orientation[1], plane_orientation[2],
                         plane_position[0], plane_position[1], plane_position[2], -1,
                         *[PAD_VAL]*(N_ARGS_EXT - N_ARGS_TRANS - N_ARGS_PLANE),
                         -1, -1, -1, -1, -1, -1, hole_radius, hole_depth, hole_type,
                         -1, -1, -1, -1])
    vec = np.concatenate([vec, topo, np.array([hole_vec])])
    # 产生侧面，可能还有底面
    edge_vec = np.array([SELECT_IDX, *[PAD_VAL]*(N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0])
    topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), np.array([[SELECT_IDX, *[PAD_VAL]*(N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Hole'), operation_map['Hole'], 0]])]))
    topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), topo[1:],
                                           np.array([[SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'),BODY_TYPE.index('Hole'), operation_map['Hole'], 0]]),
                                           np.array([edge_vec])]))
    if hole_type == EXTENT_TYPE.index('OffsetLimit'):
        topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]), np.array([[SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Hole'), operation_map['Hole'], 1]])]))
        topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]),
                                               np.array([[SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Hole'), operation_map['Hole'], 1]]),
                                               np.array([[SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Hole'), operation_map['Hole'], 0]]),
                                               np.array([edge_vec])]))
    else:
        bottom_topo = deepcopy(topo)
        bottom_topo[-1][-1] = 1
        topo_twice_list.append(np.concatenate([np.array([TOPO_VEC]),
                                               np.array([[SELECT_IDX, *[PAD_VAL] * (N_ARGS - N_ARGS_SELECT_PARAM), SELECT_TYPE.index('Face'), BODY_TYPE.index('Hole'), operation_map['Hole'], 0]]),
                                               bottom_topo[1:],
                                               np.array([edge_vec])]))
    return vec, topo_twice_list, (hole_radius - 128) * 2

def random_shell_twice(vec, topo, max_scale):
    # 设定参数插入向量
    if get_probability_flag(SHELL_IT_RESTRICTION):
        internal_thickness = 128 + get_scale_n(max_scale / 2, max_scale / 2)
        external_thickness = 128
    else:
        internal_thickness = 128 + get_scale_n(max_scale / 2, max_scale / 2)
        external_thickness = 128 + get_scale_n(max_scale / 2, max_scale / 2)
    shell_vec = np.array([SHELL_IDX, *[PAD_VAL] * (N_ARGS_SKETCH + N_ARGS_EXT), internal_thickness, external_thickness, *[PAD_VAL]*(N_ARGS_FINISH_PARAM - 2 + N_ARGS_SELECT_PARAM)])
    vec = np.concatenate([vec, topo, np.array([shell_vec])])

    return vec

def random_chamfer_twice(vec, topo, max_scale):
    # 设定参数插入向量
    length1 = 128 + get_scale_n(max_scale / 2, max_scale / 2)
    length2 = 128 + get_scale_n(max_scale / 2, max_scale / 2)
    chamfer_vec = np.array([CHAMFER_IDX, *[PAD_VAL] * (N_ARGS_SKETCH + N_ARGS_EXT), -1, -1, length1, length2, *[PAD_VAL] * (N_ARGS_FINISH_PARAM - 4 + N_ARGS_SELECT_PARAM)])
    vec = np.concatenate([vec, topo, np.array([chamfer_vec])])
    return vec

def random_fillet_twice(vec, topo, max_scale):
    # 设定参数插入向量
    radius = 128 + get_scale_n(max_scale / 2, max_scale / 2)
    fillet_vec = np.array([FILLET_IDX, *[PAD_VAL] * (N_ARGS_SKETCH + N_ARGS_EXT), -1, -1, -1, -1, radius, *[PAD_VAL] * (N_ARGS_FINISH_PARAM - 5 + N_ARGS_SELECT_PARAM)])
    vec = np.concatenate([vec, topo, np.array([fillet_vec])])
    return vec

def random_mirror_twice(vec, topo):
    mirror_vec = np.array([MIRROR_IDX, *[PAD_VAL] * N_ARGS])
    vec = np.concatenate([vec, topo, np.array([mirror_vec])])
    return vec

file_count = 0
input_paths = sorted(os.listdir(INPUT_PATH))
for input_path in input_paths:
    if not os.path.exists(os.path.join(SAVE_PATH, input_path)):
        os.makedirs(os.path.join(SAVE_PATH, input_path))
    truck_root = os.path.join(INPUT_PATH, input_path)

    file_paths = sorted(glob.glob(os.path.join(truck_root, "*.h5")))
    for path in file_paths:
        file_count += 1

        if file_count <= 0:
            continue

        # 记录重开次数，若大于10则放弃
        remake_count = 0
        # 记录名字用于命名
        name = path[path.find('\\') + 1:-3]
        with h5py.File(path, 'r') as fp:
            if 'vec' in fp.keys():
                origin_vec = fp["vec"][:].astype(np.float)
            else:
                origin_vec = fp["out_vec"][:].astype(np.float)

        while remake_count < 10:
            try:
                # 记录当前各操作的数量，用于序号
                operation_map = {'Sketch': 0, 'Extrude': 0, 'Revolve': 0, 'Chamfer': 0, 'Fillet': 0, 'Shell': 0,
                                 'Mirror': 0, 'Draft': 0, 'Hole': 0}
                origin_vec_copy = deepcopy(origin_vec)
                # 遍历，根据开始指令分为n段
                body_list = []
                body_indices = [-1] + np.where(origin_vec_copy[:, 0] == EXT_IDX)[0].tolist()
                for i in range(len(body_indices) - 1):
                    # 若最后的指令不是EXT则无效跳过
                    if origin_vec_copy[body_indices[i + 1]][0] == EXT_IDX:
                        body_list.append(origin_vec_copy[body_indices[i] + 1:body_indices[i + 1] + 1])

                # 对每段分别进行处理
                for i in range(body_list.__len__()):
                    operation_map['Sketch'] += 1
                    # 计算Scale
                    max_scale = get_max_scale(body_list[i])
                    # 随机添加Spline
                    body_list[i] = random_spline(body_list[i])
                    # 随机添加Revolve
                    if get_probability_flag(REVOLVE_RESTRICTION):
                        # 如果没有Line，则跳过
                        skip_flag = True
                        for one_vec in body_list[i]:
                            if one_vec[0] == LINE_IDX:
                                skip_flag = False
                                break
                        if skip_flag:
                            operation_map['Extrude'] += 1
                            is_extrude = True
                        else:
                            operation_map['Revolve'] += 1
                            body_list[i] = random_revolve(body_list[i], operation_map)
                            is_extrude = False
                    else:
                        operation_map['Extrude'] += 1
                        is_extrude = True
                    # 统计拓扑元素
                    topo_vec_list = get_topo_vec_list(body_list[i], operation_map)
                    # 记录二次生成的元素
                    topo_twice_list = []

                    # 对每个拓扑元素随机添加操作，通过随机数选择操作类型，
                    for topo in topo_vec_list:
                        if get_probability_flag(OPERATION_EXCEPTION / len(topo_vec_list)):
                            random_index = np.random.random()
                            if topo[-1][-4] == SELECT_TYPE.index('Face'):
                                if random_index < FACE_RANDOM_MAP['Shell']:
                                    # 抽壳最好只对上下面操作
                                    if not is_extrude:
                                        if topo[-1][-1] == 0:
                                            continue
                                    operation_map['Shell'] += 1
                                    body_list[i], topo_vec_list, topo_twice_list, cur_scale = random_shell(body_list[i], topo, max_scale, operation_map, topo_vec_list, topo_twice_list)
                                    max_scale = min(max_scale, cur_scale)
                                elif random_index < FACE_RANDOM_MAP['Chamfer']:
                                    operation_map['Chamfer'] += 1
                                    body_list[i], topo_vec_list, topo_twice_list, cur_scale = random_chamfer(body_list[i], topo, max_scale, operation_map, topo_vec_list, topo_twice_list)
                                    max_scale = min(max_scale, cur_scale)
                                elif random_index < FACE_RANDOM_MAP['Fillet']:
                                    operation_map['Fillet'] += 1
                                    body_list[i], topo_vec_list, topo_twice_list, cur_scale = random_fillet(body_list[i], topo, max_scale, operation_map, topo_vec_list, topo_twice_list)
                                    max_scale = min(max_scale, cur_scale)
                                elif random_index < FACE_RANDOM_MAP['Mirror']:
                                    skip_flag = judge_surface(body_list[i], topo, is_extrude)
                                    if skip_flag:
                                        continue
                                    operation_map['Mirror'] += 1
                                    body_list[i], topo_vec_list, topo_twice_list = random_mirror(body_list[i], topo, operation_map, topo_vec_list, topo_twice_list)
                            else:
                                if random_index < EDGE_RANDOM_MAP['Chamfer']:
                                    operation_map['Chamfer'] += 1
                                    body_list[i], topo_vec_list, topo_twice_list, cur_scale = random_chamfer(body_list[i], topo, max_scale, operation_map, topo_vec_list, topo_twice_list)
                                    max_scale = min(max_scale, cur_scale)
                                elif random_index < EDGE_RANDOM_MAP['Fillet']:
                                    operation_map['Fillet'] += 1
                                    body_list[i], topo_vec_list, topo_twice_list, cur_scale = random_fillet(body_list[i], topo, max_scale, operation_map, topo_vec_list, topo_twice_list)
                                    max_scale = min(max_scale, cur_scale)
                                else:
                                    # 此处并非是对边进行拔模，而是利用边将两面绑定的特性，第一个面作为中性面，第二个面作为目标
                                    first_vec, second_vec = divide_face_in_edge(topo[1:-1])
                                    first_flag = judge_surface(body_list[i], first_vec, is_extrude)
                                    second_flag = judge_surface(body_list[i], second_vec, is_extrude)
                                    # first为直面而second为曲面时，first为中性面
                                    if (not first_flag) and second_flag:
                                        operation_map['Draft'] += 1
                                        body_list[i] = random_draft(body_list[i], first_vec, second_vec)
                                    # first为曲面而second为直面时，second为中性面
                                    elif first_flag and (not second_flag):
                                        operation_map['Draft'] += 1
                                        body_list[i] = random_draft(body_list[i], second_vec, first_vec)
                                    elif first_flag and second_flag:
                                        continue
                                    else:
                                        if get_probability_flag(0.5):
                                            body_list[i] = random_draft(body_list[i], first_vec, second_vec)
                                        else:
                                            body_list[i] = random_draft(body_list[i], second_vec, first_vec)
                    # 若底面或顶面仍存在，按概率对其施加洞操作
                    if get_probability_flag(HOLE_RESTRICTION):
                        top_flag, bottom_flag = False, False
                        top_topo, bottom_topo = None, None
                        if topo_vec_list[0][-1][-4] == SELECT_TYPE.index('Face') and topo_vec_list[0][-1][-3] == BODY_TYPE.index('Pad'):
                            if topo_vec_list[0][-1][-1] == 2:
                                top_flag = True
                                top_topo = topo_vec_list[0]
                            if topo_vec_list[0][-1][-1] == 1:
                                bottom_flag = True
                                bottom_topo = topo_vec_list[0]
                        if topo_vec_list[1][-1][-4] == SELECT_TYPE.index('Face') and topo_vec_list[1][-1][-3] == BODY_TYPE.index('Pad'):
                            if topo_vec_list[1][-1][-1] == 2:
                                top_flag = True
                                top_topo = topo_vec_list[1]
                            if topo_vec_list[1][-1][-1] == 1:
                                bottom_flag = True
                                bottom_topo = topo_vec_list[1]
                        if top_flag:
                            operation_map['Hole'] += 1
                            body_list[i], topo_twice_list, cur_scale = random_hole(body_list[i], top_topo, max_scale, operation_map, topo_twice_list)
                            max_scale = min(max_scale, cur_scale)
                    # 对深度不超过限制的拓扑元素继续按概率添加操作
                    for topo in topo_twice_list:
                        if get_probability_flag(TWICE_EXCEPTION / len(topo_twice_list)):
                            random_index = np.random.random()
                            if topo[-1][-4] == SELECT_TYPE.index('Face'):
                                if random_index < FACE_RANDOM_MAP['Shell']:
                                    operation_map['Shell'] += 1
                                    body_list[i] = random_shell_twice(body_list[i], topo, max_scale)
                                elif random_index < FACE_RANDOM_MAP['Chamfer']:
                                    # 如果topo中带有chamfer或fillet，直接跳过
                                    skip_flag = False
                                    for one_vec in topo:
                                        if one_vec[-3] == BODY_TYPE.index('Chamfer') or one_vec[-3] == BODY_TYPE.index('EdgeFillet'):
                                            skip_flag = True
                                            break
                                    if skip_flag:
                                        continue
                                    operation_map['Chamfer'] += 1
                                    body_list[i] = random_chamfer_twice(body_list[i], topo, max_scale)
                                elif random_index < FACE_RANDOM_MAP['Fillet']:
                                    # 如果topo中带有chamfer或fillet，直接跳过
                                    skip_flag = False
                                    for one_vec in topo:
                                        if one_vec[-3] == BODY_TYPE.index('Chamfer') or one_vec[-3] == BODY_TYPE.index('EdgeFillet'):
                                            skip_flag = True
                                            break
                                    if skip_flag:
                                        continue
                                    operation_map['Fillet'] += 1
                                    body_list[i] = random_fillet_twice(body_list[i], topo, max_scale)
                                elif random_index < FACE_RANDOM_MAP['Mirror']:
                                    skip_flag = False
                                    for one_vec in topo:
                                        if (one_vec[-3] == BODY_TYPE.index('Hole') and one_vec[-1] == 0) or (one_vec[-3] == BODY_TYPE.index('Shaft') and one_vec[-1] == 0) or\
                                                one_vec[-3] == BODY_TYPE.index('EdgeFillet'):
                                            skip_flag = True
                                            break
                                    if skip_flag:
                                        continue
                                    operation_map['Mirror'] += 1
                                    body_list[i] = random_mirror_twice(body_list[i], topo)
                            else:
                                if random_index < EDGE_RANDOM_MAP['Chamfer']:
                                    # 如果topo中带有chamfer或fillet，直接跳过
                                    skip_flag = False
                                    for one_vec in topo:
                                        if one_vec[-3] == BODY_TYPE.index('Chamfer') or one_vec[-3] == BODY_TYPE.index('EdgeFillet'):
                                            skip_flag = True
                                            break
                                    if skip_flag:
                                        continue
                                    operation_map['Chamfer'] += 1
                                    body_list[i] = random_chamfer_twice(body_list[i], topo, max_scale)
                                elif random_index < EDGE_RANDOM_MAP['Fillet']:
                                    operation_map['Fillet'] += 1
                                    body_list[i] = random_fillet_twice(body_list[i], topo, max_scale)
                # Catia复现，若合格则保存
                final_vec = np.concatenate(body_list)
                for one_vec in final_vec:
                    print(one_vec)
                final_vec = np.concatenate([final_vec, np.array([EOS_VEC])])
                cad = Macro_Seq.from_vector(final_vec, is_numerical=True, n=256)
            except:
                remake_count += 1
                continue
            # 若未作改动，则不写入
            changed_flag = False
            for op in cad.extrude_operation:
                if not isinstance(op, Extrude):
                    changed_flag = True
                    break
            if not changed_flag:
                remake_count += 1
                continue

            catia = win32com.client.Dispatch('catia.application')
            # 初始化CATIA
            catia.visible = 0
            doc = catia.documents.add('Part')
            part = doc.part
            if not REMOVE_BUG:
                try:
                    create_CAD_CATIA(cad, catia, doc, part)
                except:
                    remake_count += 1
                    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                    print(name, "Failed")
                    doc.Close()
                    continue
                print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                print(name, "OK")
                doc.Close()
            else:
                bug_point = create_CAD_CATIA(cad, catia, doc, part, remove_bug=True)
                while bug_point != -1 and len(cad.extrude_operation) > 0:
                    doc.close()
                    doc = catia.documents.add('Part')
                    part = doc.part
                    cad.extrude_operation.remove(cad.extrude_operation[bug_point])
                    if len(cad.extrude_operation) <= 0:
                        break
                    bug_point = create_CAD_CATIA(cad, catia, doc, part, remove_bug=True)
                if len(cad.extrude_operation) <= 0:
                    remake_count += 1
                    continue
                # 若除拉伸以外的操作少于2，跳过
                else:
                    new_count = 0
                    for op in cad.extrude_operation:
                        if not isinstance(op, Extrude):
                            new_count += 1
                    if new_count < NEW_OPERATION_RESTRICTION:
                        remake_count += 1
                        continue
                    else:
                        cad.numericalize(n=ARGS_N)
                        final_vec = cad.to_vector(MAX_N_EXT, MAX_N_LOOPS, MAX_N_CURVES, MAX_TOTAL_LEN, pad=False)

            for fir in range(final_vec.shape[0]):
                for sec in range(final_vec.shape[1]):
                    if final_vec[fir][sec] > 255:
                        final_vec[fir][sec] = 255
                        print(name, ':参数大于255')
                    if final_vec[fir][sec] < -1:
                        final_vec[fir][sec] = 0
                        print(name, ':参数小于-1')
            name_count = 0
            while True:
                name_count += 1
                name_path = SAVE_PATH + '\\' + name[name.find('DeepCAD_data_32\\') + len('DeepCAD_data_32\\'):] + '_' + str(name_count) + '.h5'
                # 判断name_count是否已经存在
                if not os.path.exists(name_path):
                    with h5py.File(name_path, 'w') as fp:
                        fp.create_dataset("vec", data=final_vec, dtype=np.int)
                    break

            remake_count = 10
