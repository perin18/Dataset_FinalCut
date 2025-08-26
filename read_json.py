import json

# 文件路径
path = 'D:\\Dataset\\Fusion 360\\r1.0.1\\reconstruction\\20203_7e31e92a_0000'

# 打开文件,r是读取的意思,encoding是指定编码格式
with open(path + '.json', 'r', encoding='utf-8') as fp:

    data = json.load(fp)

print(data)
