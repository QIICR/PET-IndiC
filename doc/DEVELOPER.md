# PET-IndiC Developer Guide

## Overview

PET-IndiC is a 3D Slicer extension for PET tumor segmentation and calculation
of quantitative indices. It provides an interactive GUI where the user segments
a region of interest on a PET volume and immediately sees 22 quantitative
measurements (mean SUV, peak, TLG, SAM, quartiles, etc.).

**Repository**: <https://github.com/QIICR/PET-IndiC>
**Slicer category**: Quantification
**Target Slicer version**: 5.6+

## Repository Structure

```
PET-IndiC/
├── CMakeLists.txt                        # Root build — adds all subdirectories
├── CMake/                                # Version configuration templates
│   ├── QuantitativeIndicesExtMacroExtractRepositoryInfo.cmake
│   └── vtkQuantitativeIndicesExtVersionConfigure.h.in
│
├── PET-IndiC/                            # Main scripted module (the GUI)
│   ├── PETIndiC.py                       #   Widget, Logic, Test classes
│   ├── CMakeLists.txt
│   ├── Resources/Icons/PETIndiC.png
│   └── Testing/
│
├── QuantitativeIndicesCLI/               # C++ CLI that computes the indices
│   ├── QuantitativeIndicesCLI.cxx        #   Entry point, argument parsing
│   ├── QuantitativeIndicesCLI.xml        #   SEM parameter definitions
│   ├── include/
│   │   ├── itkQuantitativeIndicesComputationFilter.h/.cxx
│   │   └── itkPeakIntensityFilter.h/.cxx
│   ├── CMakeLists.txt
│   └── Testing/Cxx/
│
├── QuantitativeIndicesTool/              # Scripted module bridging UI ↔ CLI
│   ├── QuantitativeIndicesTool.py        #   Feature checkboxes, CLI invocation
│   ├── PETVolumeSegmentStatisticsPlugin/ #   SegmentStatistics plugin
│   │   └── PETVolumeSegmentStatisticsPlugin.py
│   ├── CMakeLists.txt
│   └── Testing/
│
├── Testing/                              # Integration test for the plugin
│   └── PETVolumeSegmentStatisticsPluginSelfTest.py
│
├── doc/                                  # Developer documentation
│   ├── DEVELOPER.md                      #   This file
│   └── MIGRATION.md                      #   Editor → Segment Editor migration
│
├── README.md
├── License.txt
└── PET-IndiC.png                         # Extension icon
```

## Module Architecture

The extension is composed of three Slicer modules that work together:

### 1. PET-IndiC (`PETIndiC.py`) — Main GUI Module

**Type**: Scripted loadable module (`ScriptedLoadableModule`)

Provides the primary user interface: volume selector, segmentation tools,
W/L presets, and a results table. When the user modifies a segment (paint,
threshold, etc.), the module automatically exports the segment to a temporary
label map and runs the CLI to compute indices.

**Key classes**:

| Class | Role |
|-------|------|
| `PETIndiC` | Module registration, metadata, help text |
| `PETIndiCWidget` | UI layout, signal wiring, segment observer, CLI orchestration |
| `PETIndiCLogic` | W/L presets, units interpretation, delegates CLI calls to QuantitativeIndicesTool |
| `CustomTableWidget` | QTableWidget subclass with Ctrl+C copy support |
| `PETIndiCTest` | Self-test using QIN-HEADNECK-01-0139 DICOM dataset |

**Data flow**:

```
User paints/thresholds segment
  → vtkSegmentation.SegmentModified event
  → 500ms debounce timer
  → _exportSegmentToLabelMap()  [segment → temp label map, value=1]
  → QuantitativeIndicesToolLogic.run()
  → slicer.cli.run(QuantitativeIndicesCLI, ...)
  → parse CLI output parameters → populate results table
  → remove temp label map node
```

### 2. QuantitativeIndicesTool (`QuantitativeIndicesTool.py`) — Computation Bridge

**Type**: Scripted loadable module

A standalone module with its own UI (volume selectors, 22 feature checkboxes,
results table). Also used programmatically by PET-IndiC as a logic backend.

**Key class**: `QuantitativeIndicesToolLogic`
- `run(inputVolume, labelVolume, cliNode, labelValue, ...flags)` — builds the
  parameter dict and calls `slicer.cli.run()` synchronously

**Submodule**: `PETVolumeSegmentStatisticsPlugin`
- Registers with `SegmentStatisticsLogic` so PET indices appear in Slicer's
  Segment Statistics module
- Exports individual segments to temporary label maps for CLI consumption

### 3. QuantitativeIndicesCLI — C++ Computation Engine

**Type**: Slicer CLI module (SEM — Slicer Execution Model)

Receives a grayscale volume, a label map, and a label value via command-line
arguments. Computes requested indices using ITK filters and writes results
back through the SEM parameter file.

**Computation pipeline**:

1. Load grayscale + label images via `itk::ImageFileReader`
2. Validate geometry — if mismatched, pad label + resample grayscale
3. `itkQuantitativeIndicesComputationFilter`:
   - `CalculateMean()` — mean, std dev, min, max, RMS, volume, TLG,
     glycolysis Q1–Q4, distribution Q1–Q4
   - `CalculateQuartiles()` — 1st quartile, median, 3rd quartile, upper adjacent
   - `CalculatePeak()` — maximum average within a 1 cm³ sphere
     (via `itkPeakIntensityFilter`)
   - `CalculateSAM()` — standardized added metabolic activity + background
4. Write output parameters (or CSV for batch mode)

## Quantitative Indices

The CLI computes 22 indices, grouped into:

| Group | Indices | Units |
|-------|---------|-------|
| Basic statistics | Mean, Std Dev, Min, Max, RMS | image units (e.g. SUVbw g/ml) |
| Volume | Volume | ml |
| Quartiles | 1st Quartile, Median, 3rd Quartile, Upper Adjacent | image units |
| Total lesion glycolysis | TLG | (units) × ml |
| Glycolysis per quarter | Glycolysis Q1–Q4 | (units) × ml |
| Quarter distributions | Q1–Q4 Distribution | % |
| Metabolic activity | SAM, SAM Background | image units |
| Peak | Peak (1 cm³ sphere) | image units |

Units are determined from DICOM attributes (`0054,1001` Units,
`0054,1101`/`1102`/`1103` correction methods) or from the volume node's
voxel value units.

## Build System

All modules are built through the Slicer extension build system:

```cmake
# Root CMakeLists.txt
find_package(Slicer REQUIRED)
add_subdirectory(PET-IndiC)              # slicerMacroBuildScriptedModule
add_subdirectory(QuantitativeIndicesCLI) # SEMMacroBuildCLI (C++ with ITK)
add_subdirectory(QuantitativeIndicesTool)# slicerMacroBuildScriptedModule
add_subdirectory(Testing)
```

The C++ CLI links against `${ITK_LIBRARIES}` and `${SlicerExecutionModel_EXTRA_EXECUTABLE_TARGET_LIBRARIES}`.

Git version info is extracted via `SlicerMacroExtractRepositoryInfo` and
injected into `vtkQuantitativeIndicesExtVersionConfigure.h`.

## Testing

### Self-tests (run inside Slicer)

Each module has a `<Module>Test` class with `runTest()`:

- **PETIndiCTest**: Downloads QIN-HEADNECK-01-0139 PET DICOM, applies
  threshold segmentation, verifies 6 reference index values, tests segment
  switching and undo/redo
- **QuantitativeIndicesToolTest**: Creates 3 synthetic spherical segments,
  computes all features, validates against reference values
- **PETVolumeSegmentStatisticsPluginSelfTest**: Tests the SegmentStatistics
  plugin integration

### Running tests

From within Slicer:
```python
slicer.modules.petindic.widgetRepresentation().self().onReloadAndTest()
```

From CTest (after building):
```bash
ctest -R PETIndiC
```

### Test data

Tests download DICOM data from `https://github.com/QIICR/PETTest` via
`urllib.request`. The dataset is QIN-HEADNECK-01-0139 (a PET/CT scan).

## Key Design Patterns

### Segment-to-label-map export

The CLI expects a traditional label map volume. Segments are exported using:
```python
slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
    segmentationNode, segmentIds, tempLabelNode, referenceVolumeNode,
    slicer.vtkMRMLSegmentationsNode.EXTENT_REFERENCE_GEOMETRY
)
```
This ensures the label map has the same geometry as the PET volume.

### Debounced recalculation

A 500 ms `QTimer.singleShot` prevents running the CLI on every paint stroke.
The timer resets on each `SegmentModified` event; calculation only fires after
the user pauses.

### W/L presets

Four presets adjust the display window/level for common PET viewing scenarios:
1. **FDG PET** — SUV body weight, inverted grey (W=6, L=3)
2. **PET Rainbow** — Rainbow colormap (W=6, L=3)
3. **FLT PET** — Narrower window for FLT tracers (W=4, L=2)
4. **Auto** — Auto window/level from scalar range

### CLI parameter passing

The SEM XML (`QuantitativeIndicesCLI.xml`) defines 22 boolean input flags and
22 string output parameters. The Logic layer builds a parameter dict and calls
`slicer.cli.run()` with `wait_for_completion=True`. Results are read back from
the CLI node's output parameters.

## Dependencies

- **3D Slicer 5.6+** (Python 3, Qt 5, VTK 9, ITK 5)
- **vtkSegmentationCore** — segment manipulation
- **SegmentStatistics** module — plugin registration
- **DICOMLib** — DICOM attribute access for units

No external Python packages are required beyond what Slicer ships.

## Contributors

Ethan Ulrich, Christian Bauer, Markus van Tol, Andrey Fedorov,
Reinhard R. Beichel, John Buatti — University of Iowa & SPL/BWH.

Funded by NIH grants U01-CA140206 (QIN) and U24-CA180918 (QIICR).
