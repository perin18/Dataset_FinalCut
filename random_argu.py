import macro_new
from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
import win32com.client
import h5py
import time

INPUT_PATH = 'D:/experiment/DeepCAD-master/data/cad_vec_21'
SAVE_PATH = 'C:/Users/45088/Desktop/WHU_dataset/random_argu'

def add_face_command(target_topo, type, size_scale):
    # size_scale = size_scale / 2 + 1
    # 若实在无法满足，设置为1
    if size_scale <= 2:
        size_scale = 2
    # 与ours保持一致，128以上为正值
    size_scale = size_scale + 128
    tmp_command = [
        [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        [13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
    ]
    if len(target_topo) == 4:
        tmp_command.append(
            [SELECT_IDX, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, target_topo[0], target_topo[1], target_topo[2], target_topo[3]])
    else:
        for i in target_topo:
            tmp_command.append([SELECT_IDX, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, i[0], i[1], i[2], i[3]])

    if type == 0 or type == 3:
        scale1 = np.random.randint(129, int(size_scale))
        scale2 = np.random.randint(128, int(size_scale))
        tmp_command.append([
            SHELL_IDX, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, scale1,  scale2, -1, -1, -1, -1, -1, -1
        ])
        tmp_command = np.array(tmp_command)
    if type == 1:
        scale1 = np.random.randint(129, int(size_scale))
        scale2 = np.random.randint(129, int(size_scale))
        tmp_command.append([
            CHAMFER_IDX, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, scale1, scale2, -1, -1, -1, -1, -1, -1
        ])
    if type == 2:
        scale = np.random.randint(129, int(size_scale))
        tmp_command.append([
            FILLET_IDX, -1, -1, -1, -1, scale, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
        ])
    if type == 4:
        tmp_command.append([
            MIRROR_IDX, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
        ])
    tmp_command = np.array(tmp_command)
    return tmp_command

def add_edge_command(target_topo, type, size_scale):
    # size_scale = size_scale / 2 + 1
    # 若实在无法满足，设置为1
    if size_scale <= 2:
        size_scale = 2
    # 与ours保持一致，128以上为正值
    size_scale = size_scale + 128
    tmp_command = [
        [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
        [13, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
    ]
    for i in target_topo:
        if len(i) == 4:
            tmp_command.append(
                [SELECT_IDX, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, i[0], i[1], i[2], i[3]])
        else:
            for j in i:
                tmp_command.append([SELECT_IDX, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, j[0], j[1], j[2], j[3]])
    if type == 0:
        scale1 = np.random.randint(129, size_scale)
        scale2 = np.random.randint(129, size_scale)
        tmp_command.append([
            CHAMFER_IDX, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, scale1, scale2, -1, -1, -1, -1, -1, -1
        ])
    if type == 1:
        scale = np.random.randint(129, size_scale)
        tmp_command.append([
            FILLET_IDX, -1, -1, -1, -1, scale, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
        ])
    tmp_command = np.array(tmp_command)
    return tmp_command




def main():
    # 读取数据，将数据划分为几个body
    input_paths = sorted(os.listdir(INPUT_PATH))
    for input_path in input_paths:
        if not os.path.exists(SAVE_PATH + "/" + input_path):
            os.makedirs(SAVE_PATH + "/" + input_path)
        truck_root = os.path.join(INPUT_PATH, input_path)

        file_paths = sorted(glob.glob(os.path.join(truck_root, "*.h5")))
        for path in file_paths:

            # if int(path[-11:-3]) < 29634:
            #     continue

            # # 判断name_count是否已经存在
            # if os.path.exists(name_path):
            #     print("Skip ", name_path)
            #     continue

            # 记录重开次数，若大于10则放弃
            re_count = 0
            while re_count < 10:
                doc = None
                # 若未作改动，则不写入
                flag = False
                with h5py.File(path, 'r') as fp:
                    out_vec = fp["vec"][:-1].astype(np.float)
                # 遍历，根据开始指令分为n段
                name = path[path.find('\\') + 1:-3]
                body_list = []
                copy_list = []
                tmp_point = 0
                for i in range(1, out_vec.shape[0]):
                    if out_vec[i][0] == 4:
                        copy_list.append(out_vec[tmp_point:i])
                        tmp_point = i
                copy_list.append(out_vec[tmp_point:])

                for body in copy_list:
                    if body[-1][0] == macro_new.EXT_IDX:
                        body_list.append(body)

                # 记录拉伸体和旋转体当前应当的序号
                extrude_no, revolve_no, sketch_no = 0, 0, 0
                # 对每段分别进行处理
                for i in range(body_list.__len__()):
                    # 操作的最大数值
                    max_scale = 256

                    # 统计草图数量，且记录最小尺寸，用于添加操作
                    curve_count = body_list[i].shape[0] - 2
                    # 若为线段或弧，计算最短长度
                    if body_list[i][1][0] != 2:
                        if curve_count > 2:
                            start_point = [body_list[i][1][1], body_list[i][1][2]]
                            cur_point = start_point
                            for j in range(2, curve_count + 1):
                                tmp_point = [body_list[i][j][1], body_list[i][j][2]]
                                dis = np.sqrt(
                                    np.power((cur_point[0] - tmp_point[0]), 2) + np.power((cur_point[1] - tmp_point[1]),
                                                                                          2))
                                cur_point = tmp_point
                                if dis < size_scale:
                                    size_scale = dis
                            dis = np.sqrt(
                                np.power((cur_point[0] - start_point[0]), 2) + np.power((cur_point[1] - start_point[1]),
                                                                                        2))
                        else:
                            start_point = [body_list[i][1][1], body_list[i][1][2]]
                            end_point = [body_list[i][2][1], body_list[i][2][2]]
                            dis = np.sqrt(
                                np.power((end_point[0] - start_point[0]), 2) + np.power((end_point[1] - start_point[1]),
                                                                                        2))
                        if dis < size_scale:
                            size_scale = dis
                    # 若为圆，得到其半径
                    else:
                        size_scale = body_list[i][1][5]

                    # 统计拓扑对象数量
                    topo_count = 0
                    # 归纳全部选取指令，对每条指令按概率添加操作
                    select_edge_list = []
                    select_face_list = []
                    wire_no = -1

                    sketch_no = sketch_no + 1

                    # 按一定概率将拉伸替换成旋转
                    change_to_shaft = 0.3
                    chance = np.random.uniform(0, 1)
                    if curve_count > 1 and chance < change_to_shaft:
                        flag = True
                        # 在curve_count中随机选择一条
                        wire_no = np.random.randint(1, curve_count + 1)
                        ori_ext = deepcopy(body_list[i][-1])
                        body_list[i][-1] = [TOPO_IDX, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
                        # 随机为Full或TwoSide
                        is_two = np.random.uniform(0, 1) < 0.4
                        angle_one, angle_two = 0, 0
                        if is_two:
                            angle_one = np.random.randint(1, 256)
                            angle_two = np.random.randint(0, angle_one)
                        body_list[i] = np.concatenate([body_list[i],
                                                       [[SELECT_IDX, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), sketch_no, wire_no]],
                                                       [[REV_IDX, -1, -1, -1, 0, -1, ori_ext[6], ori_ext[7], ori_ext[8], ori_ext[9], ori_ext[10], ori_ext[11], ori_ext[12], angle_one, angle_two, ori_ext[15], is_two, -1, -1, -1, -1]]], axis=0)

                    # 如果为拉伸
                    if body_list[i][-1][0] == 5:
                        extrude_no = extrude_no + 1
                        if body_list[i][-1][16] == 0:
                            extrude_size = body_list[i][-1][13]
                        elif body_list[i][-1][16] == 1:
                            extrude_size = body_list[i][-1][13] * 2
                        else:
                            extrude_size = body_list[i][-1][13] + body_list[i][-1][14]
                        if extrude_size < size_scale:
                            size_scale = extrude_size
                        # 下上两面
                        select_face_list.append([[SELECT_TYPE.index('Face'), BODY_TYPE.index('Pad'), extrude_no, 1]])
                        select_face_list.append([[SELECT_TYPE.index('Face'), BODY_TYPE.index('Pad'), extrude_no, 2]])
                        # 侧面一圈
                        for j in range(1, curve_count + 1):
                            select_face_list.append([[SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), sketch_no, j],
                                                     [SELECT_TYPE.index('Face'), BODY_TYPE.index('Pad'), extrude_no, 0]])
                        # 下上面的边
                        face_num = select_face_list.__len__()
                        for j in range(2, face_num):
                            select_edge_list.append([select_face_list[0], select_face_list[j],
                                                     [SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0]])
                            select_edge_list.append([select_face_list[j], select_face_list[1],
                                                     [SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0]])
                        # 侧边
                        for j in range(3, face_num):
                            select_edge_list.append([select_face_list[j], select_face_list[j - 1],
                                                     [SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0]])
                        select_edge_list.append([select_face_list[2], select_face_list[face_num - 1],
                                                 [SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0]])

                        # 对每个对象按概率插入指令,概率期望添加两条
                        topo_count = select_face_list.__len__() + select_edge_list.__len__()
                        for j in select_face_list:
                            chance = np.random.uniform(0, 1)
                            if chance < 1.0 / topo_count:
                                flag = True
                                # 添加随机操作：抽壳、倒角、圆角、镜面
                                type = np.random.randint(0, 5)
                                body_list[i] = np.append(body_list[i], add_face_command(j, type, size_scale), axis=0)
                        for j in select_edge_list:
                            chance = np.random.uniform(0, 1)
                            if chance < 1.0 / topo_count:
                                flag = True
                                # 添加随机操作：倒角、圆角
                                type = np.random.randint(0, 2)
                                body_list[i] = np.append(body_list[i], add_edge_command(j, type, size_scale), axis=0)

                    # 否则为旋转，应该判断一下旋转轴是否与图像重合？若是，与哪条重合
                    # 判断旋转是否为Full
                    else:
                        revolve_no = revolve_no + 1
                        if body_list[i][-1][16] != REVOLVE_TYPE.index('FULL'):
                            select_face_list.append([SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), revolve_no, 1])
                            select_face_list.append([SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), revolve_no, 2])

                            # 侧面一圈，要先根据旋转轴判断哪个面不存在
                            for j in range(1, curve_count + 1):
                                if j != wire_no:
                                    select_face_list.append([[SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), sketch_no, j],
                                                             [SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), revolve_no, 0]])
                                # 下上面的边
                            face_num = select_face_list.__len__()
                            for j in range(2, face_num):
                                select_edge_list.append([select_face_list[0], select_face_list[j],
                                                         [SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0,
                                                          0]])
                                select_edge_list.append([select_face_list[j], select_face_list[1],
                                                         [SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0,
                                                          0]])
                            # 侧边
                            for j in range(3, face_num):
                                select_edge_list.append([select_face_list[j], select_face_list[j - 1],
                                                         [SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0,
                                                          0]])
                            select_edge_list.append([select_face_list[2], select_face_list[face_num - 1],
                                                     [SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0]])
                        else:
                            # 侧面一圈
                            for j in range(curve_count):
                                if j != wire_no:
                                    select_face_list.append([[SELECT_TYPE.index('Wire'), BODY_TYPE.index('Sketch'), sketch_no, j],
                                                             [SELECT_TYPE.index('Face'), BODY_TYPE.index('Shaft'), revolve_no, 0]])
                            face_num = select_face_list.__len__()
                            # 侧边
                            for j in range(1, face_num):
                                select_edge_list.append([select_face_list[j], select_face_list[j - 1],
                                                         [SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0]])
                            select_edge_list.append([select_face_list[0], select_face_list[face_num - 1],
                                                     [SELECT_TYPE.index('Edge'), BODY_TYPE.index('None'), 0, 0]])

                        # 对每个对象按概率插入指令,概率期望添加两条
                        topo_count = select_face_list.__len__() + select_edge_list.__len__()
                        for j in select_face_list:
                            chance = np.random.uniform(0, 1)
                            if chance < 1.0 / topo_count:
                                flag = True
                                # 添加随机操作：抽壳、倒角、圆角
                                type = np.random.randint(0, 5)
                                body_list[i] = np.append(body_list[i], add_face_command(j, type, size_scale), axis=0)
                        for j in select_edge_list:
                            chance = np.random.uniform(0, 1)
                            if chance < 1.0 / topo_count:
                                flag = True
                                # 添加随机操作：倒角、圆角
                                type = np.random.randint(0, 2)
                                body_list[i] = np.append(body_list[i], add_edge_command(j, type, size_scale),
                                                         axis=0)
                # 若没做改动，则跳过
                if not flag:
                    re_count + 1
                    continue
                body_list = np.array(body_list)
                result_list = np.array([])
                for body in body_list:
                    if result_list.size == 0:
                        result_list = body
                    else:
                        result_list = np.append(result_list, body, axis=0)

                # 通过CATIA判断是否合理，若合理，则写入h5py
                try:
                    # with h5py.File('../bug.h5', 'w') as fp:
                    #     fp.create_dataset("vec", data=result_list, dtype=np.int)
                    catia = win32com.client.Dispatch('catia.application')
                    cad = Macro_Seq.from_vector(result_list, is_numerical=True, n=256)
                    # 初始化CATIA
                    catia.visible = 1
                    doc = catia.documents.add('Part')
                    part = doc.part
                    create_CAD_CATIA(cad, catia, part)
                    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                    print(name, "OK")

                    # 若已经打开超过50个文件，集中删除
                    doc.Close()

                    # 加入结束指令
                    eof_vec = np.array([[3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]])
                    result_list = np.append(result_list, eof_vec, axis=0)

                    # 确保指令都不大于100条，且参数都小于256
                    if result_list.shape[0] > 100:
                        re_count = re_count + 1
                        continue
                    for fir in range(result_list.shape[0]):
                        for sec in range(result_list.shape[1]):
                            if result_list[fir][sec] >= 256:
                                result_list[fir][sec] = 255

                    # 由于数量可能不够，需要多插入指令几次，以防覆盖，需要修改命名
                    name_count = 0
                    while True:
                        name_count = name_count + 1
                        name_path = SAVE_PATH + '\\' + name + '_' + str(name_count) + '.h5'
                        # 判断name_count是否已经存在
                        if not os.path.exists(name_path):
                            with h5py.File(name_path, 'w') as fp:
                                fp.create_dataset("vec", data=result_list, dtype=np.int)
                            break

                    re_count = 10

                except Exception as e:
                    re_count = re_count + 1
                    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                    print(name, "Load and create failed.")
                    if doc is not None:
                        doc.Close()
if __name__ == '__main__':
    main()

