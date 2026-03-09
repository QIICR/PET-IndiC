# PET-IndiC Extension: Segmentation Migration

## Overview

This document covers two related migrations that modernize the PET-IndiC
extension to use segmentation nodes instead of legacy label maps. Developed and
tested with Slicer 5.10.

---

# Part 1: PET-IndiC Module — Editor to Segment Editor

The PET-IndiC module was disabled in November 2021 when 3D Slicer removed the
legacy Editor module ([Slicer commit 39283db](https://github.com/Slicer/Slicer/commit/39283db420baf502fa99865c9d5d58d0e5295a6e)).
This migration replaces all legacy Editor API usage with the modern Segment
Editor (`qMRMLSegmentEditorWidget`) API.

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

## API Verification with slicer-skill

The migration was developed with the help of
[slicer-skill](https://github.com/af61/slicer-skill), an agent skill that
provides local clones of the Slicer source tree, the Extensions Index, and
Slicer Discourse archives for offline API verification.

### Setup

```bash
~/.claude/skills/slicer-skill/setup.sh   # clones Slicer source → slicer-source/
```

### Key source files consulted

| Slicer source file | What it confirmed |
|--------------------|-------------------|
| `Modules/Scripted/SegmentEditor/SegmentEditor.py` | Canonical widget setup: `setMRMLSegmentEditorNode()` **before** `setMRMLScene()` |
| `Modules/Loadable/Segmentations/Widgets/qMRMLSegmentEditorWidget.h` | C++ header — full method signatures (`setSourceVolumeNode`, `setSegmentationNode`, `installKeyboardShortcuts`, etc.) |
| `Modules/Loadable/Segmentations/EditorEffects/Python/SegmentEditorEffects/SegmentEditorThresholdEffect.py` | Threshold parameter names: `MinimumThreshold`, `MaximumThreshold` |
| `Docs/developer_guide/modules/segmenteditor.md` | Effect parameter documentation |
| `Docs/developer_guide/script_repository/segmentations.md` | Segment export and manipulation examples |
| `Modules/Loadable/Segmentations/Testing/Python/SegmentationsModuleTest2.py` | Test pattern: `effect.self().onApply()` |
| `Utilities/Templates/Modules/ScriptedSegmentEditorEffect/SegmentEditorTemplateKey.py` | Confirmed `effect.self().onApply()` convention |

### Corrections made from source verification

- **Initialization order**: The initial plan called `setMRMLScene()` before
  `setMRMLSegmentEditorNode()`. Reading `SegmentEditor.py` showed the correct
  order is parameter node first, then scene.
- **Method name**: Confirmed `setSourceVolumeNode()` (not the deprecated
  `setMasterVolumeNode()`).
- **Threshold parameters**: Confirmed exact strings `MinimumThreshold` /
  `MaximumThreshold` (not `ThresholdMin` etc.).
- **Apply pattern**: Confirmed `effect.self().onApply()` (not
  `effect.apply()` or similar).

## Interactive Testing with MCP

The migrated module was tested interactively inside a running Slicer instance
using the MCP (Model Context Protocol) server bundled with slicer-skill at
`~/.claude/skills/slicer-skill/slicer-mcp-server.py`.

### How it works

1. Paste the MCP server script into Slicer's Python console — starts an HTTP
   JSON-RPC endpoint at `localhost:2026/mcp`
2. The agent sends `tools/call` requests via `curl` to execute Python code
   (`execute_python`) and capture screenshots (`screenshot`) inside Slicer

### Test results

| Test | Result |
|------|--------|
| Module loads (`slicer.modules.petindic`) | Pass |
| Widget UI renders with Segment Editor embedded | Pass |
| Load PET volume → segmentation auto-created | Pass |
| Threshold effect → quantitative indices calculated | Pass — 22 indices returned |
| Add second segment + switch → recalculation | Pass |
| Undo/redo via `segmentEditorWidget.undo()`/`redo()` | Pass |
| W/L presets (PET SUV, PET Rainbow) | Pass |

---

# Part 2: QuantitativeIndicesTool — Label Maps to Segmentations

The QuantitativeIndicesTool module previously required users to select a
`vtkMRMLLabelMapVolumeNode` and an integer label value, then "Generate" a
parameter set for all labels before calculating. This migration replaces that
workflow with native segmentation support — users select a segmentation node
and a named segment, then calculate on demand.

## Files Changed

| File | Change |
|------|--------|
| `QuantitativeIndicesTool/QuantitativeIndicesTool.py` | Widget, Logic, and Test migration |

**Not modified**: `PETIndiC.py` (already handles its own segment-to-label-map
export and calls `QuantitativeIndicesToolLogic.run()` with a label volume),
`PETVolumeSegmentStatisticsPlugin.py` (same pattern), `QuantitativeIndicesCLI`
(C++ CLI unchanged — still receives label map + label value).

## API Migration Map

| Legacy Label Map API | Modern Segmentation API |
|----------------------|------------------------|
| `qMRMLNodeComboBox(vtkMRMLLabelMapVolumeNode)` | `qMRMLNodeComboBox(vtkMRMLSegmentationNode)` |
| `QSpinBox` for label value (1, 2, 3, ...) | `QComboBox` populated with segment names/IDs |
| `vtkImageAccumulate` to count label range | `segmentation.GetNumberOfSegments()` / `GetNthSegmentID()` |
| Pass label map + label value to CLI directly | Export segment → temp label map (value=1) → CLI → remove temp |
| Pre-generate CLI nodes for all labels ("Generate") | Calculate on demand for selected segment |
| Store results in `cliNodes[labelValue]` dict | Read results directly from CLI output node |

## Architecture Changes

### Widget: Selectors
- **Before**: Label map selector (`vtkMRMLLabelMapVolumeNode`) + label value
  spin box + "Generate" / "Change Volumes" buttons for pre-caching CLI results
- **After**: Segmentation selector (`vtkMRMLSegmentationNode`) + segment combo
  box populated dynamically. No pre-generation step — calculate on demand.

### Widget: Calculation Flow
- **Before**: `onCalculateButton()` passes `self.labelNode` and
  `labelValueSelector.value` directly to `logic.run()`, then diffs result
  against pre-generated `cliNodes[labelValue]` in `writeResults()`
- **After**: `onCalculateButton()` exports selected segment to a temporary
  label map (value=1) via `ExportSegmentsToLabelmapNode()` with
  `EXTENT_REFERENCE_GEOMETRY`, calls `logic.run()` with `labelValue=1`, removes
  temp node, reads results directly from CLI output

### Logic: `run()` Unchanged
The `run(inputVolume, labelVolume, cliNode, labelValue, ...flags)` signature is
preserved. PETIndiC.py calls this method with a label volume it already
exported. A new `runOnSegment()` convenience method is added for callers that
want to pass a segmentation node + segment ID directly.

### Logic: `runOnSegment()` Added

New convenience method for callers who have a segmentation node + segment ID:
```python
logic.runOnSegment(inputVolume, segmentationNode, segmentID,
                   mean=True, peak=True, volume=True, ...)
```
Handles segment export, CLI execution, and temp node cleanup internally.

### Widget: Additional Cleanup
- `setMargin(0)` → `setContentsMargins(0, 0, 0, 0)` (deprecated in Qt5)
- Removed `delayDisplay()` from Logic class (unused)
- Removed commented-out screenshot widgets and old constructor

## Removed Code
- `self.labelSelector` — label map volume selector
- `self.labelValueSelector` — integer spin box for label value
- `self.parameterFrame` — "Generate" / "Change Volumes" buttons and label
- `self.cliNodes` dict — pre-generated CLI nodes for each label value
- `onParameterSetButton()` — pre-generation loop running CLI for every label
- `onChangeVolumesButton()` / `confirmDelete()` — volume change workflow
- `onLabelValueSelect()` — unused handler
- `writeResults()` diff mechanism — old/new node comparison
- `delayDisplay()` and `takeScreenshot()` in Logic — unused template methods
- Commented-out screenshot widgets, old constructor, old `run()` signature

## Test Changes
- Segmentation node set directly on widget:
  `widget.segmentationSelector.setCurrentNode(segmentationNode)`
- No label map export step — the widget handles export internally
- No `onParameterSetButton()` call needed
- Segment switching via `widget.segmentSelector.setCurrentIndex(1)` instead of
  `widget.labelValueSelector.setValue(2)`
- Reference values preserved — `EXTENT_REFERENCE_GEOMETRY` ensures same geometry

## Verification
1. Open QuantitativeIndicesTool in Slicer
2. Select a grayscale volume and a segmentation with segments
3. Choose a segment from the dropdown → click Calculate → indices appear
4. Switch to another segment → recalculate → new values
5. Run self-test:
   `slicer.modules.quantitativeindicestool.widgetRepresentation().self().onReloadAndTest()`
