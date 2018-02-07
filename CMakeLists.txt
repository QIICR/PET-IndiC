cmake_minimum_required(VERSION 2.8.9)

project(PET-IndiC)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/PET-IndiC")
set(EXTENSION_CATEGORY "Quantification")
set(EXTENSION_CONTRIBUTORS "Ethan Ulrich (University of Iowa), Christian Bauer (University of Iowa), Markus van Tol (University of Iowa), Andrey Fedorov (SPL), Reinhard R. Beichel (University of Iowa), John Buatti (University of Iowa)")
set(EXTENSION_DESCRIPTION "The PET-IndiC Extension allows for fast segmentation of regions of interest and calculation of quantitative indices.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/QIICR/PET-IndiC/master/PET-IndiC.png")
set(EXTENSION_SCREENSHOTURLS "http://www.slicer.org/slicerWiki/images/3/32/PET-IndiC_Screenshot1.png http://www.slicer.org/slicerWiki/images/8/8b/PET-IndiC_Screenshot3.png http://www.slicer.org/slicerWiki/images/8/8e/PET-IndiC_Screenshot5.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(PET-IndiC)
add_subdirectory(QuantitativeIndicesCLI)
add_subdirectory(QuantitativeIndicesTool)
add_subdirectory(Testing)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})

#-----------------------------------------------------------------------------
SlicerMacroExtractRepositoryInfo(VAR_PREFIX QuantitativeIndicesExt)
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/CMake/vtkQuantitativeIndicesExtVersionConfigure.h.in
    #${CMAKE_CURRENT_BINARY_DIR}/vtkQuantitativeIndicesExtVersionConfigure.h
    ${CMAKE_CURRENT_BINARY_DIR}/QuantitativeIndicesCLI/vtkQuantitativeIndicesExtVersionConfigure.h
    )
