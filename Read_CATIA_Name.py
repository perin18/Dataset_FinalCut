import win32com.client
import time
from Catia_utils import get_plane

catia = win32com.client.Dispatch('catia.application')
partDocument1 = catia.ActiveDocument
selection = partDocument1.selection
part = partDocument1.part
shapeFactory1 = part.ShapeFactory


c = True
while c is True:
    selection = partDocument1.selection
    tar = selection.Item2(1)
    print(tar.reference.displayname)

    prompt = input("Continue? (Y/N):")
    if prompt.lower()[0] == 'n':
        c = False
    else:
        c = True
