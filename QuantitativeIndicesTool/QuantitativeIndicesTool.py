import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from SegmentStatistics import SegmentStatisticsLogic
from PETVolumeSegmentStatisticsPlugin import PETVolumeSegmentStatisticsPlugin

#
# QuantitativeIndices
#

class QuantitativeIndicesTool(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    parent.title = "Quantitative Indices Tool"
    parent.categories = ["Quantification"]
    parent.dependencies = ["QuantitativeIndicesCLI"]
    parent.contributors = ["Ethan Ulrich (University of Iowa), Andrey Fedorov (SPL), Markus van Tol (University of Iowa), Christian Bauer (University of Iowa), Reinhard Beichel (University of Iowa), John Buatti (University of Iowa)"]
    parent.helpText = """
    This extension calculates quantitative features from a grayscale volume and
    a segmentation. Select an input volume and segmentation, choose a segment,
    select the desired features, and click Calculate.
    """
    parent.acknowledgementText = """
    This work was funded in part by Quantitative Imaging to Assess Response in Cancer Therapy Trials NIH grant U01-CA140206 and Quantitative Image Informatics for Cancer Research (QIICR) NIH grant U24 CA180918.
    """

    # register segment statistics plugin
    petSegmentStatisticsPlugin = PETVolumeSegmentStatisticsPlugin()
    SegmentStatisticsLogic.registerPlugin( petSegmentStatisticsPlugin )

#
# qQuantitativeIndicesToolWidget
#

class QuantitativeIndicesToolWidget(ScriptedLoadableModuleWidget):

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
    self.grayscaleSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
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
    # segmentation selector
    #
    self.segmentationSelector = slicer.qMRMLNodeComboBox()
    self.segmentationSelector.nodeTypes = ["vtkMRMLSegmentationNode"]
    self.segmentationSelector.selectNodeUponCreation = True
    self.segmentationSelector.addEnabled = False
    self.segmentationSelector.removeEnabled = False
    self.segmentationSelector.noneEnabled = True
    self.segmentationSelector.showHidden = False
    self.segmentationSelector.showChildNodeTypes = False
    self.segmentationSelector.setMRMLScene( slicer.mrmlScene )
    self.segmentationSelector.setToolTip( "Input segmentation." )
    parametersFormLayout.addRow("Segmentation: ", self.segmentationSelector)
    self.segmentationNode = None

    #
    # segment selector
    #
    self.segmentSelector = qt.QComboBox()
    self.segmentSelector.setToolTip( "Select segment to calculate features for." )
    parametersFormLayout.addRow("Segment: ", self.segmentSelector)

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
    self.QIFrame1.layout().setContentsMargins(0, 0, 0, 0)
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
    self.QIFrame2.layout().setContentsMargins(0, 0, 0, 0)
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
    self.QIFrame3.layout().setContentsMargins(0, 0, 0, 0)
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
    self.QIFrame4.layout().setContentsMargins(0, 0, 0, 0)
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
    self.QIFrame5.layout().setContentsMargins(0, 0, 0, 0)
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
    self.QIFrame6.layout().setContentsMargins(0, 0, 0, 0)
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
    self.resultsFormLayout = qt.QVBoxLayout(self.resultsCollapsibleButton)

    self.resultsFrame = qt.QFrame(self.resultsCollapsibleButton)
    self.resultsFrame.setLayout(qt.QVBoxLayout())
    self.resultsFrame.layout().setSpacing(0)
    self.resultsFrame.layout().setContentsMargins(0, 0, 0, 0)
    self.resultsFormLayout.addWidget(self.resultsFrame)
    self.tableView = slicer.qMRMLTableView(self.resultsFrame)
    self.tableView.setMinimumHeight(150)
    self.tableView.setSelectionMode(qt.QTableView.ContiguousSelection)
    self.resultsFrame.layout().addWidget(self.tableView)

    self.tableNode = None

    # connections
    self.calculateButton.connect('clicked(bool)', self.onCalculateButton)
    self.grayscaleSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onGrayscaleSelect)
    self.segmentationSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSegmentationSelect)
    self.segmentSelector.connect('currentIndexChanged(int)', self.onSegmentSelect)
    self.selectAllButton.connect('clicked(bool)',self.onSelectAllButton)
    self.deselectAllButton.connect('clicked(bool)',self.onDeselectAllButton)

  def setMeasurementsTable(self, table):
    if table:
      self.tableNode = table
      self.tableNode.SetLocked(True)
      self.tableView.setMRMLTableNode(self.tableNode)
    else:
      if self.tableNode:
        self.tableNode.RemoveAllColumns()
      self.tableView.setMRMLTableNode(self.tableNode if self.tableNode else None)

  def onGrayscaleSelect(self, node):
    self.grayscaleNode = node
    self._updateCalculateButtonState()

  def onSegmentationSelect(self, node):
    self.segmentationNode = node
    self.segmentSelector.clear()
    if node:
      segmentation = node.GetSegmentation()
      for i in range(segmentation.GetNumberOfSegments()):
        segmentID = segmentation.GetNthSegmentID(i)
        segment = segmentation.GetSegment(segmentID)
        self.segmentSelector.addItem(segment.GetName(), segmentID)
    self._updateCalculateButtonState()

  def onSegmentSelect(self, index):
    self._updateCalculateButtonState()

  def _updateCalculateButtonState(self):
    self.calculateButton.enabled = (
      bool(self.grayscaleNode) and
      bool(self.segmentationNode) and
      self.segmentSelector.currentIndex >= 0
    )

  def onSelectAllButton(self):
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
    if not self.grayscaleNode or not self.segmentationNode:
      return False
    if not self.grayscaleNode.GetImageData():
      return False
    segmentID = self.segmentSelector.currentData
    if not segmentID:
      return False
    return True

  def _exportSegmentToLabelMap(self, segmentationNode, segmentID, referenceVolumeNode):
    """Export a single segment to a temporary label map volume (label value = 1)."""
    labelNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode', 'temp_qi_label')
    segmentIds = vtk.vtkStringArray()
    segmentIds.InsertNextValue(segmentID)
    slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
        segmentationNode, segmentIds, labelNode, referenceVolumeNode,
        slicer.vtkSegmentation.EXTENT_REFERENCE_GEOMETRY)
    return labelNode

  def onCalculateButton(self):
    if not self.volumesAreValid():
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Quantitative Indices", "Please select a valid volume, segmentation, and segment.")
      return

    self.calculateButton.text = "Working..."
    self.calculateButton.repaint()
    slicer.app.processEvents()

    segmentID = self.segmentSelector.currentData
    labelNode = self._exportSegmentToLabelMap(self.segmentationNode, segmentID, self.grayscaleNode)
    try:
      newNode = self.logic.run(self.grayscaleNode, labelNode, None, 1,
                          self.MeanCheckBox.checked, self.StdDevCheckBox.checked,
                          self.MinCheckBox.checked, self.MaxCheckBox.checked,
                          self.Quart1CheckBox.checked, self.MedianCheckBox.checked,
                          self.Quart3CheckBox.checked, self.UpperAdjacentCheckBox.checked,
                          self.Q1CheckBox.checked, self.Q2CheckBox.checked,
                          self.Q3CheckBox.checked, self.Q4CheckBox.checked,
                          self.Gly1CheckBox.checked, self.Gly2CheckBox.checked,
                          self.Gly3CheckBox.checked, self.Gly4CheckBox.checked,
                          self.TLGCheckBox.checked, self.SAMCheckBox.checked,
                          self.SAMBGCheckBox.checked, self.RMSCheckBox.checked,
                          self.PeakCheckBox.checked, self.VolumeCheckBox.checked)
    finally:
      slicer.mrmlScene.RemoveNode(labelNode)

    self.writeResults(newNode)
    self.calculateButton.text = "Calculate"

  def writeResults(self, cliNode):
    """Read CLI output and populate the results table."""
    if not self.tableNode:
      self.tableNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTableNode','Quantitative Indices Table')

    imageUnits = self.logic.getImageUnits(self.grayscaleNode)

    table = self.tableNode
    tableWasModified = table.StartModify()
    table.RemoveAllColumns()
    table.AddColumn().SetName("Index")
    table.AddColumn().SetName("Value")
    table.AddColumn().SetName("Units")

    for i in range(cliNode.GetNumberOfParametersInGroup(3)):
      result = cliNode.GetParameterDefault(3, i)
      if result != '--':
        feature = cliNode.GetParameterName(3, i)
        feature = feature.replace('_s', '').replace('_', ' ')
        if feature == '':
          continue
        units = self.logic.getUnitsForIndex(imageUnits, feature)
        row = table.AddEmptyRow()
        table.GetTable().GetColumn(0).SetValue(row, feature)
        table.GetTable().GetColumn(1).SetValue(row, result)
        table.GetTable().GetColumn(2).SetValue(row, units)

    table.SetUseColumnNameAsColumnHeader(True)
    table.Modified()
    table.EndModify(tableWasModified)
    self.setMeasurementsTable(table)

    self.software_version = cliNode.GetParameterDefault(0, 0)
    slicer.mrmlScene.RemoveNode(cliNode)

#
# QuantitativeIndicesToolLogic
#

class QuantitativeIndicesToolLogic(ScriptedLoadableModuleLogic):

  def __init__(self, parent = None):
    ScriptedLoadableModuleLogic.__init__(self, parent)

  def hasImageData(self,volumeNode):
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True

  def run(self,inputVolume,labelVolume,cliNode,labelValue=1,mean=False,stddev=False,minimum=False,maximum=False,
          quart1=False,median=False,quart3=False,adj=False,q1=False,q2=False,q3=False,q4=False,gly1=False,
          gly2=False,gly3=False,gly4=False,tlg=False,sam=False,samBG=False,rms=False,peak=False,volume=False):
    """Run the CLI with a grayscale volume and label map."""
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
    return newCLINode

  def runOnSegment(self, inputVolume, segmentationNode, segmentID, cliNode=None,
                   mean=False, stddev=False, minimum=False, maximum=False,
                   quart1=False, median=False, quart3=False, adj=False,
                   q1=False, q2=False, q3=False, q4=False,
                   gly1=False, gly2=False, gly3=False, gly4=False,
                   tlg=False, sam=False, samBG=False, rms=False,
                   peak=False, volume=False):
    """Convenience method: export segment to temp label map, run CLI, clean up."""
    labelNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode', 'temp_qi_export')
    segmentIds = vtk.vtkStringArray()
    segmentIds.InsertNextValue(segmentID)
    slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
        segmentationNode, segmentIds, labelNode, inputVolume,
        slicer.vtkSegmentation.EXTENT_REFERENCE_GEOMETRY)
    try:
      result = self.run(inputVolume, labelNode, cliNode, labelValue=1,
                        mean=mean, stddev=stddev, minimum=minimum, maximum=maximum,
                        quart1=quart1, median=median, quart3=quart3, adj=adj,
                        q1=q1, q2=q2, q3=q3, q4=q4,
                        gly1=gly1, gly2=gly2, gly3=gly3, gly4=gly4,
                        tlg=tlg, sam=sam, samBG=samBG, rms=rms,
                        peak=peak, volume=volume)
    finally:
      slicer.mrmlScene.RemoveNode(labelNode)
    return result

  def getImageUnits(self, imageNode):
    """Search for units in the image node attributes or voxel value units"""
    units = None
    if imageNode.GetAttribute('DICOM.MeasurementUnitsCodeValue'):
      units = imageNode.GetAttribute('DICOM.MeasurementUnitsCodeValue')
    elif imageNode.GetVoxelValueUnits():
      units =  imageNode.GetVoxelValueUnits().GetCodeValue()
    return units

  def getUnitsForIndex(self, imageUnits, indexName):
    """Interpret units """
    if imageUnits==None: imageUnits='{-}g/ml'
    if imageUnits not in ['{-}g/ml','{SUVbw}g/ml','{SUVlbm}g/ml','{SUVibw}g/ml']:
      return '-'
    else:
      units = (imageUnits.split('{')[1]).split('}')[0]
      if indexName in ['Mean','Std Deviation','Min','Max','Peak','First Quartile','Median','Third Quartile','Upper Adjacent','RMS','SAM Background']:
        return units
      elif indexName=='Volume':
        return 'ml'
      elif indexName in ['TLG','Glycolysis Q1','Glycolysis Q2','Glycolysis Q3','Glycolysis Q4','SAM']:
        return (units + '*ml') if units!='-' else '-'
      elif indexName in ['Q1 Distribution','Q2 Distribution','Q3 Distribution','Q4 Distribution']:
        return '%'
      else:
        return '-'

from DICOMLib import DICOMUtils
class QuantitativeIndicesToolTest(ScriptedLoadableModuleTest):
  """Test case for the QuantitativeIndicesTool module."""

  def setUp(self):
    slicer.mrmlScene.Clear(0)
    self.tempDataDir = os.path.join(slicer.app.temporaryPath,'PETTest')
    self.tempDicomDatabaseDir = os.path.join(slicer.app.temporaryPath,'PETTestDicom')

  def runTest(self):
    self.setUp()
    self.test_QuantitativeIndicesTool1()
    self.tearDown()

  def doCleanups(self):
    self.tearDown()

  def tearDown(self):
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
    zipFileUrl = 'http://github.com/QIICR/PETTumorSegmentation/releases/download/4.10.2/QIN-HEADNECK-01-0139-PET.zip'
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
    """Produce measurements using QuantitativeIndicesTool and verify results."""
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
        segmentationNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
        segmentationNode.CreateDefaultDisplayNodes()
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(petNode)

        import vtkSegmentationCorePython as vtkSegmentationCore
        segmentGeometries = [[30,-54,232,-980], [30,-41,232,-1065], [50,112,232,-1264]]
        for segmentGeometry in segmentGeometries:
          sphereSource = vtk.vtkSphereSource()
          sphereSource.SetRadius(segmentGeometry[0])
          sphereSource.SetCenter(segmentGeometry[1], segmentGeometry[2], segmentGeometry[3])
          sphereSource.Update()
          segmentationNode.AddSegmentFromClosedSurfaceRepresentation(sphereSource.GetOutput(),
              segmentationNode.GetSegmentation().GenerateUniqueSegmentID("Test"))

        widget.segmentationSelector.setCurrentNode(segmentationNode)

        self.delayDisplay('Calculating measurements for segment 1')
        widget.segmentSelector.setCurrentIndex(0)
        widget.onSelectAllButton()
        widget.onCalculateButton()
        values = {'Mean':3.67861, \
          'Peak':17.335,\
          'Volume':96.9882,\
          'SAM':199.284,\
          'Q1 Distribution':78.7157,\
          'TLG':356.782}
        self._verifyResults(widget.tableNode, values)

        self.delayDisplay('Calculating measurements for segment 2')
        widget.segmentSelector.setCurrentIndex(1)
        widget.onCalculateButton()
        values = {'Mean':3.49592, \
          'Peak':19.2768,\
          'Volume':96.4284,\
          'SAM':206.139,\
          'Q1 Distribution':83.9865,\
          'TLG':337.106}
        self._verifyResults(widget.tableNode, values)

        self.delayDisplay('Test passed!')

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e))

  def _verifyResults(self, resultsTable, referenceMeasurements={}):
    assert(resultsTable!=None)
    matchedMeasurements = set()
    for i in range(resultsTable.GetNumberOfRows()):
      index = resultsTable.GetCellText(i,0)
      value = resultsTable.GetCellText(i,1)
      if index in referenceMeasurements:
        matchedMeasurements.add(index)
        self.assertTrue(abs(float(value)-referenceMeasurements[index])<0.01) # account for potential rounding differences
    self.assertTrue(len(matchedMeasurements)==len(referenceMeasurements))
