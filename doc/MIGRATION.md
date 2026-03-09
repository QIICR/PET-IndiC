# PET-IndiC: Editor to Segment Editor Migration

## Overview

The PET-IndiC module was disabled in November 2021 when 3D Slicer removed the
legacy Editor module ([Slicer commit 39283db](https://github.com/Slicer/Slicer/commit/39283db420baf502fa99865c9d5d58d0e5295a6e)).
This migration replaces all legacy Editor API usage with the modern Segment
Editor (`qMRMLSegmentEditorWidget`) API. Developed and tested with Slicer 5.10.

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
