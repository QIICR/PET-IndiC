#ifndef __itkQuantitativeIndicesComputationFilter_h
#define __itkQuantitativeIndicesComputationFilter_h

#include "itkMeshSource.h"

namespace itk
{

template <class TImage, class TLabelImage>
class ITK_EXPORT QuantitativeIndicesComputationFilter : public ProcessObject
{
public:
  /** Standard class type aliases. */
  using Self = QuantitativeIndicesComputationFilter;
  using Superclass = ProcessObject;
  using Pointer = SmartPointer<Self>;
  using ConstPointer = SmartPointer<const Self>;

  using ImageType = TImage;
  using ImagePointer = typename ImageType::Pointer;
  using ImageConstPointer = typename ImageType::ConstPointer;
  using PixelType = typename ImageType::PixelType;

  using LabelImageType = TLabelImage;
  using LabelImagePointer = typename LabelImageType::Pointer;
  using LabelImageConstPointer = typename LabelImageType::ConstPointer;
  using LabelType = typename LabelImageType::PixelType;

  using PointType = typename ImageType::PointType;

  ITK_DISALLOW_COPY_AND_ASSIGN(QuantitativeIndicesComputationFilter);

  itkNewMacro( Self );

  /** Run-time type information (and related methods). */
  itkTypeMacro(QuantitativeIndicesComputationFilter, ProcessObject);

  //Set functions for the images, in const and non-const form
  void SetInputImage( const ImageType* input );
  void SetInputLabelImage( const LabelImageType* input );

  ImageConstPointer GetInputImage() const;
  LabelImageConstPointer GetInputLabelImage() const;

  //Set and Get macros for the various values
  itkSetMacro(CurrentLabel, LabelType);
  itkGetMacro(CurrentLabel, LabelType);

  itkGetMacro(MaximumValue, double);
  itkGetMacro(AverageValue, double);
  itkGetMacro(RMSValue, double);
  itkGetMacro(MinimumValue, double);
  itkGetMacro(PeakValue, double);
  itkGetMacro(TotalLesionGlycolysis, double);
  itkGetMacro(SegmentedVolume, double);
  itkGetMacro(PeakLocation, PointType);
  itkGetMacro(MedianValue, double);
  itkGetMacro(FirstQuartileValue, double);
  itkGetMacro(ThirdQuartileValue, double);
  itkGetMacro(UpperAdjacentValue, double);
  itkGetMacro(Variance, double);
  itkGetMacro(SAMValue, double);
  itkGetMacro(SAMBackground, double);
  itkGetMacro(Gly1, double);
  itkGetMacro(Gly2, double);
  itkGetMacro(Gly3, double);
  itkGetMacro(Gly4, double);
  itkGetMacro(Q1, double);
  itkGetMacro(Q2, double);
  itkGetMacro(Q3, double);
  itkGetMacro(Q4, double);

  void CalculateMean();
  void CalculateQuartiles();
  void CalculatePeak();
  void CalculateSAM();

protected:
  QuantitativeIndicesComputationFilter();
  ~QuantitativeIndicesComputationFilter() override = default;
  void PrintSelf(std::ostream& os, Indent indent) const override;

  void GenerateData() override;
  void CreateSegmentedValueList();

private:
  /** The label to calculate indices for. */
  LabelType m_CurrentLabel;

  /** The maximum segmented value.  */
  double m_MaximumValue;
  /** The average segmented value.  */
  double m_AverageValue;
  /** The root-mean-square segmented value */
  double m_RMSValue;
  /** The median segmented value.  */
  double m_MedianValue;
  /** The minimum segmented value.  */
  double m_MinimumValue;
  /** The peak segmented value.  */
  double m_PeakValue;
  /** The location of the peak.  */
  PointType m_PeakLocation;
  /** The segmented volume.  */
  float m_SegmentedVolume;
  /** The total lesion glycolysis.  */
  double m_TotalLesionGlycolysis;
  /** The MTV in 1st quarter of range  */
  double m_Gly1;
  /** The MTV in 2nd quarter of range  */
  double m_Gly2;
  /** The MTV in 3rd quarter of range  */
  double m_Gly3;
  /** The MTV in 4th quarter of range  */
  double m_Gly4;
  /** Distribution in 1st quarter of range  */
  double m_Q1;
  /** Distribution in 2nd quarter of range  */
  double m_Q2;
  /** Distribution in 3rd quarter of range  */
  double m_Q3;
  /** Distribution in 4th quarter of range  */
  double m_Q4;
  /** The first quartile segmented value.  */
  double m_FirstQuartileValue;
  /** The third quartile segmented value.  */
  double m_ThirdQuartileValue;
  /** The upper adjacent value */
  double m_UpperAdjacentValue;
  /** The variance of the segmented values. */
  double m_Variance;
  /** The standard added metabolic activity. */
  double m_SAMValue;
  /** SAM mean background. */
  double m_SAMBackground;

  /** Flag indicating if list has been generated */
  bool m_ListGenerated{ false };
  /** List of values in region of interest */
  std::vector<double> m_SegmentedValues;
};

} // end namespace itk

#ifndef ITK_MANUAL_INSTANTIATION
#include "itkQuantitativeIndicesComputationFilter.cxx"
#endif

#endif
