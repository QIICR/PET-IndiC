import os
import unittest
import vtk, qt, ctk, slicer, logging
from DICOMLib import DICOMUtils
from SegmentStatistics import SegmentStatisticsLogic
import vtkSegmentationCorePython as vtkSegmentationCore
from slicer.ScriptedLoadableModule import *

#
# PETVolumeSegmentStatisticsPluginSelfTest
#

class PETVolumeSegmentStatisticsPluginSelfTest(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "PETVolumeSegmentStatisticsPluginSelfTest"
    self.parent.categories = ["Testing.TestCases"]
    self.parent.dependencies = ["SegmentStatistics"]
    self.parent.contributors = ["Christian Bauer (University of Iowa)"]
    self.parent.helpText = """This is a self test for PETVolumeSegmentStatisticsPlugin."""
    parent.acknowledgementText = """This work was partially funded by NIH grants U01-CA140206 and U24-CA180918."""

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['PETVolumeSegmentStatisticsPluginSelfTest'] = self.runTest

  def runTest(self):
    tester = PETVolumeSegmentStatisticsPluginSelfTestTest()
    tester.runTest()

#
# PETVolumeSegmentStatisticsPluginSelfTestWidget
#

class PETVolumeSegmentStatisticsPluginSelfTestWidget(ScriptedLoadableModuleWidget):
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

#
# PETVolumeSegmentStatisticsPluginSelfTestLogic
#

class PETVolumeSegmentStatisticsPluginSelfTestLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    pass


class PETVolumeSegmentStatisticsPluginSelfTestTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_Plugin()
    self.tearDown()

  def setUp(self):
    """ Open temporary DICOM database
    """
    slicer.mrmlScene.Clear(0)
    self.delayMs = 700
    self.tempDataDir = os.path.join(slicer.app.temporaryPath,'PETTest')
    self.tempDicomDatabaseDir = os.path.join(slicer.app.temporaryPath,'PETTestDicom')

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
      self.delayDisplay('Test caused exception!\n' + str(e),self.delayMs*2)

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

  def test_Plugin(self):
    """ produce measurements using PETVolumeSegmentStaticsPlugin and verify results
    """
    try:
      self.assertIsNotNone( slicer.modules.quantitativeindicescli )
      with DICOMUtils.TemporaryDICOMDatabase(self.tempDicomDatabaseDir) as db:
        self.assertTrue(db.isOpen)
        self.assertEqual(slicer.dicomDatabase, db)
        
        self.delayDisplay('Checking for PET statistics plugin and configuring')
        segStatLogic = SegmentStatisticsLogic()
        params = segStatLogic.getParameterNode()
        parameterNames = params.GetParameterNamesAsCommaSeparatedList().split(',')
        self.assertIn('PETVolumeSegmentStatisticsPlugin.enabled',parameterNames)
        for p in parameterNames:
          isPETParam = p.find('PETVolumeSegmentStatisticsPlugin.')==0
          if p.find('.enabled')>0:
            params.SetParameter(p,str(True if isPETParam  else False))
    
        self.delayDisplay('Loading PET DICOM dataset (including download if necessary)')
        petNode = self.loadTestData()
        #petNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLScalarVolumeNode')
    
        self.delayDisplay('Creating segmentations')
        segmentationNode = slicer.vtkMRMLSegmentationNode()
        slicer.mrmlScene.AddNode(segmentationNode)
        segmentationNode.CreateDefaultDisplayNodes()
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(petNode)
    
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

        self.delayDisplay('Calculating measurements')
        segStatLogic.getParameterNode().SetParameter("Segmentation", segmentationNode.GetID())
        segStatLogic.getParameterNode().SetParameter("ScalarVolume", petNode.GetID())
        segStatLogic.computeStatistics()
        stats = segStatLogic.getStatistics()
        resultsTableNode = slicer.vtkMRMLTableNode()
        slicer.mrmlScene.AddNode(resultsTableNode)
        segStatLogic.exportToTable(resultsTableNode)
        segStatLogic.showTable(resultsTableNode)

        self.delayDisplay('Veriyfing results')

        self.assertTrue(len(stats["MeasurementInfo"])>=22)

        # verify completenss of meta-information using measurement 'peak'
        self.assertIn("PETVolumeSegmentStatisticsPlugin.peak", stats["MeasurementInfo"])
        mInfo = stats["MeasurementInfo"]["PETVolumeSegmentStatisticsPlugin.peak"]
        self.assertIn('name', mInfo)
        self.assertTrue(mInfo['name']=='Peak')
        self.assertIn('units', mInfo)
        self.assertTrue(mInfo['units']=='Standardized Uptake Value body weight')
        self.assertIn('DICOM.QuantityCode', mInfo)
        self.assertTrue(mInfo['DICOM.QuantityCode']=='CodeValue:126400|CodingSchemeDesignator:DCM|CodeMeaning:Standardized Uptake Value')
        self.assertIn('DICOM.UnitsCode', mInfo)
        self.assertTrue(mInfo['DICOM.UnitsCode']=='CodeValue:{SUVbw}g/ml|CodingSchemeDesignator:UCUM|CodeMeaning:Standardized Uptake Value body weight')
        self.assertIn('DICOM.DerivationCode', mInfo)
        self.assertTrue(mInfo['DICOM.DerivationCode']=='CodeValue:126031|CodingSchemeDesignator:DCM|CodeMeaning:Peak Value Within ROI')

        # verify measurements
        self.assertTrue( abs(stats["Test","PETVolumeSegmentStatisticsPlugin.mean"]-3.67861)<0.0001 )
        self.assertTrue( abs(stats["Test_1","PETVolumeSegmentStatisticsPlugin.std"]-3.81429)<0.0001 )
        self.assertTrue( abs(stats["Test_2","PETVolumeSegmentStatisticsPlugin.min"]-0.91049)<0.0001 )
        self.assertTrue( abs(stats["Test","PETVolumeSegmentStatisticsPlugin.max"]-19.5262)<0.0001 )
        self.assertTrue( abs(stats["Test_1","PETVolumeSegmentStatisticsPlugin.rms"]-5.174)<0.0001 )
        self.assertTrue( abs(stats["Test_2","PETVolumeSegmentStatisticsPlugin.volume"]-447.783)<0.0001 )
        self.assertTrue( abs(stats["Test","PETVolumeSegmentStatisticsPlugin.1st_quartile"]-1.22039)<0.0001 )
        self.assertTrue( abs(stats["Test_1","PETVolumeSegmentStatisticsPlugin.median"]-1.91971)<0.0001 )
        self.assertTrue( abs(stats["Test_2","PETVolumeSegmentStatisticsPlugin.3rd_quartile"]-2.55595)<0.0001 )
        self.assertTrue( abs(stats["Test","PETVolumeSegmentStatisticsPlugin.upper_adjacent"]-9.13507)<0.0001 )
        self.assertTrue( abs(stats["Test_1","PETVolumeSegmentStatisticsPlugin.TLG"]-337.106)<0.0001 )
        self.assertTrue( abs(stats["Test_2","PETVolumeSegmentStatisticsPlugin.glycosis_Q1"]-60.0397)<0.0001 )
        self.assertTrue( abs(stats["Test","PETVolumeSegmentStatisticsPlugin.glycosis_Q2"]-82.9484)<0.0001 )
        self.assertTrue( abs(stats["Test_1","PETVolumeSegmentStatisticsPlugin.glycosis_Q3"]-57.3372)<0.0001 )
        self.assertTrue( abs(stats["Test_2","PETVolumeSegmentStatisticsPlugin.glycosis_Q4"]-10.4696)<0.0001 )
        self.assertTrue( abs(stats["Test","PETVolumeSegmentStatisticsPlugin.Q1_distribution"]-78.7157)<0.0001 )
        self.assertTrue( abs(stats["Test_1","PETVolumeSegmentStatisticsPlugin.Q2_distribution"]-9.45815)<0.0001 )
        self.assertTrue( abs(stats["Test_2","PETVolumeSegmentStatisticsPlugin.Q3_distribution"]-20.9304)<0.0001 )
        self.assertTrue( abs(stats["Test","PETVolumeSegmentStatisticsPlugin.Q4_distribution"]-3.48725)<0.0001 )
        self.assertTrue( abs(stats["Test_1","PETVolumeSegmentStatisticsPlugin.SAM"]-206.139)<0.0001 )
        self.assertTrue( abs(stats["Test_2","PETVolumeSegmentStatisticsPlugin.SAM_BG"]-2.121)<0.0001 )
        self.assertTrue( abs(stats["Test","PETVolumeSegmentStatisticsPlugin.peak"]-17.335)<0.0001 )

        self.delayDisplay('Test passed!')

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e),self.delayMs*2)

  def _verifyResults(self, table, referenceMeasurements={}):
    self.assertTrue(table.columnCount==3)
    self.assertTrue(table.horizontalHeaderItem(0).text()=='Index')
    self.assertTrue(table.horizontalHeaderItem(1).text()=='Value')
    self.assertTrue(table.horizontalHeaderItem(2).text()=='Units')
    matchedMeasurements = set()
    for i in range(table.rowCount):
      index = table.item(i,0).text()
      value = table.item(i,1).text()
      units = table.item(i,2).text()
      if index in referenceMeasurements:
        matchedMeasurements.add(index)
        self.assertTrue(abs(float(value)-referenceMeasurements[index][0])<0.01) # account for potential rounding differences
        self.assertTrue(units==referenceMeasurements[index][1])
    self.assertTrue(len(matchedMeasurements)==len(referenceMeasurements))
