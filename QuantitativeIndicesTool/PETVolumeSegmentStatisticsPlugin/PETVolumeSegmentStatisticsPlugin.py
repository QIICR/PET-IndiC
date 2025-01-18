import vtk, slicer
from slicer.i18n import tr as _
from SegmentStatisticsPlugins import SegmentStatisticsPluginBase

class PETVolumeSegmentStatisticsPlugin(SegmentStatisticsPluginBase):
  """Statistical plugin for segmentations with PET volumes"""

  def __init__(self):
    super(PETVolumeSegmentStatisticsPlugin,self).__init__()
    self.name = "PET Volume"
    self.keys = ["mean", "std", "min", "max", "rms", "volume",
                "1st_quartile", "median", "3rd_quartile", "upper_adjacent", "TLG", "glycosis_Q1",
                "glycosis_Q2", "glycosis_Q3", "glycosis_Q4", "Q1_distribution",
                "Q2_distribution", "Q3_distribution", "Q4_distribution", "SAM", "SAM_BG",
                "peak"]
    self.defaultKeys = ["mean", "volume", "TLG", "peak"]
    self.key2cliFeatureName = {'mean':'Mean', 'std':'Std_Deviation', 'min':'Min', 'max':'Max',
        'rms':'RMS', 'volume':'Volume', '1st_quartile':'First_Quartile', 'median':'Median',
        '3rd_quartile':'Third_Quartile', 'upper_adjacent':'Upper_Adjacent', 'TLG':'TLG',
        'glycosis_Q1':'Glycolysis_Q1', 'glycosis_Q2':'Glycolysis_Q2', 'glycosis_Q3':'Glycolysis_Q3',
        'glycosis_Q4':'Glycolysis_Q4', 'Q1_distribution':'Q1_Distribution',
        'Q2_distribution':'Q2_Distribution', 'Q3_distribution':'Q3_Distribution',
        'Q4_distribution':'Q4_Distribution', 'SAM':'SAM', 'SAM_BG':'SAM_Background',
        'peak':'Peak'}
  
  def createLabelNodeFromSegment(self, segmentationNode, segmentID, grayscaleNode):
    import vtkSegmentationCorePython as vtkSegmentationCore    
    # see https://github.com/QIICR/QuantitativeReporting/blob/master/QuantitativeReporting.py#L847
    labelNode = slicer.vtkMRMLLabelMapVolumeNode()
    
    segmentationsLogic = slicer.modules.segmentations.logic()
    labelMap = slicer.vtkOrientedImageData()
    segmentationNode.GetBinaryLabelmapRepresentation(segmentID, labelMap)
    if not segmentationsLogic.CreateLabelmapVolumeFromOrientedImageData(labelMap, labelNode):
      return None
    labelNode.SetName("{}_label".format(segmentID))
    return labelNode

  def computeStatistics(self, segmentID):
    import vtkSegmentationCorePython as vtkSegmentationCore
    requestedKeys = self.getRequestedKeys()

    segmentationNode = slicer.mrmlScene.GetNodeByID(self.getParameterNode().GetParameter("Segmentation"))
    grayscaleNode = slicer.mrmlScene.GetNodeByID(self.getParameterNode().GetParameter("ScalarVolume"))

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
    
      for i in range(0,cliNode.GetNumberOfParametersInGroup(3)):
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

  def getMeasurementInfo(self, key):
    """Get information (name, description, units, ...) about the measurement for the given key""" 
    
    scalarVolumeNode = slicer.mrmlScene.GetNodeByID(self.getParameterNode().GetParameter("ScalarVolume"))
    
    scalarVolumeQuantity = scalarVolumeNode.GetVoxelValueQuantity() if scalarVolumeNode else self.createCodedEntry("", "", "")
    scalarVolumeUnits = scalarVolumeNode.GetVoxelValueUnits() if scalarVolumeNode else self.createCodedEntry("", "", "")
    if not scalarVolumeQuantity:
      scalarVolumeQuantity = self.createCodedEntry("", "", "")
    if not scalarVolumeUnits:
      scalarVolumeUnits = self.createCodedEntry("", "", "")

    info = dict()
   
    info["mean"] = \
      self.createMeasurementInfo(name="Mean", title=_("Mean"), description="Mean uptake value",
                                   units=scalarVolumeUnits.GetCodeMeaning(),
                                   quantityDicomCode=scalarVolumeQuantity.GetAsString(),
                                   unitsDicomCode=scalarVolumeUnits.GetAsString(),
                                   derivationDicomCode=self.createCodedEntry("R-00317","SRT","Mean", True))
                                   
    info["std"] = \
      self.createMeasurementInfo(name="Standard deviation", title=_("Standard deviation"), description="Standard deviation of uptake values",
                                   units=scalarVolumeUnits.GetCodeMeaning(),
                                   quantityDicomCode=scalarVolumeQuantity.GetAsString(),
                                   unitsDicomCode=scalarVolumeUnits.GetAsString(),
                                   derivationDicomCode=self.createCodedEntry('R-10047','SRT','Standard Deviation', True))     
                             
    info["min"] = \
      self.createMeasurementInfo(name="Minimum", title=_("Minimum"), description="Minimum uptake value",
                                   units=scalarVolumeUnits.GetCodeMeaning(),
                                   quantityDicomCode=scalarVolumeQuantity.GetAsString(),
                                   unitsDicomCode=scalarVolumeUnits.GetAsString(),
                                   derivationDicomCode=self.createCodedEntry("R-404FB", "SRT", "Minimum", True))

    info["max"] = \
      self.createMeasurementInfo(name="Maximum", title=_("Maximum"), description="Maximum uptake value",
                                   units=scalarVolumeUnits.GetCodeMeaning(),
                                   quantityDicomCode=scalarVolumeQuantity.GetAsString(),
                                   unitsDicomCode=scalarVolumeUnits.GetAsString(),
                                   derivationDicomCode=self.createCodedEntry("G-A437","SRT","Maximum", True))
                                   
    info["rms"] = \
      self.createMeasurementInfo(name="RMS", title=_("RMS"), description="Root mean square uptake value",
                                   units=scalarVolumeUnits.GetCodeMeaning(),
                                   quantityDicomCode=scalarVolumeQuantity.GetAsString(),
                                   unitsDicomCode=scalarVolumeUnits.GetAsString(),
                                   derivationDicomCode=self.createCodedEntry("C2347976","UMLS","RMS", True))

    info["volume"] = \
      self.createMeasurementInfo(name="Volume", title=_("Volume"), description="Sum of segmented voxel volumes", units="ml",
                                   quantityDicomCode=self.createCodedEntry("G-D705", "SRT", "Volume", True),
                                   unitsDicomCode=self.createCodedEntry("ml", "UCUM", "Milliliter", True),
                                   measurementMethodDicomCode=self.createCodedEntry('126030','DCM','Sum of segmented voxel volumes', True))
                                                          
    info["1st_quartile"] = \
      self.createMeasurementInfo(name="1st quartile", title=_("1st quartile"), description="1st quartile uptake value",
                                   units=scalarVolumeUnits.GetCodeMeaning(),
                                   quantityDicomCode=scalarVolumeQuantity.GetAsString(),
                                   unitsDicomCode=scalarVolumeUnits.GetAsString(),
                                   derivationDicomCode=self.createCodedEntry("250137","99PMP","25th Percentile Value", True))
                                                                      
    info["median"] = \
      self.createMeasurementInfo(name="Median", title=_("Median"), description="Median uptake value",
                                   units=scalarVolumeUnits.GetCodeMeaning(),
                                   quantityDicomCode=scalarVolumeQuantity.GetAsString(),
                                   unitsDicomCode=scalarVolumeUnits.GetAsString(),
                                   derivationDicomCode=self.createCodedEntry("R-00319","SRT","Median", True))
                                   
    info["3rd_quartile"] = \
      self.createMeasurementInfo(name="3rd quartile", title=_("3rd quartile"), description="3rd quartile uptake value",
                                   units=scalarVolumeUnits.GetCodeMeaning(),
                                   quantityDicomCode=scalarVolumeQuantity.GetAsString(),
                                   unitsDicomCode=scalarVolumeUnits.GetAsString(),
                                   derivationDicomCode=self.createCodedEntry("250138","99PMP","75th Percentile Value", True))
                                   
    info["upper_adjacent"] = \
      self.createMeasurementInfo(name="Upper_adjacent", title=_("Upper_adjacent"), description="Upper adjacent", units="%",
                                   quantityDicomCode=self.createCodedEntry("250139","99PMP","Upper Adjacent Value", True),
                                   unitsDicomCode=self.createCodedEntry("%","UCUM","Percent", True))
                                   
    info["TLG"] = \
      self.createMeasurementInfo(name="TLG", title=_("TLG"), description="Total lesion glycolysis", units="g",
                                   quantityDicomCode=self.createCodedEntry("126033","DCM","Total Lesion Glycolysis", True),
                                   unitsDicomCode=self.createCodedEntry("g","UCUM","Gram", True))
                                   
    info["glycosis_Q1"] = \
      self.createMeasurementInfo(name="Glycolysis Q1", title=_("Glycolysis Q1"), description="Glycolysis within first quarter of intensity range", units="g",
                                   quantityDicomCode=self.createCodedEntry("250145","99PMP","Glycolysis Within First Quarter of Intensity Range", True),
                                   unitsDicomCode=self.createCodedEntry("g","UCUM","Gram", True))
                                   
    info["glycosis_Q2"] = \
      self.createMeasurementInfo(name="Glycolysis Q2", title=_("Glycolysis Q2"), description="Glycolysis within second quarter of intensity range", units="g",
                                   quantityDicomCode=self.createCodedEntry("250146","99PMP","Glycolysis Within Second Quarter of Intensity Range", True),
                                   unitsDicomCode=self.createCodedEntry("g","UCUM","Gram", True))
                                   
    info["glycosis_Q3"] = \
      self.createMeasurementInfo(name="Glycolysis Q3", title=_("Glycolysis Q3"), description="Glycolysis within third quarter of intensity range", units="g",
                                   quantityDicomCode=self.createCodedEntry("250147","99PMP","Glycolysis Within Third Quarter of Intensity Range", True),
                                   unitsDicomCode=self.createCodedEntry("g","UCUM","Gram", True))
                                   
    info["glycosis_Q4"] = \
      self.createMeasurementInfo(name="Glycolysis Q4", title=_("Glycolysis Q4"), description="Glycolysis within fourth quarter of intensity range", units="g",
                                   quantityDicomCode=self.createCodedEntry("250148","99PMP","Glycolysis Within Fourth Quarter of Intensity Range", True),
                                   unitsDicomCode=self.createCodedEntry("g","UCUM","Gram", True))
                                   
    info["Q1_distribution"] = \
      self.createMeasurementInfo(name="Q1 distribution", title=_("Q1 distribution"), description="Percent within first quarter of intensity range", units="%",
                                   quantityDicomCode=self.createCodedEntry("250140","99PMP","Percent Within First Quarter of Intensity Range", True),
                                   unitsDicomCode=self.createCodedEntry("%","UCUM","Percent", True))
                                   
    info["Q2_distribution"] = \
      self.createMeasurementInfo(name="Q2 distribution", title=_("Q2 distribution"), description="Percent within second quarter of intensity range", units="%",
                                   quantityDicomCode=self.createCodedEntry("250141","99PMP","Percent Within Second Quarter of Intensity Range", True),
                                   unitsDicomCode=self.createCodedEntry("%","UCUM","Percent", True))
                                   
    info["Q3_distribution"] = \
      self.createMeasurementInfo(name="Q3 distribution", title=_("Q3 distribution"), description="Percent within third quarter of intensity range", units="%",
                                   quantityDicomCode=self.createCodedEntry("250142","99PMP","Percent Within Third Quarter of Intensity Range", True),
                                   unitsDicomCode=self.createCodedEntry("%","UCUM","Percent", True))
                                   
    info["Q4_distribution"] = \
      self.createMeasurementInfo(name="Q4 distribution", title=_("Q4 distribution"), description="Percent within fourth quarter of intensity range", units="%",
                                   quantityDicomCode=self.createCodedEntry("250143","99PMP","Percent Within Fourth Quarter of Intensity Range", True),
                                   unitsDicomCode=self.createCodedEntry("%","UCUM","Percent", True))
                                   
    info["SAM"] = \
      self.createMeasurementInfo(name="SAM", title=_("SAM"), description="Standardized added metabolic activity", units='g',
                                   quantityDicomCode=self.createCodedEntry("126037","DCM","Standardized Added Metabolic Activity", True),
                                   unitsDicomCode=self.createCodedEntry("g","UCUM","Gram", True))
                                   
    info["SAM_BG"] = \
      self.createMeasurementInfo(name="SAM background", title=_("SAM background"), description="Standardized added metabolic activity background",
                                   units=scalarVolumeUnits.GetCodeMeaning(),
                                   quantityDicomCode=self.createCodedEntry("126038","DCM","Standardized Added Metabolic Activity Background", True),
                                   unitsDicomCode=scalarVolumeUnits.GetAsString())
                                   
    info["peak"] = \
      self.createMeasurementInfo(name="Peak", title=_("Peak"), description="Peak value within ROI",
                                   units=scalarVolumeUnits.GetCodeMeaning(),
                                   quantityDicomCode=scalarVolumeQuantity.GetAsString(),
                                   unitsDicomCode=scalarVolumeUnits.GetAsString(),
                                   derivationDicomCode=self.createCodedEntry("126031","DCM","Peak Value Within ROI", True))

    return info[key] if key in info else None
