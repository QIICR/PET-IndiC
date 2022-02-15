#ifndef _itkQuantitativeIndicesComputationFilter_cxx
#define _itkQuantitativeIndicesComputationFilter_cxx

#include "itkQuantitativeIndicesComputationFilter.h"

#include "itkImageRegionConstIterator.h"
#include "itkImageRegionConstIteratorWithIndex.h"

#include <itkResampleImageFilter.h>
#include <itkConstShapedNeighborhoodIterator.h>
#include <itkNearestNeighborInterpolateImageFunction.h>
#include <itkRegionOfInterestImageFilter.h>
#include "itkDilateObjectMorphologyImageFilter.h"
#include "itkBinaryBallStructuringElement.h"
#include "itkPeakIntensityFilter.h"

#define QI_PEAK_RADIUS 6.204//2.5
#define QI_PEAK_RADIUS_SPACING_RATE 4.0

#define INITIAL_MARGIN 3


namespace itk
{

//----------------------------------------------------------------------------
template <class TImage, class TLabelImage>
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::QuantitativeIndicesComputationFilter()
{
  this->ProcessObject::SetNumberOfRequiredInputs(2);
  this->ProcessObject::SetNumberOfRequiredOutputs(0);
}

//----------------------------------------------------------------------------
/*
SetInputImage
Sets the input volume, expected to be PET data.

*/
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::SetInputImage( const ImageType* input )
{
// Process object is not const-correct so the const_cast is required here
  this->ProcessObject::SetNthInput(0, const_cast< ImageType * >(input));
}

//----------------------------------------------------------------------------
/*
GetInputImage
Returns the input image volume.

*/
template <class TImage, class TLabelImage>
typename QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::ImageConstPointer
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::GetInputImage() const
{
  if ( this->GetNumberOfInputs() < 1 )
  { return nullptr;  }
  else
  {
    return ImageConstPointer(static_cast< const ImageType* >( this->ProcessObject::GetInput(0) ));
  }
}


//----------------------------------------------------------------------------
/*
SetInputLabelImage
Sets the label volume for the iput volume.

*/
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::SetInputLabelImage( const LabelImageType* input )
{
// Process object is not const-correct so the const_cast is required here
  this->ProcessObject::SetNthInput(1, const_cast< LabelImageType * >(input));
}

//----------------------------------------------------------------------------
/*
GetInputLabelImage
Returns the label image volume.

*/
template <class TImage, class TLabelImage>
typename QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::LabelImageConstPointer
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::GetInputLabelImage() const
{
  if ( this->GetNumberOfInputs() < 2 )
  { return nullptr;  }
  else
  {
    return LabelImageConstPointer(static_cast< const LabelImageType* >( this->ProcessObject::GetInput(1) ));
  }
}

//----------------------------------------------------------------------------
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::GenerateData()
{
//std::cout << "GenerateData()\n";
  this->CalculateMean();
  this->CalculateQuartiles();
  this->CalculateSAM();
  this->CalculatePeak();
}

//----------------------------------------------------------------------------
/*
CreateSegmentedValueList

*/
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::CreateSegmentedValueList()
{
  typedef itk::ImageRegionConstIterator<ImageType>  InputIteratorType;
  typedef itk::ImageRegionConstIterator<LabelImageType>  LabelIteratorType;

  ImageConstPointer inputImage = this->GetInputImage();
  LabelImageConstPointer inputLabel = this->GetInputLabelImage();
  
  double d_maximumValue = itk::NumericTraits<double>::min();
  double d_minimumValue = itk::NumericTraits<double>::max();

  //Iterate through the image and label.  Determine values where the label is correct in the process.
  LabelIteratorType laIt(inputLabel, inputLabel->GetLargestPossibleRegion());
  laIt.GoToBegin();
  InputIteratorType inIt(inputImage, inputImage->GetLargestPossibleRegion());
  inIt.GoToBegin();

  while (!laIt.IsAtEnd() && !inIt.IsAtEnd())
  {
    if (laIt.Get() == m_CurrentLabel)
    {
      double curValue = (double) inIt.Get();
      m_SegmentedValues.push_back(curValue);
      if (curValue > d_maximumValue)  {d_maximumValue = curValue;}
      if (curValue < d_minimumValue)  {d_minimumValue = curValue;}
    }
    ++inIt;
    ++laIt;
  }

  m_ListGenerated = true;
  if(m_SegmentedValues.size()==0)
  {
    m_MinimumValue = std::numeric_limits<double>::quiet_NaN();
    m_MaximumValue = std::numeric_limits<double>::quiet_NaN();
  }
  else{
    m_MinimumValue = d_minimumValue;
    m_MaximumValue = d_maximumValue;
  }
}

//----------------------------------------------------------------------------
/*
CalculateMean
Actually runs the calculations to determine:
Minimum, Maximum, Average, RMS, Variance,
Segmented Volume, and Lesion Glycolysis.

*/
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::CalculateMean()
{
//std::cout << "CalculateMean()\n";
  //Declare the variables to determine
  double d_averageValue = 0.0;
  double d_rmsValue = 0.0;
  double d_variance = 0.0;
  double d_segmentedVolume = 0.0;
  double d_totalLesionGly = 0.0;
  double d_gly1 = 0.0;
  double d_gly2 = 0.0;
  double d_gly3 = 0.0;
  double d_gly4 = 0.0;
  double d_q1 = 0.0;
  double d_q2 = 0.0;
  double d_q3 = 0.0;
  double d_q4 = 0.0;

  double binSize = 0.0;
  double sum1 = 0.0;
  double sum2 = 0.0;
  double sum3 = 0.0;
  double sum4 = 0.0;

  ImageConstPointer inputImage = this->GetInputImage();
  typename ImageType::SpacingType spacing = inputImage->GetSpacing();

  //Need to store all segmented values for some computations
  if(!m_ListGenerated)
  {
    this->CreateSegmentedValueList();
  }
  if(m_SegmentedValues.size()==0)
  {
    m_AverageValue = std::numeric_limits<double>::quiet_NaN();
    m_RMSValue = std::numeric_limits<double>::quiet_NaN();
    m_SegmentedVolume = std::numeric_limits<double>::quiet_NaN();
    m_TotalLesionGlycolysis = std::numeric_limits<double>::quiet_NaN();
    m_Variance = std::numeric_limits<double>::quiet_NaN();
    m_Gly1 = std::numeric_limits<double>::quiet_NaN();
    m_Gly2 = std::numeric_limits<double>::quiet_NaN();
    m_Gly3 = std::numeric_limits<double>::quiet_NaN();
    m_Gly4 = std::numeric_limits<double>::quiet_NaN();
    m_Q1 = std::numeric_limits<double>::quiet_NaN();
    m_Q2 = std::numeric_limits<double>::quiet_NaN();
    m_Q3 = std::numeric_limits<double>::quiet_NaN();
    m_Q4 = std::numeric_limits<double>::quiet_NaN();
    return;
  }

  std::vector<double>::const_iterator listIt = m_SegmentedValues.begin();
  while (listIt != m_SegmentedValues.end())
  {
    double curValue = *listIt;
    d_segmentedVolume += 1;
    d_rmsValue += curValue*curValue;
    listIt++;
  }
  //Find the distribution within the range
  binSize = (m_MaximumValue-m_MinimumValue)*0.25;
  listIt = m_SegmentedValues.begin();
  while (listIt != m_SegmentedValues.end())
  {
    double curValue = *listIt;
    if(curValue >= m_MinimumValue && curValue <= (m_MinimumValue + binSize)){d_q1++; sum1+=curValue;};
    if(curValue > (m_MinimumValue+binSize) && curValue <= (m_MinimumValue+2*binSize)){d_q2++; sum2+=curValue;};
    if(curValue > (m_MinimumValue+2*binSize) && curValue <= (m_MinimumValue+3*binSize)){d_q3++; sum3+=curValue;};
    if(curValue > (m_MinimumValue+3*binSize) && curValue <= (m_MinimumValue+4*binSize)){d_q4++; sum4+=curValue;}; 
    listIt++;
  }

  double voxelCount = d_segmentedVolume;
  double voxelVolume = (spacing[0] * spacing[1] * spacing[2]);
  d_averageValue = (sum1+sum2+sum3+sum4) / voxelCount;
  d_rmsValue = std::sqrt(d_rmsValue / voxelCount);
  d_segmentedVolume *= voxelVolume;
  //d_totalLesionGly = (sum1+sum2+sum3+sum4)*voxelVolume;
  d_gly1 = sum1*voxelVolume;
  d_gly2 = sum2*voxelVolume;
  d_gly3 = sum3*voxelVolume;
  d_gly4 = sum4*voxelVolume;
  d_totalLesionGly = d_gly1 + d_gly2 + d_gly3 + d_gly4;
  d_q1 = d_q1/voxelCount;
  d_q2 = d_q2/voxelCount;
  d_q3 = d_q3/voxelCount;
  d_q4 = d_q4/voxelCount;

	listIt = m_SegmentedValues.begin();
	while (listIt != m_SegmentedValues.end())
	{
		d_variance += ((*listIt)-d_averageValue) * ((*listIt)-d_averageValue);
		listIt++;
	}

  d_variance /= (voxelCount);

  //Set the class variables to the values we've determined.
  m_AverageValue = d_averageValue;
  m_RMSValue = d_rmsValue;
  m_SegmentedVolume = d_segmentedVolume;
  m_TotalLesionGlycolysis = d_totalLesionGly;
  m_Variance = d_variance;
  m_Gly1 = d_gly1;
  m_Gly2 = d_gly2;
  m_Gly3 = d_gly3;
  m_Gly4 = d_gly4;
  m_Q1 = d_q1;
  m_Q2 = d_q2;
  m_Q3 = d_q3;
  m_Q4 = d_q4;

}

//----------------------------------------------------------------------------
/*
CalculateQuartiles
Actually runs the calculations to determine:
First Quartile, Median, Third Quartile, Upper adjacent

*/
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::CalculateQuartiles()
{
//std::cout << "CalculateQuartiles()\n";
  //Declare the variables to determine
  double d_medianValue = 0.0;
  double d_firstQuartileValue = 0.0;
  double d_thirdQuartileValue = 0.0;
  double d_upperAdjacentValue = 0.0;

  //Need to store all segmented values for some computations
  if(!m_ListGenerated)  // list is already generated
  {
    this->CreateSegmentedValueList();
  }
  if(m_SegmentedValues.size()==0)
  {
    m_MedianValue = std::numeric_limits<double>::quiet_NaN();
    m_FirstQuartileValue = std::numeric_limits<double>::quiet_NaN();
    m_ThirdQuartileValue = std::numeric_limits<double>::quiet_NaN();
    m_UpperAdjacentValue = std::numeric_limits<double>::quiet_NaN();
    return;
  }

  //Sort the values
  sort(m_SegmentedValues.begin(), m_SegmentedValues.end());
  int segmentedValuesSize = m_SegmentedValues.size();
	std::vector<double>::const_iterator listIt = m_SegmentedValues.begin();
  //Determine quartiles
	if(segmentedValuesSize % 2 == 0)
	{
	  d_medianValue = (m_SegmentedValues[segmentedValuesSize/2-1] + m_SegmentedValues[segmentedValuesSize/2])*0.5;
	}
	else{
	  d_medianValue = m_SegmentedValues[segmentedValuesSize/2];
	}
	if(segmentedValuesSize % 4 == 0)
	{
	  d_firstQuartileValue = (m_SegmentedValues[segmentedValuesSize/4-1] + m_SegmentedValues[segmentedValuesSize/4])*0.5;
	  d_thirdQuartileValue = (m_SegmentedValues[segmentedValuesSize*0.75-1] + m_SegmentedValues[segmentedValuesSize*0.75])*0.5;
	}
	else{
	  d_firstQuartileValue = m_SegmentedValues[segmentedValuesSize/4];
	  d_thirdQuartileValue = m_SegmentedValues[segmentedValuesSize*3/4];
	}

  // Find upper adjacent value
  double IQR = d_thirdQuartileValue - d_firstQuartileValue;
  double d_maximumValue = m_SegmentedValues[segmentedValuesSize-1];
  listIt = m_SegmentedValues.begin();
  if(IQR!=0){
    while(listIt != m_SegmentedValues.end()){
      if(*listIt < (d_thirdQuartileValue+1.5*IQR)){ d_upperAdjacentValue = *listIt; };
      listIt++;
    }
  }
  else{ d_upperAdjacentValue = d_maximumValue; }

  //Set the class variables to the values we've determined.
  m_MedianValue = d_medianValue;
  m_FirstQuartileValue = d_firstQuartileValue;
  m_ThirdQuartileValue = d_thirdQuartileValue;
  m_UpperAdjacentValue = d_upperAdjacentValue;
}


//----------------------------------------------------------------------------
/*
CalculateSAM
Actually runs the calculations to determine:
Standardized added metabolic activity

*/
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::CalculateSAM()
{
//std::cout << "CalculateSAM()\n";
  //Declare the variables to determine
  double d_SAM = 0.0;
  double d_SAMBackground = 0.0;
  double d_averageValue = 0.0;
  double d_segmentedVolume = 0.0;

  typedef itk::ImageRegionConstIterator<ImageType>  InputIteratorType;
  typedef itk::ImageRegionConstIterator<LabelImageType>  LabelIteratorType;

  ImageConstPointer inputImage = this->GetInputImage();
  LabelImageConstPointer inputLabel = this->GetInputLabelImage();

  typename ImageType::SpacingType spacing = inputImage->GetSpacing();
  double voxelSize = spacing[0] * spacing[1] * spacing[2];

  InputIteratorType inIt(inputImage, inputImage->GetLargestPossibleRegion());
  inIt.GoToBegin();

  if(!m_ListGenerated)
  {
    this->CreateSegmentedValueList();
  }
  if(m_SegmentedValues.size()==0)
  {
    m_SAMValue = std::numeric_limits<double>::quiet_NaN();
    m_SAMBackground = std::numeric_limits<double>::quiet_NaN();
    return;
  }
  std::vector<double>::const_iterator listIt = m_SegmentedValues.begin();
  while (listIt != m_SegmentedValues.end())
  {
    double curValue = *listIt;
    d_averageValue += curValue;
    d_segmentedVolume += 1;
    listIt++;
  }

  d_averageValue /= d_segmentedVolume;

  //Dilate region and collect new values
  std::list<double> dilatedRegionValues;
  typedef itk::BinaryBallStructuringElement<LabelType,3> KernelType;
  KernelType ballElement;
  typename KernelType::SizeValueType radius = 2;
  ballElement.SetRadius(radius);
  ballElement.CreateStructuringElement();
  typedef itk::DilateObjectMorphologyImageFilter<LabelImageType,LabelImageType,KernelType> DilaterType;
  typename DilaterType::Pointer dilater = DilaterType::New();
  dilater->SetObjectValue(m_CurrentLabel);
  dilater->SetKernel(ballElement);
  dilater->SetInput(inputLabel);
  try{
      dilater->Update();
    }
  catch(itk::ExceptionObject & e){
      std::cerr << "Exception caught updating dilater!" << std::endl << e << std::endl;          
    }
  LabelIteratorType dilateIt(dilater->GetOutput(), inputLabel->GetLargestPossibleRegion());
  for( dilateIt.GoToBegin(), inIt.GoToBegin(); !inIt.IsAtEnd(); ++inIt, ++dilateIt)
    {
      if(dilateIt.Get() == m_CurrentLabel)
        {
          dilatedRegionValues.push_back((double) inIt.Get());
        }
    }

  double dilatedSize = (double) dilatedRegionValues.size();
	std::list<double>::iterator dlistIt = dilatedRegionValues.begin();
  while(dlistIt != dilatedRegionValues.end())
    {
      d_SAM += *dlistIt;
      dlistIt++;
    }
  d_SAM = d_SAM / dilatedSize;
  d_SAMBackground = (d_SAM*dilatedSize-d_averageValue*d_segmentedVolume)/(dilatedSize-d_segmentedVolume);
  d_SAM = (d_averageValue-d_SAMBackground)*d_segmentedVolume*voxelSize;

  //Set the class variables to the values we've determined.
  m_SAMValue = d_SAM;
  m_SAMBackground = d_SAMBackground;
  
  //std::cout << inputLabel << std::endl;
  //std::cout << "dilatedRegionValues.size()="<<dilatedRegionValues.size() << std::endl;

}


//----------------------------------------------------------------------------
/*
CalculatePeak
Actually runs the calculations to determine:
Peak, Peak Location

*/
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::CalculatePeak()
{
//std::cout << "CalculatePeak()\n";
  typedef typename itk::PeakIntensityFilter<ImageType,LabelImageType> PeakFilterType;
  typename PeakFilterType::Pointer peakFilter = PeakFilterType::New();
  peakFilter->SetInputImage( this->GetInputImage() );
  peakFilter->SetInputLabelImage( this->GetInputLabelImage() );
  peakFilter->SetCurrentLabel( m_CurrentLabel );
  peakFilter->SetSphereVolume( 1000 ); 
  //peakFilter->SetSamplingFactor( 20 ); //TODO remove after adding exact weights to itkPeakIntensityFilter
  //peakFilter->SetUseApproximateKernel(true); //TODO remove after adding exact weights to itkPeakIntensityFilter
  //peakFilter->SetUseInteriorOnly( false );
  peakFilter->CalculatePeak();
   
  m_PeakValue = peakFilter->GetPeakValue();
  m_PeakLocation = peakFilter->GetPeakLocation();
  //std::cout << "Peak Location: " << m_PeakLocation << std::endl;
  //std::cout << "Peak Index: " << peakFilter->GetPeakIndex() << std::endl;
}



//----------------------------------------------------------------------------
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::PrintSelf(std::ostream& os, Indent indent) const
{
  Superclass::PrintSelf(os,indent);
}

} // namespace

#endif
