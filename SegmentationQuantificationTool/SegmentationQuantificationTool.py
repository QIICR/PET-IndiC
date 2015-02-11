import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# SegmentationQuantificationTool
#

class SegmentationQuantificationTool(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Segmentation Quantification Tool" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Segmentation"]
    self.parent.dependencies = ["QuantitativeIndicesTool"]
    self.parent.contributors = ["Ethan Ulrich (Univ. of Iowa), Christian Bauer (Univ. of Iowa), Markus van Tol (Univ. of Iowa), Reinhard R. Beichel (Univ. of Iowa), John Buatti (Univ. of Iowa)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    The Segmentation Quantification Tool allows for fast segmentation of regions of interest and calculation of quantitative indices.
    """
    self.parent.acknowledgementText = """
    This work is funded in part by Quantitative Imaging to Assess Response in Cancer Therapy Trials NIH grant U01-CA140206 and Quantitative Image Informatics for Cancer Research (QIICR) NIH grant U24 CA180918.""" # replace with organization, grant and thanks.

#
# SegmentationQuantificationToolWidget
#

class SegmentationQuantificationToolWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    self.logic = SegmentationQuantificationToolLogic()

    #
    # Images Area
    #
    imagesCollapsibleButton = ctk.ctkCollapsibleButton()
    imagesCollapsibleButton.text = "Images"
    self.layout.addWidget(imagesCollapsibleButton)

    # Layout within the dummy collapsible button
    imagesFormLayout = qt.QFormLayout(imagesCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.inputSelector.selectNodeUponCreation = False
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = True
    self.inputSelector.noneEnabled = True
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Choose the input image ." )
    imagesFormLayout.addRow("Input Image: ", self.inputSelector)

    #
    # input label image selector
    #
    self.labelSelector = slicer.qMRMLNodeComboBox()
    self.labelSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.labelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 1 )
    self.labelSelector.setEnabled(False)
    self.labelSelector.selectNodeUponCreation = False
    self.labelSelector.addEnabled = True
    self.labelSelector.removeEnabled = True
    self.labelSelector.renameEnabled = True
    self.labelSelector.noneEnabled = False
    self.labelSelector.showHidden = False
    self.labelSelector.showChildNodeTypes = False
    #self.labelSelector.setMRMLScene( slicer.mrmlScene )
    self.labelSelector.setToolTip( "Select active segmentation image or create a new one." )
    imagesFormLayout.addRow("Label Image: ", self.labelSelector)
    
    #
    # window/level presets
    #
    self.presetsFrame = qt.QFrame(self.parent)
    self.presetsFrame.setLayout(qt.QHBoxLayout())
    self.presetsFrame.layout().setSpacing(0)
    self.presetsFrame.layout().setMargin(0)
    imagesFormLayout.addRow("W/L Presets:", self.presetsFrame)
    self.preset1Button = qt.QPushButton("Inverted Grey")
    self.preset1Button.toolTip = "PET SUV image preset (window = 6, level = 3)" 
    self.presetsFrame.layout().addWidget(self.preset1Button)
    self.preset2Button = qt.QPushButton("Rainbow")
    self.preset2Button.toolTip = "PET SUV image preset (window = 22.6, level = 9.3)" 
    self.presetsFrame.layout().addWidget(self.preset2Button)
    self.preset3Button = qt.QPushButton("Preset 3")
    self.preset3Button.toolTip = "preset 3 (not implemented)" 
    self.presetsFrame.layout().addWidget(self.preset3Button)
    self.preset4Button = qt.QPushButton("Auto")
    self.preset4Button.toolTip = "Automatically determines a window/level based on the dynamic range" 
    self.presetsFrame.layout().addWidget(self.preset4Button)
    self.preset1Button.setEnabled(0)
    self.preset2Button.setEnabled(0)
    self.preset3Button.setEnabled(0)
    self.preset4Button.setEnabled(0)
    
    #
    # editor effects
    #
    slicer.modules.editor.createNewWidgetRepresentation()
    self.editorWidget = slicer.modules.EditorWidget
    self.layout.addWidget(self.editorWidget.editLabelMapsFrame)
    self.editorWidget.editLabelMapsFrame.collapsed = False
    
    #
    # quantitative indices
    #
    # TODO show/hide checkboxes based on current volume
    slicer.modules.quantitativeindicestool.createNewWidgetRepresentation()
    self.qiWidget = slicer.modules.QuantitativeIndicesToolWidget
    self.layout.addWidget(self.qiWidget.featuresCollapsibleButton)
    self.qiWidget.featuresCollapsibleButton.collapsed = True
    self.MeanCheckBox = self.qiWidget.MeanCheckBox
    self.MeanCheckBox.checked = True
    self.VarianceCheckBox = self.qiWidget.VarianceCheckBox
    self.MinCheckBox = self.qiWidget.MinCheckBox
    self.MinCheckBox.checked = True
    self.MaxCheckBox = self.qiWidget.MaxCheckBox
    self.MaxCheckBox.checked = True
    self.Quart1CheckBox = self.qiWidget.Quart1CheckBox
    self.MedianCheckBox = self.qiWidget.MedianCheckBox
    self.MedianCheckBox.checked = True
    self.Quart3CheckBox = self.qiWidget.Quart3CheckBox
    self.UpperAdjacentCheckBox = self.qiWidget.UpperAdjacentCheckBox
    self.Q1CheckBox = self.qiWidget.Q1CheckBox
    self.Q2CheckBox = self.qiWidget.Q2CheckBox
    self.Q3CheckBox = self.qiWidget.Q3CheckBox
    self.Q4CheckBox = self.qiWidget.Q4CheckBox
    self.Gly1CheckBox = self.qiWidget.Gly1CheckBox
    self.Gly2CheckBox = self.qiWidget.Gly2CheckBox
    self.Gly3CheckBox = self.qiWidget.Gly3CheckBox
    self.Gly4CheckBox = self.qiWidget.Gly4CheckBox
    self.TLGCheckBox = self.qiWidget.TLGCheckBox
    self.TLGCheckBox.checked = True
    self.SAMCheckBox = self.qiWidget.SAMCheckBox
    self.SAMBGCheckBox = self.qiWidget.SAMBGCheckBox
    self.RMSCheckBox = self.qiWidget.RMSCheckBox
    self.PeakCheckBox = self.qiWidget.PeakCheckBox
    self.VolumeCheckBox = self.qiWidget.VolumeCheckBox
    self.VolumeCheckBox.checked = True
    self.calculateButton = self.qiWidget.calculateButton
    
    #
    # units display
    #
    self.unitsFrame = qt.QFrame(self.parent)
    self.unitsFrame.setLayout(qt.QHBoxLayout())
    #self.unitsFrame.layout().setSpacing(0)
    #self.unitsFrame.layout().setMargin(0)
    self.unitsFrameLabel = qt.QLabel('Voxel Units: ', self.unitsFrame)
    self.unitsFrame.layout().addWidget(self.unitsFrameLabel)
    self.layout.addWidget(self.unitsFrame)
    
    #
    # results frame
    #
    self.resultsFrame = self.qiWidget.resultsFrame
    self.resultsFrame.layout().setMargin(2)
    self.layout.addWidget(self.resultsFrame)
    self.resultsFrameLabel = self.qiWidget.resultsFrameLabel
    self.resultsFrame.layout().addWidget(self.resultsFrameLabel)

    # connections
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onVolumeSelect)
    self.preset1Button.connect('clicked(bool)',self.onPreset1Button)
    self.preset2Button.connect('clicked(bool)',self.onPreset2Button)
    self.preset3Button.connect('clicked(bool)',self.onPreset3Button)
    self.preset4Button.connect('clicked(bool)',self.onPreset4Button)
    self.editorWidget.toolsColor.colorSpin.connect('valueChanged(int)', self.onLabelValueChanged)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    self.editorWidget.toolsColor.colorSpin.disconnect('valueChanged(int)', self.onLabelValueChanged)

  def onVolumeSelect(self):
    """Search for the dedicated label image. If none found, create a new one."""
    if self.inputSelector.currentNode():
      imageNode = None
      self.labelSelector.setMRMLScene( slicer.mrmlScene )
      currentNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      imageNode = self.logic.getLabelNodeForNode(currentNode)
      self.labelSelector.setCurrentNode(imageNode)
      self.unitsFrameLabel.setText('Voxel Units: ' + self.logic.getImageUnits(currentNode))
        
      appLogic = slicer.app.applicationLogic()
      selNode = appLogic.GetSelectionNode()
      selNode.SetReferenceActiveVolumeID(currentNode.GetID())
      selNode.SetReferenceActiveLabelVolumeID(imageNode.GetID())
      appLogic.PropagateVolumeSelection()

      # TODO figure out how to observe only image data changes,
      # currently this is also triggered when the image name changes      
      imageNode.AddObserver('ModifiedEvent', self.labelModified)
      #imageNode.AddObserver('ImageDataModifiedEvent', self.labelModified)
      
      r = slicer.util.getNode("vtkMRMLSliceNodeRed")
      r.UseLabelOutlineOn()
      y = slicer.util.getNode("vtkMRMLSliceNodeYellow")
      y.UseLabelOutlineOn()
      g = slicer.util.getNode("vtkMRMLSliceNodeGreen")
      g.UseLabelOutlineOn()
      self.preset1Button.setEnabled(1)
      self.preset2Button.setEnabled(1)
      self.preset3Button.setEnabled(1)
      self.preset4Button.setEnabled(1)
    else:
      self.preset1Button.setEnabled(0)
      self.preset2Button.setEnabled(0)
      self.preset3Button.setEnabled(0)
      self.preset4Button.setEnabled(0)
      

  def onPreset1Button(self):
    if self.inputSelector.currentNode():
      imageNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      self.logic.presetSUVInvertedGrey(imageNode)
      
  def onPreset2Button(self):
    if self.inputSelector.currentNode():
      imageNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      self.logic.presetSUVRainbow(imageNode)

  def onPreset3Button(self):
    if self.inputSelector.currentNode():
      print('  Preset 3 currently not implemented')

  def onPreset4Button(self):
    if self.inputSelector.currentNode():
      imageNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      self.logic.presetGreyAuto(imageNode)
      
  def labelModified(self, caller, event):
    if caller.GetID() == self.labelSelector.currentNodeID:
      print('   *** GOT EVENT FROM vtkMRMLScalarVolumeNode ***')
      cliNode = None
      cliNode = self.logic.calculateOnLabelModified(self.inputSelector.currentNode(), self.labelSelector.currentNode(), None, self.editorWidget.toolsColor.colorSpin.value, self.MeanCheckBox.checked, self.VarianceCheckBox.checked, self.MinCheckBox.checked, self.MaxCheckBox.checked, self.Quart1CheckBox.checked, self.MedianCheckBox.checked, self.Quart3CheckBox.checked, self.UpperAdjacentCheckBox.checked, self.Q1CheckBox.checked, self.Q2CheckBox.checked, self.Q3CheckBox.checked, self.Q4CheckBox.checked, self.Gly1CheckBox.checked, self.Gly2CheckBox.checked, self.Gly3CheckBox.checked, self.Gly4CheckBox.checked, self.TLGCheckBox.checked, self.SAMCheckBox.checked, self.SAMBGCheckBox.checked, self.RMSCheckBox.checked, self.PeakCheckBox.checked, self.VolumeCheckBox.checked)
      if cliNode:
        self.writeResults(cliNode)
      else:
        print('ERROR: could not read output of Quantitative Indices Calculator')
      
  def onLabelValueChanged(self, label):
    print('   *** Color Spin Box changed to label: ' + str(label) + ' ***')
    
  def writeResults(self, vtkMRMLCommandLineModuleNode):
    """ Creates an output text to display on the screen."""
    newNode = vtkMRMLCommandLineModuleNode
    labelValue = int(self.editorWidget.toolsColor.colorSpin.value)
    #oldNode = self.cliNodes[labelValue]
    resultText = ''
    #for i in xrange(0,22):
    for i in xrange(0,24):
      newResult = newNode.GetParameterDefault(3,i)
      if (newResult != '--'):
        #oldResult = oldNode.GetParameterDefault(3,i)
        #feature = oldNode.GetParameterName(3,i)
        feature = newNode.GetParameterName(3,i)
        #if (oldResult == '--'):
        #  flagName = oldNode.GetParameterName(2,i)
        #  oldNode.SetParameterAsString(feature,newResult)
        #  oldNode.SetParameterAsString(flagName,'true')
        feature = feature.replace('_s',':\t')
        feature = feature.replace('_',' ')
        if len(feature) < 14:
          feature = feature + '\t'
        resultText = resultText + feature + newResult + '\n'
    self.resultsFrameLabel.setText(resultText)
    # TODO find a better way to retrieve the software revision
    # use slicer.modules.QuantitativeIndicesToolWidget.software_version to retrieve
    self.software_version = newNode.GetParameterDefault(0,0)
    slicer.mrmlScene.RemoveNode(newNode)
      

#
# SegmentationQuantificationToolLogic
#

class SegmentationQuantificationToolLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent = None):
    ScriptedLoadableModuleLogic.__init__(self, parent)

  """def createParameterNode(self):
    node = ScriptedLoadableModuleLogic.createParameterNode(self)
    node.SetName(slicer.mrmlScene.GetUniqueNameByString(self.moduleName))
    return node"""

  def getLabelNodeForNode(self, currentNode):
    """Search for the dedicated label image. If none found, return a new one."""
    imageNode = None
    imageName = currentNode.GetName()
    scalarVolumes = slicer.mrmlScene.GetNodesByClass('vtkMRMLScalarVolumeNode')
    print('Number of scalar volumes: ' + scalarVolumes.GetNumberOfItems().__str__())
    labelFound = False
    for idx in xrange(0,scalarVolumes.GetNumberOfItems()): #TODO use while loop
      imageNode = scalarVolumes.GetItemAsObject(idx)
      if imageNode.GetName() == (imageName + '_label'):
        print('Found dedicated label ' + imageNode.GetName())
        labelFound = True
        break
    if not labelFound:
      print('Creating dedicated label ' + imageName + '_label')
      # TODO find a better way to create a blank label map
      imageNode = slicer.vtkMRMLScalarVolumeNode()
      newLabelData = vtk.vtkImageData()
      newLabelData.DeepCopy(currentNode.GetImageData())
      ijkToRAS = vtk.vtkMatrix4x4()
      currentNode.GetIJKToRASMatrix(ijkToRAS)
      imageNode.SetIJKToRASMatrix(ijkToRAS)
      caster = vtk.vtkImageCast()
      caster.SetOutputScalarTypeToShort()
      caster.SetInputData(newLabelData)
      caster.Update()
      newLabelData.DeepCopy(caster.GetOutput())
      imageNode.SetAndObserveImageData(newLabelData)
      
      multiplier = vtk.vtkImageMathematics()
      multiplier.SetOperationToMultiplyByK()
      multiplier.SetConstantK(0)
      if vtk.VTK_MAJOR_VERSION <= 5:
        multiplier.SetInput1(imageNode.GetImageData())
      else:
        multiplier.SetInput1Data(imageNode.GetImageData())
      multiplier.Update()
      imageNode.GetImageData().DeepCopy(multiplier.GetOutput())
       
      imageNode.SetLabelMap(1)
      imageNode.SetName(imageName + '_label')
      slicer.mrmlScene.AddNode(imageNode)

    return imageNode

  def presetSUVInvertedGrey(self, imageNode):
    print('  Changing W/L to 6/3')
    displayNode = imageNode.GetVolumeDisplayNode()
    displayNode.AutoWindowLevelOff()
    displayNode.SetWindowLevel(6,3)
    displayNode.SetInterpolate(0)
    displayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeInvertedGrey')
    
  def presetSUVRainbow(self, imageNode):
    print('  Changing W/L to 22.6/9.3')
    displayNode = imageNode.GetVolumeDisplayNode()
    displayNode.AutoWindowLevelOff()
    displayNode.SetWindowLevel(22.6,9.3)
    displayNode.SetInterpolate(0)
    displayNode.SetAndObserveColorNodeID('vtkMRMLPETProceduralColorNodePET-Rainbow')
    
  def presetGreyAuto(self, imageNode):
    print('  Automatically determining W/L')
    displayNode = imageNode.GetVolumeDisplayNode()
    displayNode.AutoWindowLevelOn()
    displayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeGrey')

  def getImageUnits(self, imageNode):
    """Search for units in the image node attributes """
    units = '(could not retrieve units information)'
    if imageNode.GetAttribute('DICOM.MeasurementUnitsCodeValue'):
      units = imageNode.GetAttribute('DICOM.MeasurementUnitsCodeValue')
    return units
    
  def calculateOnLabelModified(self, scalarVolume, labelVolume, cliNode, labelValue, meanFlag, varianceFlag, minFlag,
                        maxFlag, quart1Flag, medianFlag, quart3Flag, upperAdjacentFlag, q1Flag, q2Flag, q3Flag, 
                        q4Flag, gly1Flag, gly2Flag, gly3Flag, gly4Flag, TLGFlag, SAMFlag, SAMBGFlag, RMSFlag, 
                        PeakFlag, VolumeFlag):
    print('      Recalculating QIs')
    qiLogic = QuantitativeIndicesToolLogic()
    node = qiLogic.run(scalarVolume,labelVolume,cliNode,labelValue,meanFlag, varianceFlag, minFlag,
                        maxFlag, quart1Flag, medianFlag, quart3Flag, upperAdjacentFlag, q1Flag, q2Flag, q3Flag, 
                        q4Flag, gly1Flag, gly2Flag, gly3Flag, gly4Flag, TLGFlag, SAMFlag, SAMBGFlag, RMSFlag, 
                        PeakFlag, VolumeFlag)
    return node
  
  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() == None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def run(self, inputVolume, outputVolume, imageThreshold):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    logging.info('Processing completed')

    return True


class SegmentationQuantificationToolTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SegmentationQuantificationTool1()

  def test_SegmentationQuantificationTool1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = SegmentationQuantificationToolLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
