import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from SegmentStatistics import SegmentStatisticsLogic
from PETVolumeSegmentStatisticsPlugin import PETVolumeSegmentStatisticsPlugin

#
# QuantitativeIndices
#

class QuantitativeIndicesTool(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    parent.title = "Quantitative Indices Tool" # TODO make this more human readable by adding spaces
    parent.categories = ["Quantification"]
    parent.dependencies = ["QuantitativeIndicesCLI"]
    parent.contributors = ["Ethan Ulrich (University of Iowa), Andrey Fedorov (SPL), Markus van Tol (University of Iowa), Christian Bauer (University of Iowa), Reinhard Beichel (University of Iowa), John Buatti (University of Iowa)"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    This extension calculates simple quantitative features from a grayscale volume and label map.\n
    Once both volumes have been selected, a parameter set must be generated.  Quantitative indices
    may be calculated on individual values of the label map.  Even if different indices are calculated
    at different times on the same label value, the previous calculations will be stored.
    """
    parent.acknowledgementText = """
    This work is funded in part by Quantitative Imaging to Assess Response in Cancer Therapy Trials NIH grant U01-CA140206 and Quantitative Image Informatics for Cancer Research (QIICR) NIH grant U24 CA180918.
    """ # replace with organization, grant and thanks.
    #self.parent = parent

    # register segment statistics plugin
    petSegmentStatisticsPlugin = PETVolumeSegmentStatisticsPlugin()
    SegmentStatisticsLogic.registerPlugin( petSegmentStatisticsPlugin )

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    #try:
    #  slicer.selfTests
    #except AttributeError:
    #  slicer.selfTests = {}
    #slicer.selfTests['QuantitativeIndicesTool'] = self.runTest

  #def runTest(self):
  #  tester = QuantitativeIndicesToolTest()
  #  tester.runTest()

#
# qQuantitativeIndicesToolWidget
#

class QuantitativeIndicesToolWidget(ScriptedLoadableModuleWidget):
  """def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()"""

  def setup(self):
    """Instantiate and connect widgets ...
    """
    ScriptedLoadableModuleWidget.setup(self)
    self.logic = QuantitativeIndicesToolLogic()

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # grayscale volume selector
    #
    self.grayscaleSelector = slicer.qMRMLNodeComboBox()
    self.grayscaleSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.grayscaleSelector.selectNodeUponCreation = True
    self.grayscaleSelector.addEnabled = False
    self.grayscaleSelector.removeEnabled = False
    self.grayscaleSelector.noneEnabled = True
    self.grayscaleSelector.showHidden = False
    self.grayscaleSelector.showChildNodeTypes = False
    self.grayscaleSelector.setMRMLScene( slicer.mrmlScene )
    self.grayscaleSelector.setToolTip( "Input grayscale volume." )
    parametersFormLayout.addRow("Input Volume: ", self.grayscaleSelector)
    self.grayscaleNode = None

    #
    # label map volume selector
    #
    self.labelSelector = slicer.qMRMLNodeComboBox()
    self.labelSelector.nodeTypes = ( ("vtkMRMLLabelMapVolumeNode"), "" )
    self.labelSelector.selectNodeUponCreation = True
    self.labelSelector.addEnabled = False
    self.labelSelector.removeEnabled = False
    self.labelSelector.noneEnabled = True
    self.labelSelector.showHidden = False
    self.labelSelector.showChildNodeTypes = False
    self.labelSelector.setMRMLScene( slicer.mrmlScene )
    self.labelSelector.setToolTip( "Input label map volume." )
    parametersFormLayout.addRow("Label Map: ", self.labelSelector)
    self.labelNode = None

    #
    # CLI node name and set button
    #
    self.parameterFrame = qt.QFrame(self.parent)
    self.parameterFrame.setLayout(qt.QHBoxLayout())
    parametersFormLayout.addRow("Parameter Set: ", self.parameterFrame)

    self.parameterFrameLabel = qt.QLabel(" (none generated) ", self.parameterFrame)
    self.parameterFrameLabel.setToolTip( "Nodes for storing parameter flags and output." )
    self.parameterFrame.layout().addWidget(self.parameterFrameLabel)

    self.parameterName = qt.QLabel("", self.parameterFrame)
    self.parameterName.setToolTip( "Nodes for storing parameter flags and output." )
    self.parameterFrame.layout().addWidget(self.parameterName)

    self.parameterSetButton = qt.QPushButton("Generate", self.parameterFrame)
    self.parameterSetButton.setToolTip( "Generate a set of parameter nodes to store with the scene" )
    self.parameterSetButton.setEnabled(False)
    self.parameterFrame.layout().addWidget(self.parameterSetButton)
    self.cliNodes = None

    self.changeVolumesButton = qt.QPushButton("Change Volumes", self.parameterFrame)
    self.changeVolumesButton.setToolTip("Change the grayscale volume and/or the label map.  Previous calculations from the scene will be deleted.")
    self.changeVolumesButton.setEnabled(False)
    self.parameterFrame.layout().addWidget(self.changeVolumesButton)

    #
    # label map value spin box
    #
    self.labelValueSelector = qt.QSpinBox()
    self.labelValueSelector.setEnabled(False)
    self.labelValueSelector.setMinimum(0)
    self.labelValueSelector.setValue(1)
    self.labelValueSelector.setToolTip( "Label value to calculate features" )
    parametersFormLayout.addRow("Label Value: ", self.labelValueSelector)
    self.totalLabels = 0

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = False
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    #parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

    #
    # scale factor for screen shots
    #
    self.screenshotScaleFactorSliderWidget = ctk.ctkSliderWidget()
    self.screenshotScaleFactorSliderWidget.singleStep = 1.0
    self.screenshotScaleFactorSliderWidget.minimum = 1.0
    self.screenshotScaleFactorSliderWidget.maximum = 50.0
    self.screenshotScaleFactorSliderWidget.value = 1.0
    self.screenshotScaleFactorSliderWidget.setToolTip("Set scale factor for the screen shots.")
    #parametersFormLayout.addRow("Screenshot scale factor", self.screenshotScaleFactorSliderWidget)

    #
    # Create large list of quantitative features
    #
    self.featuresCollapsibleButton = ctk.ctkCollapsibleButton()
    self.featuresCollapsibleButton.text = "Features to Calculate"
    self.layout.addWidget(self.featuresCollapsibleButton)
    self.featuresFormLayout = qt.QFormLayout(self.featuresCollapsibleButton)

    self.QIFrame1 = qt.QFrame(self.parent)
    self.QIFrame1.setLayout(qt.QHBoxLayout())
    self.QIFrame1.layout().setSpacing(0)
    self.QIFrame1.layout().setMargin(0)
    self.featuresFormLayout.addRow("", self.QIFrame1)

    self.MeanCheckBox = qt.QCheckBox("Mean", self.QIFrame1)
    self.QIFrame1.layout().addWidget(self.MeanCheckBox)
    self.MeanCheckBox.checked = False
    self.MeanCheckBox.setToolTip("mean value in region of interest")

    self.StdDevCheckBox = qt.QCheckBox("Std Deviation", self.QIFrame1)
    self.QIFrame1.layout().addWidget(self.StdDevCheckBox)
    self.StdDevCheckBox.checked = False
    self.StdDevCheckBox.setToolTip("standard deviation in region of interest")

    self.MinCheckBox = qt.QCheckBox("Minimum", self.QIFrame1)
    self.QIFrame1.layout().addWidget(self.MinCheckBox)
    self.MinCheckBox.checked = False
    self.MinCheckBox.setToolTip("minimum value in region of interest")

    self.MaxCheckBox = qt.QCheckBox("Maximum", self.QIFrame1)
    self.QIFrame1.layout().addWidget(self.MaxCheckBox)
    self.MaxCheckBox.checked = False
    self.MaxCheckBox.setToolTip("maximum value in region of interest")

    self.QIFrame2 = qt.QFrame(self.parent)
    self.QIFrame2.setLayout(qt.QHBoxLayout())
    self.QIFrame2.layout().setSpacing(0)
    self.QIFrame2.layout().setMargin(0)
    self.featuresFormLayout.addRow("", self.QIFrame2)

    self.Quart1CheckBox = qt.QCheckBox("1st Quartile", self.QIFrame2)
    self.QIFrame2.layout().addWidget(self.Quart1CheckBox)
    self.Quart1CheckBox.checked = False
    self.Quart1CheckBox.setToolTip("25th percentile value in region of interest")

    self.MedianCheckBox = qt.QCheckBox("Median", self.QIFrame2)
    self.QIFrame2.layout().addWidget(self.MedianCheckBox)
    self.MedianCheckBox.checked = False
    self.MedianCheckBox.setToolTip("50th percentile value in region of interest")

    self.Quart3CheckBox = qt.QCheckBox("3rd Quartile", self.QIFrame2)
    self.QIFrame2.layout().addWidget(self.Quart3CheckBox)
    self.Quart3CheckBox.checked = False
    self.Quart3CheckBox.setToolTip("75th percentile value in region of interest")

    self.UpperAdjacentCheckBox = qt.QCheckBox("Upper Adjacent", self.QIFrame2)
    self.QIFrame2.layout().addWidget(self.UpperAdjacentCheckBox)
    self.UpperAdjacentCheckBox.checked = False
    self.UpperAdjacentCheckBox.setToolTip("first value in region of interest not greater than 1.5 times the interquartile range")

    self.QIFrame3 = qt.QFrame(self.parent)
    self.QIFrame3.setLayout(qt.QHBoxLayout())
    self.QIFrame3.layout().setSpacing(0)
    self.QIFrame3.layout().setMargin(0)
    self.featuresFormLayout.addRow("", self.QIFrame3)

    self.Q1CheckBox = qt.QCheckBox("Q1 Distribution", self.QIFrame3)
    self.QIFrame3.layout().addWidget(self.Q1CheckBox)
    self.Q1CheckBox.checked = False
    self.Q1CheckBox.setToolTip("% of gray values that fall within the 1st quarter of the grayscale range within the region of interest")

    self.Q2CheckBox = qt.QCheckBox("Q2 Distribution", self.QIFrame3)
    self.QIFrame3.layout().addWidget(self.Q2CheckBox)
    self.Q2CheckBox.checked = False
    self.Q2CheckBox.setToolTip("% of gray values that fall within the 2nd quarter of the grayscale range within the region of interest")

    self.Q3CheckBox = qt.QCheckBox("Q3 Distribution", self.QIFrame3)
    self.QIFrame3.layout().addWidget(self.Q3CheckBox)
    self.Q3CheckBox.checked = False
    self.Q3CheckBox.setToolTip("% of gray values that fall within the 3rd quarter of the grayscale range within the region of interest")

    self.Q4CheckBox = qt.QCheckBox("Q4 Distribution", self.QIFrame3)
    self.QIFrame3.layout().addWidget(self.Q4CheckBox)
    self.Q4CheckBox.checked = False
    self.Q4CheckBox.setToolTip("% of gray values that fall within the 4th quarter of the grayscale range within the region of interest")

    self.QIFrame4 = qt.QFrame(self.parent)
    self.QIFrame4.setLayout(qt.QHBoxLayout())
    self.QIFrame4.layout().setSpacing(0)
    self.QIFrame4.layout().setMargin(0)
    self.featuresFormLayout.addRow("", self.QIFrame4)

    self.Gly1CheckBox = qt.QCheckBox("Glycolysis Q1", self.QIFrame4)
    self.QIFrame4.layout().addWidget(self.Gly1CheckBox)
    self.Gly1CheckBox.checked = False
    self.Gly1CheckBox.setToolTip("lesion glycolysis calculated from the 1st quarter of the grayscale range within the region of interest")

    self.Gly2CheckBox = qt.QCheckBox("Glycolysis Q2", self.QIFrame4)
    self.QIFrame4.layout().addWidget(self.Gly2CheckBox)
    self.Gly2CheckBox.checked = False
    self.Gly2CheckBox.setToolTip("lesion glycolysis calculated from the 2nd quarter of the grayscale range within the region of interest")

    self.Gly3CheckBox = qt.QCheckBox("Glycolysis Q3", self.QIFrame4)
    self.QIFrame4.layout().addWidget(self.Gly3CheckBox)
    self.Gly3CheckBox.checked = False
    self.Gly3CheckBox.setToolTip("lesion glycolysis calculated from the 3rd quarter of the grayscale range within the region of interest")

    self.Gly4CheckBox = qt.QCheckBox("Glycolysis Q4", self.QIFrame4)
    self.QIFrame4.layout().addWidget(self.Gly4CheckBox)
    self.Gly4CheckBox.checked = False
    self.Gly4CheckBox.setToolTip("lesion glycolysis calculated from the 4th quarter of the grayscale range within the region of interest")

    self.QIFrame5 = qt.QFrame(self.parent)
    self.QIFrame5.setLayout(qt.QHBoxLayout())
    self.QIFrame5.layout().setSpacing(0)
    self.QIFrame5.layout().setMargin(0)
    self.featuresFormLayout.addRow("", self.QIFrame5)

    self.TLGCheckBox = qt.QCheckBox("TLG", self.QIFrame5)
    self.QIFrame5.layout().addWidget(self.TLGCheckBox)
    self.TLGCheckBox.checked = False
    self.TLGCheckBox.setToolTip("total lesion glycolysis")

    self.SAMCheckBox = qt.QCheckBox("SAM", self.QIFrame5)
    self.QIFrame5.layout().addWidget(self.SAMCheckBox)
    self.SAMCheckBox.checked = False
    self.SAMCheckBox.setToolTip("standardized added metabolic activity")

    self.SAMBGCheckBox = qt.QCheckBox("SAM Background", self.QIFrame5)
    self.QIFrame5.layout().addWidget(self.SAMBGCheckBox)
    self.SAMBGCheckBox.checked = False
    self.SAMBGCheckBox.setToolTip("local background estimator near region of interest")

    self.RMSCheckBox = qt.QCheckBox("RMS", self.QIFrame5)
    self.QIFrame5.layout().addWidget(self.RMSCheckBox)
    self.RMSCheckBox.checked = False
    self.RMSCheckBox.setToolTip("root-mean-square value in region of interest")

    self.QIFrame6 = qt.QFrame(self.parent)
    self.QIFrame6.setLayout(qt.QHBoxLayout())
    self.QIFrame6.layout().setSpacing(0)
    self.QIFrame6.layout().setMargin(0)
    self.featuresFormLayout.addRow("", self.QIFrame6)

    self.PeakCheckBox = qt.QCheckBox("Peak", self.QIFrame6)
    self.QIFrame6.layout().addWidget(self.PeakCheckBox)
    self.PeakCheckBox.checked = False
    self.PeakCheckBox.setToolTip("maximum average gray value that is calculated from a 1 cm^3 sphere placed within the region of interest")

    self.VolumeCheckBox = qt.QCheckBox("Volume", self.QIFrame6)
    self.QIFrame6.layout().addWidget(self.VolumeCheckBox)
    self.VolumeCheckBox.checked = False
    self.VolumeCheckBox.setToolTip("volume of region of interest")

    self.selectAllButton = qt.QPushButton("Select All")
    self.selectAllButton.toolTip = "Select all quantitative features."
    self.QIFrame6.layout().addWidget(self.selectAllButton)

    self.deselectAllButton = qt.QPushButton("Deselect All")
    self.deselectAllButton.toolTip = "Deselect all quantitative features."
    self.QIFrame6.layout().addWidget(self.deselectAllButton)

    #
    # Calculate Button
    #
    self.calculateButton = qt.QPushButton("Calculate")
    self.calculateButton.toolTip = "Calculate quantitative features."
    self.calculateButton.enabled = False
    self.featuresFormLayout.addRow(self.calculateButton)

    #
    # Results Frame
    #
    self.resultsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.resultsCollapsibleButton.text = "Results"
    self.layout.addWidget(self.resultsCollapsibleButton)
    self.resultsFormLayout = qt.QFormLayout(self.resultsCollapsibleButton)

    self.resultsFrame = qt.QFrame(self.resultsCollapsibleButton)
    self.resultsFrame.setLayout(qt.QHBoxLayout())
    self.resultsFrame.layout().setSpacing(0)
    self.resultsFrame.layout().setMargin(0)
    self.resultsFormLayout.addWidget(self.resultsFrame)
    self.resultsFrameLabel = qt.QLabel('', self.resultsFrame)
    self.resultsFrame.layout().addWidget(self.resultsFrameLabel)

    # Add vertical spacer
    self.layout.addStretch(1)

    # connections
    self.calculateButton.connect('clicked(bool)', self.onCalculateButton)
    self.grayscaleSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onGrayscaleSelect)
    self.labelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onLabelSelect)
    self.parameterSetButton.connect('clicked(bool)', self.onParameterSetButton)
    self.changeVolumesButton.connect('clicked(bool)',self.onChangeVolumesButton)
    self.labelValueSelector.connect('valueChanged(int)',self.onLabelValueSelect)
    self.selectAllButton.connect('clicked(bool)',self.onSelectAllButton)
    self.deselectAllButton.connect('clicked(bool)',self.onDeselectAllButton)


  def onGrayscaleSelect(self, node):
    """ Set the grayscale volume node.  Check if other buttons can be enabled
    """
    self.grayscaleNode = node
    self.parameterSetButton.enabled = bool(self.grayscaleNode) and bool(self.labelNode)
    self.calculateButton.enabled = bool(self.grayscaleNode) and bool(self.labelNode) and bool(self.cliNodes)


  def onLabelSelect(self, node):
    """ Set the label volume node.  Read the image and determine the number of label values.  Check if other
    buttons can be enabled
    """
    self.labelNode = node
    if bool(self.labelNode):
      #find the correct number of label values
      stataccum = vtk.vtkImageAccumulate()
      stataccum.SetInputData(self.labelNode.GetImageData())
      stataccum.Update()
      lo = int(stataccum.GetMin()[0])
      hi = int(stataccum.GetMax()[0])
      self.labelValueSelector.setRange(lo,hi)
      self.labelValueSelector.setEnabled(True)
      self.totalLabels = (hi-lo)+1
    else:
      self.labelValueSelector.setEnabled(False)
    self.parameterSetButton.enabled = bool(self.grayscaleNode) and bool(self.labelNode)
    self.calculateButton.enabled = bool(self.grayscaleNode) and bool(self.labelNode) and bool(self.cliNodes)


  def onParameterSetButton(self):
    """ Generate mostly-blank vtkMRMLCommandLineModuleNodes for every label value.  Give each node a unique name
    so it can easily be found later.  Disable the volume selectors.  Enable the calculate button.
    """
    if not bool(self.cliNodes):
      self.cliNodes = {}
      self.parameterSetButton.setText('Generating...')
      self.parameterSetButton.repaint()
      slicer.app.processEvents()
      for i in range(self.totalLabels):
        parameters = {}
        parameters['Grayscale_Image'] = self.grayscaleNode.GetID()
        parameters['Label_Image'] = self.labelNode.GetID()
        parameters['Label_Value'] = str(i)
        self.cliNodes[i] = slicer.cli.run(slicer.modules.quantitativeindicescli,None,parameters,wait_for_completion=True)
        self.cliNodes[i].SetName('Label_'+str(i)+'_Quantitative_Indices')
      self.parameterFrameLabel.setText('Quantitative Indices')
      self.parameterSetButton.setText('Generate')
    self.calculateButton.enabled = bool(self.grayscaleNode) and bool(self.labelNode) and bool(self.cliNodes)
    self.grayscaleSelector.enabled = not (bool(self.grayscaleNode) and bool(self.labelNode) and bool(self.cliNodes))
    self.labelSelector.enabled = not (bool(self.grayscaleNode) and bool(self.labelNode) and bool(self.cliNodes))
    self.changeVolumesButton.enabled = bool(self.grayscaleNode) and bool(self.labelNode) and bool(self.cliNodes)
    self.parameterSetButton.enabled = not (bool(self.grayscaleNode) and bool(self.labelNode) and bool(self.cliNodes))


  def onChangeVolumesButton(self):
    """ Bring up a warning window.  If proceeding, delete all vtkMRMLCommandLineModuleNodes that were previously
    generated.  Re-enable the volume selectors and parameter set button.
    """
    if self.confirmDelete('Changing the volumes will delete any previous calculations from the scene.  Proceed?'):
      for i in range(self.totalLabels):
        slicer.mrmlScene.RemoveNode(self.cliNodes[i])
      self.cliNodes = None
      self.grayscaleSelector.enabled = bool(self.grayscaleNode) and bool(self.labelNode) and not bool(self.cliNodes)
      self.labelSelector.enabled = bool(self.grayscaleNode) and bool(self.labelNode) and not bool(self.cliNodes)
      self.parameterSetButton.enabled = bool(self.grayscaleNode) and bool(self.labelNode)
      self.calculateButton.enabled = bool(self.grayscaleNode) and bool(self.labelNode) and bool(self.cliNodes)
      self.parameterFrameLabel.setText(' (none generated) ')
      self.resultsFrameLabel.setText('')
    else:
      return


  def confirmDelete(self, message):
    """ Warning pop-up before deleting previously calculated nodes
    """
    delete = qt.QMessageBox.question(slicer.util.mainWindow(),'Quantitative Indices',message,
                    qt.QMessageBox.Yes, qt.QMessageBox.No)
    return delete == qt.QMessageBox.Yes


  def onLabelValueSelect(self, int):
    #TODO make this do something, possibly select the correct node associated with label value?
    pass


  def onSelectAllButton(self):
    """ Check all quantitative features
    """
    self.MeanCheckBox.checked = True
    self.StdDevCheckBox.checked = True
    self.MinCheckBox.checked = True
    self.MaxCheckBox.checked = True
    self.Quart1CheckBox.checked = True
    self.MedianCheckBox.checked = True
    self.Quart3CheckBox.checked = True
    self.UpperAdjacentCheckBox.checked = True
    self.Q1CheckBox.checked = True
    self.Q2CheckBox.checked = True
    self.Q3CheckBox.checked = True
    self.Q4CheckBox.checked = True
    self.Gly1CheckBox.checked = True
    self.Gly2CheckBox.checked = True
    self.Gly3CheckBox.checked = True
    self.Gly4CheckBox.checked = True
    self.TLGCheckBox.checked = True
    self.SAMCheckBox.checked = True
    self.SAMBGCheckBox.checked = True
    self.RMSCheckBox.checked = True
    self.PeakCheckBox.checked = True
    self.VolumeCheckBox.checked = True


  def onDeselectAllButton(self):
    """ Uncheck all quantitative features
    """
    self.MeanCheckBox.checked = False
    self.StdDevCheckBox.checked = False
    self.MinCheckBox.checked = False
    self.MaxCheckBox.checked = False
    self.Quart1CheckBox.checked = False
    self.MedianCheckBox.checked = False
    self.Quart3CheckBox.checked = False
    self.UpperAdjacentCheckBox.checked = False
    self.Q1CheckBox.checked = False
    self.Q2CheckBox.checked = False
    self.Q3CheckBox.checked = False
    self.Q4CheckBox.checked = False
    self.Gly1CheckBox.checked = False
    self.Gly2CheckBox.checked = False
    self.Gly3CheckBox.checked = False
    self.Gly4CheckBox.checked = False
    self.TLGCheckBox.checked = False
    self.SAMCheckBox.checked = False
    self.SAMBGCheckBox.checked = False
    self.RMSCheckBox.checked = False
    self.PeakCheckBox.checked = False
    self.VolumeCheckBox.checked = False


  def cleanup(self):
    pass


  def volumesAreValid(self):
    """ Returns true if grayscale volume and label volume are the same dimensions
    """
    if not self.grayscaleNode or not self.labelNode:
      return False
    if not self.grayscaleNode.GetImageData() or not self.labelNode.GetImageData():
      return False
    #if self.grayscaleNode.GetImageData().GetDimensions() != self.labelNode.GetImageData().GetDimensions():
      #return False
    return True


  def onCalculateButton(self):
    """ Creates a temporary vtkMRMLCommandLineModuleNode after running the logic and passes it
    to writeResults() method
    """
    if not self.volumesAreValid():
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Quantitative Indices", "Volumes do not have the same geometry.")
      return

    self.calculateButton.text = "Working..."
    self.calculateButton.repaint()
    slicer.app.processEvents()

    #logic = QuantitativeIndicesToolLogic(self.grayscaleNode,self.labelNode)
    #logic = QuantitativeIndicesToolLogic()
    #enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    #screenshotScaleFactor = int(self.screenshotScaleFactorSliderWidget.value)
    labelValue = int(self.labelValueSelector.value)
    # Connections to quantitative feature selections
    meanFlag = self.MeanCheckBox.checked
    stddevFlag = self.StdDevCheckBox.checked
    minFlag = self.MinCheckBox.checked
    maxFlag = self.MaxCheckBox.checked
    quart1Flag = self.Quart1CheckBox.checked
    medianFlag = self.MedianCheckBox.checked
    quart3Flag = self.Quart3CheckBox.checked
    upperAdjacentFlag = self.UpperAdjacentCheckBox.checked
    q1Flag = self.Q1CheckBox.checked
    q2Flag = self.Q2CheckBox.checked
    q3Flag = self.Q3CheckBox.checked
    q4Flag = self.Q4CheckBox.checked
    gly1Flag = self.Gly1CheckBox.checked
    gly2Flag = self.Gly2CheckBox.checked
    gly3Flag = self.Gly3CheckBox.checked
    gly4Flag = self.Gly4CheckBox.checked
    TLGFlag = self.TLGCheckBox.checked
    SAMFlag = self.SAMCheckBox.checked
    SAMBGFlag = self.SAMBGCheckBox.checked
    RMSFlag = self.RMSCheckBox.checked
    PeakFlag = self.PeakCheckBox.checked
    VolumeFlag = self.VolumeCheckBox.checked

    """newNode = logic.run(self.grayscaleNode, self.labelNode, None, enableScreenshotsFlag, screenshotScaleFactor,
                        labelValue, meanFlag, stddevFlag, minFlag, maxFlag, quart1Flag, medianFlag, quart3Flag,
                        upperAdjacentFlag, q1Flag, q2Flag, q3Flag, q4Flag, gly1Flag, gly2Flag, gly3Flag, gly4Flag,
                        TLGFlag, SAMFlag, SAMBGFlag, RMSFlag, PeakFlag, VolumeFlag)"""

    newNode = self.logic.run(self.grayscaleNode, self.labelNode, None, labelValue, meanFlag, stddevFlag, minFlag,
                        maxFlag, quart1Flag, medianFlag, quart3Flag, upperAdjacentFlag, q1Flag, q2Flag, q3Flag,
                        q4Flag, gly1Flag, gly2Flag, gly3Flag, gly4Flag, TLGFlag, SAMFlag, SAMBGFlag, RMSFlag,
                        PeakFlag, VolumeFlag)

    newNode.SetName('Temp_CommandLineModule')

    self.writeResults(newNode)
    self.calculateButton.text = "Calculate"


  def writeResults(self,vtkMRMLCommandLineModuleNode):
    """ Determines the difference between the temporary vtkMRMLCommandLineModuleNode and the "member"
    vtkMRMLCommandLineModuleNode for every quantitative feature.  Creates an output text to display
    on the screen.  Deletes the temporary node.
    """
    newNode = vtkMRMLCommandLineModuleNode
    labelValue = int(self.labelValueSelector.value)
    oldNode = self.cliNodes[labelValue]
    resultText = ''
    for i in range(24):
      newResult = newNode.GetParameterDefault(3,i)
      if (newResult != '--'):
        oldResult = oldNode.GetParameterDefault(3,i)
        feature = oldNode.GetParameterName(3,i)
        if (oldResult == '--'):
          flagName = oldNode.GetParameterName(2,i)
          oldNode.SetParameterAsString(feature,newResult)
          oldNode.SetParameterAsString(flagName,'true')
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
# QuantitativeIndicesToolLogic
#

class QuantitativeIndicesToolLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  #def __init__(self, grayscaleVolume, labelVolume):
    #TODO initialize the nodes
    #pass
  def __init__(self, parent = None):
    ScriptedLoadableModuleLogic.__init__(self, parent)

  def hasImageData(self,volumeNode):
    """This is a dummy logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True


  def delayDisplay(self,message,msec=1000):
    #
    # logic version of delay display
    #
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()


  """def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    self.delayDisplay(description)

    if self.enableScreenshots == 0:
      return

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == -1:
      # full window
      widget = slicer.util.mainWindow()
    elif type == slicer.qMRMLScreenShotDialog().FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog().ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog().Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog().Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog().Green:
      # green slice window
      widget = lm.sliceWidget("Green")

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, self.screenshotScaleFactor, imageData)"""


  """def run(self,inputVolume,labelVolume,cliNode,enableScreenshots=0,screenshotScaleFactor=1,labelValue=1,mean=False,
          stddev=False,minimum=False,maximum=False,quart1=False,median=False,quart3=False,adj=False,
          q1=False,q2=False,q3=False,q4=False,gly1=False,gly2=False,gly3=False,gly4=False,tlg=False,
          sam=False,samBG=False,rms=False,peak=False,volume=False):"""
  def run(self,inputVolume,labelVolume,cliNode,labelValue=1,mean=False,stddev=False,minimum=False,maximum=False,
          quart1=False,median=False,quart3=False,adj=False,q1=False,q2=False,q3=False,q4=False,gly1=False,
          gly2=False,gly3=False,gly4=False,tlg=False,sam=False,samBG=False,rms=False,peak=False,volume=False):
    """
    Run the actual algorithm
    """
    qiModule = slicer.modules.quantitativeindicescli

    parameters = {}
    parameters['Grayscale_Image'] = inputVolume.GetID()
    parameters['Label_Image'] = labelVolume.GetID()
    parameters['Label_Value'] = str(labelValue)
    if(mean):
      parameters['Mean'] = 'true'
    if(stddev):
      parameters['Std_Deviation'] = 'true'
    if(minimum):
      parameters['Min'] = 'true'
    if(maximum):
      parameters['Max'] = 'true'
    if(quart1):
      parameters['First_Quartile'] = 'true'
    if(median):
      parameters['Median'] = 'true'
    if(quart3):
      parameters['Third_Quartile'] = 'true'
    if(adj):
      parameters['Upper_Adjacent'] = 'true'
    if(q1):
      parameters['Q1_Distribution'] = 'true'
    if(q2):
      parameters['Q2_Distribution'] = 'true'
    if(q3):
      parameters['Q3_Distribution'] = 'true'
    if(q4):
      parameters['Q4_Distribution'] = 'true'
    if(gly1):
      parameters['Glycolysis_Q1'] = 'true'
    if(gly2):
      parameters['Glycolysis_Q2'] = 'true'
    if(gly3):
      parameters['Glycolysis_Q3'] = 'true'
    if(gly4):
      parameters['Glycolysis_Q4'] = 'true'
    if(tlg):
      parameters['TLG'] = 'true'
    if(sam):
      parameters['SAM'] = 'true'
    if(samBG):
      parameters['SAM_Background'] = 'true'
    if(rms):
      parameters['RMS'] = 'true'
    if(peak):
      parameters['Peak'] = 'true'
    if(volume):
      parameters['Volume'] = 'true'


    newCLINode = slicer.cli.run(qiModule,cliNode,parameters,wait_for_completion=True)

    #self.takeScreenshot('QuantitativeIndicesTool-Start','Start',-1)

    return newCLINode

from DICOMLib import DICOMUtils
class QuantitativeIndicesToolTest(ScriptedLoadableModuleTest):
#class QuantitativeIndicesToolTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def setUp(self):
    """ Open temporary DICOM database
    """
    slicer.mrmlScene.Clear(0)
    self.tempDataDir = os.path.join(slicer.app.temporaryPath,'PETTest')
    self.tempDicomDatabaseDir = os.path.join(slicer.app.temporaryPath,'PETTestDicom')

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_QuantitativeIndicesTool1()
    self.tearDown()

  def doCleanups(self):
    """ cleanup temporary data in case an exception occurs
    """
    self.tearDown()

  def tearDown(self):
    """ Close temporary DICOM database and remove temporary data
    """
    try:
      import shutil
      if os.path.exists(self.tempDataDir):
        shutil.rmtree(self.tempDataDir)
    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e))

  def loadTestData(self):
    self.patienName = 'QIN-HEADNECK-01-0139'
    #download data and add to dicom database
    zipFileUrl = 'http://slicer.kitware.com/midas3/download/item/257234/QIN-HEADNECK-01-0139-PET.zip'
    zipFilePath = self.tempDataDir+'/dicom.zip'
    zipFileData = self.tempDataDir+'/dicom'
    expectedNumOfFiles = 545
    if not os.access(self.tempDataDir, os.F_OK):
      os.mkdir(self.tempDataDir)
    if not os.access(zipFileData, os.F_OK):
      os.mkdir(zipFileData)
      slicer.util.downloadAndExtractArchive( zipFileUrl, zipFilePath, zipFileData, expectedNumOfFiles)
    DICOMUtils.importDicom(zipFileData)

    # load dataset
    dicomFiles = slicer.util.getFilesInDirectory(zipFileData)
    loadablesByPlugin, loadEnabled = DICOMUtils.getLoadablesFromFileLists([dicomFiles],['DICOMScalarVolumePlugin'])
    loadedNodeIDs = DICOMUtils.loadLoadables(loadablesByPlugin)
    imageNode = slicer.mrmlScene.GetNodeByID(loadedNodeIDs[0])
    imageNode.SetSpacing(3.3940266832237, 3.3940266832237, 2.02490234375) # mimic spacing as produced by Slicer 4.10 for which the test was originally developed
    imageNode.SetOrigin(285.367523193359375,494.58682250976556816,-1873.3819580078125) # mimic origin as produced by Slicer 4.10 for which the test was originally developed

    # apply the SUVbw conversion factor and set units and quantity
    suvNormalizationFactor = 0.00040166400000000007
    quantity = slicer.vtkCodedEntry()
    quantity.SetFromString('CodeValue:126400|CodingSchemeDesignator:DCM|CodeMeaning:Standardized Uptake Value')
    units = slicer.vtkCodedEntry()
    units.SetFromString('CodeValue:{SUVbw}g/ml|CodingSchemeDesignator:UCUM|CodeMeaning:Standardized Uptake Value body weight')
    multiplier = vtk.vtkImageMathematics()
    multiplier.SetOperationToMultiplyByK()
    multiplier.SetConstantK(suvNormalizationFactor)
    multiplier.SetInput1Data(imageNode.GetImageData())
    multiplier.Update()
    imageNode.GetImageData().DeepCopy(multiplier.GetOutput())
    imageNode.GetVolumeDisplayNode().SetWindowLevel(6,3)
    imageNode.GetVolumeDisplayNode().SetAndObserveColorNodeID('vtkMRMLColorTableNodeInvertedGrey')
    imageNode.SetVoxelValueQuantity(quantity)
    imageNode.SetVoxelValueUnits(units)

    return imageNode

  def test_QuantitativeIndicesTool1(self):
    """ produce measurements using QuantitativeIndicesTool and verify results
    """
    try:
      self.assertIsNotNone( slicer.modules.quantitativeindicescli )
      with DICOMUtils.TemporaryDICOMDatabase(self.tempDicomDatabaseDir) as db:
        self.assertTrue(db.isOpen)
        self.assertEqual(slicer.dicomDatabase, db)

        m = slicer.util.mainWindow()
        m.moduleSelector().selectModule('QuantitativeIndicesTool')
        widget = slicer.modules.QuantitativeIndicesToolWidget

        self.delayDisplay('Loading PET DICOM dataset (including download if necessary)')
        petNode = self.loadTestData()
        widget.grayscaleSelector.setCurrentNode(petNode)

        self.delayDisplay('Creating segmentations')
        segmentationNode = slicer.vtkMRMLSegmentationNode()
        slicer.mrmlScene.AddNode(segmentationNode)
        segmentationNode.CreateDefaultDisplayNodes()
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(petNode)

        import vtkSegmentationCorePython as vtkSegmentationCore
        # Geometry for each segment is defined by: radius, posX, posY, posZ
        segmentGeometries = [[30,-54,232,-980], [30,-41,232,-1065], [50,112,232,-1264]]
        for segmentGeometry in segmentGeometries:
          sphereSource = vtk.vtkSphereSource()
          sphereSource.SetRadius(segmentGeometry[0])
          sphereSource.SetCenter(segmentGeometry[1], segmentGeometry[2], segmentGeometry[3])
          sphereSource.Update()
          segment = vtkSegmentationCore.vtkSegment()
          uniqueSegmentID = segmentationNode.GetSegmentation().GenerateUniqueSegmentID("Test")
          segmentationNode.AddSegmentFromClosedSurfaceRepresentation(sphereSource.GetOutput(), uniqueSegmentID)

        labelNode = slicer.vtkMRMLLabelMapVolumeNode()
        slicer.mrmlScene.AddNode(labelNode)
        labelNode.CreateDefaultDisplayNodes()
        slicer.modules.segmentations.logic().ExportAllSegmentsToLabelmapNode(segmentationNode, labelNode)
        widget.labelSelector.setCurrentNode(labelNode)

        self.delayDisplay('Calculating measurements for label 1')
        widget.onParameterSetButton()
        widget.onSelectAllButton()
        widget.onCalculateButton()
        values = {'Mean':3.67861, \
          'Peak':17.335,\
          'Volume':96.9882,\
          'SAM':199.284,\
          'Q1 Distribution':78.7157,\
          'TLG':356.782}
        self._verifyResults(widget.resultsFrameLabel.text, values)

        self.delayDisplay('Calculating measurements for label 2')
        widget.labelValueSelector.setValue(2)
        widget.onCalculateButton()
        values = {'Mean':3.49592, \
          'Peak':19.2768,\
          'Volume':96.4284,\
          'SAM':206.139,\
          'Q1 Distribution':83.9865,\
          'TLG':337.106}
        self._verifyResults(widget.resultsFrameLabel.text, values)

        self.delayDisplay('Test passed!')

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e))

  def _verifyResults(self, resultsString, referenceMeasurements={}):
    assert(resultsString!=None)
    matchedMeasurements = set()
    for line in resultsString.split('\n'):
      items = line.split(':')
      if len(items)<2: continue
      index,value = items[0], float(items[1].strip())
      if index in referenceMeasurements:
        matchedMeasurements.add(index)
        self.assertTrue(abs(float(value)-referenceMeasurements[index])<0.01) # account for potential rounding differences
    self.assertTrue(len(matchedMeasurements)==len(referenceMeasurements))
