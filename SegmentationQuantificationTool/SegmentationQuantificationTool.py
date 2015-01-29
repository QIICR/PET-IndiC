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
    self.parent.dependencies = []
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

    #
    # threshold value
    #
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 0.1
    self.imageThresholdSliderWidget.minimum = -100
    self.imageThresholdSliderWidget.maximum = 100
    self.imageThresholdSliderWidget.value = 0.5
    self.imageThresholdSliderWidget.setToolTip("Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
    imagesFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    imagesFormLayout.addRow(self.applyButton)
    
    #
    # editor effect area
    #
    editorCollapsibleButton = ctk.ctkCollapsibleButton()
    editorCollapsibleButton.text = "Segmentation Editor"
    #self.layout.addWidget(editorCollapsibleButton)
    editorFormLayout = qt.QFormLayout(editorCollapsibleButton)
    
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
    slicer.modules.quantitativeindicestool.createNewWidgetRepresentation()
    self.qiWidget = slicer.modules.QuantitativeIndicesToolWidget
    self.layout.addWidget(self.qiWidget.featuresCollapsibleButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onVolumeSelect)
    self.labelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.preset1Button.connect('clicked(bool)',self.onPreset1Button)
    self.preset2Button.connect('clicked(bool)',self.onPreset2Button)
    self.preset3Button.connect('clicked(bool)',self.onPreset3Button)
    self.preset4Button.connect('clicked(bool)',self.onPreset4Button)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onVolumeSelect(self):
    """Search for the dedicated label image. If none found, create a new one."""
    if self.inputSelector.currentNode():
      imageNode = None
      self.labelSelector.setMRMLScene( slicer.mrmlScene )
      currentNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      imageName = currentNode.GetName()
      scalarVolumes = slicer.mrmlScene.GetNodesByClass('vtkMRMLScalarVolumeNode')
      print('Number of scalar volumes: ' + scalarVolumes.GetNumberOfItems().__str__())
      labelFound = False
      for idx in xrange(0,scalarVolumes.GetNumberOfItems()):
        imageNode = scalarVolumes.GetItemAsObject(idx)
        if imageNode.GetName() == (imageName + '_label'):
          print('Found dedicated label ' + imageNode.GetName())
          self.labelSelector.setCurrentNode(imageNode)
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
        self.labelSelector.setCurrentNode(imageNode)
        
      appLogic = slicer.app.applicationLogic()
      selNode = appLogic.GetSelectionNode()
      selNode.SetReferenceActiveLabelVolumeID(imageNode.GetID())
      appLogic.PropagateVolumeSelection()
      
      r = slicer.util.getNode("vtkMRMLSliceNodeRed")
      r.UseLabelOutlineOn()
      y = slicer.util.getNode("vtkMRMLSliceNodeYellow")
      y.UseLabelOutlineOn()
      g = slicer.util.getNode("vtkMRMLSliceNodeGreen")
      g.UseLabelOutlineOn()

  def onPreset1Button(self):
    if self.inputSelector.currentNode():
      print('  Changing W/L to 6/3')
      imageNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      displayNode = imageNode.GetVolumeDisplayNode()
      displayNode.AutoWindowLevelOff()
      displayNode.SetWindowLevel(6,3)
      displayNode.SetInterpolate(0)
      displayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeInvertedGrey')
      
  def onPreset2Button(self):
    if self.inputSelector.currentNode():
      print('  Changing W/L to 22.6/9.3')
      imageNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      displayNode = imageNode.GetVolumeDisplayNode()
      displayNode.AutoWindowLevelOff()
      displayNode.SetWindowLevel(22.6,9.3)
      displayNode.SetInterpolate(0)
      displayNode.SetAndObserveColorNodeID('vtkMRMLPETProceduralColorNodePET-Rainbow')

  def onPreset3Button(self):
    if self.inputSelector.currentNode():
      print('  Preset 3 currently not implemented')

  def onPreset4Button(self):
    if self.inputSelector.currentNode():
      print('  Automatically determining W/L')
      imageNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      displayNode = imageNode.GetVolumeDisplayNode()
      displayNode.AutoWindowLevelOn()
      displayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeGrey')

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.labelSelector.currentNode()

  def onApplyButton(self):
    logic = SegmentationQuantificationToolLogic()
    imageThreshold = self.imageThresholdSliderWidget.value
    logic.run(self.inputSelector.currentNode(), self.labelSelector.currentNode(), imageThreshold)

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
