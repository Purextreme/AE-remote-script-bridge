# AE API Table

High-frequency After Effects scripting APIs only. This is not a full SDK.

## Project

| Task | API | Notes |
|---|---|---|
| Active item | `app.project.activeItem` | Check `instanceof CompItem` before comp work. |
| Project item count | `app.project.numItems` | Pair with 1-based `item(index)`. |
| Get project item | `app.project.item(index)` | 1-based. |
| Import file | `app.project.importFile(importOptions)` | Requires `new ImportOptions(file)`. |
| Save project | `app.project.save()` / `app.project.save(file)` | `file` is ExtendScript `File`. |
| Render queue | `app.project.renderQueue` | See render section. |

## Comp

| Task | API | Notes |
|---|---|---|
| Create comp | `app.project.items.addComp(name, width, height, pixelAspect, duration, frameRate)` | Returns `CompItem`. |
| Layer count | `comp.numLayers` | Layer indexes are 1-based. |
| Get layer | `comp.layer(index)` | 1-based. |
| Selected layers | `comp.selectedLayers` | 0-based array; can be empty. |
| Add solid | `comp.layers.addSolid(color, name, width, height, pixelAspect, duration)` | `color` is `[r,g,b]`, 0..1. |
| Add text | `comp.layers.addText(text)` | Returns `TextLayer`. |
| Add null | `comp.layers.addNull(duration)` | Returns `AVLayer`. |
| Work area | `comp.workAreaStart`, `comp.workAreaDuration` | Seconds. |

## Layer

| Task | API | Notes |
|---|---|---|
| Duplicate | `layer.duplicate()` | Returns new layer. |
| Remove | `layer.remove()` | Destructive; use undo group. |
| Move order | `layer.moveTo(index)` | 1-based. |
| Replace source | `avLayer.replaceSource(newSource, fixExpressions)` | Use `false` unless expression fixing is required. |
| 3D switch | `layer.threeDLayer` | Position dimensions differ for 2D vs 3D. |
| Source item | `avLayer.source` | Only on `AVLayer` subclasses. |

## Property

| Task | API | Notes |
|---|---|---|
| Get property group | `layer.property("ADBE Transform Group")` | Prefer verified matchName. |
| Get property | `group.property("ADBE Position")` | Null-check result. |
| Static value | `property.value` | Read-only snapshot. |
| Set static value | `property.setValue(value)` | Avoid on keyframed properties. |
| Value at time | `property.valueAtTime(time, preExpression)` | `time` in seconds. |
| Can animate | `property.canVaryOverTime` | Check before keyframing unknown props. |
| Value type | `property.propertyValueType` | Use to avoid wrong value shape. |

## Keyframe

| Task | API | Notes |
|---|---|---|
| Key count | `property.numKeys` | Key indexes are 1-based. |
| Add/set at time | `property.setValueAtTime(time, value)` | Creates key if needed. |
| Key time | `property.keyTime(keyIndex)` | 1-based. |
| Key value | `property.keyValue(keyIndex)` | 1-based. |
| Remove key | `property.removeKey(keyIndex)` | Remove from highest index downward. |
| Interpolation | `property.setInterpolationTypeAtKey(index, inType, outType)` | Use `KeyframeInterpolationType.*`. |

## Text

| Task | API | Notes |
|---|---|---|
| Create text layer | `comp.layers.addText(text)` | Returns `TextLayer`. |
| Source Text property | `layer.property("ADBE Text Properties").property("ADBE Text Document")` | Verified matchName path. |
| Read text doc | `sourceText.value` | Returns `TextDocument`. |
| Write text doc | `sourceText.setValue(textDoc)` | Required after edits. |
| Text fields | `textDoc.text`, `textDoc.fontSize`, `textDoc.fillColor` | Availability varies by AE version for newer fields. |

## Footage / Import

| Task | API | Notes |
|---|---|---|
| File object | `new File(path)` | Use forward slashes or escaped backslashes. |
| Import options | `new ImportOptions(file)` | Check `file.exists`. |
| Import as | `importOptions.importAs = ImportAsType.FOOTAGE` | Use `canImportAs()` for PSD/AI comp imports. |
| Image sequence | `importOptions.sequence = true` | Sequence edge cases need testing. |
| Replace source | `layer.replaceSource(footageItem, false)` | Requires selected `AVLayer`. |

## Render Queue

| Task | API | Notes |
|---|---|---|
| Add comp | `app.project.renderQueue.items.add(comp)` | Returns `RenderQueueItem`. |
| Output module | `rqItem.outputModule(1)` | 1-based. |
| Output file | `outputModule.file = new File(path)` | File path only; folder must exist. |
| Apply template | `rqItem.applyTemplate(name)`, `outputModule.applyTemplate(name)` | Template names vary by version/language. |
| Render | `app.project.renderQueue.render()` | Blocks until complete. |

