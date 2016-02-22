#ifndef __itkPeakIntensityFilter_h
#define __itkPeakIntensityFilter_h

#include "itkNeighborhoodOperatorImageFunction.h"

namespace itk
{

template <class TImage, class TLabelImage>
class ITK_EXPORT PeakIntensityFilter : public ProcessObject
{
public:
  /** Standard class typedefs. */
  typedef PeakIntensityFilter      Self;
  typedef ProcessObject            Superclass;
  typedef SmartPointer<Self>       Pointer;
  typedef SmartPointer<const Self> ConstPointer;
  
  /** Useful class typedefs*/
  typedef TImage                           ImageType;
  typedef typename ImageType::Pointer      ImagePointer;
  typedef typename ImageType::ConstPointer ImageConstPointer;
  typedef typename ImageType::PixelType    PixelType;
  typedef typename ImageType::PointType    PointType;
  typedef typename ImageType::SpacingType  SpacingType;
  typedef typename ImageType::SizeType     SizeType;
  typedef typename ImageType::IndexType    IndexType;

  typedef TLabelImage                           LabelImageType;
  typedef typename LabelImageType::Pointer      LabelImagePointer;
  typedef typename LabelImageType::ConstPointer LabelImageConstPointer;
  typedef typename LabelImageType::PixelType    LabelPixelType;
  typedef typename itk::Image<double, ImageType::ImageDimension> InternalImageType;
  
  itkNewMacro( Self );
  
  /** Dimension of the underlying image. */
  itkStaticConstMacro(ImageDimension, unsigned int, ImageType::ImageDimension); 

  /** Run-time type information (and related methods). */
  itkTypeMacro(PeakIntensityFilter, ProcessObject);
  
  /** Set/Get functions for the images, in const and non-const form */
  void SetInputImage( const ImageType* input );
  void SetInputImage( ImageType* input );
  void SetInputLabelImage( const LabelImageType* input );
  void SetInputLabelImage( LabelImageType* input );
  ImagePointer GetInputImage() const;
  LabelImagePointer GetInputLabelImage() const;

  /** Set/Get functions for the various values */
  itkSetMacro(CurrentLabel, LabelPixelType);
  itkGetMacro(CurrentLabel, LabelPixelType);
  itkGetMacro(PeakValue, double);
  itkGetMacro(PeakIndex, IndexType);
  itkGetMacro(PeakLocation, PointType);
  itkSetMacro(SphereRadius, PointType);
  itkGetMacro(SphereRadius, PointType);
  itkGetMacro(SphereVolume, double);
  itkSetMacro(SamplingFactor, int);
  itkSetMacro(UseInteriorOnly, bool);
  itkSetMacro(UseApproximateKernel, bool);
  itkGetMacro(KernelImage, typename InternalImageType::Pointer);
  
  /** Set the radii of the peak kernel for all dimensions. */
  void SetSphereRadius(double r);
  
  /** Sets the volume of the sphere and updates the radii. Should only be used for 3-D sphere. */
  void SetSphereVolume(double volume);
  
  /** Determines the total volume of the kernel based on the voxel size and weights */
  double GetKernelVolume();
  
  /** Creates the peak kernel based on image spacing and kernel size */
  void BuildPeakKernel();
  
  /** Applies the peak kernel to determine peak intensity value */
  void CalculatePeak();


protected:
  PeakIntensityFilter();
  ~PeakIntensityFilter();
  virtual void PrintSelf(std::ostream& os, Indent indent) const;
  
  typedef typename itk::Neighborhood<double, ImageType::ImageDimension> NeighborhoodType;
  typedef typename itk::NeighborhoodOperatorImageFunction<ImageType, double> NeighborhoodOperatorImageFunctionType;
  typedef typename itk::NeighborhoodOperatorImageFunction<LabelImageType, int> LabelNeighborhoodOperatorImageFunctionType;
  
  void GenerateData();
  
  void ApproximatePeakKernel();
  void MakeKernelOperators( NeighborhoodOperatorImageFunctionType* neighborhoodOperator,
                            LabelNeighborhoodOperatorImageFunctionType* labelNeighborhoodOperator );
  void ExtractLabelRegion();
  void CalculateSphereRadius();
  
  double FEdge( double r, double a, double b );
  double FCorner( double r, double a, double b, double c );
  double GetVoxelVolume( double r, double x, double y, double z, double spx, double spy, double spz );
  
private:
  PeakIntensityFilter(const PeakIntensityFilter&); //purposely not implemented
  void operator=(const PeakIntensityFilter&); //purposely not implemented

  /** Label used to calculate indices. */
  LabelPixelType m_CurrentLabel;
  /** The peak segmented value.  */
  double m_PeakValue;
  /** The index of the peak.  */
  IndexType m_PeakIndex;
  /** The physical location of the peak.  */
  PointType m_PeakLocation;
  /** Exact radius of the peak kernel for all dimensions */
  PointType m_SphereRadius;
  /** Total volume of the peak kernel */
  double m_SphereVolume;
  /** Total number of non-zero coefficients in the peak kernel */
  int m_MaskCount;
  /** Integer radius of the kernel */
  SizeType m_KernelRadius;
  /** Number of sub-samples to take along each dimension for the approximate peak kernel */
  int m_SamplingFactor;
  /** Cropped version of the input image */
  typename ImageType::Pointer m_CroppedInputImage;
  /** Cropped version of the label image */
  typename LabelImageType::Pointer m_CroppedLabelImage;
  /** Set to true to ignore when any part of the kernel is placed outside the label region */
  bool m_UseInteriorOnly;
  /** Set to true to use an approximation of the peak kernel (follows Siemens' method) */
  bool m_UseApproximateKernel;
  /** Image containing the coefficents of the peak kernel */
  typename InternalImageType::Pointer m_KernelImage;

};

} // end namespace itk

#ifndef ITK_MANUAL_INSTANTIATION
#include "itkPeakIntensityFilter.cxx"
#endif

#endif
