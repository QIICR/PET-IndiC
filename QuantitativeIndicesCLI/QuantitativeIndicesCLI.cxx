#include "QuantitativeIndicesCLICLP.h"

#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkConstantPadImageFilter.h"
#include "itkResampleImageFilter.h"
#include <itkImageRegionConstIterator.h>
#include <iostream>

// make isnan available for older Visual Studio compilers
#if defined(_MSC_VER) && (_MSC_VER<1800)
#define isnan(x) _isnan(x)
#endif

// make isnan non-ambiguous for C++11
#if __cplusplus >= 201103L
#define isnan(x) std::isnan(x)
#endif

#include "itkQuantitativeIndicesComputationFilter.h"
#include "itkPluginUtilities.h"

//versioning info
#include "vtkQuantitativeIndicesExtVersionConfigure.h"

using namespace std;

int main( int argc, char * argv[] )
{
  PARSE_ARGS;
  typedef  float  PixelType;
	const unsigned int Dimension = 3;

  typedef itk::Image< PixelType, Dimension >   ImageType;
  typedef itk::Image< int, Dimension > LabelImageType;

	//image reader
  typedef itk::ImageFileReader< ImageType >  ReaderType;
  typedef itk::ImageFileReader< LabelImageType > LabelReaderType;
	ReaderType::Pointer ptImageReader = ReaderType::New();
	//itk::PluginFilterWatcher watchReader(ptImage, "Read Scalar Volume", CLPProcessInformation);
	//ptImage->ReleaseDataFlagOn();
  LabelReaderType::Pointer labelImageReader = LabelReaderType::New();
  //itk::PluginFilterWatcher watchLabelReader(labelImage, "Read Label Image", CLPProcessInformation);
  //labelImage->ReleaseDataFlagOn();

  ptImageReader->SetFileName( Grayscale_Image );
  labelImageReader->SetFileName( Label_Image );
  ptImageReader->Update();
  labelImageReader->Update();
  ImageType::Pointer ptImage = ptImageReader->GetOutput();
  LabelImageType::Pointer labelImage = labelImageReader->GetOutput();
  
  // check if image and label occupy about the same space
  bool sameSpace = true;
  ImageType::SpacingType ptSpacing = ptImage->GetSpacing();
  ImageType::PointType ptOrigin = ptImage->GetOrigin();
  ImageType::SizeType ptSize = ptImage->GetLargestPossibleRegion().GetSize();
  LabelImageType::SpacingType labelSpacing = labelImage->GetSpacing();
  LabelImageType::PointType labelOrigin = labelImage->GetOrigin();
  LabelImageType::SizeType labelSize = labelImage->GetLargestPossibleRegion().GetSize();
  for(unsigned int i=0; i<Dimension; ++i)
  {
    if(abs(ptSpacing[i]-labelSpacing[i]) > 1e-6) sameSpace = false;
    if(abs(ptOrigin[i]-labelOrigin[i]) > 1e-6) sameSpace = false;
    if(ptSize[i] != labelSize[i]) sameSpace = false;
  }
  
  //resample the image to the resolution of the labelmap after padding the labelmap
  typedef itk::ConstantPadImageFilter<LabelImageType, LabelImageType> PadderType;
  PadderType::Pointer padder = PadderType::New();
  typedef itk::ResampleImageFilter<ImageType, ImageType> ResamplerType;
  ResamplerType::Pointer resampler = ResamplerType::New();
  //itk::PluginFilterWatcher watchResampler(resampler, "Resample Image", CLPProcessInformation);
  if(!sameSpace)
  {
    ImageType::SizeType extend;
    extend.Fill(2); // for SAM calculation we need a 2 voxel boundary around the object
    padder->SetInput(labelImage);
    padder->SetPadLowerBound(extend);
    padder->SetPadUpperBound(extend);
    padder->SetConstant(0);
    padder->Update();
    labelImage = padder->GetOutput();
    //labelImage->DisconnectPipeline();
    // reset non-zero index
    LabelImageType::RegionType r = labelImage->GetLargestPossibleRegion();
    LabelImageType::IndexType idx = r.GetIndex();
    for( unsigned int i = 0; i < LabelImageType::ImageDimension; ++i )
    {
      if ( idx[i] != 0 )
      {
        // if any of the indcies are non-zero, then just fix it
        typename LabelImageType::PointType o;
        labelImage->TransformIndexToPhysicalPoint( idx, o );
        labelImage->SetOrigin( o );
        idx.Fill( 0 );
        r.SetIndex(idx);
        labelImage->SetRegions(r);
        break;       
      }
    }
      
    resampler->SetInput(ptImage);
    resampler->UseReferenceImageOn();
    resampler->SetReferenceImage(labelImage);
    resampler->UpdateLargestPossibleRegion();
    resampler->Update();
    ptImage = resampler->GetOutput();
  }
  typedef itk::QuantitativeIndicesComputationFilter<ImageType,LabelImageType> QIFilterType;

  if(!returnCSV){
    ofstream writeFile;
    writeFile.open( returnParameterFile.c_str() );
    if(!Mean){writeFile << "Mean_s = --" << endl;};
    //if(!Variance){writeFile << "Variance_s = --" << endl;};
    if(!Std_Deviation){writeFile << "Std_Deviation_s = --" << endl;};
    if(!RMS){writeFile << "RMS_s = --" << endl;};
    if(!Max){writeFile << "Max_s = --" << endl;};
    if(!Min){writeFile << "Min_s = --" << endl;};
    if(!Volume){writeFile << "Volume_s = --" << endl;};
    if(!First_Quartile){writeFile << "First_Quartile_s = --" << endl;};
    if(!Median){writeFile << "Median_s = --" << endl;};
    if(!Third_Quartile){writeFile << "Third_Quartile_s = --" << endl;};
    if(!Upper_Adjacent){writeFile << "Upper_Adjacent_s = --" << endl;};
    if(!TLG){writeFile << "TLG_s = --" << endl;};
    if(!Glycolysis_Q1){writeFile << "Glycolysis_Q1_s = --" << endl;};
    if(!Glycolysis_Q2){writeFile << "Glycolysis_Q2_s = --" << endl;};
    if(!Glycolysis_Q3){writeFile << "Glycolysis_Q3_s = --" << endl;};
    if(!Glycolysis_Q4){writeFile << "Glycolysis_Q4_s = --" << endl;};
    if(!Q1_Distribution){writeFile << "Q1_Distribution_s = --" << endl;};
    if(!Q2_Distribution){writeFile << "Q2_Distribution_s = --" << endl;};
    if(!Q3_Distribution){writeFile << "Q3_Distribution_s = --" << endl;};
    if(!Q4_Distribution){writeFile << "Q4_Distribution_s = --" << endl;};
    if(!SAM){writeFile << "SAM_s = --" << endl;};
    if(!SAM_Background){writeFile << "SAM_Background_s = --" << endl;};
    if(!Peak){writeFile << "Peak_s = --" << endl;};

    QIFilterType::Pointer qiCompute = QIFilterType::New();
    //itk::PluginFilterWatcher watchFilter(qiCompute, "Quantitative Indices Computation", CLPProcessInformation);
    qiCompute->SetInputImage(ptImage);
    qiCompute->SetInputLabelImage(labelImage);
    qiCompute->SetCurrentLabel( (int)Label_Value );
    //qiCompute->Update();

    if(Mean||RMS||Std_Deviation||Max||Min||Volume||TLG||Glycolysis_Q1||Glycolysis_Q2||Glycolysis_Q3||Glycolysis_Q4||Q1_Distribution||Q2_Distribution||Q3_Distribution||Q4_Distribution)
      {
        qiCompute->CalculateMean();
        if(Mean){
          double mean = qiCompute->GetAverageValue();
          if(!isnan(mean)){
            writeFile << "Mean_s = " << mean << endl;
            cout << "Mean: " << mean << endl;
          }
        }
        if(RMS){
          double rms = qiCompute->GetRMSValue();
          if(!isnan(rms)){
            writeFile << "RMS_s = " << rms << endl;
            cout << "RMS: " << rms << endl;
          }
        }
        /*if(Variance){
          double var = (double) qiCompute->GetVariance();
          if(!isnan(var)){
            writeFile << "Variance_s = " << var << endl;
            cout << "Variance: " << var << endl;
          }
        }*/
        if(Std_Deviation){
          double stddev = sqrt(qiCompute->GetVariance());
          if(!isnan(stddev)){
            writeFile << "Std_Deviation_s = " << stddev << endl;
            cout << "Std_Deviation: " << stddev << endl;
          }
        }
        if(Max){
          double max = qiCompute->GetMaximumValue();
          if(!isnan(max)){
            writeFile << "Max_s = " << max << endl;
            cout << "Max: " << max << endl;
          }
        }
        if(Min){
          double min = qiCompute->GetMinimumValue();
          if(!isnan(min)){
            writeFile << "Min_s = " << min << endl;
            cout << "Min: " << min << endl;
          }
        }
        if(Volume){
          double vol = qiCompute->GetSegmentedVolume();
          if(!isnan(vol)){
            writeFile << "Volume_s = " << 0.001*vol << endl;
            cout << "Volume: " << 0.001*vol << endl;
          }
        }
        if(TLG){
          double tlg = qiCompute->GetTotalLesionGlycolysis();
          if(!isnan(tlg)){
            writeFile << "TLG_s = " << 0.001*tlg << endl;
            cout << "TLG: " << 0.001*tlg << endl;
          }
        }
        if(Glycolysis_Q1){
          double gly1 = qiCompute->GetGly1();
          if(!isnan(gly1)){
            writeFile << "Glycolysis_Q1_s = " << 0.001*gly1 << endl;
            cout << "Glycolysis Q1: " << 0.001*gly1 << endl;
          }
        }
        if(Glycolysis_Q2){
          double gly2 = qiCompute->GetGly2();
          if(!isnan(gly2)){
            writeFile << "Glycolysis_Q2_s = " << 0.001*gly2 << endl;
            cout << "Glycolysis Q2: " << 0.001*gly2 << endl;
          }
        }
        if(Glycolysis_Q3){
          double gly3 = qiCompute->GetGly3();
          if(!isnan(gly3)){
            writeFile << "Glycolysis_Q3_s = " << 0.001*gly3 << endl;
            cout << "Glycolysis Q3: " << 0.001*gly3 << endl;
          }
        }
        if(Glycolysis_Q4){
          double gly4 = qiCompute->GetGly4();
          if(!isnan(gly4)){
            writeFile << "Glycolysis_Q4_s = " << 0.001*gly4 << endl;
            cout << "Glycolysis Q4: " << 0.001*gly4 << endl;
          }
        }
        if(Q1_Distribution){
          double q1 = qiCompute->GetQ1();
          if(!isnan(q1)){
            writeFile << "Q1_Distribution_s = " << 100*q1 << endl;
            cout << "Q1 Distribution: " << 100*q1 << endl;
          }
        }
        if(Q2_Distribution){
          double q2 = qiCompute->GetQ2();
          if(!isnan(q2)){
            writeFile << "Q2_Distribution_s = " << 100*q2 << endl;
            cout << "Q2 Distribution: " << 100*q2 << endl;
          }
        }
        if(Q3_Distribution){
          double q3 = qiCompute->GetQ3();
          if(!isnan(q3)){
            writeFile << "Q3_Distribution_s = " << 100*q3 << endl;
            cout << "Q3 Distribution: " << 100*q3 << endl;
          }
        }
        if(Q4_Distribution){
          double q4 = qiCompute->GetQ4();
          if(!isnan(q4)){
            writeFile << "Q4_Distribution_s = " << 100*q4 << endl;
            cout << "Q4 Distribution: " << 100*q4 << endl;
          }
        }
      }

    if(First_Quartile || Median || Third_Quartile || Upper_Adjacent)
      {
        qiCompute->CalculateQuartiles();
        if(First_Quartile){
          double quart1 = qiCompute->GetFirstQuartileValue();
          if(!isnan(quart1)){
            writeFile << "First_Quartile_s = " << quart1 << endl;
            cout << "1st Quartile: " << quart1 << endl;
          }
        }
        if(Median){
          double median = qiCompute->GetMedianValue();
          if(!isnan(median)){
            writeFile << "Median_s = " << median << endl;
            cout << "Median: " << median << endl;
          }
        }
        if(Third_Quartile){
          double quart3 = qiCompute->GetThirdQuartileValue();
          if(!isnan(quart3)){
            writeFile << "Third_Quartile_s = " << quart3 << endl;
            cout << "3rd Quartile: " << quart3 << endl;
          }
        }
        if(Upper_Adjacent){
          double adj = qiCompute->GetUpperAdjacentValue();
          if(!isnan(adj)){
            writeFile << "Upper_Adjacent_s = " << adj << endl;
            cout << "Upper Adjacent: " << adj << endl;
          }
        }
      }

    if(SAM||SAM_Background)
      {
        qiCompute->CalculateSAM();
        if(SAM){
          double sam = qiCompute->GetSAMValue();
          if(!isnan(sam)){
            writeFile << "SAM_s = " << 0.001*sam << endl;
            cout << "SAM: " << 0.001*sam << endl;
          }
        }
        if(SAM_Background){
          double sambg = qiCompute->GetSAMBackground();
          if(!isnan(sambg)){
            writeFile << "SAM_Background_s = " << sambg << endl;
            cout << "SAM mean background: " << sambg << endl;
          }
        }
      }

    if(Peak)
      {
        qiCompute->CalculatePeak();
        writeFile << "Peak_s = " << (double) qiCompute->GetPeakValue() << endl;
        cout << "Peak: " << (double) qiCompute->GetPeakValue() << endl;
      }
      
    writeFile << "Software_Version = " << QuantitativeIndicesExt_WC_REVISION << endl;

    writeFile.close();
  }
  else{ // create the csv file
    cout << "Writing to file " << CSVFile.c_str() << endl;
    
    ofstream writeFile; // needed always?
    writeFile.open( returnParameterFile.c_str() );
    writeFile << "Mean_s = --" << endl;
    //writeFile << "Variance_s = --" << endl;
    writeFile << "Std_Deviation_s = --" << endl;
    writeFile << "RMS_s = --" << endl;
    writeFile << "Max_s = --" << endl;
    writeFile << "Min_s = --" << endl;
    writeFile << "Volume_s = --" << endl;
    writeFile << "First_Quartile_s = --" << endl;
    writeFile << "Median_s = --" << endl;
    writeFile << "Third_Quartile_s = --" << endl;
    writeFile << "Upper_Adjacent_s = --" << endl;
    writeFile << "TLG_s = --" << endl;
    writeFile << "Glycolysis_Q1_s = --" << endl;
    writeFile << "Glycolysis_Q2_s = --" << endl;
    writeFile << "Glycolysis_Q3_s = --" << endl;
    writeFile << "Glycolysis_Q4_s = --" << endl;
    writeFile << "Q1_Distribution_s = --" << endl;
    writeFile << "Q2_Distribution_s = --" << endl;
    writeFile << "Q3_Distribution_s = --" << endl;
    writeFile << "Q4_Distribution_s = --" << endl;
    writeFile << "SAM_s = --" << endl;
    writeFile << "SAM_Background_s = --" << endl;
    writeFile << "Peak_s = --" << endl;
    writeFile.close();
    
    ofstream csvFile;
    csvFile.open( CSVFile.c_str() );
    
    // get the label values
    typedef itk::ImageRegionConstIterator<LabelImageType> IteratorType;
    IteratorType it(labelImage, labelImage->GetLargestPossibleRegion());
    it.GoToBegin();
    std::set<int> regionLabels;

    while(!it.IsAtEnd())
    {
      int labelValue = it.Get();
      if(labelValue > 0)
      {
        if(regionLabels.find(labelValue)==regionLabels.end())
        {
          regionLabels.insert(labelValue);
        }
      }
      ++it;
    }
    
    // create the column header
    csvFile << "Label_Value,";
    if(Mean){csvFile << "Mean,";};
    if(Min){csvFile << "Min,";};
    if(Max){csvFile << "Max,";};
    if(Peak){csvFile << "Peak,";};
    if(Volume){csvFile << "Volume,";};
    if(TLG){csvFile << "TLG,";};
    //if(Variance){csvFile << "Variance,";};
    if(Std_Deviation){csvFile << "Std_Deviation,";};
    if(First_Quartile){csvFile << "First_Quartile,";};
    if(Median){csvFile << "Median,";};
    if(Third_Quartile){csvFile << "Third_Quartile,";};
    if(Upper_Adjacent){csvFile << "Upper_Adjacent,";};
    if(RMS){csvFile << "RMS,";};
    if(Glycolysis_Q1){csvFile << "Glycolysis_Q1,";};
    if(Glycolysis_Q2){csvFile << "Glycolysis_Q2,";};
    if(Glycolysis_Q3){csvFile << "Glycolysis_Q3,";};
    if(Glycolysis_Q4){csvFile << "Glycolysis_Q4,";};
    if(Q1_Distribution){csvFile << "Q1_Distribution,";};
    if(Q2_Distribution){csvFile << "Q2_Distribution,";};
    if(Q3_Distribution){csvFile << "Q3_Distribution,";};
    if(Q4_Distribution){csvFile << "Q4_Distribution,";};
    if(SAM){csvFile << "SAM,";};
    if(SAM_Background){csvFile << "SAM_Background,";};
    
    
    
    // calculate indices for each non-zero label value
    for (std::set<int>::iterator sit=regionLabels.begin(); sit!=regionLabels.end(); ++sit)
    {
      csvFile << endl;
      int labelValue = *sit;
      csvFile << labelValue << ",";
      
      QIFilterType::Pointer qiCompute = QIFilterType::New();
      //itk::PluginFilterWatcher watchFilter(qiCompute, "Quantitative Indices Computation", CLPProcessInformation);
      qiCompute->SetInputImage(ptImage);
      qiCompute->SetInputLabelImage(labelImage);
      qiCompute->SetCurrentLabel( labelValue );
      qiCompute->Update();
      
      if(Mean||RMS||Std_Deviation||Max||Min||Volume||TLG||Glycolysis_Q1||Glycolysis_Q2||Glycolysis_Q3||Glycolysis_Q4||Q1_Distribution||Q2_Distribution||Q3_Distribution||Q4_Distribution)
      {
        qiCompute->CalculateMean();
      }
      if(First_Quartile || Median || Third_Quartile || Upper_Adjacent)
      {
        qiCompute->CalculateQuartiles();
      }
      if(SAM||SAM_Background)
      {
        qiCompute->CalculateSAM();
      }
      if(Peak)
      {
        qiCompute->CalculatePeak();
      }

      if(Mean){csvFile << qiCompute->GetAverageValue() << ",";};
      if(Min){csvFile << qiCompute->GetMinimumValue() << ",";};
      if(Max){csvFile << qiCompute->GetMaximumValue() << ",";};
      if(Peak){csvFile << qiCompute->GetPeakValue() << ",";};
      if(Volume){csvFile << 0.001*(qiCompute->GetSegmentedVolume()) << ",";};
      if(TLG){csvFile << 0.001*(qiCompute->GetTotalLesionGlycolysis()) << ",";};
      //if(Variance){csvFile << qiCompute->GetVariance() << ",";};
      if(Std_Deviation){csvFile << sqrt(qiCompute->GetVariance()) << ",";};
      if(First_Quartile){csvFile << qiCompute->GetFirstQuartileValue() << ",";};
      if(Median){csvFile << qiCompute->GetMedianValue() << ",";};
      if(Third_Quartile){csvFile << qiCompute->GetThirdQuartileValue() << ",";};
      if(Upper_Adjacent){csvFile << qiCompute->GetUpperAdjacentValue() << ",";};
      if(RMS){csvFile << qiCompute->GetRMSValue() << ",";}; 
      if(Glycolysis_Q1){csvFile << 0.001*(qiCompute->GetGly1()) << ",";};
      if(Glycolysis_Q2){csvFile << 0.001*(qiCompute->GetGly2()) << ",";};
      if(Glycolysis_Q3){csvFile << 0.001*(qiCompute->GetGly3()) << ",";};
      if(Glycolysis_Q4){csvFile << 0.001*(qiCompute->GetGly4()) << ",";};
      if(Q1_Distribution){csvFile << 100*(qiCompute->GetQ1()) << ",";};
      if(Q2_Distribution){csvFile << 100*(qiCompute->GetQ2()) << ",";};
      if(Q3_Distribution){csvFile << 100*(qiCompute->GetQ3()) << ",";};
      if(Q4_Distribution){csvFile << 100*(qiCompute->GetQ4()) << ",";};
      if(SAM){csvFile << 0.001*(qiCompute->GetSAMValue()) << ",";};
      if(SAM_Background){csvFile << qiCompute->GetSAMBackground() << ",";};
      
    }
    csvFile.close();
  }
  
  return EXIT_SUCCESS;
}
