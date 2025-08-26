import h5py
import os
from copy import deepcopy
from Catia_utils import *
from CAD_Class import *
from Geometry_utils import *
in_path = 'C:\\Users\\45088\\Desktop\\WHU_dataset\\vec_data'
out_path = 'C:\\Users\\45088\\Desktop\\WHU_dataset\\valid_data\\vec_data_100_simple'

delete_op_count = 0
delete_command_count = 0
delete_select_count = 0
total_select_op_count = 0
total_command_count = 0
total_select_count = 0
file_count = 0

# 递归查看选取命名是否复杂，若是，返回True
def recursive_find_com(select):
    if len(select.no_shared_included) > 0 or len(select.all_oriented_included) > 0 or select.all_partially_included is not None:
        return True
    else:
        for i in select.operation_list:
            if recursive_find_com(i):
                return True

def delete_op(op):
    this_count = 0
    # Draft特殊处理
    if isinstance(op, Draft):
        if recursive_find_com(op.Neutral):
            return None, 0
        new_select = []
        for one_select in op.select_list:
            if not recursive_find_com(one_select):
                new_select.append(one_select)
        this_count = len(op.select_list) - len(new_select)
        if len(op.select_list) == 0:
            return None, 0
        op.select_list = deepcopy(new_select)
    else:
        new_select = []
        for one_select in op.select_list:
            if not recursive_find_com(one_select):
                new_select.append(one_select)
        this_count = len(op.select_list) - len(new_select)
        if len(new_select) == 0:
            return None, 0
        op.select_list = deepcopy(new_select)
    # 3.在选取操作中递归判断每一个选取对象是否包含混淆，若是则删除该选取，若选取对象为空，删除操作
    return deepcopy(op), this_count



input_paths = os.listdir(in_path)
for input_path in input_paths:
    files = os.listdir(in_path + '\\' + input_path)
    if not os.path.exists(out_path + '\\' + input_path):
        os.makedirs(out_path + '\\' + input_path)
    for file in files:
        file_count = file_count + 1
        # if file_count <= 103:
        #     continue
        ori_vec = h5py.File(in_path + '\\' + input_path + '\\' + file, 'r')['vec'][:]

        # 1.读取向量转为类
        cad = Macro_Seq.from_vector(ori_vec, is_numerical=True, n=256)
        new_extrude_operation = []
        # 2.在类中查找带选取的操作
        for operation in cad.extrude_operation:
            if isinstance(operation, Chamfer) or isinstance(operation, Fillet) or \
                    isinstance(operation, Shell) or isinstance(operation, Mirror) or isinstance(operation, Draft):
                total_select_op_count = total_select_op_count + 1
                total_select_count = total_select_count + len(operation.select_list)
                new_op, this_delete_select_count = delete_op(operation)
                delete_select_count = delete_select_count + this_delete_select_count
                if new_op is None:
                    delete_op_count = delete_op_count + 1
                else:
                    new_extrude_operation.append(new_op)
            else:
                new_extrude_operation.append(operation)
        cad.extrude_operation = deepcopy(new_extrude_operation)
        # 4.转回向量并保存到output_path
        cad.numericalize()
        macro_vec = cad.to_vector(MAX_N_EXT, MAX_N_LOOPS, MAX_N_CURVES, MAX_TOTAL_LEN, pad=False)
        if macro_vec.shape[0] <= 100:
            with h5py.File(out_path + '\\' + input_path + '\\' + file) as f:
                f['vec'] = macro_vec
        # 5.统计
        delete_command_count = delete_command_count + ori_vec.shape[0] - macro_vec.shape[0]
        total_command_count = total_command_count + ori_vec.shape[0]
        print(file_count, ' ', file, ': OK')
        for i in range(macro_vec.shape[0]):
            if 16 <= macro_vec[i][0] <= 21:
                print(file_count, ' ', file, '!!!!!!!!!!!!!!!!!!!!')
                print(file_count, ' ', file, '!!!!!!!!!!!!!!!!!!!!')
                print(file_count, ' ', file, '!!!!!!!!!!!!!!!!!!!!')
                print(file_count, ' ', file, '!!!!!!!!!!!!!!!!!!!!')
                print(file_count, ' ', file, '!!!!!!!!!!!!!!!!!!!!')

print('Delete operation:', delete_op_count)
print('Delete command:', delete_command_count)
print('Delete select:', delete_select_count)
print('Total select operation:', total_select_op_count)
print('Total command:', total_command_count)
print('Total select:', total_select_count)