import glob
import json
import os

from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
import win32com.client
import h5py

def parse_select_name(select_name, type, no_map, offset_map={}):
    if type == 'Wire':
        select_name = select_name[select_name.find('(') + 1:-1]
        body_name = select_name[:select_name.find('.')]
        # 根据offset_map对草图序号调整
        body_no = int(select_name[select_name.find('.') + 1:select_name.find(';')])
        tmp = 0
        for i in offset_map:
            if body_no >= i:
                tmp = tmp + offset_map[i]
        body_no = body_no + tmp
        # curve的序号不一定是按序，需进行转化
        topo_no = no_map[select_name]
        select = Select('Wire', body_name, body_no, topo_no, [], [], {})
        return select
    if type == 'WireREdge':
        select_name = select_name[select_name.find('(') + 1:]
        name_str = select_name[select_name.find('(') + 1: select_name.find(')')]
        body_name = name_str[:name_str.find('.')]
        # 根据offset_map对草图序号调整
        body_no = int(name_str[name_str.find('.') + 1:name_str.find(';')])
        for i in offset_map:
            if body_no >= i:
                body_no = body_no + offset_map[i]
        topo_no = no_map[name_str]
        select = Select('Wire', body_name, body_no, topo_no, [], [], {})
        return select
    if type == 'Edge':
        select_name = select_name[select_name.find('(') + 1:]
        select = Select('Edge', 'None', 0, 0, [], [], {})
        # 将各个面的命名分开
        while select_name[:4] == 'Face':
            start_point = 0
            end_point = select_name.find('(') + 1
            bracket_count = 1
            while bracket_count > 0:
                if select_name[end_point] == '(':
                    bracket_count = bracket_count + 1
                elif select_name[end_point] == ')':
                    bracket_count = bracket_count - 1
                end_point = end_point + 1
            select.operation_list.append(parse_select_name(select_name[start_point: end_point], 'Face', no_map, offset_map))
            select_name = select_name[end_point + 1:]

        # 查看是否有NoSharedIncluded
        if 'AtLeastOneNoSharedIncluded' in select_name:
            no_shared_str = select_name[select_name.find('AtLeastOneNoSharedIncluded') + len('AtLeastOneNoSharedIncluded') + 1:]
            end_point = no_shared_str.index('(') + 1
            bracket_count = 1
            while bracket_count > 0 and end_point < no_shared_str.__len__():
                if no_shared_str[end_point] == '(':
                    bracket_count = bracket_count + 1
                elif no_shared_str[end_point] == ')':
                    bracket_count = bracket_count - 1
                end_point = end_point + 1
            no_shared_str = no_shared_str[1:end_point - 1]
            # 去掉Limits1
            no_shared_str = no_shared_str[no_shared_str.find('Limits1:(') + len('Limits1:('):]
            while no_shared_str[:3] == 'Brp':
                start_point = 0
                end_point = no_shared_str.find('(') + 1
                bracket_count = 1
                while bracket_count > 0:
                    if no_shared_str[end_point] == '(':
                        bracket_count = bracket_count + 1
                    elif no_shared_str[end_point] == ')':
                        bracket_count = bracket_count - 1
                    end_point = end_point + 1
                select.no_shared_included.append(
                    parse_select_name('Face:(' + no_shared_str[start_point: end_point] + ')', 'Face', no_map,
                                      offset_map))
                no_shared_str = no_shared_str[end_point + 1:]

        # 查看是否有AllOrientedIncluded
        if 'AllOrientedIncluded' in select_name:
            all_oriented_str = select_name[select_name.find('AllOrientedIncluded') + len('AllOrientedIncluded') + 1:]
            end_point = all_oriented_str.index('(') + 1
            bracket_count = 1
            while bracket_count > 0 and end_point < all_oriented_str.__len__():
                if all_oriented_str[end_point] == '(':
                    bracket_count = bracket_count + 1
                elif all_oriented_str[end_point] == ')':
                    bracket_count = bracket_count - 1
                end_point = end_point + 1
            all_oriented_str = all_oriented_str[1:end_point - 1]

            # 将Limits1和Limits2分开
            Limits1_str = all_oriented_str[all_oriented_str.find('Limits1'):all_oriented_str.find('Limits2')]
            Limits2_str = all_oriented_str[all_oriented_str.find('Limits2'):]
            Limits1_str = Limits1_str[Limits1_str.find('Limits1:(') + len('Limits1:('):]
            Limits2_str = Limits2_str[Limits2_str.find('Limits2:(') + len('Limits2:('):]

            Limits1_select = []
            Limits2_select = []
            while Limits1_str[:3] == 'Brp':
                start_point = 0
                end_point = Limits1_str.find('(') + 1
                bracket_count = 1
                while bracket_count > 0:
                    if Limits1_str[end_point] == '(':
                        bracket_count = bracket_count + 1
                    elif Limits1_str[end_point] == ')':
                        bracket_count = bracket_count - 1
                    end_point = end_point + 1
                Limits1_select.append(
                    parse_select_name('Face:(' + Limits1_str[start_point: end_point] + ')', 'Face', no_map, offset_map))
                Limits1_str = Limits1_str[end_point + 1:]

            while Limits2_str[:3] == 'Brp':
                start_point = 0
                end_point = Limits2_str.find('(') + 1
                bracket_count = 1
                while bracket_count > 0:
                    if Limits2_str[end_point] == '(':
                        bracket_count = bracket_count + 1
                    elif Limits2_str[end_point] == ')':
                        bracket_count = bracket_count - 1
                    end_point = end_point + 1
                Limits2_select.append(
                    parse_select_name('Face:(' + Limits2_str[start_point: end_point] + ')', 'Face', no_map,
                                      offset_map))
                Limits2_str = Limits2_str[end_point + 1:]

            select.all_oriented_included['Limits1'] = deepcopy(Limits1_select)
            select.all_oriented_included['Limits2'] = deepcopy(Limits2_select)


        return select
    if type == 'Face':
        select_name = select_name[select_name.find('(') + 1:]
        end_point = select_name.index('(') + 1
        strat_point = end_point
        bracket_count = 1
        while bracket_count > 0 and end_point < select_name.__len__():
            if select_name[end_point] == '(':
                bracket_count = bracket_count + 1
            elif select_name[end_point] == ')':
                bracket_count = bracket_count - 1
            end_point = end_point + 1
        name_str = select_name[strat_point:end_point - 1]


        # 此时判断是否有多个Brp，若有，则说明此面由多个面聚合
        if name_str[0] == '(':
            name_str = name_str[1:-1]
            select = Select('Multiply_Face', 'None', 0, 0, [], [], {})
            # 将各个面的命名分开
            while name_str[:3] == 'Brp':
                start_point = 0
                end_point = name_str.find('(') + 1
                bracket_count = 1
                while bracket_count > 0:
                    if name_str[end_point] == '(':
                        bracket_count = bracket_count + 1
                    elif name_str[end_point] == ')':
                        bracket_count = bracket_count - 1
                    end_point = end_point + 1
                select.operation_list.append(
                    parse_select_name('Face:(' + name_str[start_point: end_point] + ')', 'Face', no_map, offset_map))
                select.operation_list[-1].select_type = 'Sub_Face'
                name_str = name_str[end_point + 1:]
        # 若为Shell，则视为Multiply_Face
        elif name_str[:5] == 'Shell':
            body_no = int(name_str[name_str.find('.') + 1:name_str.find('_')])
            no = int(name_str[name_str.find(';') + 1: name_str.find(':')])
            select = Select('Face', 'Shell', body_no, no, [], [], {})
            name_str = name_str[name_str.find('Brp:(') + 5:-2]
            # 若是，说明为多个面
            if name_str[0] == '(':
                name_str = name_str[1:-1]
                # 将各个面的命名分开
                while name_str[:3] == 'Brp':
                    start_point = 0
                    end_point = name_str.find('(') + 1
                    bracket_count = 1
                    while bracket_count > 0:
                        if name_str[end_point] == '(':
                            bracket_count = bracket_count + 1
                        elif name_str[end_point] == ')':
                            bracket_count = bracket_count - 1
                        end_point = end_point + 1
                    select.operation_list.append(
                        parse_select_name('Face:(' + name_str[start_point: end_point] + ')', 'Face', no_map, offset_map))
                    select.operation_list[-1].select_type = 'Sub_Face'
                    name_str = name_str[end_point + 1:]
            else:
                select.operation_list.append(
                    parse_select_name('Face:(Brp:(' + name_str + '))', 'Face', no_map, offset_map))
                select.operation_list[-1].select_type = 'Sub_Face'
        else:
            body_name = name_str[:name_str.find('.')]
            if body_name == 'Chamfer' or body_name == 'EdgeFillet':
                body_no = int(name_str[name_str.find('.') + 1:name_str.find('_')])
                select_name_tmp = select_name[select_name.find('(') + 1:]
                select_name_tmp = select_name_tmp[select_name_tmp.find('(') + 1:]
                select = Select('Face', body_name, body_no, 0, [], [], {})
                # 将各个面的命名分开
                while select_name_tmp[:3] == 'Brp':
                    start_point = 0
                    end_point = select_name_tmp.find('(') + 1
                    bracket_count = 1
                    while bracket_count > 0:
                        if select_name_tmp[end_point] == '(':
                            bracket_count = bracket_count + 1
                        elif select_name_tmp[end_point] == ')':
                            bracket_count = bracket_count - 1
                        end_point = end_point + 1
                    select.operation_list.append(parse_select_name('Face:(' + select_name_tmp[start_point: end_point] + ')', 'Face', no_map, offset_map))
                    select_name_tmp = select_name_tmp[end_point + 1:]

            else:
                body_no = int(name_str[name_str.find('.') + 1:name_str.find(';')])
                topo_no = int(name_str[name_str.find(';') + 1])
                select = Select('Face', body_name, body_no, topo_no, [], [], {})
                if topo_no == 0:
                    sub_str = name_str[name_str.find(':(') + 2:-1]
                    sub_select = parse_select_name(sub_str, 'Wire', no_map, offset_map)
                    select.operation_list.append(sub_select)
        # 查看是否有NoSharedIncluded
        if 'AtLeastOneNoSharedIncluded' in select_name:
            no_shared_str = select_name[select_name.find('AtLeastOneNoSharedIncluded') + len('AtLeastOneNoSharedIncluded') + 1:]
            end_point = no_shared_str.index('(') + 1
            bracket_count = 1
            while bracket_count > 0 and end_point < no_shared_str.__len__():
                if no_shared_str[end_point] == '(':
                    bracket_count = bracket_count + 1
                elif no_shared_str[end_point] == ')':
                    bracket_count = bracket_count - 1
                end_point = end_point + 1
            no_shared_str = no_shared_str[1:end_point - 1]
            while no_shared_str[:3] == 'Brp':
                start_point = 0
                end_point = no_shared_str.find('(') + 1
                bracket_count = 1
                while bracket_count > 0:
                    if no_shared_str[end_point] == '(':
                        bracket_count = bracket_count + 1
                    elif no_shared_str[end_point] == ')':
                        bracket_count = bracket_count - 1
                    end_point = end_point + 1
                select.no_shared_included.append(
                    parse_select_name('Face:(' + no_shared_str[start_point: end_point] + ')', 'Face', no_map, offset_map))
                no_shared_str = no_shared_str[end_point + 1:]
        return deepcopy(select)

def process_on(input_path, catia, doc):
    input_macro = sorted(glob.glob(os.path.join(input_path, "*.catvbs")))[0]
    input_json = sorted(glob.glob(os.path.join(input_path, "*.json")))[0]

    with open(input_macro, "r", encoding='UTF-8') as f:
        str = f.read()

    # 通过换行将命令之间分开
    command_list = str.split('\n')
    for i in command_list:
        if i == '':
            command_list.remove(i)

    # 记录拉伸、旋转或其他操作
    extrude_operation = []
    # 直接寻找草图参数
    sketch_para = []
    # 寻找草图curve
    sketch_curve = []
    # 记录实际应该的序号
    trueNo = 0
    # 记录curve真实序号和命名序号的map
    no_map = {}
    sketch_plane = None
    sketch_profile = None
    sketch_pos = None
    sketch_size = None

    # 用于记录旋转的轴是否出现两次
    not_first_flag = False
    first_ref = ''

    all_operation = []
    # 用于记录上一个创建的Spline控制点，与下一个连成线
    spline_point_list = []

    # 标记当前的Extrude、Revolve、Pocket
    extrude_pocket_point = 0
    # 标记当前操作在所有操作中的序号
    point_in_all = 0

    # 记录多个选取对象
    select_list = []

    # 记录草图数量
    sketch_count = 0

    # 用于记录例如lengthx对应的是哪个body的哪个参数
    parameter_map = {}

    # 正常是一个body对应一个草图，但会出现一个草图对应多个body的情况，或者出现多余草图的情况，需要记录
    # 格式：A(int): B(int), 意为当草图的命名序号大于A时，其序号需自加B
    # 例如，若map = {3: 1, 5: -1}, 代表当命名中出现草图sketch.3、sketch.4时，需自加1变为sketch.4, sketch.5， 当出现sketch.5及以后序号时，需先加1再减1
    sketch_offset_map = {}
    # 标记是否一个草图对应一个body，若是则为True
    offset_flag = False

    # 增加一个缓存select的容器，用于暂时保存未被Add的对象
    select_cache = {}
    # 增加一个缓存sketch的容器，用于暂时保存可能被选取的sketch对象
    sketch_cache = {}

    bounding_box = None
    bounding_size = 0

    with open(input_json, "r", encoding='UTF-8') as js:
        js = json.load(js)
        bounding_box = js.values()
    for i in bounding_box:
        if i == '' or i == '-':
            i = 0
        else:
            if not isinstance(i, float):
                if i[-2:] == 'mm' or i[-2:] == 'in':
                    i = i[:-2]
            size = float(i)
        if bounding_size < abs(size):
            bounding_size = abs(size)

    # 指令指针
    command_no = 0
    while command_no < command_list.__len__():
        # 若定义数组，则为定义草图位置信息
        # 出现这句，可能是第一个body的定义，也可能是上一个body的结束
        if 'Dim arrayOfVariantOfDouble' in command_list[command_no]:
            # 初始化
            if extrude_operation != []:
                all_operation.append(extrude_operation)
            extrude_operation = []
            sketch_para = []
            sketch_curve = []
            trueNo = 0
            sketch_plane = None
            sketch_profile = None
            sketch_pos = None
            sketch_size = None
            not_first_flag = False
            first_ref = ''
            spline_point_list = []
            extrude_pocket_point = 0
            select_list = []

            for i in range(9):
                command_no = command_no + 1
                para_str = command_list[command_no][command_list[command_no].find('=') + 2:]
                sketch_para.append(float(para_str))
            origin = np.array(sketch_para[:3])
            x_axis = np.array(sketch_para[3:6])
            y_axis = np.array(sketch_para[6:])
            z_axis = np.cross(x_axis, y_axis)
            theta, phi, gamma = polar_parameterization(z_axis, x_axis)
            sketch_plane = CoordSystem(origin, theta, phi, gamma, y_axis=cartesian2polar(y_axis))
            sketch_count = sketch_count + 1
            offset_flag = True
        elif 'CreateLine' in command_list[command_no]:
            trueNo = trueNo + 1
            para = (command_list[command_no][command_list[command_no].find('(') + 1:-1]).split(',')
            command_no = command_no + 1
            while 'ReportName' not in command_list[command_no]:
                command_no = command_no + 1
            reportNo = int(command_list[command_no][command_list[command_no].find('=') + 2:])
            start_point = np.array([float(para[0]), float(para[1])])
            end_point = np.array([float(para[2]), float(para[3])])
            sketch_curve.append(Line(start_point, end_point, reportNo))
        elif 'CreateCircle' in command_list[command_no]:
            trueNo = trueNo + 1
            para = (command_list[command_no][command_list[command_no].find('(') + 1:-1]).split(',')
            command_no = command_no + 1
            while 'ReportName' not in command_list[command_no]:
                command_no = command_no + 1
            reportNo = int(command_list[command_no][command_list[command_no].find('=') + 2:])
            center = np.array([float(para[0]), float(para[1])])
            start_arc = np.float(para[3])
            end_arc = np.float(para[4])
            if start_arc < end_arc:
                mid_arc = (start_arc + end_arc) / 2
            else:
                mid_arc = (start_arc + end_arc + 2 * np.pi) / 2
            sketch_curve.append(Arc(center, np.float(para[2]), start_arc, end_arc, mid_arc, reportNo))
        elif 'CreateClosedCircle' in command_list[command_no]:
            trueNo = trueNo + 1
            para = (command_list[command_no][command_list[command_no].find('(') + 1:-1]).split(',')
            para_name = command_list[command_no][
                        command_list[command_no].find(' ') + 1:command_list[command_no].find('=') - 1]
            command_no = command_no + 1
            while 'ReportName' not in command_list[command_no]:
                command_no = command_no + 1
            reportNo = int(command_list[command_no][command_list[command_no].find('=') + 2:])
            center = np.array([float(para[0]), float(para[1])])
            sketch_curve.append(Circle(center, np.float(para[2]), reportNo))
            parameter_map[para_name] = Parameter(all_operation.__len__(), extrude_operation.__len__(), 'circle',
                                                 sketch_curve.__len__() - 1)
        # Spline_point
        elif 'CreateControlPoint' in command_list[command_no]:
            point_x = float(
                command_list[command_no][command_list[command_no].find('(') + 1:command_list[command_no].find(',')])
            point_y = float(
                command_list[command_no][command_list[command_no].find(',') + 1:command_list[command_no].find(')')])
            spline_point_list.append(np.array([point_x, point_y]))
        # Spline
        elif 'CreateSpline' in command_list[command_no]:
            while 'ReportName' not in command_list[command_no]:
                command_no = command_no + 1
            reportNo = int(command_list[command_no][command_list[command_no].find('=') + 2:])
            spline_point_list.reverse()
            sketch_curve.append(Spline(spline_point_list, reportNo))
            spline_point_list = []
        # 若CloseEdition，则矫正草图的顺逆顺序
        elif 'CloseEdition' in command_list[command_no]:

            # 若sketch_curve为空，则说明误操作，且草图数量减一
            if sketch_curve.__len__() == 0:
                command_no = command_no + 1
                sketch_offset_map[sketch_count] = -1
                continue
            # 由于可能因为误操作，出现多个CloseEdition，因此以最后一个为准
            close_sketch = command_list[command_no][:command_list[command_no].find('.')]
            # 若flag为真，则说明当前closeedition无效，跳过这条语句
            skip_flag = False
            # 向后扫描到下一个CloseEdition
            for i in range(command_no + 1, command_list.__len__()):
                if 'CloseEdition' in command_list[i]:
                    close_sketch_next = command_list[i][:command_list[i].find('.')]
                    # 若下一个与现在的草图相同，跳过此closeedition
                    if close_sketch == close_sketch_next:
                        skip_flag = True
                        break
                    else:
                        skip_flag = False
                        break
            if skip_flag:
                command_no = command_no + 1
                continue

            # 首先将curves划分为不同的loop， 假设都按逆时针绘制草图
            loop_start_point = []
            loop_cur_point = []
            loops = []
            begin_point = 0

            # 首先将所有圆剔除出来，因为圆不需要组成loop
            sketch_curve_copy = copy(sketch_curve)

            for i in range(0, sketch_curve_copy.__len__()):
                if isinstance(sketch_curve_copy[i], Circle):
                    loops.append([sketch_curve_copy[i]])
                    sketch_curve.remove(sketch_curve_copy[i])
            if sketch_curve.__len__() > 0:
                # 矫正其他点的顺逆关系
                for i in range(0, sketch_curve.__len__()):
                    if loop_start_point == []:
                        # 矫正开始点
                        if np.allclose(sketch_curve[i].start_point, sketch_curve[i + 1].start_point,
                                       atol=0.0001) or np.allclose(
                                sketch_curve[i].start_point, sketch_curve[i + 1].end_point, atol=0.0001):
                            sketch_curve[i].reverse()
                        # 否则，若开始curve不与下一curve有任何关系，则说明loop不连续，向下寻找到连续的点
                        elif not np.allclose(sketch_curve[i].end_point, sketch_curve[i + 1].start_point,
                                             atol=0.0001) or np.allclose(
                                sketch_curve[i].end_point, sketch_curve[i + 1].end_point, atol=0.0001):
                            j = i + 1
                            while j < sketch_curve.__len__():
                                if np.allclose(sketch_curve[i].end_point, sketch_curve[j].start_point,
                                               atol=0.0001) or np.allclose(
                                        sketch_curve[i].end_point, sketch_curve[j].end_point, atol=0.0001):
                                    sketch_curve[i + 1], sketch_curve[j] = sketch_curve[j], sketch_curve[i + 1]
                                    break
                                j = j + 1
                        # 开始点处理
                        loop_start_point = sketch_curve[i].start_point
                        loop_cur_point = sketch_curve[i].end_point
                        continue
                    # 若当前curve的结束点与上一curve的结束点重叠，reverse当前curve
                    if np.allclose(loop_cur_point, sketch_curve[i].end_point, atol=0.0001):
                        sketch_curve[i].reverse()
                    # 若当前curve的结束点与上一curve的开始点重叠，继续向下
                    if np.allclose(loop_cur_point, sketch_curve[i].start_point, atol=0.0001):
                        loop_cur_point = sketch_curve[i].end_point
                    # 若当前curve不与下一条curve相交，则可能是1.与开始点重合，形成了loop; 2.loop定义不连续
                    if i + 1 < sketch_curve.__len__() and not (
                            np.allclose(sketch_curve[i].end_point, sketch_curve[i + 1].start_point,
                                        atol=0.0001) or np.allclose(sketch_curve[i].end_point,
                                                                    sketch_curve[i + 1].end_point, atol=0.0001)):
                        # 若当前curve的结束点与最开始点重合，将之前的curves分为一个loop
                        if np.allclose(loop_start_point, sketch_curve[i].end_point, atol=0.0001):
                            loops.append(sketch_curve[begin_point:i + 1])
                            begin_point = i + 1
                            loop_start_point = []
                            loop_cur_point = []
                        # 否则当前curve既不与开始curve相交，又不与下一个curve相交，这种情况可能是出现了loop不连续的情况
                        # 此时进行遍历，找到下一个相交的点并与下一个curve位置交换，以达成连续
                        else:
                            j = i + 1
                            while j < sketch_curve.__len__():
                                if np.allclose(sketch_curve[i].end_point, sketch_curve[j].start_point,
                                               atol=0.0001) or np.allclose(sketch_curve[i].end_point,
                                                                           sketch_curve[j].end_point, atol=0.0001):
                                    sketch_curve[i + 1], sketch_curve[j] = sketch_curve[j], sketch_curve[i + 1]
                                    break
                                j = j + 1
                if begin_point < sketch_curve.__len__():
                    loops.append(sketch_curve[begin_point:])
            # 遍历loops，对同一loop中的spline进行标序以便区分开
            for i in range(loops.__len__()):
                no_count = 0
                for j in range(loops[i].__len__()):
                    if isinstance(loops[i][j], Spline):
                        no_count = no_count + 1
                        loops[i][j].no_in_loop = no_count
            all_loop = []
            for i in loops:
                all_loop.append(Loop(i))

            # this_loop = Loop(sketch_curve)
            # all_loop = [this_loop]

            sketch_profile = Profile(all_loop)
            # 矫正草图的顺逆时针，且将开始点矫正到原点，因为会打乱顺序，所以要修改no_map
            count = 1
            for this_loop in sketch_profile.children:
                for i in this_loop.children:
                    no_map['Sketch.' + repr(sketch_count) + ';' + repr(i.reportName)] = count
                    count = count + 1

            point = sketch_profile.start_point
            sketch_pos = point[0] * sketch_plane.x_axis + point[1] * sketch_plane.y_axis + sketch_plane.origin
            sketch_size = sketch_profile.bbox_size
            sketch_profile.normalize(size=ARGS_N)

            sketch_cache[close_sketch] = Sketch(sketch_plane, sketch_pos, sketch_size, sketch_profile)

        # 若为AddNewPad, 则为拉伸
        elif 'AddNewPad' in command_list[command_no]:
            # 因为默认定义时参数为20，所以要注意后面是否定义新的修改
            extrude_one = float(
                command_list[command_no][command_list[command_no].find(',') + 1:command_list[command_no].find(')')])
            extrude_two = 0
            sketch_name = command_list[command_no][
                          command_list[command_no].find('(') + 1:command_list[command_no].find(',')]
            isSymmetric, isInverse = False, False
            operation = EXTRUDE_OPERATIONS.index('NewBodyFeatureOperation')
            extent_type = EXTENT_TYPE.index('OneSideFeatureExtentType')

            cur_sketch = deepcopy(sketch_cache[sketch_name])
            # 先保存，若后续有修改再处理
            extrude_operation.append(Extrude(extrude_one, extrude_two, isSymmetric, isInverse, operation, extent_type,
                                             cur_sketch.sketch_plane, cur_sketch.sketch_pos,
                                             cur_sketch.sketch_size, cur_sketch.sketch_profile))
            extrude_pocket_point = extrude_operation.__len__() - 1
            parameter_map[command_list[command_no][
                          command_list[command_no].find(' ') + 1:command_list[command_no].find(' =')]] = Parameter(
                all_operation.__len__(), extrude_operation.__len__() - 1, 'pad')
            if not offset_flag:
                sketch_offset_map[sketch_count + 1] = 1
            offset_flag = False

        elif 'AddNewPocket' in command_list[command_no]:
            extrude_one = float(
                command_list[command_no][command_list[command_no].find(',') + 1:command_list[command_no].find(')')])
            extrude_two = 0
            sketch_name = command_list[command_no][
                          command_list[command_no].find('(') + 1:command_list[command_no].find(',')]
            isSymmetric, isInverse = False, False
            extent_type = EXTENT_TYPE.index('OneSideFeatureExtentType')
            cur_sketch = deepcopy(sketch_cache[sketch_name])
            extrude_operation.append(Pocket(extrude_one, extrude_two, isSymmetric, isInverse, extent_type,
                                            cur_sketch.sketch_plane, cur_sketch.sketch_pos,
                                            cur_sketch.sketch_size, cur_sketch.sketch_profile))
            extrude_pocket_point = extrude_operation.__len__() - 1
            parameter_map[command_list[command_no][
                          command_list[command_no].find(' ') + 1:command_list[command_no].find(' =')]] = Parameter(
                all_operation.__len__(), extrude_operation.__len__() - 1, 'pocket')
            if not offset_flag:
                sketch_offset_map[sketch_count + 1] = 1
            offset_flag = False
        elif 'AddNewShaft' in command_list[command_no]:
            select = []
            angle_one = 360
            angle_two = 0
            sketch_name = command_list[command_no][
                          command_list[command_no].find('(') + 1:command_list[command_no].find(')')]
            isInverse = False
            operation = EXTRUDE_OPERATIONS.index('NewBodyFeatureOperation')
            cur_sketch = deepcopy(sketch_cache[sketch_name])
            extrude_operation.append(Revolve(select, angle_one, angle_two, isInverse, operation,
                                             cur_sketch.sketch_plane, cur_sketch.sketch_pos,
                                             cur_sketch.sketch_size, cur_sketch.sketch_profile))
            extrude_pocket_point = extrude_operation.__len__() - 1
            parameter_map[command_list[command_no][
                          command_list[command_no].find(' ') + 1:command_list[command_no].find(' =')]] = Parameter(
                all_operation.__len__(), extrude_operation.__len__() - 1, 'shaft')
            if not offset_flag:
                # 因为旋转一定用的是自身新建草图的线作为轴，因此offset从自身开始而非下一个
                sketch_offset_map[sketch_count] = 1
            offset_flag = False
        elif 'AddNewAdd' in command_list[command_no]:
            extrude_operation[extrude_pocket_point].operation = EXTRUDE_OPERATIONS.index('JoinFeatureOperation')
        elif 'AddNewIntersect' in command_list[command_no]:
            extrude_operation[extrude_pocket_point].operation = EXTRUDE_OPERATIONS.index('IntersectFeatureOperation')
        elif 'AddNewRemove' in command_list[command_no]:
            extrude_operation[extrude_pocket_point].operation = EXTRUDE_OPERATIONS.index('CutFeatureOperation')
        elif '.FirstLimit' in command_list[command_no]:
            while '.Value' not in command_list[command_no]:
                command_no = command_no + 1
            extrude_one = float(command_list[command_no][command_list[command_no].find('=') + 2:])
            extrude_operation[extrude_pocket_point].extent_one = extrude_one
            parameter_map[command_list[command_no][:command_list[command_no].find('.')]] = Parameter(
                all_operation.__len__(), extrude_operation.__len__() - 1, 'extent_one')
        elif '.SecondLimit' in command_list[command_no]:
            while '.Value' not in command_list[command_no]:
                command_no = command_no + 1
            extrude_two = float(command_list[command_no][command_list[command_no].find('=') + 2:])
            extrude_operation[extrude_pocket_point].extent_two = extrude_two
            parameter_map[command_list[command_no][:command_list[command_no].find('.')]] = Parameter(
                all_operation.__len__(), extrude_operation.__len__() - 1, 'extent_two')
        elif '.FirstAngle' in command_list[command_no]:
            while '.Value' not in command_list[command_no]:
                command_no = command_no + 1
            angle_one = float(command_list[command_no][command_list[command_no].find('=') + 2:])
            extrude_operation[extrude_pocket_point].angle_one = angle_one
            parameter_map[command_list[command_no][:command_list[command_no].find('.')]] = Parameter(
                all_operation.__len__(), extrude_operation.__len__() - 1, 'angle_one')
        elif '.SecondAngle' in command_list[command_no]:
            while '.Value' not in command_list[command_no]:
                command_no = command_no + 1
            angle_two = float(command_list[command_no][command_list[command_no].find('=') + 2:])
            extrude_operation[extrude_pocket_point].angle_two = angle_two
            parameter_map[command_list[command_no][:command_list[command_no].find('.')]] = Parameter(
                all_operation.__len__(), extrude_operation.__len__() - 1, 'angle_two')
        elif '.IsSymmetric' in command_list[command_no]:
            if command_list[command_no][:command_list[command_no].find('.')] in parameter_map.keys():
                parameter = parameter_map[command_list[command_no][:command_list[command_no].find('.')]]
                body_point = parameter.body_point
                op_point = parameter.op_point
                para_type = parameter.para_type
                if all_operation.__len__() <= body_point:
                    extrude_operation[op_point].isSymmetric = command_list[command_no][
                                                              command_list[command_no].find('=') + 2:] == 'True'
                else:
                    all_operation[body_point][op_point].isSymmetric = command_list[command_no][
                                                                      command_list[command_no].find('=') + 2:] == 'True'
        elif 'catInverseOrientation' in command_list[command_no]:
            if command_list[command_no][:command_list[command_no].find('.')] in parameter_map.keys():
                parameter = parameter_map[command_list[command_no][:command_list[command_no].find('.')]]
                body_point = parameter.body_point
                op_point = parameter.op_point
                para_type = parameter.para_type
                if all_operation.__len__() <= body_point:
                    extrude_operation[op_point].isInverse = True
                else:
                    all_operation[body_point][op_point].isInverse = True
        elif 'catRegularOrientation' in command_list[command_no]:
            if command_list[command_no][:command_list[command_no].find('.')] in parameter_map.keys():
                parameter = parameter_map[command_list[command_no][:command_list[command_no].find('.')]]
                body_point = parameter.body_point
                op_point = parameter.op_point
                para_type = parameter.para_type
                if all_operation.__len__() <= body_point:
                    extrude_operation[op_point].isInverse = False
                else:
                    all_operation[body_point][op_point].isInverse = False
        # 选取坐标轴
        elif 'Set reference' in command_list[command_no] and (
                '.GetItem("横向")' in command_list[command_no] or '.GetItem("HDirection")' in command_list[command_no]):
            ref_name = command_list[command_no][
                       command_list[command_no].find(' ') + 1:command_list[command_no].find('=') - 1]
            select_cache[ref_name] = Select('Wire', 'OriginElements', 0, 1)
        elif 'Set reference' in command_list[command_no] and (
                '.GetItem("纵向")' in command_list[command_no] or '.GetItem("VDirection")' in command_list[command_no]):
            ref_name = command_list[command_no][
                       command_list[command_no].find(' ') + 1:command_list[command_no].find('=') - 1]
            select_cache[ref_name] = Select('Wire', 'OriginElements', 0, 2)
        # 选取坐标面
        elif '.PlaneXY' in command_list[command_no]:
            command_no = command_no + 1
            if 'Set reference' in command_list[command_no]:
                ref_name = command_list[command_no][
                           command_list[command_no].find(' ') + 1:command_list[command_no].find('=') - 1]
                select_cache[ref_name] = Select('Face', 'OriginElements', 0, 1)
            else:
                command_no = command_no - 1
        elif '.PlaneYZ' in command_list[command_no]:
            command_no = command_no + 1
            if 'Set reference' in command_list[command_no]:
                ref_name = command_list[command_no][
                           command_list[command_no].find(' ') + 1:command_list[command_no].find('=') - 1]
                select_cache[ref_name] = Select('Face', 'OriginElements', 0, 2)
            else:
                command_no = command_no - 1
        elif '.PlaneZX' in command_list[command_no]:
            command_no = command_no + 1
            if 'Set reference' in command_list[command_no]:
                ref_name = command_list[command_no][
                           command_list[command_no].find(' ') + 1:command_list[command_no].find('=') - 1]
                select_cache[ref_name] = Select('Face', 'OriginElements', 0, 3)
            else:
                command_no = command_no - 1
        # 旋转的Inverse很奇怪，每重新选择一次相同的轴引用则为一次颠倒
        elif '.RevoluteAxis' in command_list[command_no]:
            ref = command_list[command_no][command_list[command_no].find('=') + 2:]
            extrude_operation[extrude_pocket_point].select_list = deepcopy([select_cache[ref]])
            if not_first_flag:
                if ref == first_ref:
                    extrude_operation[extrude_pocket_point].isInverse = not extrude_operation[
                        extrude_pocket_point].isInverse
                else:
                    first_ref = ref
            else:
                not_first_flag = True
                first_ref = ref

        # 圆角，后面可能会修改，所以先保存
        elif 'AddNewSolidEdgeFilletWithConstantRadius' in command_list[command_no]:
            para_list = command_list[command_no][command_list[command_no].find('(') + 1:-1].split(', ')
            radius = float(para_list[2])
            select_mode = para_list[1]
            select_ref = {}
            extrude_operation.append(Fillet(select_ref, radius, select_mode))
        elif ('\\Radius' in command_list[command_no] or '\\半径' in command_list[command_no]) and \
                ('EdgeFillet' in command_list[command_no] or '倒圆角' in command_list[command_no]):
            command_no = command_no + 1
            extrude_operation[extrude_operation.__len__() - 1].radius = float(
                command_list[command_no][command_list[command_no].find('=') + 2:])
        elif '.EdgePropagation' in command_list[command_no]:
            extrude_operation[extrude_operation.__len__() - 1].edgePropagation = command_list[command_no][
                                                                                 command_list[command_no].find(
                                                                                     '=') + 2:]
        # 若出现选取，则为extrude_operation中最后一条指令的对象
        # 利用栈将命名取出
        elif 'CreateReferenceFromBRepName' in command_list[command_no]:
            # 先查看字符串内是否有" & "，若有，去掉
            while '" & "' in command_list[command_no]:
                command_list[command_no] = command_list[command_no][:command_list[command_no].find('" & "')] + \
                                           command_list[command_no][
                                           command_list[command_no].find('" & "') + len('" & "'):]
            select = None
            # 若既不是Edge也不是Face，则为空引用，用来预定义操作的
            if 'WireREdge' in command_list[command_no]:
                name_str = command_list[command_no][command_list[command_no].find('WireREdge'):]
                name_str = name_str[name_str.find('(') + 1:]
                select = parse_select_name(name_str, 'WireREdge', no_map, sketch_offset_map)
            elif 'REdge' in command_list[command_no]:
                name_str = command_list[command_no][command_list[command_no].find('REdge'):]
                name_str = name_str[name_str.find('(') + 1:]
                select = parse_select_name(name_str, 'Edge', no_map, sketch_offset_map)
            elif 'RFace' in command_list[command_no]:
                name_str = command_list[command_no][command_list[command_no].find('RFace'):]
                name_str = name_str[name_str.find('(') + 1:]
                select = parse_select_name(name_str, 'Face', no_map, sketch_offset_map)
            elif 'RSur' in command_list[command_no]:
                name_str = command_list[command_no][command_list[command_no].find('RSur'):]
                name_str = name_str[name_str.find('(') + 1:]
                select = parse_select_name(name_str, 'Face', no_map, sketch_offset_map)
            elif 'FSur' in command_list[command_no]:
                name_str = command_list[command_no][command_list[command_no].find('FSur'):]
                name_str = name_str[name_str.find('(') + 1:]
                select = parse_select_name(name_str, 'Face', no_map, sketch_offset_map)
            select_name = command_list[command_no][
                          command_list[command_no].find(' ') + 1:command_list[command_no].find(' =')]
            select_cache[select_name] = select
        elif 'NeutralElement' in command_list[command_no]:
            extrude_operation[extrude_operation.__len__() - 1].Neutral = deepcopy(select_cache[select_name])
        elif 'PullingDirectionElement' in command_list[command_no]:
            extrude_operation[extrude_operation.__len__() - 1].Parting = deepcopy(select_cache[select_name])
        elif 'AddFaceToDraft' in command_list[command_no] or 'AddFaceToRemove' in command_list[command_no] or \
                'AddObjectToFillet' in command_list[command_no] or 'AddElementToChamfer' in command_list[command_no]:
            extrude_operation[extrude_operation.__len__() - 1].select_list[select_name] = deepcopy(
                select_cache[select_name])
        # 若出现remove、withdraw等，说明取消了某选取
        elif 'WithdrawElementToChamfer' in command_list[command_no] or 'RemoveFaceToDraft' in command_list[
            command_no] or \
                'WithdrawFaceToRemove' in command_list[command_no] or 'WithdrawObjectToFillet' in command_list[
            command_no]:
            select_name = command_list[command_no][command_list[command_no].find(' ') + 1:]
            extrude_operation[extrude_operation.__len__() - 1].select_list.pop(select_name)
        elif 'AddNewChamfer' in command_list[command_no]:
            para_list = command_list[command_no][command_list[command_no].find('(') + 1:-1].split(', ')
            length1 = float(para_list[-2])
            angle_or_length2 = float(para_list[-1])
            mode = para_list[2]
            orientation = para_list[3]
            propagation = para_list[1]
            select_ref = {}
            extrude_operation.append(Chamfer(select_ref, length1, angle_or_length2, mode, propagation, orientation))
        elif '.Mode' in command_list[command_no] and 'chamfer' in command_list[command_no]:
            extrude_operation[extrude_operation.__len__() - 1].mode = command_list[command_no][
                                                                      command_list[command_no].find('=') + 2:]
            if extrude_operation[extrude_operation.__len__() - 1].mode == 'catTwoLengthChamfer':
                extrude_operation[extrude_operation.__len__() - 1].angle_or_length2 = 1
        elif '.Propagation' in command_list[command_no] and 'chamfer' in command_list[command_no]:
            extrude_operation[extrude_operation.__len__() - 1].propagation = command_list[command_no][
                                                                             command_list[command_no].find('=') + 2:]
        elif '.Orientation' in command_list[command_no] and 'chamfer' in command_list[command_no]:
            extrude_operation[extrude_operation.__len__() - 1].orientation = command_list[command_no][
                                                                             command_list[command_no].find('=') + 2:]
        elif '\\Length1' in command_list[command_no]:
            command_no = command_no + 1
            extrude_operation[extrude_operation.__len__() - 1].length1 = float(
                command_list[command_no][command_list[command_no].find('=') + 2:])
        elif '\\Angle' in command_list[command_no] or '\\Length2' in command_list[command_no]:
            command_no = command_no + 1
            extrude_operation[extrude_operation.__len__() - 1].angle_or_length2 = float(
                command_list[command_no][command_list[command_no].find('=') + 2:])
        elif '\\长度 1' in command_list[command_no]:
            command_no = command_no + 1
            extrude_operation[extrude_operation.__len__() - 1].length1 = float(
                command_list[command_no][command_list[command_no].find('=') + 2:])
        elif '\\角度' in command_list[command_no] or '\\长度 2' in command_list[command_no]:
            command_no = command_no + 1
            extrude_operation[extrude_operation.__len__() - 1].angle_or_length2 = float(
                command_list[command_no][command_list[command_no].find('=') + 2:])
        elif 'AddNewShell' in command_list[command_no]:
            para_list = command_list[command_no][command_list[command_no].find('(') + 1:-1].split(', ')
            select_ref = {}
            internalThickness = float(para_list[1])
            externalThickness = float(para_list[2])
            shell = Shell(select_ref, internalThickness, externalThickness)
            extrude_operation.append(shell)
        elif 'InternalThickness' in command_list[command_no]:
            command_no = command_no + 1
            extrude_operation[extrude_operation.__len__() - 1].thickness = float(
                command_list[command_no][command_list[command_no].find('=') + 2:])
        elif 'ExternalThickness' in command_list[command_no]:
            command_no = command_no + 1
            extrude_operation[extrude_operation.__len__() - 1].second_thickness = float(
                command_list[command_no][command_list[command_no].find('=') + 2:])
        # 若.Value单独出现，则可能为单独修改，也可能为不需要考虑的参数定义
        elif '.Value' in command_list[command_no] or '.MirroringPlane' in command_list[command_no] or '.SetData' in \
                command_list[command_no]:
            if command_list[command_no][:command_list[command_no].find('.')] in parameter_map.keys():
                parameter = parameter_map[command_list[command_no][:command_list[command_no].find('.')]]
                body_point = parameter.body_point
                op_point = parameter.op_point
                para_type = parameter.para_type
                if para_type == 'extent_one':
                    if all_operation.__len__() <= body_point:
                        extrude_operation[op_point].extent_one = float(
                            command_list[command_no][command_list[command_no].find('=') + 2:])
                    else:
                        all_operation[body_point][op_point].extent_one = float(
                            command_list[command_no][command_list[command_no].find('=') + 2:])
                elif para_type == 'extent_two':
                    if all_operation.__len__() <= body_point:
                        extrude_operation[op_point].extent_two = float(
                            command_list[command_no][command_list[command_no].find('=') + 2:])
                    else:
                        all_operation[body_point][op_point].extent_two = float(
                            command_list[command_no][command_list[command_no].find('=') + 2:])
                elif para_type == 'angle_one':
                    if all_operation.__len__() <= body_point:
                        extrude_operation[op_point].angle_one = float(
                            command_list[command_no][command_list[command_no].find('=') + 2:])
                    else:
                        all_operation[body_point][op_point].angle_one = float(
                            command_list[command_no][command_list[command_no].find('=') + 2:])
                elif para_type == 'angle_two':
                    if all_operation.__len__() <= body_point:
                        extrude_operation[op_point].extent_two = float(
                            command_list[command_no][command_list[command_no].find('=') + 2:])
                    else:
                        all_operation[body_point][op_point].angle_two = float(
                            command_list[command_no][command_list[command_no].find('=') + 2:])
                elif para_type == 'DraftAngle':
                    if all_operation.__len__() <= body_point:
                        extrude_operation[op_point].DraftAngle = float(
                            command_list[command_no][command_list[command_no].find('=') + 2:])
                    else:
                        all_operation[body_point][op_point].DraftAngle = float(
                            command_list[command_no][command_list[command_no].find('=') + 2:])
                elif para_type == 'MirrorPlane':
                    select_name = command_list[command_no][command_list[command_no].find('=') + 2:]
                    if all_operation.__len__() <= body_point:
                        extrude_operation[op_point].select_list = deepcopy([select_cache[select_name]])
                    else:
                        all_operation[body_point][op_point].select_list = deepcopy([select_cache[select_name]])
                elif para_type == 'circle':
                    para_list = command_list[command_no].split(', ')
                    sketch_curve[parameter.curve_point].center = np.array(
                        [float(para_list[0][para_list[0].find(' ') + 1:]), float(para_list[1])])
                    sketch_curve[parameter.curve_point].radius = float(para_list[2])
        # 若.DraftValue单独出现，则可能为单独修改，也可能为不需要考虑的参数定义
        elif '.DraftAngle' in command_list[command_no]:
            while '.Value' not in command_list[command_no]:
                command_no = command_no + 1
            draft_angle = float(command_list[command_no][command_list[command_no].find('=') + 2:])
            extrude_operation[extrude_operation.__len__() - 1].DraftAngle = draft_angle
            parameter_map[command_list[command_no][:command_list[command_no].find('.')]] = Parameter(
                all_operation.__len__(), extrude_operation.__len__() - 1, 'DraftAngle')
        elif 'AddNewDraft' in command_list[command_no]:
            para_list = command_list[command_no][command_list[command_no].find('(') + 1:-1].split(', ')
            draft = Draft({}, {}, {}, [float(para_list[4]), float(para_list[5]), float(para_list[6])],
                          float(para_list[8]), False, para_list[2], para_list[7], para_list[9])
            extrude_operation.append(draft)
        elif 'SetPullingDirection' in command_list[command_no]:
            command_str = command_list[command_no][command_list[command_no].find(' ') + 1:]
            para_list = command_str.split(', ')
            extrude_operation[extrude_operation.__len__() - 1].dir = [float(para_list[0]), float(para_list[1]),
                                                                      float(para_list[2])]
        elif 'AddNewMirror' in command_list[command_no]:
            # 镜面操作是现选取再操作，而非先使用空引用操作
            select_name = command_list[command_no][command_list[command_no].find('(') + 1:-1]
            select_list = {select_name: select_cache[select_name]}
            mirror = Mirror(select_list)
            extrude_operation.append(mirror)
            parameter_map[command_list[command_no][:command_list[command_no].find('.')]] = Parameter(
                all_operation.__len__(), extrude_operation.__len__() - 1, 'MirroringPlane')
        command_no = command_no + 1

    if extrude_operation != []:
        all_operation.append(extrude_operation)
    all_operation = np.array(all_operation)
    all_operation = np.concatenate(all_operation, axis=0)

    # 将所有select_list从字典转为list
    for i in range(all_operation.__len__()):
        if isinstance(all_operation[i], Chamfer) or isinstance(all_operation[i], Fillet) or \
                isinstance(all_operation[i], Shell) or isinstance(all_operation[i], Draft) or \
                isinstance(all_operation[i], Mirror):
            # select_dic = all_operation[i].select_list
            # cur_list = select_dic.values()
            all_operation[i].select_list = list(all_operation[i].select_list.values())

    macro_seq = Macro_Seq(all_operation, bounding_size)
    macro_seq.normalize()
    macro_seq.numericalize(n=ARGS_N)
    macro_vec = macro_seq.to_vector(MAX_N_EXT, MAX_N_LOOPS, MAX_N_CURVES, MAX_TOTAL_LEN, pad=False)

    ##################################################################################################

    cad = macro_seq.from_vector(macro_vec, is_numerical=True, n=ARGS_N)
    part = doc.part
    create_CAD_CATIA(cad, catia, part)

    doc.close()

    return macro_vec

input_paths = 'C:\\Users\\45088\\Desktop\\1.4Whu数据集汇总'
output_path = './'
input_trunks = os.listdir(input_paths)
for input_trunk in input_trunks:
    files_path = os.listdir(input_paths + '\\' + input_trunk)

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if input_trunk != 'Whu_0020_MAC_v00':
        continue
    for cur_file in files_path:
        catia = win32com.client.Dispatch('catia.application')
        catia.visible = 0
        doc = catia.documents.add('Part')
        try:
            macro_vec = process_on(input_paths + '\\' + input_trunk + '\\' + cur_file, catia, doc)
            print(cur_file, ":OK")
        except:
            print(cur_file, ":Failed")
            fileName = input_trunk + '.txt'
            with open(fileName, 'a') as file:
                file.write(cur_file + '\n')
