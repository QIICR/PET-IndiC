#ifndef _itkPeakIntensityFilter_cxx
#define _itkPeakIntensityFilter_cxx

#include "itkPeakIntensityFilter.h"
#include "itkImageRegionIteratorWithIndex.h"
#include "itkExtractImageFilter.h"
#include <math.h>

#define PI 3.14159265359

#include "itkImageFileWriter.h"
#include "math.h"


namespace itk
{

//----------------------------------------------------------------------------
template <class TImage, class TLabelImage>
PeakIntensityFilter<TImage, TLabelImage>
::PeakIntensityFilter()
{
  this->ProcessObject::SetNumberOfRequiredInputs(5);
  this->ProcessObject::SetNumberOfRequiredOutputs(0);
  double r = std::pow(1000*0.75/PI,1.0/3.0);
  m_SphereRadius.Fill(r); // approx. 1cc sphere
  m_UseInteriorOnly = true;
  m_UseApproximateKernel = false;
  m_SamplingFactor = 10;
}

//----------------------------------------------------------------------------
template <class TImage, class TLabelImage>
PeakIntensityFilter<TImage, TLabelImage>
::~PeakIntensityFilter()
{}


//----------------------------------------------------------------------------
/*
SetSphereVolume
Sets the volume of the sphere and updates the radii.
Should only be used for 3-D sphere.
*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
::SetSphereVolume(double volume)
{
  m_SphereVolume = volume;
  this->CalculateSphereRadius();
}


//----------------------------------------------------------------------------
/*
SetSphereRadius
Sets the radii for the sphere.

*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
::SetSphereRadius(double r)
{
  m_SphereRadius.Fill(r);
  this->Modified();
}


//----------------------------------------------------------------------------
/*
CalculateSphereRadius
Determines the radius based on sphere volume.

*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
::CalculateSphereRadius()
{
  double r = pow(m_SphereVolume*0.75/PI,1.0/3.0);
  m_SphereRadius.Fill(r);
  this->Modified();
}

//----------------------------------------------------------------------------
/*
SetInputImage
Sets the input volume.

*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
::SetInputImage( const ImageType* input )
{
  // Process object is not const-correct so the const_cast is required here
  this->ProcessObject::SetNthInput(0, input);
}

//----------------------------------------------------------------------------
/*
SetInputImage
Sets the input volume.

*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
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
typename PeakIntensityFilter<TImage, TLabelImage>
::ImagePointer
PeakIntensityFilter<TImage, TLabelImage>
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
PeakIntensityFilter<TImage, TLabelImage>
::SetInputLabelImage( const LabelImageType* input )
{
  // Process object is not const-correct so the const_cast is required here
  this->ProcessObject::SetNthInput(1, input);//this->ProcessObject::SetNthInput( 0, const_cast< HistogramType * >( input ) );
}

//----------------------------------------------------------------------------
/*
SetInputLabelImage
Sets the label volume for the input volume.

*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
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
typename PeakIntensityFilter<TImage, TLabelImage>
::LabelImagePointer
PeakIntensityFilter<TImage, TLabelImage>
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
PeakIntensityFilter<TImage, TLabelImage>
::GenerateData()
{
//std::cout << "    GenerateData()\n";
  this->CalculatePeak();
}


//----------------------------------------------------------------------------
/*
ExtractLabelRegion
Crops the input images to the area near the specified label.

*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
::ExtractLabelRegion()
{
//std::cout << "  ExtractLabelRegion()\n";
  ImagePointer inputImage = this->GetInputImage();
  LabelImagePointer inputLabel = this->GetInputLabelImage();
  m_CroppedInputImage = ImageType::New();
  m_CroppedLabelImage = LabelImageType::New();
  
  // determine extent of label
  typedef typename itk::ImageRegionConstIteratorWithIndex<LabelImageType> LabelIteratorType;
  LabelIteratorType lit(inputLabel,inputLabel->GetLargestPossibleRegion());
  lit.GoToBegin();
  IndexType lowerIndex;
  IndexType upperIndex;

  for(unsigned int i=0; i<ImageDimension; ++i)
  {
    lowerIndex[i] = itk::NumericTraits<int>::max();
    upperIndex[i] = itk::NumericTraits<int>::min();
  }
  bool labelFound = false;
  while(!lit.IsAtEnd())
  {
    if(lit.Get() == m_CurrentLabel)
    {
      labelFound = true;
      typename LabelImageType::IndexType idx = lit.GetIndex();
      for(unsigned int i=0; i<ImageDimension; ++i)
      {
        if(idx[i]<lowerIndex[i]) lowerIndex[i]=idx[i];
        if(idx[i]>upperIndex[i]) upperIndex[i]=idx[i];
      }
    }
    ++lit;
  }
  if(!labelFound)
  {
    m_PeakValue = std::numeric_limits<double>::quiet_NaN();
    m_CroppedInputImage = NULL;
    m_CroppedLabelImage = NULL;
    return;
  }
  
  // define new region (pad region by 1.5x radius)
  SpacingType voxelSize = inputImage->GetSpacing();
  SizeType imageSize = inputImage->GetLargestPossibleRegion().GetSize();
  IndexType imageIndex = inputImage->GetLargestPossibleRegion().GetIndex();
  SizeType pad;
  SizeType size;
  IndexType minIndex;
  IndexType maxIndex;
  for(unsigned int i=0; i<ImageDimension; ++i)
  {
    pad[i] = ceil(1.5*m_SphereRadius[i]/voxelSize[i]);
    minIndex[i] = lowerIndex[i]-pad[i];
    if(minIndex[i]<imageIndex[i]) minIndex[i]=imageIndex[i];
    maxIndex[i] = upperIndex[i]+pad[i];
    if(maxIndex[i]>imageSize[i]-1) maxIndex[i]=imageSize[i]-1;
    size[i] = maxIndex[i]-minIndex[i]+1;
  }
  typename ImageType::RegionType region(minIndex, size);
  
  typedef typename itk::ExtractImageFilter<ImageType,ImageType> ImageExtractorType;
  typedef typename itk::ExtractImageFilter<LabelImageType,LabelImageType> LabelExtractorType;
  typename ImageExtractorType::Pointer imageExtractor = ImageExtractorType::New();
  typename LabelExtractorType::Pointer labelExtractor = LabelExtractorType::New();
  imageExtractor->SetInput(inputImage);
  labelExtractor->SetInput(inputLabel);
  imageExtractor->SetExtractionRegion(region);
  labelExtractor->SetExtractionRegion(region);
#if ITK_VERSION_MAJOR >= 4 // This is required.
  imageExtractor->SetDirectionCollapseToIdentity();
  labelExtractor->SetDirectionCollapseToIdentity();
#endif
  imageExtractor->Update();
  labelExtractor->Update();

  m_CroppedInputImage = imageExtractor->GetOutput();
  m_CroppedLabelImage = labelExtractor->GetOutput();

}


//----------------------------------------------------------------------------
/*
BuildPeakKernel
Creates the NeighborhoodOperatorImageFunction for the peak kernel.

*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
::BuildPeakKernel()
{
//std::cout << "  BuildPeakKernel()\n";
  ImagePointer inputImage = this->GetInputImage();
  LabelImagePointer labelImage = this->GetInputLabelImage();
  SpacingType voxelSize = inputImage->GetSpacing();

  // build the full-resolution image of the kernel
  SizeType kernelSize;
  for(unsigned int i=0; i<ImageDimension; ++i)
  {
    kernelSize[i] = ceil((m_SphereRadius[i]/voxelSize[i])-0.5)*2+1;
    m_KernelRadius[i] = (kernelSize[i]-1)*0.5;
  }

  PointType origin; origin.Fill(0);
  IndexType startIndex; startIndex.Fill(0);
  m_KernelImage = InternalImageType::New();
  m_KernelImage->SetOrigin(origin);
  typename InternalImageType::RegionType kernelRegion(startIndex, kernelSize);
  m_KernelImage->SetRegions(kernelRegion);
  m_KernelImage->SetSpacing(voxelSize);
  m_KernelImage->Allocate();
  m_KernelImage->FillBuffer(0.0);

  typename InternalImageType::Pointer octant = InternalImageType::New();
  octant->SetOrigin(origin);
  SizeType octantSize;
  for(unsigned int i=0; i<ImageDimension; ++i)
  {
    octantSize[i] = ceil(m_SphereRadius[i]/voxelSize[i])+1;
  }
  typename InternalImageType::RegionType octantRegion(startIndex, octantSize);
  octant->SetRegions(octantRegion);
  octant->SetSpacing(voxelSize);
  octant->Allocate();
  octant->FillBuffer(0.0);

  typedef typename itk::ImageRegionIteratorWithIndex<InternalImageType> KernelIteratorType;
  KernelIteratorType okit(octant, octantRegion);
  okit.GoToBegin();
  while(!okit.IsAtEnd())
  {
    IndexType currentIndex = okit.GetIndex();
    okit.Set( this->GetVoxelVolume(m_SphereRadius[0],currentIndex[0]*voxelSize[0],currentIndex[1]*voxelSize[1],
					currentIndex[2]*voxelSize[2],voxelSize[0],voxelSize[1],voxelSize[2]) );
    ++okit;
  }

  KernelIteratorType kit(m_KernelImage, kernelRegion);
  kit.GoToBegin();

  double x = kernelSize[0]*0.5;
  double y = kernelSize[1]*0.5;
  double z = kernelSize[2]*0.5;

  while(!kit.IsAtEnd())
  {
    IndexType transIndex = kit.GetIndex();

    if ( transIndex[0] < x )
    {
      transIndex[0] = x - transIndex[0];
    }
    else
    {
      transIndex[0] = transIndex[0] - x + 1;
    }
    if ( transIndex[1] < y )
    {
      transIndex[1] = y - transIndex[1];
    }
    else
    {
      transIndex[1] = transIndex[1] - y + 1;
    }
    if ( transIndex[2] < z )
    {
      transIndex[2] = z - transIndex[2];
    }
    else
    {
      transIndex[2] = transIndex[2] - z + 1;
    };

    okit.SetIndex( transIndex );
    double compensation = okit.Get();
    if ( transIndex[0] == 0 )
    {
      compensation *= 2;
    }
    if ( transIndex[1] == 0 )
    {
      compensation *= 2;
    }
    if ( transIndex[2] == 0 )
    {
      compensation *= 2;
    }

    kit.Set( compensation );
    ++kit;
  }
}

//HELPER FUNCTIONS FOR BuildPeakKernel()------------------------------------------------
template <class TImage, class TLabelImage>
double
PeakIntensityFilter<TImage, TLabelImage>
::FEdge( double r, double a, double b )
{
//FEDGE Returns the volume fraction of a sphere that intersects with two 
//faces and an edge of a box.
//   Input:
//     r - radius of the sphere
//     a - distance from center of sphere to box edge in x-direction
//     b - distance from center of sphere to box edge in y-direction
//   Output:
//     fraction of sphere's volume that intersects the box

  if ( pow(a,2) + pow(b,2) >= pow(r,2) )
  {
    return 0.0;
  }

  if ( a==0 && b==0 )
  {
    return 0.25;
  }

  double ahat = a/r;
  double bhat = b/r;
  double xhat = sqrt(1-pow(ahat,2) - pow(bhat,2));

  return (1/(4*PI))*(2*ahat*bhat*xhat + 2*atan(bhat*xhat/ahat)
                   + 2*atan(ahat*xhat/bhat)
                   - (3*bhat-pow(bhat,3))*atan(xhat/ahat)
                   - (3*ahat-pow(ahat,3))*atan(xhat/bhat));
}

template <class TImage, class TLabelImage>
double
PeakIntensityFilter<TImage, TLabelImage>
::FCorner( double r, double a, double b, double c )
{
//FCORNER Returns the volume fraction of a sphere that intersects with three 
//faces and a corner of a box.
//   Input:
//     r - radius of the sphere
//     a - distance from center of sphere to box corner in x-direction
//     b - distance from center of sphere to box corner in y-direction
//     c - distance from center of sphere to box corner in z-direction
//   Output:
//     fraction of sphere's volume that intersects the box

  if ( pow(a,2)+pow(b,2)+pow(c,2)>=pow(r,2) )
  {
    return 0.0;
  }

  if ( a==0 && b==0 && c==0 )
  {
    return 0.125;
  }

  double f_edge = FEdge(r,a,b);
  double ahat = a/r;
  double bhat = b/r;
  double chat = c/r;
  double Ahat = sqrt(1-pow(ahat,2)-pow(chat,2));
  double Bhat = sqrt(1-pow(bhat,2)-pow(chat,2));

  return 0.5*f_edge-0.125*(1/PI)*( 6*ahat*bhat*chat - 2*ahat*Ahat*chat
                                - 2*bhat*Bhat*chat
                                - (3*bhat-pow(bhat,3))*atan(chat/Bhat)
                                - (3*ahat-pow(ahat,3))*atan(chat/Ahat)
                                + (3*chat-pow(chat,3))*(atan(Ahat/ahat)-atan(bhat/Bhat))
                                + 2*(atan(chat*ahat/Ahat)+atan(chat*bhat/Bhat)) );
}

template <class TImage, class TLabelImage>
double
PeakIntensityFilter<TImage, TLabelImage>
::GetVoxelVolume( double r, double x, double y, double z, double spx, double spy, double spz )
{
//GET_VOXEL_VOLUME Returns the volume fraction of a voxel intersecting with
//a sphere
//   Input:
//     r - radius of sphere
//     x - x-coordinate of the center of the voxel
//     y - y-coordinate of the center of the voxel
//     z - z-coordinate of the center of the voxel
//     spx - spacing of voxel in the x direction
//     spy - spacing of voxel in the y direction
//     spz - spacing of voxel in the z direction
//   Output:
//     fraction of the voxel's volume that intersects the sphere

  // define the eight corners of the voxel
  double corners[8][3] = { {x-0.5*spx, y-0.5*spy, z-0.5*spz},
			 {x+0.5*spx, y-0.5*spy, z-0.5*spz},
			 {x-0.5*spx, y+0.5*spy, z-0.5*spz},
			 {x-0.5*spx, y-0.5*spy, z+0.5*spz},
			 {x+0.5*spx, y-0.5*spy, z+0.5*spz},
			 {x-0.5*spx, y+0.5*spy, z+0.5*spz},
			 {x+0.5*spx, y+0.5*spy, z-0.5*spz},
			 {x+0.5*spx, y+0.5*spy, z+0.5*spz} };

  for ( int m = 0; m < 8; ++m )
  {
    for ( int n = 0; n < 3; ++n )
    {
      if ( corners[m][n] < 0.0 )
      {
        corners[m][n] = 0.0;
      }
    }
  }

  if ( pow(corners[0][0],2)+pow(corners[0][1],2)+pow(corners[0][2],2) >= pow(r,2) )
  { 
    return 0.0;
  }

  // get the volume defined by each corner
  double v1 = FCorner(r,corners[0][0],corners[0][1],corners[0][2])*(4*PI/3)*pow(r,3);
  double v2 = FCorner(r,corners[1][0],corners[1][1],corners[1][2])*(4*PI/3)*pow(r,3);
  double v3 = FCorner(r,corners[2][0],corners[2][1],corners[2][2])*(4*PI/3)*pow(r,3);
  double v4 = FCorner(r,corners[3][0],corners[3][1],corners[3][2])*(4*PI/3)*pow(r,3);
  double v5 = FCorner(r,corners[4][0],corners[4][1],corners[4][2])*(4*PI/3)*pow(r,3);
  double v6 = FCorner(r,corners[5][0],corners[5][1],corners[5][2])*(4*PI/3)*pow(r,3);
  double v7 = FCorner(r,corners[6][0],corners[6][1],corners[6][2])*(4*PI/3)*pow(r,3);
  double v8 = FCorner(r,corners[7][0],corners[7][1],corners[7][2])*(4*PI/3)*pow(r,3);

  // determine the volume fraction of the voxel
  return (v1-v2-v3-v4+v5+v6+v7-v8)/(spx*spy*spz);
}

//----------------------------------------------------------------------------
/*
ApproximatePeakKernel
Creates the NeighborhoodOperatorImageFunction for the peak kernel.
Approximates the weights of the peak kernel by subsampling the image spacing.
Larger voxel sizes will require a higher sampling factor.
*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
::ApproximatePeakKernel()
{
//std::cout << "  ApproximatePeakKernel()\n";
  ImagePointer inputImage = this->GetInputImage();
  LabelImagePointer labelImage = this->GetInputLabelImage();
  SpacingType voxelSize = inputImage->GetSpacing();
  
  // build a higher-resolution image of the kernel
  SpacingType upsampledKernelSpacing;
  SizeType upsampledKernelSize;
  double voxelFraction = 1.0;
  for(unsigned int i=0; i<ImageDimension; ++i)
  {
    upsampledKernelSpacing[i] = voxelSize[i]/m_SamplingFactor;
    upsampledKernelSize[i] = (ceil((m_SphereRadius[i]/voxelSize[i])-0.5)*2+1)*m_SamplingFactor;
    voxelFraction /= m_SamplingFactor; // volume fraction of upsampled voxel
  }
  PointType origin; origin.Fill(0);
  IndexType startIndex; startIndex.Fill(0);
  typename InternalImageType::RegionType upsampledKernelRegion(startIndex, upsampledKernelSize);
  typename InternalImageType::Pointer upsampledKernel = InternalImageType::New();
  upsampledKernel->SetOrigin(origin);
  upsampledKernel->SetRegions(upsampledKernelRegion);
  upsampledKernel->SetSpacing(upsampledKernelSpacing);
  upsampledKernel->Allocate();
  
  itk::ContinuousIndex<double,ImageDimension> centerIndex;
  for(unsigned int i=0; i<ImageDimension; ++i)
  {
    centerIndex[i] = (upsampledKernelSize[i]-1)*0.5;
  }
  PointType centerPoint;
  upsampledKernel->TransformContinuousIndexToPhysicalPoint(centerIndex, centerPoint);

  typedef typename itk::ImageRegionIteratorWithIndex<InternalImageType> KernelIteratorType;
  KernelIteratorType ukit(upsampledKernel,upsampledKernelRegion);
  ukit.GoToBegin();
  while(!ukit.IsAtEnd())
  {
    IndexType currentIndex = ukit.GetIndex();
    PointType currentPoint;
    upsampledKernel->TransformIndexToPhysicalPoint(currentIndex, currentPoint);
    double r = 0.0;
    for(unsigned int i=0; i<ImageDimension; ++i)
    {
      double psq = (currentPoint[i]-centerPoint[i])*(currentPoint[i]-centerPoint[i]);
      r += psq/(m_SphereRadius[i]*m_SphereRadius[i]);
    }
    if(r <= 1.0)
    {
      ukit.Set(1.0);
    }
    else{
      ukit.Set(0.0);
    }
    ++ukit;
  }
  
  // build the full-resolution image of the kernel
  SizeType kernelSize;
  for(unsigned int i=0; i<ImageDimension; ++i)
  {
    kernelSize[i] = ceil((m_SphereRadius[i]/voxelSize[i])-0.5)*2+1;
    m_KernelRadius[i] = (kernelSize[i]-1)*0.5;
  }

  m_KernelImage = InternalImageType::New();
  m_KernelImage->SetOrigin(origin);
  typename InternalImageType::RegionType kernelRegion(startIndex, kernelSize);
  m_KernelImage->SetRegions(kernelRegion);
  m_KernelImage->SetSpacing(voxelSize);
  m_KernelImage->Allocate();
  m_KernelImage->FillBuffer(0.0);
  KernelIteratorType kit(m_KernelImage, kernelRegion);
  kit.GoToBegin();
  const double inv_samplingFactor = 1/(double)m_SamplingFactor;
  ukit.GoToBegin();
  while(!ukit.IsAtEnd())
  {
    IndexType currentIndex = ukit.GetIndex();
    double val = ukit.Get();
    IndexType newIndex;
    for(unsigned int i=0; i<ImageDimension; ++i)
    {
      newIndex[i] = std::floor((double)currentIndex[i]*inv_samplingFactor);
    }
    kit.SetIndex( newIndex );
    double old_val = kit.Get();
    kit.Set( old_val + val );
    ++ukit;
  }

  // apply the voxel fraction to get the final kernel values
  kit.GoToBegin();
  while(!kit.IsAtEnd())
  {
    kit.Set( kit.Get()*voxelFraction );
    ++kit;
  }
  
}


//----------------------------------------------------------------------------
/*
CalculatePeak
Actually runs the calculations to determine:
Peak, Peak Location

*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
::CalculatePeak()
{

  if(m_UseApproximateKernel)
  {
    this->ApproximatePeakKernel();
  }
  else{
    this->BuildPeakKernel();
  }
  this->ExtractLabelRegion();
  
  if(!m_CroppedInputImage || !m_CroppedLabelImage)
  {
    return;
  }
  
  // create the kernel operators
  typename NeighborhoodOperatorImageFunctionType::Pointer peakOperator = NeighborhoodOperatorImageFunctionType::New();
  peakOperator->SetInputImage(this->GetInputImage());
  typename LabelNeighborhoodOperatorImageFunctionType::Pointer maskOperator = LabelNeighborhoodOperatorImageFunctionType::New();
  maskOperator->SetInputImage(this->GetInputLabelImage());
  this->MakeKernelOperators(peakOperator,maskOperator);
  
//std::cout << "  CalculatePeak()\n";
  
  // convolve the kernel and evaluate at valid indices
  typedef typename itk::ImageRegionIterator<ImageType> IteratorType;
  IteratorType it(m_CroppedInputImage,m_CroppedInputImage->GetRequestedRegion());
//std::cout << "Mask Count: " << m_MaskCount << std::endl;
  typedef typename itk::ImageRegionIterator<LabelImageType> LabelIteratorType;
  LabelIteratorType lit(m_CroppedLabelImage,m_CroppedLabelImage->GetRequestedRegion());
  it.GoToBegin(); lit.GoToBegin(); 
  double peak = itk::NumericTraits<double>::min();
  double max_center_val = itk::NumericTraits<double>::min();
  bool validPlacementFound = false;
  IndexType peakIndex;
  SpacingType spacing = this->GetInputImage()->GetSpacing();
  SizeType imageSize = this->GetInputImage()->GetLargestPossibleRegion().GetSize();
  while(!it.IsAtEnd())
  {
    if(lit.Get() == m_CurrentLabel)
    {
      IndexType currentIndex = lit.GetIndex();
      double xPosition = (currentIndex[0] + 0.5)*spacing[0];
      double yPosition = (currentIndex[1] + 0.5)*spacing[1];
      double zPosition = (currentIndex[2] + 0.5)*spacing[2];
      if ( !m_UseInteriorOnly ||
	( xPosition - m_SphereRadius[0] >= 0 && xPosition + m_SphereRadius[0] < imageSize[0]*spacing[0] &&
	  yPosition - m_SphereRadius[1] >= 0 && yPosition + m_SphereRadius[1] < imageSize[1]*spacing[1] &&
	  zPosition - m_SphereRadius[2] >= 0 && zPosition + m_SphereRadius[2] < imageSize[2]*spacing[2] ) )
      {
	int labelSum = (maskOperator->EvaluateAtIndex(currentIndex))/m_CurrentLabel;
	if( !m_UseInteriorOnly )
        {
          labelSum = m_MaskCount;
        }
        if( labelSum == m_MaskCount ) // valid kernel placement
        {
          validPlacementFound = true;
          double center_val = it.Get();
          double val = peakOperator->EvaluateAtIndex(currentIndex);
          if( (float)val>(float)peak )
          {
            peak = val;
            max_center_val = center_val;
            peakIndex = currentIndex;
          }
          if((float)val==(float)peak)
          {
            if(center_val > max_center_val)
            {
              max_center_val = center_val;
              peakIndex = currentIndex;
            }
          }
        }
      }
    }
    ++it; ++lit;
  }
  
  if(validPlacementFound)
  {
    m_PeakValue = peak;
    m_PeakIndex = peakIndex;
    PointType peakLocation;
    m_CroppedInputImage->TransformIndexToPhysicalPoint(peakIndex,peakLocation);
    m_PeakLocation = peakLocation;
//std::cout << "Max Center Value: " << max_center_val << std::endl;
//std::cout << "Kernel Volume: " << this->GetKernelVolume() << std::endl;
  }
  else{
    m_PeakValue = std::numeric_limits<double>::quiet_NaN();
    for(unsigned int i=0; i<ImageDimension; ++i)
    {
      //m_PeakIndex[i] = std::numeric_limits<int>::quiet_NaN();
      m_PeakIndex[i] = -1;
      m_PeakLocation[i] = std::numeric_limits<double>::quiet_NaN();
    }
  }

}


//----------------------------------------------------------------------------
/*
MakeKernelOperators
Builds the NeighborhoodOperatorImageFunctions for the peak kernel.
Requires a pointer for the weighted version of the kernel and a pointer for
the binary version of the kernel.

*/
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
::MakeKernelOperators( NeighborhoodOperatorImageFunctionType* neighborhoodOperator,
                      LabelNeighborhoodOperatorImageFunctionType* labelNeighborhoodOperator)
{
//std::cout << "  MakeKernelOperators()" << std::endl;

  // create the mask kernel
  typedef typename itk::Neighborhood<LabelPixelType, ImageType::ImageDimension> LabelNeighborhoodType;
  LabelNeighborhoodType labelNeighborhood;
  labelNeighborhood.SetRadius(m_KernelRadius);
  
  // create the convolution kernel
  NeighborhoodType neighborhood;
  neighborhood.SetRadius(m_KernelRadius);
  
  typedef typename itk::ImageRegionConstIterator<InternalImageType> KernelIteratorType;
  KernelIteratorType kit(this->m_KernelImage,this->m_KernelImage->GetLargestPossibleRegion());
  kit.GoToBegin();
  
  typename NeighborhoodType::Iterator nit = neighborhood.Begin();
  typename LabelNeighborhoodType::Iterator lnit = labelNeighborhood.Begin();
  double kernelSum = 0.0;
  m_MaskCount = 0;
  while(!kit.IsAtEnd())
  {
    double val = kit.Get();
    *nit = val;
    kernelSum += val;
    if( val > 0.0 )
    {
      *lnit = 1;
      ++m_MaskCount;
    }
    else{
      *lnit = 0;
    }
    ++nit; ++kit; ++lnit;
  }
  nit = neighborhood.Begin();
  while( nit != neighborhood.End() )
  {
    double val = *nit;
    *nit = val/kernelSum;
    ++nit;
  }
  
  labelNeighborhoodOperator->SetOperator(labelNeighborhood); 
  neighborhoodOperator->SetOperator(neighborhood);
  
  /*typedef typename itk::ImageFileWriter<InternalImageType> WriterType;
  typename WriterType::Pointer writer = WriterType::New();
  writer->SetFileName( "mask.nrrd" );
  writer->SetInput( m_KernelImage );
  writer->Update();*/

}


//----------------------------------------------------------------------------
/*
GetKernelVolume
Determines the total volume of the kernel based on the voxel size and weights

*/
template <class TImage, class TLabelImage>
double
PeakIntensityFilter<TImage, TLabelImage>
::GetKernelVolume()
{
  // determine voxel volume
  typename InternalImageType::SpacingType spacing = this->m_KernelImage->GetSpacing();
  double voxelVolume = 1.0;
  for(unsigned int i=0; i<ImageDimension; ++i)
  {
    voxelVolume *= spacing[i];
  }
  
  // sum up the weights of the kernel image
  double weightSum = 0.0;
  typedef typename itk::ImageRegionConstIterator<InternalImageType> KernelIteratorType;
  KernelIteratorType kit(this->m_KernelImage,this->m_KernelImage->GetLargestPossibleRegion());
  kit.GoToBegin();
  while(!kit.IsAtEnd())
  {
    weightSum += kit.Get();
    ++kit;
  }
  
  return voxelVolume*weightSum;
  
}


//----------------------------------------------------------------------------
template <class TImage, class TLabelImage>
void
PeakIntensityFilter<TImage, TLabelImage>
::PrintSelf(std::ostream& os, Indent indent) const
{
  Superclass::PrintSelf(os,indent);
}

} // namespace

#endif
