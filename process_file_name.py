import os
import glob
from shutil import copyfile

flag_0_1 = 1
if flag_0_1 == 0:
    input_path = 'D:\\Dataset\\Random_Argu\\fuse'
    output_path = 'D:\\Dataset\\Random_Argu\\final'

    file_count = 0
    input_trunk = os.listdir(input_path)
    for trunk in input_trunk:
        files_path = os.listdir(os.path.join(input_path, trunk))
        for file in files_path:
            target_filename = str(file_count).zfill(8) + '.h5'
            target_trunkname = str(int((file_count - (file_count % 1419)) / 1419)).zfill(4)
            final_path = os.path.join(output_path, target_trunkname)
            if not os.path.exists(final_path):
                os.makedirs(final_path)
            copyfile(os.path.join(input_path, trunk, file), os.path.join(final_path, target_filename))
            file_count = file_count + 1
else:
    input_path = 'D:\\Dataset\\Ours'
    output_path = 'D:\\Dataset\\Random_Argu\\final'

    file_count = 0
    input_trunk = os.listdir(input_path)
    for trunk in input_trunk:
        files_path = os.listdir(os.path.join(input_path, trunk))
        for file in files_path:
            target_filename = str(file_count + 100000000).zfill(8) + '.h5'
            target_trunkname = str(int((file_count - (file_count % 1419)) / 1419) + 100).zfill(4)
            final_path = os.path.join(output_path, target_trunkname)
            if not os.path.exists(final_path):
                os.makedirs(final_path)
            copyfile(os.path.join(input_path, trunk, file), os.path.join(final_path, target_filename))
            file_count = file_count + 1