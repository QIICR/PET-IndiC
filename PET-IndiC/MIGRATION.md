# PET-IndiC: Editor to Segment Editor Migration

## Overview

The PET-IndiC module was disabled in November 2021 when 3D Slicer removed the
legacy Editor module ([Slicer commit 39283db](https://github.com/Slicer/Slicer/commit/39283db420baf502fa99865c9d5d58d0e5295a6e)).
This migration replaces all legacy Editor API usage with the modern Segment
Editor (`qMRMLSegmentEditorWidget`) API, targeting Slicer 5.6+.

## Files Changed

| File | Change |
|------|--------|
| `PET-IndiC/PETIndiC.py` | Full migration of Widget, Logic, and Test classes |
| `CMakeLists.txt` | Re-enabled `add_subdirectory(PET-IndiC)` |
| `QuantitativeIndicesTool/QuantitativeIndicesTool.py` | Fixed legacy `from __main__` import |

## API Migration Map

| Legacy Editor API | Modern Segment Editor API |
|-------------------|--------------------------|
| `slicer.modules.editor.createNewWidgetRepresentation()` | `slicer.qMRMLSegmentEditorWidget()` |
| `slicer.modules.EditorWidget` | `self.segmentEditorWidget` (local instance) |
| `editorWidget.editLabelMapsFrame` | Full `qMRMLSegmentEditorWidget` embedded |
| `editorWidget.toolsColor.colorSpin.value` | `segmentEditorWidget.currentSegmentID()` |
| `editorWidget.toolsBox.selectEffect('ThresholdEffect')` | `segmentEditorWidget.setActiveEffectByName('Threshold')` |
| `toolsBox.currentOption.threshold.minimumValue` | `effect.setParameter('MinimumThreshold', value)` |
| `toolsBox.currentOption.threshold.maximumValue` | `effect.setParameter('MaximumThreshold', value)` |
| `thresholdOptions.onApply()` | `effect.self().onApply()` |
| `editorWidget.toolsBox.buttons['PreviousCheckPoint']` | `segmentEditorWidget.undo()` |
| `editorWidget.toolsBox.buttons['NextCheckPoint']` | `segmentEditorWidget.redo()` |
| `editorWidget.exit()` | `segmentEditorWidget.setActiveEffect(None)` |
| `vtkMRMLLabelMapVolumeNode` selector | `vtkMRMLSegmentationNode` selector |
| Label map `ModifiedEvent` observer | `vtkSegmentation.SegmentModified` observer |
| `colorSpin.connect('valueChanged(int)', ...)` | `connect('currentSegmentIDChanged(QString)', ...)` |

## Architecture Changes

### Segmentation Workflow
- **Before**: Label map volumes with integer label values; Editor widget for painting
- **After**: Segmentation nodes with named segments; Segment Editor widget for all effects

### Calculation Flow
- **Before**: CLI receives label map + label value directly
- **After**: Selected segment is exported to a temporary label map (value=1) via
  `ExportSegmentsToLabelmapNode()` with `EXTENT_REFERENCE_GEOMETRY`, passed to CLI,
  then the temp node is removed

### Debouncing
Added a 500ms debounce timer on `vtkSegmentation.SegmentModified` to prevent
running the CLI on every interactive paint stroke. The timer resets on each
modification event, so the CLI only runs after the user pauses editing.

### Undo/Redo
Enabled with `setMaximumNumberOfUndoStates(10)`. The Segment Editor widget
manages undo/redo state internally.

### Keyboard Shortcuts
Added `installKeyboardShortcuts()` / `uninstallKeyboardShortcuts()` and
`setupViewObservations()` / `removeViewObservations()` in `enter()` / `exit()`
per the canonical Slicer `SegmentEditor.py` pattern.

## Removed Code
- `getLabelNodeForNode()` — manual label map creation with VTK filters
- `volumeDictionary` — monkey-patched attributes on volume nodes
- VTK 5 compatibility checks (`vtk.VTK_MAJOR_VERSION <= 5`)
- `isValidInputOutputData()` and `run()` — unused template methods
- `setMargin(0)` — replaced with `setContentsMargins(0, 0, 0, 0)` (Qt5+)

## Test Changes
- Threshold effect uses `setParameter()` / `effect.self().onApply()` instead of
  direct widget property access
- New segments created via `segmentation.AddEmptySegment()` +
  `setCurrentSegmentID()` instead of `colorSpin.value = N`
- Undo/redo via `segmentEditorWidget.undo()` / `redo()` instead of button clicks
- Reference values preserved; `EXTENT_REFERENCE_GEOMETRY` ensures matching geometry

## Verification
1. Build extension in Slicer (PET-IndiC module should now appear)
2. Load a PET volume → segmentation node auto-created
3. Use Threshold / Paint effects → quantitative indices calculated on segment modification
4. Switch segments → recalculation triggered
5. W/L presets → unchanged behavior
6. Run self-test: `slicer.modules.petindic.widgetRepresentation().self().onReloadAndTest()`
