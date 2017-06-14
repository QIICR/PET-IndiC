import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
from SegmentStatistics import SegmentStatisticsCalculatorBase, SegmentStatisticsLogic

#
# PETIndiC
#

class PETIndiC(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "PET-IndiC" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Quantification"]
    self.parent.dependencies = ["QuantitativeIndicesTool"]
    self.parent.contributors = ["Ethan Ulrich (Univ. of Iowa), Christian Bauer (Univ. of Iowa), Markus van Tol (Univ. of Iowa), Reinhard R. Beichel (Univ. of Iowa), John Buatti (Univ. of Iowa)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    The PET-IndiC extension allows for fast segmentation of regions of interest and calculation of quantitative indices. 
    For more information about the indices calculated, see 
    <a href=\"http://www.slicer.org/slicerWiki/index.php/Documentation/4.4/Modules/QuantitativeIndicesCLI#Module_Description\">here</a>
    ."""
    self.parent.acknowledgementText = """
    This work is funded in part by Quantitative Imaging to Assess Response in Cancer Therapy Trials NIH grant U01-CA140206 and Quantitative Image Informatics for Cancer Research (QIICR) NIH grant U24 CA180918.""" # replace with organization, grant and thanks.
    
    # register segment statistics calculator
    petCalculator = PETVolumeStatisticsCalculator()
    SegmentStatisticsLogic.registerCalculator( petCalculator )

class PETVolumeStatisticsCalculator(SegmentStatisticsCalculatorBase):

  def __init__(self):
    super(PETVolumeStatisticsCalculator,self).__init__()
    self.name = "PET Volume Statistics"
    self.keys = ("PT mean", "PT std", "PT min", "PT max", "PT rms", "PT volume", "PT 1st quartile", "PT median", "PT 3rd quartile",
                 "PT upper adjacent", "PT TLG", "PT glycosis Q1", "PT glycosis Q2", "PT glycosis Q3", "PT glycosis Q4", 
                 "PT Q1 distribution", "PT Q2 distribution", "PT Q3 distribution", "PT Q4 distribution", "PT SAM", 
                 "PT SAM BG", "PT peak")
    self.defaultKeys = ("PT mean", "PT volume", "PT TLG", "PT peak")
    super(PETVolumeStatisticsCalculator,self).createDefaultOptionsWidget()
    self.key2cliFeatureName = {'PT mean':'Mean', 'PT std':'Std_Deviation', 'PT min':'Min', 'PT max':'Max',
        'PT rms':'RMS', 'PT volume':'Volume', 'PT 1st quartile':'First_Quartile', 'PT median':'Median',
        'PT 3rd quartile':'Third_Quartile', 'PT upper adjacent':'Upper_Adjacent', 'PT TLG':'TLG',
        'PT glycosis Q1':'Glycolysis_Q1', 'PT glycosis Q2':'Glycolysis_Q2', 'PT glycosis Q3':'Glycolysis_Q3',
        'PT glycosis Q4':'Glycolysis_Q4', 'PT Q1 distribution':'Q1_Distribution',
        'PT Q2 distribution':'Q2_Distribution', 'PT Q3 distribution':'Q3_Distribution',
        'PT Q4 distribution':'Q4_Distribution', 'PT SAM':'SAM', 'PT SAM BG':'SAM_Background',
        'PT peak':'Peak'}
    
  def createLabelNodeFromSegment(self, segmentationNode, segmentID, grayscaleNode):
    import vtkSegmentationCorePython as vtkSegmentationCore
    # Get geometry of grayscale volume node as oriented image data
    referenceGeometry_Reference = vtkSegmentationCore.vtkOrientedImageData() # reference geometry in reference node coordinate system
    referenceGeometry_Reference.SetExtent(grayscaleNode.GetImageData().GetExtent())
    ijkToRasMatrix = vtk.vtkMatrix4x4()
    grayscaleNode.GetIJKToRASMatrix(ijkToRasMatrix)
    referenceGeometry_Reference.SetGeometryFromImageToWorldMatrix(ijkToRasMatrix)

    # Get transform between grayscale volume and segmentation
    segmentationToReferenceGeometryTransform = vtk.vtkGeneralTransform()
    slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(segmentationNode.GetParentTransformNode(),
      grayscaleNode.GetParentTransformNode(), segmentationToReferenceGeometryTransform)

    segment = segmentationNode.GetSegmentation().GetSegment(segmentID)
    segmentLabelmap = segment.GetRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())

    segmentLabelmap_Reference = vtkSegmentationCore.vtkOrientedImageData()
    vtkSegmentationCore.vtkOrientedImageDataResample.ResampleOrientedImageToReferenceOrientedImage(
    segmentLabelmap, referenceGeometry_Reference, segmentLabelmap_Reference,
    False, # nearest neighbor interpolation
    False, # no padding
    segmentationToReferenceGeometryTransform)
    
    # see https://github.com/QIICR/QuantitativeReporting/blob/master/QuantitativeReporting.py#L847
    labelNode = slicer.vtkMRMLLabelMapVolumeNode()
    
    segmentationsLogic = slicer.modules.segmentations.logic()
    labelMap = segmentationNode.GetBinaryLabelmapRepresentation(segmentID)
    if not segmentationsLogic.CreateLabelmapVolumeFromOrientedImageData(labelMap, labelNode):
      return None
    labelNode.SetName("{}_label".format(segmentID))
    return labelNode
    
  def computeStatistics(self, segmentationNode, segmentID, grayscaleNode):
    import vtkSegmentationCorePython as vtkSegmentationCore
    requestedKeys = self.getRequestedKeys()

    if len(requestedKeys)==0:
      return {}

    containsLabelmapRepresentation = segmentationNode.GetSegmentation().ContainsRepresentation(
      vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
    if not containsLabelmapRepresentation:
      return {}

    if grayscaleNode is None or grayscaleNode.GetImageData() is None:
      return {}
    
    labelNode = self.createLabelNodeFromSegment( segmentationNode, segmentID, grayscaleNode )
    if not labelNode or not labelNode.GetImageData() or labelNode.GetImageData().GetDimensions()[0]==0: # empty segmentation
      return {}
    slicer.mrmlScene.AddNode(labelNode)
    resultMap = {}
    try:
      parameters = {}
      parameters['Grayscale_Image'] = grayscaleNode.GetID()
      parameters['Label_Image'] = labelNode.GetID()
      parameters['Label_Value'] = 1
      for key in requestedKeys:
        cliFeatureName = self.key2cliFeatureName[key]
        parameters[cliFeatureName] = 'true'
        
      qiModule = slicer.modules.quantitativeindicescli
      cliNode = None
      cliNode = slicer.cli.run(qiModule,cliNode,parameters,wait_for_completion=True)
    
      for i in xrange(0,cliNode.GetNumberOfParametersInGroup(3)):
        newResult = cliNode.GetParameterDefault(3,i)
        if (newResult != '--'):
          feature = cliNode.GetParameterName(3,i)
          feature = feature.replace('_s','')
          resultMap[feature]=float(newResult)
      
    finally:
      slicer.mrmlScene.RemoveNode(labelNode)
                          
    statistics = {}
    for key in requestedKeys:
      cliFeatureName = self.key2cliFeatureName[key]
      if cliFeatureName in resultMap:
        statistics[key] = resultMap[cliFeatureName]
    return statistics
    
  def getMeasurementInfo(self, key, segmentationNode=None, grayscaleNode=None):
    """Get information (name, description, units and DICOM codes) about the measurement for the given key"""
    info = {}
    # fixed values
    info['PT mean'] = {'name': 'mean', 'description': 'mean uptake value', 'DICOM.ModifierRelationship': ('121401','DCM','Derivation'), 'DICOM.ModifierCode': ('R-00317','SRT','Mean')}
    info['PT std'] = {'name': 'std', 'description': 'standard deviation', 'DICOM.ModifierRelationship': ('121401','DCM','Derivation'), 'DICOM.ModifierCode': ('R-10047','SRT','Standard Deviation')}
    info['PT min'] = {'name': 'min', 'description': 'minimum uptake value', 'DICOM.ModifierRelationship': ('121401','DCM','Derivation'), 'DICOM.ModifierCode': ('R-404FB','SRT','Minimum')}
    info['PT max'] = {'name': 'max', 'description': 'maximum uptake value', 'DICOM.ModifierRelationship': ('121401','DCM','Derivation'), 'DICOM.ModifierCode': ('G-A437','SRT','Maximum')}
    info['PT rms'] = {'name': 'rms', 'description': 'root mean square uptake value', 'DICOM.ModifierRelationship': ('121401','DCM','Derivation'), 'DICOM.ModifierCode': ('C2347976','UMLS','RMS')}
    info['PT volume'] = {'name': 'volume', 'description': 'sum of segmented voxel volumes', 'units': 'ml', 'DICOM.MeasurementCode': ('G-D705','SRT','Volume'), 'DICOM.ModifierRelationship': ('G-C036','SRT','Measurement Method'), 'DICOM.ModifierCode': ('126030','DCM','Sum of segmented voxel volumes'), 'DICOM.UnitsCode': ('ml','UCUM','Milliliter')}
    info['PT 1st quartile'] = {'name': '1st quartile', 'description': '1st quartile uptake value', 'DICOM.ModifierRelationship': ('121401','DCM','Derivation'), 'DICOM.ModifierCode': ('250137','99PMP','25th Percentile Value')}
    info['PT median'] = {'name': 'median', 'description': 'median uptake value', 'DICOM.ModifierRelationship': ('121401','DCM','Derivation'), 'DICOM.ModifierCode': ('R-00319','SRT','Median')}
    info['PT 3rd quartile'] = {'name': '3rd quartile', 'description': '3rd quartile uptake value', 'DICOM.ModifierRelationship': ('121401','DCM','Derivation'), 'DICOM.ModifierCode': ('250138','99PMP','75th Percentile Value')}
    info['PT upper adjacent'] = {'name': 'upper adjacent', 'description': 'upper adjacent', 'units': '%', 'DICOM.MeasurementCode': ('250139','99PMP','Upper Adjacent Value'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode': ('%','UCUM','Percent')}
    info['PT TLG'] = {'name': 'TLG', 'description': 'total lesion glycolysis', 'units': 'g', 'DICOM.MeasurementCode': ('126033','DCM','Total Lesion Glycolysis'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode': ('g','UCUM','Gram')}
    info['PT glycosis Q1'] = {'name': 'glycolysis Q1', 'description': 'glycolysis within first quarter of intensity range', 'units': 'g', 'DICOM.MeasurementCode': ('250145','99PMP','Glycolysis Within First Quarter of Intensity Range'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode': ('g','UCUM','Gram')}
    info['PT glycosis Q2'] = {'name': 'glycolysis Q2', 'description': 'glycolysis within second quarter of intensity range', 'units': 'g', 'DICOM.MeasurementCode': ('250146','99PMP','Glycolysis Within Second Quarter of Intensity Range'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode': ('g','UCUM','Gram')}
    info['PT glycosis Q3'] = {'name': 'glycolysis Q3', 'description': 'glycolysis within third quarter of intensity range', 'units': 'g', 'DICOM.MeasurementCode': ('250147','99PMP','Glycolysis Within Third Quarter of Intensity Range'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode': ('g','UCUM','Gram')}
    info['PT glycosis Q4'] = {'name': 'glycolysis Q4', 'description': 'glycolysis within fourth quarter of intensity range', 'units': 'g', 'DICOM.MeasurementCode': ('250148','99PMP','Glycolysis Within Fourth Quarter of Intensity Range'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode': ('g','UCUM','Gram')}
    info['PT Q1 distribution'] = {'name': 'Q1 distribution', 'description': 'percent within fist quarter of intensity range', 'units': '%', 'DICOM.MeasurementCode': ('250140','99PMP','Percent Within First Quarter of Intensity Range'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode':('%','UCUM','Percent')}
    info['PT Q2 distribution'] = {'name': 'Q2 distribution', 'description': 'percent within second quarter of intensity range', 'units': '%', 'DICOM.MeasurementCode': ('250141','99PMP','Percent Within Second Quarter of Intensity Range'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode':('%','UCUM','Percent')}
    info['PT Q3 distribution'] = {'name': 'Q3 distribution', 'description': 'percent within third quarter of intensity range', 'units': '%', 'DICOM.MeasurementCode': ('250142','99PMP','Percent Within Third Quarter of Intensity Range'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode':('%','UCUM','Percent')}
    info['PT Q4 distribution'] = {'name': 'Q4 distribution', 'description': 'percent within fourth quarter of intensity range', 'units': '%', 'DICOM.MeasurementCode': ('250143','99PMP','Percent Within Fourth Quarter of Intensity Range'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode':('%','UCUM','Percent')}
    info['PT SAM'] = {'name': 'SAM', 'description': 'standardized added metabolic activity', 'DICOM.MeasurementCode': ('126037','DCM','Standardized Added Metabolic Activity'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None, 'DICOM.UnitsCode': ('g','UCUM','Gram')}
    info['PT SAM BG'] = {'name': 'SAM background', 'description': 'standardized added metabolic activity background', 'DICOM.MeasurementCode': ('126038','DCM','Standardized Added Metabolic Activity Background'), 'DICOM.ModifierRelationship': None, 'DICOM.ModifierCode': None}
    info['PT peak'] = {'name': 'peak', 'description': 'peak value within ROI', 'DICOM.ModifierRelationship': ('121401','DCM','Derivation'), 'DICOM.ModifierCode': ('126031','DCM','Peak Value Within ROI')}
    
    # units specific DICOM codes
    if grayscaleNode and grayscaleNode.GetAttribute("DICOM.MeasurementUnitsCodeValue"):
      units = grayscaleNode.GetAttribute("DICOM.MeasurementUnitsCodeValue") # for PET DICOMs imported with our extension this is per default "{SUVbw}g/ml"    
      SUVSpecificMeasurements = ['PT mean', 'PT min', 'PT max', 'PT rms', 'PT 1st quartile', 'PT median', 'PT 3rd quartile', 'PT SAM BG','PT peak']
      SUVSpecificUnits = {}
      SUVSpecificMeasurementCode = {}
      SUVSpecificUnitsCode = {}
      
      SUVSpecificUnits['{SUVbw}g/ml'] = '{SUVbw}g/ml'
      SUVSpecificMeasurementCode['{SUVbw}g/ml'] = ('126401','DCM','SUVbw')
      SUVSpecificUnitsCode['{SUVbw}g/ml'] = ('{SUVbw}g/ml','UCUM','Standardized Uptake Value body weight')
      
      SUVSpecificUnits['{SUVlbm}g/ml'] = '{SUVlbm}g/ml'
      SUVSpecificMeasurementCode['{SUVlbm}g/ml'] = ('126402','DCM','SUVlbm')
      SUVSpecificUnitsCode['{SUVlbm}g/ml'] = ('{SUVlbm}g/ml','UCUM','Standardized Uptake Value lean body mass')
      
      SUVSpecificUnits['{SUVbsa}g/ml'] = '{SUVbsa}g/ml'
      SUVSpecificMeasurementCode['{SUVbsa}g/ml'] = ('126403','DCM','SUVbsa')
      SUVSpecificUnitsCode['{SUVbsa}g/ml'] = ('{SUVbsa}g/ml','UCUM','Standardized Uptake Value body surface area')
      
      SUVSpecificUnits['{SUVibw}g/ml'] = '{SUVibw}g/ml'
      SUVSpecificMeasurementCode['{SUVibw}g/ml'] = ('126404','DCM','SUVibw')
      SUVSpecificUnitsCode['{SUVibw}g/ml'] = ('{SUVibw}g/ml','UCUM','Standardized Uptake Value ideal body weight')

      SUVSpecificUnits['{SUV}g/ml'] = '{SUV}g/ml'
      SUVSpecificMeasurementCode['{SUV}g/ml'] = ('126400','DCM','SUV')
      SUVSpecificUnitsCode['{SUV}g/ml'] = ('{SUV}g/ml','UCUM','Standardized Uptake Value')
            
      for m in SUVSpecificMeasurements:
        # only set what has not been specified previously
        if not 'units' in info[m] and units in SUVSpecificUnits:
          info[m]['units'] = SUVSpecificUnits[units]
        if not 'DICOM.MeasurementCode' in info[m] and units in SUVSpecificMeasurementCode:
          info[m]['DICOM.MeasurementCode'] = SUVSpecificMeasurementCode[units]
        if not 'DICOM.UnitsCode' in info[m] and units in SUVSpecificUnitsCode:
          info[m]['DICOM.UnitsCode'] = SUVSpecificUnitsCode[units]    
    
    return info[key] if key in info else None

#
# PETIndiCWidget
#

class PETIndiCWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    self.logic = PETIndiCLogic()

    sliceNodes = slicer.util.getNodes('vtkMRMLSliceNode*')
    for sliceNode in sliceNodes:
      sliceNodes[sliceNode].UseLabelOutlineOn()

    self.volumeDictionary = {}
    self.items = []

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
    self.labelSelector.nodeTypes = ( ("vtkMRMLLabelMapVolumeNode"), "" )
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
    self.preset1Button = qt.QPushButton("FDG PET")
    self.preset1Button.toolTip = "PET SUV image preset (W/L=6/3)" 
    self.presetsFrame.layout().addWidget(self.preset1Button)
    self.preset2Button = qt.QPushButton("PET Rainbow")
    self.preset2Button.toolTip = "PET SUV image preset (W/L=22.6/9.3)" 
    self.presetsFrame.layout().addWidget(self.preset2Button)
    self.preset3Button = qt.QPushButton("FLT PET")
    self.preset3Button.toolTip = "PET SUV image preset (W/L=4/2)" 
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
    self.StdDevCheckBox = self.qiWidget.StdDevCheckBox
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
    self.selectAllButton = self.qiWidget.selectAllButton
    self.deselectAllButton = self.qiWidget.deselectAllButton
    self.calculateButton = self.qiWidget.calculateButton
    self.calculateButton.hide()
    
    #
    # recalculate button
    #
    self.recalculateButton = self.qiWidget.calculateButton
    self.recalculateButton = qt.QPushButton("Recalculate")
    self.recalculateButton.toolTip = "Recalculate using current quantitative features."
    self.recalculateButton.enabled = False
    self.qiWidget.featuresFormLayout.addRow(self.recalculateButton)
    
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
    # results table
    #
    #self.resultsTable = qt.QTableWidget()
    self.resultsTable = CustomTableWidget()
    self.resultsTable.visible = False # hide until populated
    self.resultsTable.setColumnCount(3)
    self.resultsTable.setColumnWidth(0,170)
    self.resultsTable.alternatingRowColors = True
    self.resultsTable.setHorizontalHeaderLabels(['Index','Value','Units'])
    rowHeader = self.resultsTable.verticalHeader()
    rowHeader.visible = False
    font = self.resultsTable.font
    font.setPointSize(12)
    self.resultsTable.setFont(font)
    aiv = qt.QAbstractItemView()
    self.resultsTable.setEditTriggers(aiv.NoEditTriggers) # disable editing
    self.layout.addWidget(self.resultsTable)

    # connections
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onVolumeSelect)
    self.preset1Button.connect('clicked(bool)',self.onPreset1Button)
    self.preset2Button.connect('clicked(bool)',self.onPreset2Button)
    self.preset3Button.connect('clicked(bool)',self.onPreset3Button)
    self.preset4Button.connect('clicked(bool)',self.onPreset4Button)
    self.editorWidget.toolsColor.colorSpin.connect('valueChanged(int)', self.calculateIndicesFromCurrentLabel)
    self.MeanCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.StdDevCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.MinCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.MaxCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.Quart1CheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.MedianCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.Quart3CheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.UpperAdjacentCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.Q1CheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.Q2CheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.Q3CheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.Q4CheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.Gly1CheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.Gly2CheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.Gly3CheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.Gly4CheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.TLGCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.SAMCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.SAMBGCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.RMSCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.PeakCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.VolumeCheckBox.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.selectAllButton.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.deselectAllButton.connect('clicked(bool)', self.onFeatureSelectionChanged)
    self.recalculateButton.connect('clicked(bool)', self.onRecalculate)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    self.editorWidget.toolsColor.colorSpin.disconnect('valueChanged(int)', self.calculateIndicesFromCurrentLabel)
    for volume in self.volumeDictionary:
      labelNode = self.volumeDictionary[volume].labelNode
      labelNode.RemoveObserver(self.volumeDictionary[volume].observerTag)
      # delete the custom attributes on the volume node
      try:
        del self.volumeDictionary[volume].labelNode
        del self.volumeDictionary[volume].observerTag
        del self.volumeDictionary[volume].labels
      except AttributeError:
        pass
    self.items = []
  
  def enter(self):
    self.moduleVisible = True
    if not self.resultsTable.visible: # update values when widget opens
      self.calculateIndicesFromCurrentLabel(self.editorWidget.toolsColor.colorSpin.value)
      
  def exit(self):
    self.moduleVisible = False
    self.editorWidget.exit()

  def onVolumeSelect(self):
    """Search for the dedicated label image. If none found, create a new one."""
    if self.inputSelector.currentNode():
      labelNode = None
      self.labelSelector.setMRMLScene( slicer.mrmlScene )
      volumeNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      labelNode = self.logic.getLabelNodeForNode(volumeNode)
      if not hasattr(volumeNode, 'labelNode'):
        volumeNode.labelNode = labelNode
        volumeNode.labels = [0]
        stataccum = vtk.vtkImageAccumulate()
        stataccum.SetInputData(labelNode.GetImageData())
        stataccum.Update()
        lo = int(stataccum.GetMin()[0])
        hi = int(stataccum.GetMax()[0])
        for value in xrange(lo,hi):
          volumeNode.labels.append(value+1)
      self.labelSelector.setCurrentNode(labelNode)
      if self.resultsTable.columnCount != 3:
        self.resultsTable.setColumnCount(3)
        self.resultsTable.setHorizontalHeaderLabels(['Index','Value','Units'])
      units = self.logic.getImageUnits(volumeNode)
      if units == '(could not retrieve units information)':
        self.resultsTable.removeColumn(2) # no units information
      self.unitsFrameLabel.setText('Voxel Units: ' + units)
        
      appLogic = slicer.app.applicationLogic()
      selNode = appLogic.GetSelectionNode()
      selNode.SetReferenceActiveVolumeID(volumeNode.GetID())
      selNode.SetReferenceActiveLabelVolumeID(labelNode.GetID())
      appLogic.PropagateVolumeSelection()
      
      self.preset1Button.setEnabled(1)
      self.preset2Button.setEnabled(1)
      self.preset3Button.setEnabled(1)
      self.preset4Button.setEnabled(1)
      
      if volumeNode.GetName() not in self.volumeDictionary:
        self.volumeDictionary[volumeNode.GetName()] = volumeNode
        # TODO figure out how to observe only image data changes,
        # currently this is also triggered when the image name changes
        volumeNode.observerTag = labelNode.AddObserver('ModifiedEvent', self.labelModified)
        
      self.calculateIndicesFromCurrentLabel(self.editorWidget.toolsColor.colorSpin.value)
      
    else:
      self.preset1Button.setEnabled(0)
      self.preset2Button.setEnabled(0)
      self.preset3Button.setEnabled(0)
      self.preset4Button.setEnabled(0)
      self.resultsTable.visible = False
            

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
      imageNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      self.logic.presetSUVInvertedGreyFLT(imageNode)

  def onPreset4Button(self):
    if self.inputSelector.currentNode():
      imageNode = slicer.mrmlScene.GetNodeByID(self.inputSelector.currentNodeID)
      self.logic.presetGreyAuto(imageNode)
      
  def labelModified(self, caller, event):
    if caller.GetID() == self.labelSelector.currentNodeID:
      self.resultsTable.visible = False
      if not self.moduleVisible: # do not calculate values if module is not shown
        return
      volumeNode = self.inputSelector.currentNode()
      labelNode = self.labelSelector.currentNode()
      labelValue = self.editorWidget.toolsColor.colorSpin.value
      if labelValue > 0:
        if volumeNode and labelNode:
          if labelValue not in volumeNode.labels:
            volumeNode.labels.append(labelValue)
          pd = qt.QProgressDialog('Calculating...', 'Cancel', 0, 100, slicer.util.mainWindow())
          pd.setModal(True)
          pd.setMinimumDuration(0)
          pd.show()
          pd.setValue(1)
          slicer.app.processEvents()
          cliNode = None
          cliNode = self.calculateIndices(volumeNode, labelNode, None, labelValue)
          if cliNode:
            self.populateResultsTable(cliNode)
          else:
            print('ERROR: could not read output of Quantitative Indices Calculator')
          pd.setValue(100)
      
  def calculateIndicesFromCurrentLabel(self, labelValue):
    self.resultsTable.visible = False
    if not self.moduleVisible: # do not calculate values if module is not shown
      return
    volumeNode = self.inputSelector.currentNode()
    labelNode = self.labelSelector.currentNode()
    if labelValue > 0:
      if volumeNode and labelNode:
        if labelValue in volumeNode.labels:
          pd = qt.QProgressDialog('Calculating...', 'Cancel', 0, 100, slicer.util.mainWindow())
          pd.setModal(True)
          pd.setMinimumDuration(0)
          pd.show()
          pd.setValue(1)
          slicer.app.processEvents()
          cliNode = None
          cliNode = self.calculateIndices(volumeNode, labelNode, None, labelValue)
          if cliNode:
            self.populateResultsTable(cliNode)
          else:
            print('ERROR: could not read output of Quantitative Indices Calculator')
          pd.setValue(100)
  
  def onFeatureSelectionChanged(self):
    self.recalculateButton.enabled = True
    
  def onRecalculate(self):
    self.recalculateButton.enabled = False
    self.calculateIndicesFromCurrentLabel(self.editorWidget.toolsColor.colorSpin.value)
            
  def calculateIndices(self, volumeNode, labelNode, cliNode, labelValue):
    newNode = None
    newNode = self.logic.calculateOnLabelModified(volumeNode, labelNode, cliNode, labelValue, self.MeanCheckBox.checked, self.StdDevCheckBox.checked, self.MinCheckBox.checked, self.MaxCheckBox.checked, self.Quart1CheckBox.checked, self.MedianCheckBox.checked, self.Quart3CheckBox.checked, self.UpperAdjacentCheckBox.checked, self.Q1CheckBox.checked, self.Q2CheckBox.checked, self.Q3CheckBox.checked, self.Q4CheckBox.checked, self.Gly1CheckBox.checked, self.Gly2CheckBox.checked, self.Gly3CheckBox.checked, self.Gly4CheckBox.checked, self.TLGCheckBox.checked, self.SAMCheckBox.checked, self.SAMBGCheckBox.checked, self.RMSCheckBox.checked, self.PeakCheckBox.checked, self.VolumeCheckBox.checked)
    return newNode
    
  def populateResultsTable(self, vtkMRMLCommandLineModuleNode):
    """Reads the output of QuantitativeIndicesCLI and populates the results table"""
    newNode = vtkMRMLCommandLineModuleNode
    resultArray = []
    self.items = []
    for i in xrange(0,newNode.GetNumberOfParametersInGroup(3)):
      newResult = newNode.GetParameterDefault(3,i)
      if (newResult != '--'):
        feature = newNode.GetParameterName(3,i)
        feature = feature.replace('_s','')
        resultArray.append([feature,newResult])
    numRows = len(resultArray)
    self.resultsTable.setRowCount(numRows)
    for i in xrange(0,numRows):
      if not self.resultsTable.item(i,0):
        indexEntry = qt.QTableWidgetItem()
        indexEntry.setText(resultArray[i][0])
        self.resultsTable.setItem(i,0,indexEntry)
        self.items.append(indexEntry)
      else:
        indexEntry = self.resultsTable.item(i,0)
        indexEntry.setText(resultArray[i][0])
      if not self.resultsTable.item(i,1):
        valueEntry = qt.QTableWidgetItem()
        valueEntry.setText(resultArray[i][1])
        self.resultsTable.setItem(i,1,valueEntry)
        self.items.append(valueEntry)
      else:
        valueEntry = self.resultsTable.item(i,1)
        valueEntry.setText(resultArray[i][1])
      if self.resultsTable.columnCount == 3:
        imageUnits = self.unitsFrameLabel.text.replace('Voxel Units: ','')
        if not self.resultsTable.item(i,2):
          unitsEntry = qt.QTableWidgetItem()
          unitsEntry.setText(self.logic.getUnitsForIndex(imageUnits, resultArray[i][0]))
          self.resultsTable.setItem(i,2,unitsEntry)
          self.items.append(unitsEntry)
        else:
          unitsEntry = self.resultsTable.item(i,2)
          unitsEntry.setText(self.logic.getUnitsForIndex(imageUnits, resultArray[i][0]))
    rowHeight = self.resultsTable.rowHeight(0)
    self.resultsTable.setFixedHeight(rowHeight*(numRows+1)+1)
    self.resultsTable.visible = True
    slicer.mrmlScene.RemoveNode(newNode)      

#
# PETIndiCLogic
#

class PETIndiCLogic(ScriptedLoadableModuleLogic):
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
    scalarVolumes.UnRegister(slicer.mrmlScene)
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
      imageNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLLabelMapVolumeNode())
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
       
      imageNode.SetName(imageName + '_label')

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
    
  def presetSUVInvertedGreyFLT(self, imageNode):
    print('  Changing W/L to 4/2')
    displayNode = imageNode.GetVolumeDisplayNode()
    displayNode.AutoWindowLevelOff()
    displayNode.SetWindowLevel(4,2)
    displayNode.SetInterpolate(0)
    displayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeInvertedGrey')
    
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
    
  def calculateOnLabelModified(self, scalarVolume, labelVolume, cliNode, labelValue, meanFlag, stddevFlag, minFlag,
                        maxFlag, quart1Flag, medianFlag, quart3Flag, upperAdjacentFlag, q1Flag, q2Flag, q3Flag, 
                        q4Flag, gly1Flag, gly2Flag, gly3Flag, gly4Flag, TLGFlag, SAMFlag, SAMBGFlag, RMSFlag, 
                        PeakFlag, VolumeFlag):
    print('      Recalculating QIs')
    qiLogic = slicer.modules.QuantitativeIndicesToolWidget.logic
    node = qiLogic.run(scalarVolume,labelVolume,cliNode,labelValue,meanFlag, stddevFlag, minFlag,
                        maxFlag, quart1Flag, medianFlag, quart3Flag, upperAdjacentFlag, q1Flag, q2Flag, q3Flag, 
                        q4Flag, gly1Flag, gly2Flag, gly3Flag, gly4Flag, TLGFlag, SAMFlag, SAMBGFlag, RMSFlag, 
                        PeakFlag, VolumeFlag)
    return node
    
  def getUnitsForIndex(self, imageUnits, indexName):
    """Attempt to interpret units """
    if imageUnits not in ['{SUVbw}g/ml','{SUVlbm}g/ml','{SUVibw}g/ml']: # TODO '{SUVbsa}cm2/ml'
      print('WARNING: could not interpret units for '+ indexName +'. Units: '+ imageUnits)
      return '-'
    else:
      units = (imageUnits.split('{')[1]).split('}')[0]
      if indexName in ['Mean','Std Deviation','Min','Max','Peak','First Quartile','Median','Third Quartile','Upper Adjacent','RMS','SAM Background']:
        return units
      elif indexName=='Volume':
        return 'ml'
      #elif indexName=='Variance':
        #return units + '^2'
      elif indexName in ['TLG','Glycolysis Q1','Glycolysis Q2','Glycolysis Q3','Glycolysis Q4','SAM']:
        return units + '*ml'
      elif indexName in ['Q1 Distribution','Q2 Distribution','Q3 Distribution','Q4 Distribution']:
        return '%'
      else:
        print('WARNING: could not interpret units for '+ indexName +'. Units: '+ imageUnits)
        return '-'
  
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


class CustomTableWidget(qt.QTableWidget):
  """Allows for copying the table to clipboard"""
  def __init__(self, parent=None):
    super(CustomTableWidget, self).__init__(parent)
    
  def keyPressEvent(self, event):
    if event.matches(qt.QKeySequence.Copy):
      self.copyCells()
    else:
      qt.QTableWidget.keyPressEvent(self, event)

  def copyCells(self):
    indexes = self.getSelectedCells()
    #print indexes
    text = ''
    highestCol = indexes[len(indexes)-1][1]
    for index in indexes:
      cell = self.item(index[0],index[1])
      if cell:
        text += cell.text()
        if index[1] != highestCol:
          text += '\t'
        else:
          text += '\n'
    #print text
    qt.QApplication.clipboard().setText(text)
    
  def getSelectedCells(self):
    cells = []
    for row in xrange(0, self.rowCount):
      for col in xrange(0, self.columnCount):
        cell = self.item(row,col)
        if cell.isSelected():
          cells.append([row,col])
    return cells
    

class PETIndiCTest(ScriptedLoadableModuleTest):
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
    self.test_PETIndiC1()

  def test_PETIndiC1(self):
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
    logic = PETIndiCLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
