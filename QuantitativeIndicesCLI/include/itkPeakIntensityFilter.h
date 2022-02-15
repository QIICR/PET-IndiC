#ifndef __itkPeakIntensityFilter_h
#define __itkPeakIntensityFilter_h

#include "itkNeighborhoodOperatorImageFunction.h"

namespace itk
{

template <class TImage, class TLabelImage>
class ITK_EXPORT PeakIntensityFilter : public ProcessObject
{
public:
  /** Standard class type aliases. */
  using Self = PeakIntensityFilter;
  using Superclass = ProcessObject;
  using Pointer = SmartPointer<Self>;
  using ConstPointer = SmartPointer<const Self>;

  /** Useful class  type aliases*/
  using ImageType = TImage;
  using ImagePointer = typename ImageType::Pointer;
  using ImageConstPointer = typename ImageType::ConstPointer;
  using PixelType = typename ImageType::PixelType;
  using PointType = typename ImageType::PointType;
  using SpacingType = typename ImageType::SpacingType;
  using SizeType = typename ImageType::SizeType;
  using IndexType = typename ImageType::IndexType;

  using LabelImageType = TLabelImage;
  using LabelImagePointer = typename LabelImageType::Pointer;
  using LabelImageConstPointer = typename LabelImageType::ConstPointer;
  using LabelPixelType = typename LabelImageType::PixelType;
  using InternalImageType = typename itk::Image<double, ImageType::ImageDimension>;

  ITK_DISALLOW_COPY_AND_ASSIGN(PeakIntensityFilter);

  itkNewMacro( Self );

  /** Dimension of the underlying image. */
  static constexpr unsigned int ImageDimension = ImageType::ImageDimension;

  /** Run-time type information (and related methods). */
  itkTypeMacro(PeakIntensityFilter, ProcessObject);

  /** Set/Get functions for the images, in const and non-const form */
  void SetInputImage( const ImageType* input );
  void SetInputLabelImage( const LabelImageType* input );
  ImageConstPointer GetInputImage() const;
  LabelImageConstPointer GetInputLabelImage() const;

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
  ~PeakIntensityFilter() override = default;
  void PrintSelf(std::ostream& os, Indent indent) const override;

  void GenerateData() override;

  using NeighborhoodType = itk::Neighborhood<double, ImageDimension>;
  using NeighborhoodOperatorImageFunctionType = itk::NeighborhoodOperatorImageFunction<ImageType, double>;
  using LabelNeighborhoodOperatorImageFunctionType = itk::NeighborhoodOperatorImageFunction<LabelImageType, int>;

  void ApproximatePeakKernel();
  void MakeKernelOperators( NeighborhoodOperatorImageFunctionType* neighborhoodOperator,
                            LabelNeighborhoodOperatorImageFunctionType* labelNeighborhoodOperator );
  void ExtractLabelRegion();
  void CalculateSphereRadius();

  double FEdge( double r, double a, double b );
  double FCorner( double r, double a, double b, double c );
  double GetVoxelVolume( double r, double x, double y, double z, double spx, double spy, double spz );

private:
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
  int m_SamplingFactor{ 10 };
  /** Cropped version of the input image */
  ImagePointer m_CroppedInputImage;
  /** Cropped version of the label image */
  LabelImagePointer m_CroppedLabelImage;
  /** Set to true to ignore when any part of the kernel is placed outside the label region */
  bool m_UseInteriorOnly{ true };
  /** Set to true to use an approximation of the peak kernel (follows Siemens' method) */
  bool m_UseApproximateKernel{ false };
  /** Image containing the coefficents of the peak kernel */
  typename InternalImageType::Pointer m_KernelImage;

};

} // end namespace itk

#ifndef ITK_MANUAL_INSTANTIATION
#include "itkPeakIntensityFilter.cxx"
#endif

#endif
