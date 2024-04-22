cmake_minimum_required(VERSION 2.8.9)

project(PET-IndiC)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/PET-IndiC")
set(EXTENSION_CATEGORY "Quantification")
set(EXTENSION_CONTRIBUTORS "Ethan Ulrich (University of Iowa), Christian Bauer (University of Iowa), Markus van Tol (University of Iowa), Andrey Fedorov (SPL), Reinhard R. Beichel (University of Iowa), John Buatti (University of Iowa)")
set(EXTENSION_DESCRIPTION "The PET-IndiC Extension allows for fast segmentation of regions of interest and calculation of quantitative indices.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/QIICR/PET-IndiC/master/PET-IndiC.png")
set(EXTENSION_SCREENSHOTURLS "https://www.slicer.org/slicerWiki/images/3/32/PET-IndiC_Screenshot1.png https://www.slicer.org/slicerWiki/images/8/8b/PET-IndiC_Screenshot3.png https://www.slicer.org/slicerWiki/images/8/8e/PET-IndiC_Screenshot5.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

if(CMAKE_CONFIGURATION_TYPES)
  set(DEPENDENCIES_ADDITIONAL_MODULE_PATHS "")
  foreach(config ${CMAKE_CONFIGURATION_TYPES})
    list(APPEND DEPENDENCIES_ADDITIONAL_MODULE_PATHS "${CMAKE_BINARY_DIR}/${Slicer_CLIMODULES_LIB_DIR}/${config}")
    list(APPEND DEPENDENCIES_ADDITIONAL_MODULE_PATHS "${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}/${config}")
  endforeach()
else()
  set(DEPENDENCIES_ADDITIONAL_MODULE_PATHS
    ${CMAKE_BINARY_DIR}/${Slicer_CLIMODULES_LIB_DIR}
    ${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}
    )
endif()

#-----------------------------------------------------------------------------
# Extension modules
# add_subdirectory(PET-IndiC) # requires legacy Editor with got removed: https://github.com/Slicer/Slicer/commit/39283db420baf502fa99865c9d5d58d0e5295a6e
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
