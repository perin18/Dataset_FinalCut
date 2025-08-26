from plotly.graph_objs import Bar, Layout
from plotly import  offline
import numpy as np

# x_values = ['≤10', '10~20', '20~30', '30~40', '40~50', '50~60', '60~70', '70~80', '80~90', '90~100', '=100']
# data = [Bar(x=x_values, y=(np.array(list(target.values()))) * 100)]
#
# x_axis = {'title': 'Sequence Length'}
# y_axis = {'title': 'Percentage(*100％)'}
#
# my_layout = Layout(title='指令数量', xaxis=x_axis, yaxis=y_axis)
# offline.plot({'data': data, 'layout': my_layout}, filename='result.html')

import matplotlib.pyplot as plt


# target = {0: 0.0653, 1: 0.2479, 2: 0.2097, 5: 0.0695, 3: 0.1619, 6: 0.0573, 4: 0.1131, 7: 0.0351, 8: 0.0226, 9: 0.0167, 10: 0.0009}
#
# target[9] = target[9] + target[10]
#
# target.pop(10)

target = {0: 0.1458, 2: 0.1783, 3: 0.0549, 1: 0.5858, 7: 0.0015, 4: 0.0206, 5: 0.0087, 8: 0.0006, 6: 0.0037, 9: 0.0001}

name_list = ['≤10', '10~20', '20~30', '30~40', '40~50', '50~60', '60~70', '70~80', '80~90', '90~100']

num_list = np.round(np.array(list(target.values())) * 100, 2)

rects = plt.bar(range(len(num_list)), num_list, color='royalblue')

# X轴标题

index = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# index=[float(c)+0.4 for c in index]

plt.ylim(ymax=num_list.max(), ymin=0)

plt.xticks(index, name_list)

plt.xlabel("Sequence Length") #X轴标签

plt.ylabel("Percentage(%)") #X轴标签

for rect in rects:
    height = rect.get_height()

    plt.text(rect.get_x() + rect.get_width() / 2, height, str(height)+'%', ha='center', va='bottom')

plt.show()
