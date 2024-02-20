import maya.cmds as cmds
import maya.mel as mel

"""Tis is a python tool to streamline the process of rigging a character """

WhiteList = []
CurrentCreated = []
AllCreated = []

def FreezeTransforms(Anim):
	cmds.delete(Anim, constructionHistory=True)
	cmds.makeIdentity(Anim, apply=True, t=1, r=1, s=1, n=0)
	
def FindChildren(Joint, JointList):
    """ Recursively build a list of all the joints """
	Children = cmds.listRelatives(Joint, fullPath=True, type='joint') or []
	if Children:
		for child in Children:
			JointList.append(child)
			FindChildren(child, JointList)
	return JointList
    
def GetCurrentSelection(type):
    """ get the current scene selection filtered by type """
	selected = cmds.ls(sl=True,long=True, type=type) or []
	try:
		selected.append(0)
		selected.remove(0)
	except:
		string = selected
		selected = []
		selected[0] = string
	return selected
	
def FindShortName(LongName):
	ShortName = LongName
	if '|' in LongName:
		ShortName = LongName.split("|")[-1]
	return ShortName
	
def FindParentJoint(Joints):
    CurrentBest = 0
    CurrentHighScore = 0
    for i in range(len(Joints)):
    	Children = cmds.listRelatives(Joints[i], fullPath=False, ad=True, type='joint')
    	if Children:
    		if len(Children) > CurrentHighScore:
    			CurrentBest = Joints[i]
    			CurrentHighScore = len(Children)
    return CurrentBest
        
def SortJointChain(Joints):
    """ sorts a list of joints in a random order into hierarchhical order """
	ChainLength = len(Joints)
	SortedJoints = []
	for i in range(ChainLength):
		SortedJoints.append(0)
	for i in range(ChainLength):
		Children = cmds.listRelatives(Joints[i], fullPath=True, ad=True, type='joint')
		if Children:
			ChildrenInJoints = []
			for j in range(len(Joints)):
				if Joints[j] in Children:
					ChildrenInJoints.append(Joints[j])
			SortedJoints[ChainLength-len(ChildrenInJoints)-1] = Joints[i]
		else:
			SortedJoints[-1] = Joints[i]
	return SortedJoints
		
def CombineAnimCurves(Anim):
    """ Combines the individual NURBS curves into a single object """
	Curves = cmds.listConnections(Anim[-1], shapes=True, source=False, type = 'shape')
	ParentTransform = cmds.listRelatives(Curves[0], fullPath=True, parent=True)
	for i in range(len(Curves)):
		shape = Curves[i]
		CurrentTransform = cmds.listRelatives(Curves[i], fullPath=False, parent=True)
		if i>0:
			cmds.parent(shape, ParentTransform, shape=True, relative=True)
	AnimParent = cmds.listRelatives(ParentTransform, fullPath=True, parent=True)
	ParentTransform = cmds.parent(ParentTransform, world=True)
	cmds.delete(AnimParent)
	return ParentTransform
		
def MatchTransformGrp(Anim, Joint):
    """ match the transforms of an anim control curve and make a group to add it to """
	cmds.matchTransform(Anim, Joint, pivots=False, scale=False, rot=True, pos=True)
	Grp = cmds.group(name = Anim+'_grp', empty=True)
	cmds.matchTransform(Grp, Joint, pivots=False, scale=False, rot=True, pos=True)
	cmds.parent(Anim, Grp)
	return Anim

def ShortName(LongName):
	ShortName = 0
	try:
		shortName = (LongName.split("|")[-1])
		shortName = shortName.replace('|', '')
	except:
		shortName = (LongName[0].split("|")[-1])
		shortName = shortName.replace('|', '')
	return shortName
	
def FindMiddleJoints(Joints):
    """ Given a start and end point of a joint chain, find the full chain. 
    Used when duplicating chains for IK and FK switching """
	StartJoint = Joints[0]
	EndJoint = Joints[-1]
	startJointChildren = cmds.listRelatives(StartJoint, fullPath=True, ad=True, type='joint')
	endJointChildren = cmds.listRelatives(EndJoint, fullPath=True, allDescendents=True)
	
	JointsToDuplicate = [StartJoint]
	for i in range(len(startJointChildren)):
		try:
			if startJointChildren[i] not in endJointChildren:
				JointsToDuplicate.append(startJointChildren[i])
		except:
			JointsToDuplicate = [StartJoint, EndJoint]
	return JointsToDuplicate
	
#--------------------------------------------------------------------------------------------------#

def DuplicateJointChain(Joints, Prefix):
    """ Used when duplicating chains for IK and FK switching """
	JointsToDuplicate = FindMiddleJoints(Joints)	
	cmds.select(clear=True)
	for current in JointsToDuplicate:
		cmds.select(current, add=True)
		
	selected = cmds.ls(sl=True,long=True, type='joint') or []
	newJoints = cmds.duplicate(parentOnly=True)
	newJoints = cmds.ls(sl=True,long=True, type='joint') or []
	newJoints = SortJointChain(newJoints)
	for i in range(len(newJoints)): #this loop goes backwards, otherwise it cant find children
		if '|' in newJoints[len(newJoints)-i-1]:
			shortName = (selected[len(newJoints)-i-1].split("|")[-1])
		else:
			shortName = newJoints[len(newJoints)-i-1]
		newJoints[len(newJoints)-i-1] = cmds.rename(newJoints[len(newJoints)-i-1], Prefix+shortName)
		if (i == len(newJoints)-1):
			newJoints = cmds.ls(sl=True,long=True, type='joint') or []
	return newJoints
	
def MakeControlsIK(Joints):
	Anims = []
	Joints = SortJointChain(Joints)
	name = ShortName(Joints[-1])
	print(name)
	if 'IK_' in name:
		name = name.replace('IK_', '')

	WristSquare = cmds.nurbsSquare(name='IK_Anim%s' %name, sl1=10, sl2=10)
	cmds.setAttr(WristSquare[1]+'.normalX', 1)
	cmds.setAttr(WristSquare[1]+'.normalY', 0)
	cmds.setAttr(WristSquare[1]+'.normalZ', 0)
	
	WristSquare = CombineAnimCurves(WristSquare)
	WristSquare = MatchTransformGrp(WristSquare[0], Joints[-1])
	WristSquare = cmds.rename(WristSquare, 'IK_Anim_%s' %name)
	try:
		cmds.connectAttr( '%s.rotate'%WristSquare[0], '%s.rotate' %Joints[-1])
	except:
		cmds.connectAttr( '%s.rotate'%WristSquare, '%s.rotate' %Joints[-1])
	Anims.append(WristSquare)
	name = ShortName(Joints[-2])
	ElbowSphere = cmds.sphere(name='IK_PoleVector_%s' %name)
	ElbowSphere = MatchTransformGrp(ElbowSphere[0], Joints[-2])
	Anims.append(ElbowSphere)
	print('IK anims created')
	return Anims
	
def MakeConstraintsIK(Joints, Anims):
	if len(Joints) == 3:
		Joints = SortJointChain(Joints)
		cmds.select(Joints[0], Joints[2])
		IK = cmds.ikHandle(Joints[0], Joints[2])
		cmds.setAttr(IK[0]+'.visibility', 0)
		Name = str(ShortName(Joints[-1]))
		IK = cmds.rename(Name + '_Handle')
		cmds.select(Anims[0], add=True)
		cmds.parent()
		IK = cmds.ls(sl=True,long=True, type='ikHandle') or []
		Anims[1] = Anims[1].replace('|','')
		cmds.poleVectorConstraint(Anims[1], IK[0])
	print('IK constraints created')
		
def MakeControlFK(Joint, ParentAnim):
	ShortName = []
	try:
		ShortName = Joint.split("|")[-1]
	except:
		ShortName = Joint[0].split("|")[-1]
		Joint = Joint[0]
	jointRotation = cmds.xform(Joint, query=True, rotation=True, worldSpace=True)
	jointTranslation = cmds.xform(Joint, query=True, translation=True, worldSpace=True)
	NurbsCircle = cmds.circle(nr=(1,0,0), c=(0, 0, 0), r=5, n='FK_Anim_%s' % ShortName)
	cmds.xform(NurbsCircle[0], translation=jointTranslation, worldSpace=True)
	cmds.xform(NurbsCircle[0], rotation=jointRotation, worldSpace=True)
	
	Grp = cmds.group(empty=True, n='FK_Anim_%s_grp' % ShortName)
	cmds.xform(Grp, translation=jointTranslation, worldSpace=True)
	cmds.xform(Grp, rotation=jointRotation, worldSpace=True)
	cmds.parent(NurbsCircle[0], Grp)
	NurbsCircle[0] = NurbsCircle[0].replace('|', '')
		
	cmds.orientConstraint(NurbsCircle[0], Joint, mo=True)
	cmds.pointConstraint(NurbsCircle[0], Joint, mo=True)
	handle = (cmds.listConnections(Grp + ".matrix") or [None])[0]
	
	if ParentAnim:
	    cmds.parent(Grp, ParentAnim[0])
	
	return NurbsCircle

def Rename(Joint):
    ShortName = Joint.split("|")[-1]
    newName = cmds.rename(Joint, 'FK_%s' %ShortName)
    return newName
    
def Search(Joint, PrevAnim):
	ChildJoints = cmds.listRelatives(Joint, fullPath=True, type='joint')
	IgnoreLeaf = cmds.checkBox('IgnoreLeaf', query=True, value=True)
	if ChildJoints:
		for children in ChildJoints:
			ChJ = cmds.listRelatives(children, fullPath=True, type='joint')
			if ChJ or not IgnoreLeaf:
				NewAnim = MakeControlFK(children, PrevAnim)
				Search(children, NewAnim)
			
def RenameHierarchy(Joint, Prefix):
	print(Joint)
	ShortName = Joint.split("|")[-1]
	newName = []
	LongName = 0
	if Prefix not in ShortName:
		newName = cmds.rename(Joint, Prefix+ShortName)
		LongName = cmds.ls(sl=True,long=True, type='joint') or []
	else:
		newName = ShortName
	ChildJoints = cmds.listRelatives(newName, fullPath=True, type='joint')
	if ChildJoints:
		for children in ChildJoints:
			RenameHierarchy(children, Prefix)
	return LongName
	
def MakeAnimIKFK(Joints):
	Curve = cmds.nurbsSquare(name='IK-FK_switch', sl1=10, sl2=10, nr=(0, 1, 0))
	Curve = CombineAnimCurves(Curve)
	WristLocation = cmds.xform(Joints[-1], query=True, translation=True, worldSpace=True)
	ElbowLocation = cmds.xform(Joints[-2], query=True, translation=True, worldSpace=True)
	
	CurveLocation = [0,0,0]
	for i in range(3):
		CurveLocation[i] = (WristLocation[i] - ElbowLocation[i])/2 + ElbowLocation[i]

	node = cmds.createNode('pickMatrix', name='pickMatrix'+Joints[-2])
	cmds.setAttr(node+'.useScale', 0)
	cmds.setAttr(node+'.useShear', 0)
	cmds.connectAttr(Joints[-1]+'.worldMatrix[0]', '%s.inputMatrix' %node) 
	cmds.connectAttr('%s.outputMatrix' %node, '%s.offsetParentMatrix' %Curve[0]) 
	cmds.addAttr(Curve, longName='IKFK', shortName='IKFK', at='float', dv=0, min=0, max=1, k=True)
	print('IK/FK switch created')
	return Curve
	
def FindChildNamesAfterParenting(OriginalJoints, ParentedJoint):
	NewJoints = []
	try:
		cmds.select(ParentedJoint)
		NewJoints = cmds.ls(sl=True,long=True, type='joint') or []
		print(NewJoints)
	except:
		print('no joint could be selected  '+ParentedJoint)
		return
	NewChildrenL = []
	NewChildrenS = []
	for i in range(len(OriginalJoints)):
		if i==0:
			NewChildrenL = cmds.listRelatives(NewJoints[0], fullPath=True, ad=True, type='joint')
			NewChildrenS = cmds.listRelatives(NewJoints[0], fullPath=False, ad=True, type='joint')
		else:
			print(NewChildrenS)
			int=i-1
			print(int)
			OriginalShort = ShortName(OriginalJoints[i])
			if OriginalShort in NewChildrenS[i-1]:
				NewJoints.append(NewChildrenL[i-1])
	return NewJoints
		

def AddToSwitch(*args):
	JointsSelected = cmds.ls(sl=True,long=True, type='joint') or []
	AllSelected = cmds.ls(sl=True,long=True) or []
	SwitchAnim = 0

	for i in range(len(AllSelected)):
		if AllSelected[i] not in JointsSelected:
			SwitchAnim = AllSelected[i]
	
	for joints in JointsSelected:
		connections = cmds.listConnections(joints+'.rotate', d=False)
		if connections:
			print('There is already an incoming connection to '+joints)
			break
	#Make FK
	FKChain = DuplicateJointChain(JointsSelected, 'FK_')
	ParentJoint = cmds.listRelatives(FKChain, fullPath=True, p=True, type='joint')
	Short = ShortName(ParentJoint[0])
	try:
		temp = cmds.parent(FKChain[0], 'FK_'+Short)
		FKChain[0] = temp[0]
	except:
		try:
			temp = cmds.parent(FKChain[0], 'FK_'+Short+'1')
			FKChain[0] = temp[0]
		except:
			temp = cmds.parent(FKChain[0], world=True)
			FKChain[0] = temp[0]
			
	FKChain = FindChildNamesAfterParenting(JointsSelected, FKChain[0])
	print(FKChain)
	FKAnim = MakeControlFK(FKChain[0], 0)
	
	Search(FKChain[0], FKAnim)
	FKAnims = cmds.listRelatives(FKAnim, fullPath=True, ad=True, type='nurbsCurve')

	#Make IK
	IKChain = DuplicateJointChain(JointsSelected, 'IK_')
	print(IKChain)
	ParentJoint = cmds.listRelatives(IKChain, fullPath=True, p=True, type='joint')
	Short = ShortName(ParentJoint[0])
	try:
		temp = cmds.parent(IKChain[0], 'IK_'+Short)
		IKChain[0] = temp[0]
	except:
		try:
			temp = cmds.parent(IKChain[0], 'IK_'+Short+'1')
			IKChain[0] = temp[0]
		except:
			temp = cmds.parent(IKChain[0], world=True)
			IKChain[0] = temp[0]
	IKChain = FindChildNamesAfterParenting(JointsSelected, IKChain[0])
	print(IKChain)
	for i in range(len(JointsSelected)):
		short = ShortName(JointsSelected[i])
		
		blendNode = cmds.createNode('blendColors', name='blendIKFK'+short)
		try:
			cmds.connectAttr(SwitchAnim+'.IKFK', blendNode+'.blender')
		except:
			print('No usable anim selected')
			break
			
		#cmds
		cmds.connectAttr(IKChain[i]+'.rotate', blendNode+'.color2')
		cmds.connectAttr(FKChain[i]+'.rotate', blendNode+'.color1')
		cmds.connectAttr(blendNode+'.output', JointsSelected[i]+'.rotate')
	
	MinusNode = cmds.createNode('plusMinusAverage')
	cmds.connectAttr(SwitchAnim+'.IKFK', MinusNode+'.input3D[1].input3Dx')
	if (FKAnims):
		for i in range(len(FKAnims)):
			curveParent = cmds.listRelatives(FKAnims[i], fullPath=True, parent=True)
			cmds.connectAttr(SwitchAnim+'.IKFK', curveParent[0]+'.visibility')
	
	for i in range(len(FKChain)):
		cmds.connectAttr(SwitchAnim+'.IKFK', FKChain[i]+'.visibility')

	
	cmds.setAttr(MinusNode+'.operation', 2)
	cmds.setAttr(MinusNode+'.input3D[0].input3Dx', 1)

	for i in range(len(IKChain)):
		cmds.connectAttr(MinusNode+'.output3Dx', IKChain[i]+'.visibility')
		
	print('Addition to IK/FK completed')
		
	
#--------------------------------------------------------------------------------------------------#
# Deciding what to build

def StartIK(*args):
	DuplicateJoints = cmds.checkBox('Duplicate', query=True, value=True)
	selected = cmds.ls(sl=True,long=True, type='joint') or []
	SelOnly = cmds.checkBox('SelOnly', query=True, value=True)
	
	if len(selected) == 2:
		zeroChildren = cmds.listRelatives(selected[0], fullPath=True, type='joint')
		oneParent = cmds.listRelatives(selected[1], parent=True, fullPath=True, type='joint')
		if oneParent[0] in zeroChildren:
			if args[0] or DuplicateJoints:
				selected = DuplicateJointChain(selected, 'IK_')
			else:
				selected = FindMiddleJoints(selected)
			Anims = MakeControlsIK(selected)
			MakeConstraintsIK(selected, Anims)
			print('IK created')
			return selected, Anims
			
def StartFK(*args):
	selected = GetCurrentSelection('joint')
	DuplicateJoints = cmds.checkBox('Duplicate', query=True, value=True)
	SelOnly = cmds.checkBox('SelOnly', query=True, value=True)
	
	
	if SelOnly:
		if DuplicateJoints:
			selected = DuplicateJointChain(selected, 'FK_')
			Anim = MakeControlFK(selected[0], 0)
			Search(selected[0], Anim)
		else:
			for i in range(len(selected)):
				Anim = MakeControlFK(selected[i], 0)
	else:
		Hierachies =[]
		if DuplicateJoints:
			for i in range(len(selected)):
				cmds.duplicate(selected[i])
				Hierachies.append(cmds.ls(sl=True,long=True, type='joint') or [])
				Hierachies[-1] = RenameHierarchy(Hierachies[-1][0], 'FK_')
				Hierachies[-1] = cmds.parent(Hierachies[-1], world=True)

		else:
			Hierachies = selected
		if len(selected)==1:
			temp = selected
			list = [temp]
			selected = list
			Hierachies = selected
		for i in range(len(Hierachies)):
			Anim = MakeControlFK(Hierachies[i], 0)
			Search(Hierachies[i], Anim)
	print('FK controls completed')
			
def StartSwitch(*args):
	selected = cmds.ls(sl=True,long=True, type='joint') or []
	#Make FK
	FKChain = DuplicateJointChain(selected, 'FK_')
	FKAnim = MakeControlFK(FKChain[0], 0)
	Search(FKChain[0], FKAnim)

	#Make IK
	cmds.select(clear=True)
	for i in range(len(selected)):
		cmds.select(selected[i], add=True)
	selected = cmds.ls(sl=True,long=True, type='joint') or []
	IK = StartIK(True)
	selected = FindMiddleJoints(selected)
	selectedCopy=selected
		
	selected = SortJointChain(selected)
	IKSwitchAnim = MakeAnimIKFK(selected)
	IKChain = SortJointChain(IK[0])
	FKChain = SortJointChain(FKChain)
	IKAnims = IK[1]
	
	FKAnims = cmds.listRelatives(FKAnim, fullPath=True, ad=True, type='nurbsCurve')
	
	for i in range(len(selected)):
		short = ShortName(selected[i])
		blendNode = cmds.createNode('blendColors', name='blendIKFK'+short)
		cmds.connectAttr(IKSwitchAnim[0]+'.IKFK', blendNode+'.blender')
		cmds.connectAttr(IKChain[i]+'.rotate', blendNode+'.color2')
		cmds.connectAttr(FKChain[i]+'.rotate', blendNode+'.color1')
		cmds.connectAttr(blendNode+'.output', selected[i]+'.rotate')
	
	MinusNode = cmds.createNode('plusMinusAverage')
	cmds.connectAttr(IKSwitchAnim[0]+'.IKFK', MinusNode+'.input3D[1].input3Dx')
	for i in range(len(FKAnims)):
		curveParent = cmds.listRelatives(FKAnims[i], fullPath=True, parent=True)
		cmds.connectAttr(IKSwitchAnim[0]+'.IKFK', curveParent[0]+'.visibility')
	for i in range(len(FKChain)):
		cmds.connectAttr(IKSwitchAnim[0]+'.IKFK', FKChain[i]+'.visibility')

	
	cmds.setAttr(MinusNode+'.operation', 2)
	cmds.setAttr(MinusNode+'.input3D[0].input3Dx', 1)
	cmds.connectAttr(MinusNode+'.output3Dx', IKAnims[0]+'.visibility')
	cmds.connectAttr(MinusNode+'.output3Dx', IKAnims[1]+'.visibility')
	for i in range(len(IKChain)):
		cmds.connectAttr(MinusNode+'.output3Dx', IKChain[i]+'.visibility')
	print('IK/FK switch completed')
			
def StartTwist(*args):
	selected = cmds.ls(sl=True,long=True, type='joint') or []
	for i in range(len(selected)):
		TwistJoint = cmds.duplicate(selected[i], parentOnly=True)
		TwistJoint = cmds.parent(TwistJoint, selected[i])
		
		ShortName = FindShortName(selected[i])
		TwistJoint = cmds.rename(TwistJoint[0], 'Twist_'+ShortName)
		Child = cmds.listRelatives(selected[i], fullPath=True, type='joint')
		if Child:
			cmds.connectAttr('%s.rotateX' %Child[0], '%s.rotateX'%TwistJoint)
			Translate = cmds.xform(Child[0], query=True, translation=True, r=True)
			Translate[0] = Translate[0]/2
			cmds.xform(TwistJoint, translation = Translate, r=True)
	print('Twist joints completed')

def ConnectFootRollAttr(AnimAttr, Grp):
	GrpRotation = cmds.xform(Grp, query=True, rotation=True)
	GrpPMA = cmds.createNode('plusMinusAverage')
	cmds.setAttr(GrpPMA+'.operation', 2)
	cmds.connectAttr(AnimAttr, GrpPMA+'.input1D[1]')
	cmds.setAttr(GrpPMA+'.input1D[0]', GrpRotation[1])
	cmds.connectAttr( '%s.output1D'%GrpPMA, Grp+'.rotateY')

def StartFootRoll(*args):
	JointsSelected = cmds.ls(sl=True,long=True, type='joint') or []
	Transforms = cmds.ls(sl=True,long=True, type='transform') or []
	LegIK = cmds.ls(sl=True,long=True, type='ikHandle') or []
	Joints = []
	Anim = 0
	if len(JointsSelected) > 1:
		Joints = FindMiddleJoints(JointsSelected)
	else:
		Joints = FindChildren(JointsSelected, JointsSelected)
	for i in range(len(Transforms)):
		children = cmds.listRelatives(Transforms[i], type='nurbsCurve')
		if children:
			Anim = Transforms[i]
			
	if not LegIK:
		effector = cmds.listConnections(Joints[0], source=False, type = 'ikEffector')
		LegIK = cmds.listConnections(effector[0], source=False, type = 'ikHandle')
	
	NamePrefix = ShortName(JointsSelected[0])
	if not Anim:
		Anim = cmds.circle(nr=(0,1,0), c=(0, 0, 0), r=6, n='FootRoll_Anim_%s' % NamePrefix)
		Anim = Anim[0]
		cmds.matchTransform(Anim, JointsSelected[1], pivots=False, scale=False, rot=False, pos=True)
		cmds.setAttr(Anim+'.translateY', 0)
		Grp = cmds.group(name = Anim+'_grp', empty=True)
		cmds.matchTransform(Grp, Anim, pivots=False, scale=False, rot=True, pos=True)
		cmds.parent(Anim, Grp)
	
	AnimName = ShortName(Anim)
	ParentFootGrp = cmds.group(name = NamePrefix+'_Roll_Parent_grp', empty=True)
	cmds.matchTransform(ParentFootGrp, Joints[1], pivots=False, scale=False, rot=True, pos=True)
	FootGrp = cmds.group(name = NamePrefix+'_Roll_grp', empty=True)
	cmds.matchTransform(FootGrp, Joints[-1], pivots=False, scale=False, rot=True, pos=True)
	ToeGrp = cmds.group(name = NamePrefix+'_FrontPivot_grp', empty=True)
	cmds.matchTransform(ToeGrp, Joints[-1], pivots=False, scale=False, rot=True, pos=True)
	HeelGrp = cmds.group(name = NamePrefix+'_BackPivot_grp', empty=True)
	cmds.matchTransform(HeelGrp, Joints[0], pivots=False, scale=False, rot=True, pos=True)
	
	cmds.parent(HeelGrp, ToeGrp)
	cmds.parent(ToeGrp, FootGrp)
	cmds.parent(FootGrp, ParentFootGrp)

	if len(Joints) == 2 or len(Joints) > 3:	
			
		cmds.addAttr(Anim, ln='FootRoll', at='float', dv=0, min=-60, max=60, k=True)
		IKname = ShortName(Joints[1]) + '_ikHandle'
		cmds.select(Joints[0])
		cmds.select(Joints[1], add=True)
		ToeIK = cmds.ikHandle(name=IKname, sol='ikSCsolver')
		
		cmds.parent(ToeIK[0], HeelGrp)
		cmds.parent(LegIK, HeelGrp)
		cmds.parentConstraint(Anim, ParentFootGrp, maintainOffset=True)
		
		#HEEL
		HeelClamp = cmds.createNode('clamp')
		cmds.connectAttr(Anim+'.FootRoll', HeelClamp+'.inputR')
		cmds.setAttr(HeelClamp+'.maxR', 60)
		cmds.setAttr(HeelClamp+'.minR', 0)
		HeelMD = cmds.createNode('multiplyDivide')
		cmds.connectAttr(HeelClamp+'.outputR', HeelMD+'.input1X')
		cmds.setAttr(HeelMD+'.input2X', 0.5)
		
		#TOE
		ToeClamp = cmds.createNode('clamp')
		cmds.connectAttr(Anim+'.FootRoll', ToeClamp+'.inputR')
		cmds.setAttr(ToeClamp+'.maxR', 0)
		cmds.setAttr(ToeClamp+'.minR', -60)
		
		ConnectFootRollAttr(HeelClamp+'.outputR', HeelGrp)
		ConnectFootRollAttr(ToeClamp+'.outputR', ToeGrp)
		
		print('Simple foot roll completed')
	elif len(Joints) == 3:
			
		cmds.addAttr(Anim, ln='FootRoll', at='float', dv=0, min=-60, max=60, k=True)
		cmds.addAttr(Anim, ln='AnkleBend', at='float', dv=0, min=0, max=60, k=True)
		cmds.addAttr(Anim, ln='ToeFlap', at='float', dv=0, min=-60, max=60, k=True)
		IKname = ShortName(Joints[1]) + '_ikHandle'
		cmds.select(Joints[0])
		cmds.select(Joints[1], add=True)
		AnkleBall = cmds.ikHandle( name=IKname, sol='ikSCsolver')
		IKname = ShortName(Joints[2]) + '_ikHandle'
		cmds.select(clear=True)
		cmds.select(Joints[1])
		cmds.select(Joints[2], add=True)
		BallToe = cmds.ikHandle(name=IKname, sol='ikSCsolver')
			
		BallToeGrp = cmds.group(name = NamePrefix+'_BallToe_grp', empty=True)
		cmds.matchTransform(BallToeGrp, Joints[1], pivots=False, scale=False, rot=True, pos=True)
		LegGrp = cmds.group(name = NamePrefix+'_Leg_grp', empty=True)
		cmds.matchTransform(LegGrp, Joints[1], pivots=False, scale=False, rot=True, pos=True)
		
		cmds.parent(BallToe[0], BallToeGrp)
		cmds.parent(LegIK, LegGrp)
		cmds.parent(BallToeGrp, HeelGrp)
		cmds.parent(LegGrp, HeelGrp)
		cmds.parent(AnkleBall[0], HeelGrp)
		cmds.parentConstraint(Anim, ParentFootGrp, maintainOffset=True)
		
		#HEEL
		HeelClamp = cmds.createNode('clamp')
		cmds.connectAttr(Anim+'.FootRoll', HeelClamp+'.inputR')
		cmds.setAttr(HeelClamp+'.maxR', 60)
		cmds.setAttr(HeelClamp+'.minR', 0)
		HeelMD = cmds.createNode('multiplyDivide')
		cmds.connectAttr(HeelClamp+'.outputR', HeelMD+'.input1X')
		cmds.setAttr(HeelMD+'.input2X', 0.5)
		
		#TOE
		ToeClamp = cmds.createNode('clamp')
		cmds.connectAttr(Anim+'.FootRoll', ToeClamp+'.inputR')
		cmds.setAttr(ToeClamp+'.maxR', 0)
		cmds.setAttr(ToeClamp+'.minR', -60)
		
		#LEG
		LegMD = cmds.createNode('multiplyDivide')
		cmds.connectAttr(Anim+'.AnkleBend', LegMD+'.input1X')
		cmds.setAttr(LegMD+'.input2X', -1)
		LegMDb = cmds.createNode('multiplyDivide')
		cmds.connectAttr(ToeClamp+'.outputR', LegMDb+'.input1X')
		cmds.setAttr(LegMDb+'.input2X', 1.5)
		LegPMA = cmds.createNode('plusMinusAverage')
		cmds.setAttr(LegPMA+'.operation', 1)
		cmds.connectAttr(LegMDb+'.outputX', LegPMA+'.input1D[0]')
		cmds.connectAttr(LegMD+'.outputX', LegPMA+'.input1D[1]')
		
	
		ConnectFootRollAttr(HeelMD+'.outputX', HeelGrp)
		ConnectFootRollAttr(ToeClamp+'.outputR', ToeGrp)
		ConnectFootRollAttr(LegPMA+'.output1D', LegGrp)
		ConnectFootRollAttr(Anim+'.ToeFlap', BallToeGrp)
		
		print('Foot roll completed')

	
####################################################################################################

def Flip(Joint):
	children = cmds.listRelatives(Joint, fullPath=True)
	Grp = []
	if children:
		Grp = cmds.group(name = 'Temp_Flip_grp', empty=True)
		for i in range(len(children)):
			cmds.parent(children[i], Grp)
	cmds.rotate(0, '180deg', 0, Joint, r=True, os=True)
	if children:
		children = cmds.listRelatives(Grp, fullPath=True)
		for i in range(len(children)):
			Child = cmds.parent(children[i], Joint)
			Flip(Child)
		cmds.delete(Grp)

def StartFlipJoints(*args):
	selected = cmds.ls(sl=True,long=True) or []
	for i in range(len(selected)):
		Flip(selected[i])
		cmds.makeIdentity(selected[i], apply=True, t=False, r=True, s=False, n=False, pn=True)
		cmds.joint(selected[i], e=True, spa=True, ch=True)
	
def AddToWhiteList(*args):
	selected = cmds.ls(sl=True,long=True) or []
	if selected:
		for i in range(len(selected)):
			WhiteList.append(selected[i])
			
def ClearAll(*args):
	cmds.select(clear=True)
	if WhiteList:
		for i in range(len(WhiteList)):
			cmds.select(WhiteList[i], add=True)
	print('cmds.invertSelection mel')
			
def Recolour(*args):
	selected = cmds.ls(sl=True,long=True) or []
	colour = cmds.colorSliderGrp('colourslider', query=True, rgb=True)

	R = colour[0]
	G = colour[1]
	B = colour[2]
	for curve in selected:
		try:
			shape = cmds.listRelatives(curve, fullPath=True, shapes=True)
			print(shape)
			for i in range(len(shape)):
				# Trun on overrides
				cmds.setAttr(shape[i] + ".overrideEnabled", 1)
				cmds.setAttr(shape[i] + ".overrideRGBColors",1)
				cmds.setAttr(shape[i] + ".overrideColorRGB", R ,G ,B)
		except:
			pass
			
def ReSize(*args):
	size = cmds.floatSlider('Resize', query=True, value=True)
	selected = cmds.ls(sl=True,long=True,type='transform') or []
	for i in range(len(selected)):
		try:
			shape = cmds.listRelatives(selected[i], shapes=True, fullPath=True)
			makeNurbs = cmds.listConnections(shape[0])
			try:
				cmds.setAttr(makeNurbs[0]+'.radius', size)
			except:
				try:
					cmds.setAttr(makeNurbs[0]+'.sideLength1', size*2)
					cmds.setAttr(makeNurbs[0]+'.sideLength2', size*2)
				except:
					pass
		except:
			pass

def MatchTransforms(*args):
	cmds.matchTransform(pivots=False, scale=False, rot=True, pos=True)
	
def MatchOnlyPosition(*args):
	cmds.matchTransform(pivots=False, scale=False, rot=False, pos=True)
	
def ParentOffset(*args):
	selected = cmds.ls(sl=True,long=True) or []
	if len(selected)==2:
		cmds.connectAttr('%s.worldMatrix[0]' %selected[1], '%s.offsetParentMatrix' %selected[0]) 

	
####################################################################################################
           
def MakeWindow():
	windowEditor = cmds.window(title='Rig Helper Tool', widthHeight=(600, 460))
	cmds.columnLayout(adjustableColumn=True)
	cmds.separator(height=20, style='in')
	Ann='Reverses the X direction for joints, useful for joints mirrored by behaviour'
	cmds.button(label='Flip joint orientations', command= StartFlipJoints, ann=Ann)
	cmds.separator(height=20, style='in')
	Ann='Duplicates the selected joint chain before making FK or IK controls'
	cmds.checkBox('Duplicate', label='Duplicate joints', ann=Ann)
	Ann='Creates FK controls on only the selected joints, rather than the whole hierarchy'
	cmds.checkBox('SelOnly', label='Selected joints only', ann=Ann)
	cmds.checkBox('IgnoreLeaf', label='Ignore leaf joints')
	cmds.button(label='generate FK', command= StartFK)
	Ann='Select the uppermost, then lowermost joints for the IK'
	cmds.button(label='generate IK', command= StartIK, ann=Ann)
	cmds.separator(height=20, style='in')
	cmds.button(label='generate IK/FK switch', command= StartSwitch, ann=Ann+'/FK switch')
	ATSann='Select the joints to be added, and the switch anim to control them'
	cmds.button(label='add to existing IK/FK switch', command= AddToSwitch, ann=ATSann)
	cmds.button(label='generate twist joint', command= StartTwist)
	cmds.separator(height=20, style='in')
	FRann='select the ankle joint, the leg IK and optionally the anim to hold the attribute'
	FRann=FRann+'\n after running, hold d and move the heel group to the heel pivot point'
	cmds.button(label='Add foot roll', command= StartFootRoll, ann=FRann)
	cmds.separator(height=20, style='in')
	cmds.button(label='recolour', command= Recolour)
	cmds.colorSliderGrp('colourslider', label='colour')
	cmds.floatSlider('Resize', min=0, max=20, dragCommand = ReSize)
	cmds.separator(height=20, style='in')
	cmds.button(label='Match Transforms', command= MatchTransforms)
	cmds.button(label='Match Position', command= MatchOnlyPosition)
	cmds.button(label='Offset Parent Matrix', command= ParentOffset)
	cmds.showWindow( windowEditor ) 

####################################################################################################


MakeWindow()
