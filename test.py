import win32com.client

# 创建一个catia COM对象
catia = win32com.client.Dispatch('catia.Application')

# 创建一个新的文档
document = catia.ActiveDocument
part = document.part
shapeFactory = part.ShapeFactory
# BrepName = "Edge:(Face:(Brp:(Pad.1;0:(Brp:(Sketch.1;1)));None:();Cf11:());Face:(Brp:(Pad.1;0:(Brp:(Sketch.1;2)));None:();Cf11:());AllOrientedIncluded:(Limits1:(Brp:(Pad.1;1));Limits2:(Brp:(Pad.1;2)));Cf11:())"
BrepName = "Edge:(Face:(Brp:(Pad.1;0:(Brp:(Sketch.1;1)));AllOrientedIncluded:(Brp:(Pocket.1;0:(Brp:(Sketch.2;2)));Brp:(Pad.1;2);Brp:(Pad.1;0:(Brp:(Sketch.1;2)));Brp:(Pad.1;1));Cf11:());Face:(Brp:(Pad.1;0:(Brp:(Sketch.1;2)));None:();Cf11:());None:(Limits1:();Limits2:());Cf11:())"
# last_name = "RSur:(" + BrepName + ";WithTemporaryBody;WithoutBuildError;WithSelectingFeatureSupport;MFBRepVersion_CXR15)"
last_name = "REdge:(" + BrepName + ";WithTemporaryBody;WithoutBuildError;WithSelectingFeatureSupport;MFBRepVersion_CXR15)"
temp_reference = part.CreateReferenceFromName(last_name)


constRadEdgeFillet1 = shapeFactory.AddNewSolidEdgeFilletWithConstantRadius(temp_reference, 1, 1)

part.update()