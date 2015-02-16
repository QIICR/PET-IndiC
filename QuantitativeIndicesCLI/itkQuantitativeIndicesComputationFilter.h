#ifndef __itkQuantitativeIndicesComputationFilter_h
#define __itkQuantitativeIndicesComputationFilter_h

#include "itkMeshSource.h"

namespace itk
{

template <class TImage, class TLabelImage>
class ITK_EXPORT QuantitativeIndicesComputationFilter : public ProcessObject
{
public:
  /** Standard class typedefs. */
  typedef QuantitativeIndicesComputationFilter     Self;
  typedef ProcessObject  Superclass;
  typedef SmartPointer<Self>       Pointer;
  typedef SmartPointer<const Self> ConstPointer;
  
  typedef TImage                  ImageType;
  typedef typename ImageType::Pointer      ImagePointer;
  typedef typename ImageType::ConstPointer ImageConstPointer;
  typedef typename ImageType::PixelType     PixelType;
  

  typedef TLabelImage                  LabelImageType;
  typedef typename LabelImageType::Pointer      LabelImagePointer;
  typedef typename LabelImageType::ConstPointer LabelImageConstPointer;
  typedef typename LabelImageType::PixelType     LabelType;
  itkNewMacro( Self );

  typedef typename ImageType::PointType PointType;
  
  /** Run-time type information (and related methods). */
  itkTypeMacro(QuantitativeIndicesComputationFilter, ProcessObject);
  
  //Set functions for the images, in const and non-const form
  void SetInputImage( const ImageType* input );
  void SetInputImage( ImageType* input );
  void SetInputLabelImage( const LabelImageType* input );
  void SetInputLabelImage( LabelImageType* input );

  ImagePointer GetInputImage() const;
  LabelImagePointer GetInputLabelImage() const;

  //Set and Get macros for the various values
  itkSetMacro(CurrentLabel, LabelType);
  itkGetMacro(CurrentLabel, LabelType);

  itkGetMacro(MaximumValue, PixelType);
  itkGetMacro(AverageValue, double);
  itkGetMacro(RMSValue, double);
  itkGetMacro(MinimumValue, PixelType);
  itkGetMacro(PeakValue, double);
  itkGetMacro(TotalLesionGlycolysis, double);
  itkGetMacro(SegmentedVolume, double);
  itkGetMacro(PeakLocation, typename ImageType::PointType);
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
  ~QuantitativeIndicesComputationFilter();
  virtual void PrintSelf(std::ostream& os, Indent indent) const;
  
  void GenerateData();

  
private:
  QuantitativeIndicesComputationFilter(const QuantitativeIndicesComputationFilter&); //purposely not implemented
  void operator=(const QuantitativeIndicesComputationFilter&); //purposely not implemented

  /** The label to calculate indices for. */
  LabelType m_CurrentLabel;

  /** The maximum segmented value.  */
  PixelType m_MaximumValue;
  /** The average segmented value.  */
  double m_AverageValue;
  /** The root-mean-square segmented value */
  double m_RMSValue;
  /** The median segmented value.  */
  double m_MedianValue;
  /** The minimum segmented value.  */
  PixelType m_MinimumValue;
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
  bool m_ListGenerated;
  /** List of values in region of interest */
  std::list<double> m_SegmentedValues;
};

} // end namespace itk

#ifndef ITK_MANUAL_INSTANTIATION
#include "itkQuantitativeIndicesComputationFilter.cxx"
#endif

#endif
