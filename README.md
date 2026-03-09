PET-IndiC Extension
=====================================

3D Slicer extension for fast segmentation of regions of interest and
calculation of quantitative PET indices.

Developed and tested with **3D Slicer 5.10**.

## Features

- Interactive segmentation using the Segment Editor (threshold, paint, scissors, etc.)
- Automatic calculation of 22 quantitative indices on segment modification
- Window/level presets for common PET viewing scenarios (FDG, FLT, Rainbow)
- Integration with Slicer's Segment Statistics module via the
  PETVolumeSegmentStatisticsPlugin
- Undo/redo support and keyboard shortcuts

## Quantitative Indices

| Group | Indices |
|-------|---------|
| Basic statistics | Mean, Std Dev, Min, Max, RMS |
| Volume | Volume (ml) |
| Quartiles | 1st Quartile, Median, 3rd Quartile, Upper Adjacent |
| Glycolysis | TLG, Glycolysis Q1–Q4 |
| Distributions | Q1–Q4 Distribution (%) |
| Metabolic activity | SAM, SAM Background |
| Peak | Peak (1 cm³ sphere) |

## Modules

| Module | Type | Description |
|--------|------|-------------|
| PET-IndiC | Scripted | Main GUI — volume selection, segmentation, results table |
| QuantitativeIndicesTool | Scripted | Computation bridge with feature checkboxes and CLI invocation |
| QuantitativeIndicesCLI | C++ CLI | ITK-based computation engine (SEM) |

## Documentation

- [Developer Guide](doc/DEVELOPER.md) — architecture, build system, design patterns
- [Migration Guide](doc/MIGRATION.md) — legacy Editor to Segment Editor migration

## Contributors

[Ethan Ulrich](https://github.com/ejulrich),
[Christian Bauer](https://github.com/chribaue),
Markus van Tol,
Reinhard R. Beichel,
John Buatti
(University of Iowa),
[Andrey Fedorov](https://github.com/fedorov) (SPL, Brigham and Women's Hospital),
[Jean-Christophe Fillion-Robin](https://github.com/jcfr) (Kitware),
[Andras Lasso](https://github.com/lassoan) (Queen's University).

## Acknowledgements

This work is funded in part by [Quantitative Imaging to Assess Response in Cancer Therapy Trials][] NIH grant U01-CA140206 (PIs John Buatti, Tom Casavant, Michael Graham, Milan Sonka) and [Quantitative Image Informatics for Cancer Research][] (QIICR) NIH grant U24 CA180918.

[Quantitative Imaging to Assess Response in Cancer Therapy Trials]: http://imaging.cancer.gov/programsandresources/specializedinitiatives/qin/iowa
[Quantitative Image Informatics for Cancer Research]: http://qiicr.org
