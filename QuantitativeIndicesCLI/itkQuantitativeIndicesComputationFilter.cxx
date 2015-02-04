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
  m_ListGenerated = false;
}

//----------------------------------------------------------------------------
template <class TImage, class TLabelImage>
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::~QuantitativeIndicesComputationFilter()
{}


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
  this->ProcessObject::SetNthInput(0, input);
}

//----------------------------------------------------------------------------
/*
SetInputImage
Sets the input volume, expected to be PET data.

*/
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::SetInputImage( ImageType* input )
{
// Process object is not const-correct so the const_cast is required here
  this->ProcessObject::SetNthInput(0, input);
}


//----------------------------------------------------------------------------
/*
GetInputImage
Returns the input image volume.

*/
template <class TImage, class TLabelImage>
typename QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::ImagePointer
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::GetInputImage() const
{
  if ( this->GetNumberOfInputs() < 1 )
  { return NULL;  }
  else
  {
    ImagePointer image = ImageType::New();
    image->Graft(this->ProcessObject::GetInput(0));
    return image;
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
  this->ProcessObject::SetNthInput(1, input);//this->ProcessObject::SetNthInput( 0, const_cast< HistogramType * >( input ) );
}

//----------------------------------------------------------------------------
/*
SetInputLabelImage
Sets the label volume for the iput volume.

*/
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::SetInputLabelImage( LabelImageType*  input )
{
// Process object is not const-correct so the const_cast is required here
  this->ProcessObject::SetNthInput(1, /*const_cast< const LabelImageType* >*/(input));//this->ProcessObject::SetNthInput( 0, const_cast< HistogramType * >( input ) );
}


//----------------------------------------------------------------------------
/*
GetInputLabelImage
Returns the label image volume.

*/
template <class TImage, class TLabelImage>
typename QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::LabelImagePointer
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::GetInputLabelImage() const
{
  if ( this->GetNumberOfInputs() < 2 )
  { return NULL;  }
  else
  {
    LabelImagePointer labelImage = LabelImageType::New();
    labelImage->Graft(this->ProcessObject::GetInput(1));
    return labelImage;
  }
  //{ return static_cast< LabelImageConstPointer >( this->ProcessObject::GetInput(1) );  }
}

//----------------------------------------------------------------------------
template <class TImage, class TLabelImage>
void
QuantitativeIndicesComputationFilter<TImage, TLabelImage>
::GenerateData()
{
  this->CalculateMean();
  this->CalculateQuartiles();
  this->CalculateSAM();
  this->CalculatePeak();
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

  //Declare the variables to determine
  double d_maximumValue = itk::NumericTraits<double>::min();
  double d_minimumValue = itk::NumericTraits<double>::max();
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

  typedef itk::ImageRegionConstIterator<ImageType>  InputIteratorType;
  typedef itk::ImageRegionConstIterator<LabelImageType>  LabelIteratorType;

  ImagePointer inputImage = this->GetInputImage();

  LabelImagePointer inputLabel = this->GetInputLabelImage();

  PointType labelStartPoint;
  inputLabel->TransformIndexToPhysicalPoint(inputLabel->GetLargestPossibleRegion().GetIndex(), labelStartPoint);
  
  typename ImageType::IndexType inputStartIndex;
  inputImage->TransformPhysicalPointToIndex(labelStartPoint, inputStartIndex);
  
  typename ImageType::RegionType inputLabelRegion;
  inputLabelRegion.SetIndex(inputStartIndex);
  inputLabelRegion.SetSize(inputLabel->GetLargestPossibleRegion().GetSize());

  typename ImageType::SpacingType spacing = inputImage->GetSpacing();

  //Need to store all segmented values for some computations
  std::list<double> segmentedValues;
  if(m_ListGenerated)  // list is already generated
  {
    segmentedValues = m_SegmentedValues;
    std::list<double>::iterator listIt = segmentedValues.begin();
    //Find min and max values
    while (listIt != segmentedValues.end())
    {
      double curValue = *listIt;
      if (curValue > d_maximumValue)  {d_maximumValue = curValue;}
      if (curValue < d_minimumValue)  {d_minimumValue = curValue;}
      d_segmentedVolume += 1;
      d_rmsValue += curValue*curValue;
      listIt++;
    }
    //Find the distribution within the range
    binSize = (d_maximumValue-d_minimumValue)*0.25;
    listIt = segmentedValues.begin();
    while (listIt != segmentedValues.end())
    {
      double curValue = *listIt;
      if(curValue >= d_minimumValue && curValue <= (d_minimumValue + binSize)){d_q1++; sum1+=curValue;};
      if(curValue > (d_minimumValue+binSize) && curValue <= (d_minimumValue+2*binSize)){d_q2++; sum2+=curValue;};
      if(curValue > (d_minimumValue+2*binSize) && curValue <= (d_minimumValue+3*binSize)){d_q3++; sum3+=curValue;};
      if(curValue > (d_minimumValue+3*binSize) && curValue <= (d_minimumValue+4*binSize)){d_q4++; sum4+=curValue;}; 
      listIt++;
    }
  }else{
    //Iterate through the image and label.  Determine values where the label is correct in the process.
    LabelIteratorType laIt(inputLabel, inputLabel->GetLargestPossibleRegion());
    laIt.GoToBegin();
    InputIteratorType inIt(inputImage, inputLabelRegion);
    inIt.GoToBegin();

    while (!laIt.IsAtEnd() && !inIt.IsAtEnd())
    {
      if (laIt.Get() == m_CurrentLabel)
      {
        double curValue = (double) inIt.Get();
        segmentedValues.push_back(curValue);
        if (curValue > d_maximumValue)  {d_maximumValue = curValue;}
        if (curValue < d_minimumValue)  {d_minimumValue = curValue;}
        d_rmsValue += curValue*curValue;
        d_segmentedVolume += 1;
      }
      ++inIt;
      ++laIt;
    }
    std::list<double>::iterator listIt = segmentedValues.begin();
    //Find the distribution within the range
    binSize = (d_maximumValue-d_minimumValue)*0.25;
    while (listIt != segmentedValues.end())
    {
      double curValue = *listIt;
      if(curValue >= d_minimumValue && curValue <= (d_minimumValue + binSize)){d_q1++; sum1+=curValue;};
      if(curValue > (d_minimumValue+binSize) && curValue <= (d_minimumValue+2*binSize)){d_q2++; sum2+=curValue;};
      if(curValue > (d_minimumValue+2*binSize) && curValue <= (d_minimumValue+3*binSize)){d_q3++; sum3+=curValue;};
      if(curValue > (d_minimumValue+3*binSize) && curValue <= (d_minimumValue+4*binSize)){d_q4++; sum4+=curValue;}; 
      listIt++;
    }
    //Set the member variables after the list is generated
    m_SegmentedValues = segmentedValues;
    m_ListGenerated = true;
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

	std::list<double>::iterator listIt = segmentedValues.begin();
	while (listIt != segmentedValues.end())
	{
		d_variance += ((*listIt)-d_averageValue) * ((*listIt)-d_averageValue);
		listIt++;
	}

  d_variance /= (voxelCount);


  //Set the class variables to the values we've determined.
  m_AverageValue = (PixelType) d_averageValue;
  m_RMSValue = (PixelType) d_rmsValue;
  m_MinimumValue = (PixelType) d_minimumValue;
  m_MaximumValue = (PixelType) d_maximumValue;
  m_SegmentedVolume = (float) d_segmentedVolume;
  m_TotalLesionGlycolysis = d_totalLesionGly;
  m_Variance = (PixelType) d_variance;
  m_Gly1 = d_gly1;
  m_Gly2 = d_gly2;
  m_Gly3 = d_gly3;
  m_Gly4 = d_gly4;
  m_Q1 = (float) d_q1;
  m_Q2 = (float) d_q2;
  m_Q3 = (float) d_q3;
  m_Q4 = (float) d_q4;

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

  //Declare the variables to determine
  double d_medianValue = 0.0;
  double d_firstQuartileValue = 0.0;
  double d_thirdQuartileValue = 0.0;
  double d_upperAdjacentValue = 0.0;
  //double d_maximumValue = itk::NumericTraits<double>::min();

  typedef itk::ImageRegionConstIterator<ImageType>  InputIteratorType;
  typedef itk::ImageRegionConstIterator<LabelImageType>  LabelIteratorType;

  ImagePointer inputImage = this->GetInputImage();

  LabelImagePointer inputLabel = this->GetInputLabelImage();

  PointType labelStartPoint;
  inputLabel->TransformIndexToPhysicalPoint(inputLabel->GetLargestPossibleRegion().GetIndex(), labelStartPoint);
  
  typename ImageType::IndexType inputStartIndex;
  inputImage->TransformPhysicalPointToIndex(labelStartPoint, inputStartIndex);
  
  typename ImageType::RegionType inputLabelRegion;
  inputLabelRegion.SetIndex(inputStartIndex);
  inputLabelRegion.SetSize(inputLabel->GetLargestPossibleRegion().GetSize());

  //Need to store all segmented values for some computations
  std::list<double> segmentedValues;
  if(m_ListGenerated)  // list is already generated
  {
    segmentedValues = m_SegmentedValues;
  }else{
    //Iterate through the image and label.  Determine values where the label is correct in the process.
    LabelIteratorType laIt(inputLabel, inputLabel->GetLargestPossibleRegion());
    laIt.GoToBegin();
    InputIteratorType inIt(inputImage, inputLabelRegion);
    inIt.GoToBegin();

    while (!laIt.IsAtEnd() && !inIt.IsAtEnd())
    {
      if (laIt.Get() == m_CurrentLabel)
      {
        double curValue = (double) inIt.Get();
        segmentedValues.push_back(curValue);
      }
      ++inIt;
      ++laIt;
    }
    m_SegmentedValues = segmentedValues;
    m_ListGenerated = true;
  }

  //Sort the values to simplify getting the quartiles and median.
  segmentedValues.sort();
  float segmentedValuesSize = segmentedValues.size();
  int list_progress = 0;
	std::list<double>::iterator listIt = segmentedValues.begin();
  //Now scan through to find the quartiles.
	while (listIt != segmentedValues.end())
	{
		list_progress++;
		if (list_progress == (int)(segmentedValuesSize*0.25))
		{ d_firstQuartileValue = (*listIt); }
		if (list_progress == (int)(segmentedValuesSize*0.5))
		{ d_medianValue = (*listIt);  }
		if (list_progress == (int)(segmentedValuesSize*0.75))
		{ d_thirdQuartileValue = (*listIt); }
		listIt++;
	}

  // Find upper adjacent value
  double IQR = d_thirdQuartileValue - d_firstQuartileValue;
  listIt = segmentedValues.end();
  listIt--;
  double d_maximumValue = *listIt;
  listIt = segmentedValues.begin();
  if(IQR!=0){
    while(listIt != segmentedValues.end()){
      if(*listIt < (d_thirdQuartileValue+1.5*IQR)){ d_upperAdjacentValue = *listIt; };
      listIt++;
    }
  }
  else{ d_upperAdjacentValue = d_maximumValue; }

  //Set the class variables to the values we've determined.
  m_MedianValue = (PixelType) d_medianValue;
  m_FirstQuartileValue = (PixelType) d_firstQuartileValue;
  m_ThirdQuartileValue = (PixelType) d_thirdQuartileValue;
  m_UpperAdjacentValue = (PixelType) d_upperAdjacentValue;

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

  //Declare the variables to determine
  double d_SAM = 0.0;
  double d_SAMBackground = 0.0;
  double d_averageValue = 0.0;
  double d_segmentedVolume = 0.0;

  typedef itk::ImageRegionConstIterator<ImageType>  InputIteratorType;
  typedef itk::ImageRegionConstIterator<LabelImageType>  LabelIteratorType;

  ImagePointer inputImage = this->GetInputImage();

  LabelImagePointer inputLabel = this->GetInputLabelImage();

  typename ImageType::SpacingType spacing = inputImage->GetSpacing();
  double voxelSize = spacing[0] * spacing[1] * spacing[2];

  InputIteratorType inIt(inputImage, inputImage->GetLargestPossibleRegion());
  inIt.GoToBegin();

  //Need to store all segmented values for some computations
  std::list<double> segmentedValues;
  if(m_ListGenerated)  // list is already generated
  {
    segmentedValues = m_SegmentedValues;
    std::list<double>::iterator listIt = segmentedValues.begin();
    while (listIt != segmentedValues.end())
    {
      double curValue = *listIt;
      d_averageValue += curValue;
      d_segmentedVolume += 1;
      listIt++;
    }
  }else{
    //Iterate through the image and label.  Determine values where the label is correct in the process.
    LabelIteratorType laIt(inputLabel, inputLabel->GetLargestPossibleRegion());
    laIt.GoToBegin();

    while (!laIt.IsAtEnd() && !inIt.IsAtEnd())
    {
      if (laIt.Get() == m_CurrentLabel)
      {
        double curValue = (double) inIt.Get();
        segmentedValues.push_back(curValue);
        d_averageValue += curValue;
        d_segmentedVolume += 1;
      }
      ++inIt;
      ++laIt;
    }
    m_SegmentedValues = segmentedValues;
    m_ListGenerated = true;
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
	std::list<double>::iterator listIt = dilatedRegionValues.begin();
  while(listIt != dilatedRegionValues.end())
    {
      d_SAM += *listIt;
      listIt++;
    }
  d_SAM = d_SAM / dilatedSize;
  d_SAMBackground = (d_SAM*dilatedSize-d_averageValue*d_segmentedVolume)/(dilatedSize-d_segmentedVolume);
  d_SAM = (d_averageValue-d_SAMBackground)*d_segmentedVolume*voxelSize;

  //Set the class variables to the values we've determined.
  m_SAMValue = (PixelType) d_SAM;
  m_SAMBackground = (PixelType) d_SAMBackground;

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

  //Declare the variables to determine
  //double d_maximumValue = itk::NumericTraits<double>::min();
  //double d_minimumValue = itk::NumericTraits<double>::max();
  double d_peakValue = itk::NumericTraits<double>::min();

  typedef itk::ImageRegionIterator<ImageType> ModifyingIteratorType;
  typedef itk::ImageRegionConstIterator<LabelImageType>  LabelIteratorType;
  typedef itk::ImageRegionConstIteratorWithIndex<LabelImageType>  IndexedLabelIteratorType;

  ImagePointer inputImage = this->GetInputImage();

  LabelImagePointer inputLabel = this->GetInputLabelImage();

  PointType labelStartPoint;
  inputLabel->TransformIndexToPhysicalPoint(inputLabel->GetLargestPossibleRegion().GetIndex(), labelStartPoint);
  
  typename ImageType::IndexType inputStartIndex;
  inputImage->TransformPhysicalPointToIndex(labelStartPoint, inputStartIndex);
  
  typename ImageType::RegionType inputLabelRegion;
  inputLabelRegion.SetIndex(inputStartIndex);
  inputLabelRegion.SetSize(inputLabel->GetLargestPossibleRegion().GetSize());

  //typename ImageType::SpacingType spacing = inputImage->GetSpacing();
  //double voxelSize = spacing[0] * spacing[1] * spacing[2];
  //lowest and highest indices with nonzero labels
  typename LabelImageType::IndexType lowestIndex;
  typename LabelImageType::IndexType highestIndex;

  //Initializing lowest/highest indices to their opposites for the overall image so that less than or greater than each changes them immediately
  for (int i = 0; i < 3; i++)
  {
    lowestIndex[i] = inputStartIndex[i];
    highestIndex[i] = inputStartIndex[i];
    lowestIndex[i] += inputLabel->GetLargestPossibleRegion().GetSize()[i];
  } 

  //Iterate through the image and label.  Determine values where the label is correct in the process.
  LabelIteratorType laIt(inputLabel, inputLabel->GetLargestPossibleRegion());
  laIt.GoToBegin();

  while (!laIt.IsAtEnd())
  {
    if (laIt.Get() == m_CurrentLabel)
    {
      typename ImageType::IndexType currentIndex = laIt.GetIndex();
      for (int i = 0; i < 3; i++)
      {
        if (lowestIndex[i] > currentIndex[i])
        { lowestIndex[i] = currentIndex[i]; }
        if (highestIndex[i] < currentIndex[i])
        { highestIndex[i] = currentIndex[i];  }
      }
    }
    ++laIt;
  }

  //Getting the lowest indices in the input and label images
  typename ImageType::PointType lowestInputPoint;
  typename ImageType::IndexType lowestInputIndex;
  inputLabel->TransformIndexToPhysicalPoint(lowestIndex, lowestInputPoint);
  inputImage->TransformPhysicalPointToIndex(lowestInputPoint, lowestInputIndex);
  
  typename LabelImageType::SizeType validSize;
  validSize[0] = highestIndex[0] - lowestIndex[0];
  validSize[1] = highestIndex[1] - lowestIndex[1];
  validSize[2] = highestIndex[2] - lowestIndex[2];

  int lowerMargin[3] = {0, 0, 0};
  int upperMargin[3] = {0, 0, 0};

  typename ImageType::IndexType lowestPossibleInputIndex = inputImage->GetLargestPossibleRegion().GetIndex();
  typename LabelImageType::IndexType lowestPossibleLabelIndex = inputLabel->GetLargestPossibleRegion().GetIndex();

  //Expanding the lower side of the region by as much of the margin as possible.
  for (int i = 0; i < 3; i++)
  {
    int j = INITIAL_MARGIN;
    bool works = false;
    while (j > 0 && works == false)
    {
      if (lowestIndex[i] - j > lowestPossibleLabelIndex[i] && lowestInputIndex[i] - j > lowestPossibleInputIndex[i])
      { works = true; }
      else
      { j--;  }
    }
    lowerMargin[i] = j;
  }

  //Getting the highest indices in the input and label images
  typename ImageType::IndexType highestPossibleInputIndex = inputImage->GetLargestPossibleRegion().GetIndex();
  highestPossibleInputIndex[0] += inputImage->GetLargestPossibleRegion().GetSize()[0];
  highestPossibleInputIndex[1] += inputImage->GetLargestPossibleRegion().GetSize()[1];
  highestPossibleInputIndex[2] += inputImage->GetLargestPossibleRegion().GetSize()[2];
  typename LabelImageType::IndexType highestPossibleLabelIndex = inputLabel->GetLargestPossibleRegion().GetIndex();
  highestPossibleLabelIndex[0] += inputLabel->GetLargestPossibleRegion().GetSize()[0];
  highestPossibleLabelIndex[1] += inputLabel->GetLargestPossibleRegion().GetSize()[1];
  highestPossibleLabelIndex[2] += inputLabel->GetLargestPossibleRegion().GetSize()[2];

  //Expanding the upper side of the region by as much of the margin as possible.
  for (int i = 0; i < 3; i++)
  {
    int j = INITIAL_MARGIN;
    bool works = false;
    while (j > 0 && works == false)
    {
      if (lowestIndex[i] + (int) validSize[i] + j < highestPossibleLabelIndex[i] && lowestInputIndex[i] + (int) validSize[i] + j < highestPossibleInputIndex[i])
      { works = true; }
      else
      { j--;  }
    }
    upperMargin[i] = j;
  }

  //Setting the regions based on the margins that were available.
  for (int i = 0; i < 3; i++)
  {
    lowestIndex[i] -= lowerMargin[i];
    lowestInputIndex[i] -= lowerMargin[i];
    validSize[i] += upperMargin[i] + lowerMargin[i];
  }

  //Seting regions to resample; don't want to resample the entire image.
  typename ImageType::RegionType inputResampleRegion;
  inputResampleRegion.SetIndex(lowestInputIndex);
  inputResampleRegion.SetSize(validSize);

  typename LabelImageType::RegionType labelResampleRegion;
  labelResampleRegion.SetIndex(lowestIndex);
  labelResampleRegion.SetSize(validSize);

  //Extract the region to get narrower input and label images.
  typedef typename itk::RegionOfInterestImageFilter<ImageType, ImageType> ImageROIFilterType;
  typename ImageROIFilterType::Pointer inputROIFilter = ImageROIFilterType::New();
  inputROIFilter->SetInput(inputImage);
  inputROIFilter->SetRegionOfInterest(inputResampleRegion);

  typedef typename itk::RegionOfInterestImageFilter<LabelImageType, LabelImageType> LabelImageROIFilterType;
  typename LabelImageROIFilterType::Pointer labelROIFilter = LabelImageROIFilterType::New();
  labelROIFilter->SetInput(inputLabel);
  labelROIFilter->SetRegionOfInterest(labelResampleRegion);

  //Must use subregion to determine area for resampling filter


  //Resampled spacing is just by subdividing the initial spacing in all directions
	typename ImageType::SpacingType resampledSpacing;
	typename ImageType::SizeType resampledSize;
	typename ImageType::SpacingType initialSpacing = inputLabel->GetSpacing();

	resampledSpacing[0] = initialSpacing[0]/QI_PEAK_RADIUS_SPACING_RATE;
	resampledSpacing[1] = initialSpacing[1]/QI_PEAK_RADIUS_SPACING_RATE;
	resampledSpacing[2] = initialSpacing[2]/QI_PEAK_RADIUS_SPACING_RATE;

  //Size must change with the spacing
	double numerator = (double) validSize[0] * (double) initialSpacing[0];
	numerator /= (double) resampledSpacing[0];
	numerator = std::ceil(numerator);
	resampledSize[0] = std::ceil((double) validSize[0] * (double) initialSpacing[0] / (double) resampledSpacing[0]);
  resampledSize[1] = std::ceil((double) validSize[1] * (double) initialSpacing[1] / (double) resampledSpacing[1]);
	resampledSize[2] = std::ceil((double) validSize[2] * (double) initialSpacing[2] / (double) resampledSpacing[2]);

	typedef typename itk::ResampleImageFilter<ImageType, ImageType> InputResamplerType;
	typedef itk::ResampleImageFilter<LabelImageType, LabelImageType> LabelResamplerType;
	typedef itk::ConstShapedNeighborhoodIterator<ImageType> InputNeighborhoodIteratorType;
	typedef typename InputNeighborhoodIteratorType::RadiusType InputRadiusType;
  typedef typename InputNeighborhoodIteratorType::OffsetType OffsetType;

	typedef itk::IdentityTransform<double, 3> InputTransformType;
	typedef itk::IdentityTransform<double, 3> LabelTransformType;
	typedef typename itk::NearestNeighborInterpolateImageFunction<ImageType, double >  InputInterpolatorType;
	typedef typename itk::NearestNeighborInterpolateImageFunction<LabelImageType, double >  LabelInterpolatorType;

	typename ImageType::IndexType resampledInputStartIndex;
	resampledInputStartIndex[0] = (int) QI_PEAK_RADIUS_SPACING_RATE * lowestInputIndex[0];
	resampledInputStartIndex[1] = (int) QI_PEAK_RADIUS_SPACING_RATE * lowestInputIndex[1];
	resampledInputStartIndex[2] = (int) QI_PEAK_RADIUS_SPACING_RATE * lowestInputIndex[2];
	typename LabelImageType::IndexType resampledLabelStartIndex;
	resampledLabelStartIndex[0] = (int) QI_PEAK_RADIUS_SPACING_RATE * lowestIndex[0];
	resampledLabelStartIndex[1] = (int) QI_PEAK_RADIUS_SPACING_RATE * lowestIndex[1];
	resampledLabelStartIndex[2] = (int) QI_PEAK_RADIUS_SPACING_RATE * lowestIndex[2];

  //Resample the label image and the input image
	typename LabelResamplerType::Pointer segResampler = LabelResamplerType::New();
	segResampler->SetInput(labelROIFilter->GetOutput());
	segResampler->SetOutputSpacing(resampledSpacing);
	segResampler->SetTransform(LabelTransformType::New());
	segResampler->SetInterpolator(LabelInterpolatorType::New());
	segResampler->SetOutputOrigin(inputLabel->GetOrigin());
	segResampler->SetSize(resampledSize);
	segResampler->SetOutputStartIndex(resampledInputStartIndex);
	segResampler->Update();

	typename InputResamplerType::Pointer petResampler = InputResamplerType::New();
	petResampler->SetInput(inputROIFilter->GetOutput());
	petResampler->SetOutputSpacing(resampledSpacing);
	petResampler->SetTransform(InputTransformType::New());
	petResampler->SetInterpolator(InputInterpolatorType::New());
	petResampler->SetSize(resampledSize);
	petResampler->SetOutputStartIndex(resampledLabelStartIndex);
	petResampler->SetOutputOrigin(inputImage->GetOrigin());
	petResampler->Update();


  typedef itk::ImageRegionIterator<ImageType> ModifyingIteratorType;
  typedef itk::ImageRegionConstIterator<LabelImageType>  LabelIteratorType;

  //Where the label is incorrect, set the input image to an absolute minimum possible value.
  ModifyingIteratorType petModIt(petResampler->GetOutput(), petResampler->GetOutput()->GetLargestPossibleRegion());
  LabelIteratorType labelIt(segResampler->GetOutput(), segResampler->GetOutput()->GetLargestPossibleRegion());
  petModIt.GoToBegin();
  labelIt.GoToBegin();
  PixelType absoluteMinimum = itk::NumericTraits<PixelType>::min();
  while (petModIt.IsAtEnd() == false && labelIt.IsAtEnd() == false)
  {
    if (labelIt.Get() != m_CurrentLabel)
    { petModIt.Set(absoluteMinimum);  }
    ++petModIt;
    ++labelIt;
  }


	InputRadiusType neighborRadius;
  //in each direction, radius = number of voxels to width in that direction = std::ceil(width / resampledspacing)
  neighborRadius[0] = std::ceil(QI_PEAK_RADIUS / resampledSpacing[0]);
  neighborRadius[1] = std::ceil(QI_PEAK_RADIUS / resampledSpacing[1]);
  neighborRadius[2] = std::ceil(QI_PEAK_RADIUS / resampledSpacing[2]);

	IndexedLabelIteratorType resSegIt(segResampler->GetOutput(), segResampler->GetOutput()->GetLargestPossibleRegion());
	resSegIt.GoToBegin();
	  
	InputNeighborhoodIteratorType neiIt(neighborRadius, petResampler->GetOutput(), petResampler->GetOutput()->GetLargestPossibleRegion());
	neiIt.GoToBegin();

  //Need to find the lowest and highest offset in each direction to narrow our region
  OffsetType lowestOffset;
  lowestOffset[0] = 1000;
  lowestOffset[1] = 1000;
  lowestOffset[2] = 1000;
  OffsetType highestOffset;
  highestOffset[0] = -1000;
  highestOffset[1] = -1000;
  highestOffset[2] = -1000;
  std::vector<OffsetType> usefulOffsets;

  //Check each index in the neighborhood and see if it's within the peak radius.  If it is, add it to the active set.
  int qi_peak_max_neighbor = (1+2*neighborRadius[0]) * (1+2*neighborRadius[1]) * (1+2*neighborRadius[2]);
	int firsti = qi_peak_max_neighbor;
	unsigned int usefulCount = 0;
	std::vector<int> usefulIndices;
	typename ImageType::IndexType baseIndex = resSegIt.GetIndex();

	for (int i = 0; i < qi_peak_max_neighbor; i++)
	{
		typename ImageType::IndexType curIndex = neiIt.GetIndex(i);
		curIndex[0] -= baseIndex[0];
		curIndex[1] -= baseIndex[1];
		curIndex[2] -= baseIndex[2];
		typename ImageType::SpacingType space = petResampler->GetOutput()->GetSpacing();
		double distance = curIndex[0] * curIndex[0] * space[0] * space[0];
		distance += curIndex[1] * curIndex[1] * space[1] * space[1];
		distance += curIndex[2] * curIndex[2] * space[2] * space[2];
		if (distance <= (double) QI_PEAK_RADIUS * (double) QI_PEAK_RADIUS)
		{
      OffsetType curOffset;
      curOffset[0] = curIndex[0];
      curOffset[1] = curIndex[1];
      curOffset[2] = curIndex[2];
      if (curOffset[0] < lowestOffset[0]) lowestOffset[0] = curOffset[0];
      if (curOffset[1] < lowestOffset[1]) lowestOffset[1] = curOffset[1];
      if (curOffset[2] < lowestOffset[2]) lowestOffset[2] = curOffset[2];
      if (curOffset[0] > highestOffset[0]) highestOffset[0] = curOffset[0];
      if (curOffset[1] > highestOffset[1]) highestOffset[1] = curOffset[1];
      if (curOffset[2] > highestOffset[2]) highestOffset[2] = curOffset[2];

      usefulOffsets.push_back(curOffset);
			usefulIndices.push_back(i);
			if (i < firsti) firsti = i;
			usefulCount++;
		}
	}


  //Don't iterate the neighborhood iterator through the parts that are too close to the edge to possibly be valid.
  typename ImageType::RegionType narrowedRegion = petResampler->GetOutput()->GetLargestPossibleRegion();
  typename ImageType::IndexType narrowedIndex = narrowedRegion.GetIndex();
  typename ImageType::SizeType narrowedSize = narrowedRegion.GetSize();
  narrowedIndex[0] += -lowestOffset[0];
  narrowedSize[0] += lowestOffset[0];
  narrowedIndex[1] += -lowestOffset[1];
  narrowedSize[1] += lowestOffset[1];
  narrowedIndex[2] += -lowestOffset[2];
  narrowedSize[2] += lowestOffset[2];

  narrowedSize[0] -= highestOffset[0];
  narrowedSize[1] -= highestOffset[1];
  narrowedSize[2] -= highestOffset[2];
  narrowedRegion.SetIndex(narrowedIndex);
  narrowedRegion.SetSize(narrowedSize);

  //Activate the active set for the iterator.
  InputNeighborhoodIteratorType narrowNeiIt(neighborRadius, petResampler->GetOutput(), narrowedRegion);
  for (unsigned int i = 0; i < usefulOffsets.size(); i++)
  { narrowNeiIt.ActivateOffset(usefulOffsets[i]); }
	narrowNeiIt.GoToBegin();


	typename ImageType::PixelType highestPeak = itk::NumericTraits<PixelType>::min();
	typename ImageType::IndexType highestPeakIndex;
	
	highestPeakIndex.Fill(-1.0);
  bool badPoint = true;
  PixelType currentVolume;
  PixelType curPixel;

  //Iterate through the segmented image in the narrowed region
  typename InputNeighborhoodIteratorType::ConstIterator innerIt;
	narrowNeiIt.GoToBegin();
  try
  {

	  while (!narrowNeiIt.IsAtEnd())
	  {
      badPoint = false;
      currentVolume = 0.0;
      innerIt = narrowNeiIt.Begin();

      //Check that *all* indices within the sphere are segmented, to be sure a sphere would fit within the image here.
		  for (unsigned int h = 0; h < usefulCount; h++)
		  {
        curPixel = narrowNeiIt.GetPixel(usefulIndices[h]);

		    if ( curPixel != absoluteMinimum)
        { currentVolume += curPixel;  }
        else
        {
          badPoint = true;
          h = usefulCount;
        }
		  }

      //If we've found a new highest sphere, use it.
      if (!badPoint && currentVolume > highestPeak)
      {
			  highestPeak = currentVolume;
			  highestPeakIndex = narrowNeiIt.GetIndex();
      }

		  ++narrowNeiIt;
	  }
  }
  catch( itk::ExceptionObject & e )
  {
    std::cout << e << std::endl;
    highestPeak = 0;

  }
  //Divide the sphere to get the average voxel value, which is our peak.
  d_peakValue = (double) highestPeak /  (double) usefulCount;
  typename ImageType::PointType highestPeakPoint;

  //Get the physical location of the center of the peak we found.
  petResampler->GetOutput()->TransformIndexToPhysicalPoint(highestPeakIndex, highestPeakPoint);

  //Set the class variables to the values we've determined.
  m_PeakValue = (PixelType) d_peakValue;
  m_PeakLocation[0] = highestPeakPoint[0];
  m_PeakLocation[1] = highestPeakPoint[1];
  m_PeakLocation[2] = highestPeakPoint[2];

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
