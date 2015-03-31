#include "QuantitativeIndicesCLICLP.h"

#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkResampleImageFilter.h"
#include <iostream>
#include <math.h>

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
	ReaderType::Pointer ptImage = ReaderType::New();
	itk::PluginFilterWatcher watchReader(ptImage, "Read Scalar Volume", CLPProcessInformation);
  LabelReaderType::Pointer labelImage = LabelReaderType::New();
  itk::PluginFilterWatcher watchLabelReader(labelImage, "Read Label Image", CLPProcessInformation);

  ptImage->SetFileName( Grayscale_Image );
  labelImage->SetFileName( Label_Image );
  ptImage->Update();
  labelImage->Update();
  
  //resample the image to the resolution of the label
  typedef itk::ResampleImageFilter<ImageType, ImageType> ResamplerType;
  ResamplerType::Pointer resampler = ResamplerType::New();
  itk::PluginFilterWatcher watchResampler(resampler, "Resample Image", CLPProcessInformation);
  resampler->SetInput(ptImage->GetOutput());
  resampler->UseReferenceImageOn();
  resampler->SetReferenceImage(labelImage->GetOutput());
  resampler->UpdateLargestPossibleRegion();

  ofstream writeFile;
  writeFile.open( returnParameterFile.c_str() );
  if(!Mean){writeFile << "Mean_s = --" << endl;};
  if(!Variance){writeFile << "Variance_s = --" << endl;};
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

  typedef itk::QuantitativeIndicesComputationFilter<ImageType,LabelImageType> QIFilterType;
  QIFilterType::Pointer qiCompute = QIFilterType::New();
  itk::PluginFilterWatcher watchFilter(qiCompute, "Quantitative Indices Computation", CLPProcessInformation);
  //qiCompute->SetInputImage(ptImage->GetOutput());
  qiCompute->SetInputImage(resampler->GetOutput());
  qiCompute->SetInputLabelImage(labelImage->GetOutput());
  qiCompute->SetCurrentLabel( (int)Label_Value );
  qiCompute->Update();


  if(Mean||RMS||Variance||Max||Min||Volume||TLG||Glycolysis_Q1||Glycolysis_Q2||Glycolysis_Q3||Glycolysis_Q4||Q1_Distribution||Q2_Distribution||Q3_Distribution||Q4_Distribution)
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
      if(Variance){
        double var = (double) qiCompute->GetVariance();
        if(!isnan(var)){
          writeFile << "Variance_s = " << var << endl;
          cout << "Variance: " << var << endl;
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
          writeFile << "Volume_s = " << vol * 0.001 << endl;
          cout << "Volume: " << vol * 0.001 << endl;
        }
      }
      if(TLG){
        double tlg = qiCompute->GetTotalLesionGlycolysis();
        if(!isnan(tlg)){
          writeFile << "TLG_s = " << tlg * 0.001 << endl;
          cout << "TLG: " << tlg * 0.001 << endl;
        }
      }
      if(Glycolysis_Q1){
        double gly1 = qiCompute->GetGly1();
        if(!isnan(gly1)){
          writeFile << "Glycolysis_Q1_s = " << gly1 * 0.001 << endl;
          cout << "Glycolysis Q1: " << gly1 * 0.001 << endl;
        }
      }
      if(Glycolysis_Q2){
        double gly2 = qiCompute->GetGly2();
        if(!isnan(gly2)){
          writeFile << "Glycolysis_Q2_s = " << gly2 * 0.001 << endl;
          cout << "Glycolysis Q2: " << gly2 * 0.001 << endl;
        }
      }
      if(Glycolysis_Q3){
        double gly3 = qiCompute->GetGly3();
        if(!isnan(gly3)){
          writeFile << "Glycolysis_Q3_s = " << gly3 * 0.001 << endl;
          cout << "Glycolysis Q3: " << gly3 * 0.001 << endl;
        }
      }
      if(Glycolysis_Q4){
        double gly4 = qiCompute->GetGly4();
        if(!isnan(gly4)){
          writeFile << "Glycolysis_Q4_s = " << gly4 * 0.001 << endl;
          cout << "Glycolysis Q4: " << gly4 * 0.001 << endl;
        }
      }
      if(Q1_Distribution){
        double q1 = qiCompute->GetQ1();
        if(!isnan(q1)){
          writeFile << "Q1_Distribution_s = " << q1 * 100 << endl;
          cout << "Q1 Distribution: " << q1 << endl;
        }
      }
      if(Q2_Distribution){
        double q2 = qiCompute->GetQ2();
        if(!isnan(q2)){
          writeFile << "Q2_Distribution_s = " << q2 * 100 << endl;
          cout << "Q2 Distribution: " << q2 << endl;
        }
      }
      if(Q3_Distribution){
        double q3 = qiCompute->GetQ3();
        if(!isnan(q3)){
          writeFile << "Q3_Distribution_s = " << q3 * 100 << endl;
          cout << "Q3 Distribution: " << q3 << endl;
        }
      }
      if(Q4_Distribution){
        double q4 = qiCompute->GetQ4();
        if(!isnan(q4)){
          writeFile << "Q4_Distribution_s = " << q4 * 100 << endl;
          cout << "Q4 Distribution: " << q4 << endl;
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
          writeFile << "SAM_s = " << sam * 0.001 << endl;
          cout << "SAM: " << sam * 0.001 << endl;
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

  return EXIT_SUCCESS;
}
