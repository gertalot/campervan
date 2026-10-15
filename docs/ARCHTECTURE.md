# Campervan CAD — Project Specification

## 1. Project Overview

Build a fully parametric, code-driven 3D CAD system for designing a campervan interior.

The system replaces the existing Onshape + FeatureScript + MCP workflow with a completely local, open-source architecture based on:

- **build123d** — Parametric 3D CAD modelling using Python.
- **OCP CAD Viewer (standalone)** — Interactive browser-based 3D visualization.
- **FastAPI** — Backend API for parameters, configurations, model execution and metadata.
- **Custom web frontend** — Parameter controls, configuration presets, component visibility and manufacturing information.
- **OpenAI Codex** — AI-assisted development and modification of the CAD model and application.

The primary workflow is conversational CAD development:

1. The user describes a desired modification to Codex.
2. Codex modifies the Python CAD source code.
3. Codex executes the updated model.
4. The running browser-based OCP CAD Viewer displays the new geometry.
5. The user inspects the result by rotating, panning and zooming.
6. The process repeats.

**Live updating means the viewer automatically displays the latest successfully generated model after code execution. Continuous rendering while Codex generates code is NOT required.**

The system must not depend on proprietary CAD services, paid CAD APIs, cloud geometry processing, or API usage quotas.

All modelling and rendering should run locally.

---

## 2. Existing System

### 2.1 Current Technology

The existing campervan model is implemented using:

- Onshape Free
- FeatureScript
- FeatureScript MCP
- OpenAI Codex

Codex currently creates and modifies FeatureScript code through MCP.

The model is displayed interactively in Onshape.

### 2.2 Reason for Migration

Onshape's free tier has an annual API usage allowance.

MCP operations consume this allowance, making extensive AI-driven modelling impractical.

The existing workflow consumed approximately 25% of the annual allowance in two days.

The replacement must eliminate this dependency entirely.

### 2.3 Existing Model

The current campervan model includes, or is intended to include:

- Campervan floor
- Vehicle interior sides and body geometry
- Side doors and rear doors
- Furniture and cabinetry
- Storage compartments
- Sliding drawers
- Hinged doors and lids
- Slide-out slatted bed
- Bed support structures
- Cushions and mattresses
- Other interior components

The existing model is parametrically generated using FeatureScript.

It supports numerous configurable dimensions and options.

The model supports different physical configurations, including:

- Daytime configuration
- Nighttime configuration
- Bed extended
- Bed retracted
- Drawers extended/retracted
- Doors open/closed
- Lids open/closed
- Selected components shown/hidden

The original FeatureScript implementation is the primary source of design intent for migration.

---

# 3. Project Objectives

## 3.1 Primary Objectives

1. Replace Onshape entirely.
2. Preserve the parametric nature of the existing design.
3. Allow Codex to create, modify and debug the CAD model through Python.
4. Automatically update the interactive 3D viewer after successful model execution.
5. Provide a browser-based interface for configuring model parameters.
6. Support multiple model configurations and component states.
7. Maintain precise, dimensionally accurate CAD geometry.
8. Support future generation of bills of materials and manufacturing cut lists.
9. Operate locally without external CAD APIs.
10. Keep the system simple, lightweight and maintainable.

## 3.2 Explicit Non-Goals

The project does NOT require:

- Onshape compatibility at the API level.
- FeatureScript execution.
- A traditional desktop CAD interface.
- VS Code.
- Jupyter Notebook.
- Jupyter kernels.
- build123d Studio.
- A bundled Python distribution.
- A custom CAD geometry engine.
- Real-time collaborative editing.
- Cloud-based rendering.
- Cloud storage.
- Continuous viewport updates while Codex is generating code.
- A complete CAD sketching interface.
- A general-purpose CAD editor.

The project is a purpose-built, code-driven campervan CAD application.

---

# 4. Technology Stack

## 4.1 CAD Geometry: build123d

Repository:
https://github.com/gumyr/build123d

Documentation:
https://build123d.readthedocs.io/

build123d is a Python-based parametric CAD modelling library built on OpenCascade.

It provides:

- Precise solid geometry
- Boolean operations
- Extrusions
- Fillets and chamfers
- Sketch-based modelling
- Coordinate transformations
- Part composition
- Assemblies
- STEP export
- STL export
- Geometric measurements

All CAD geometry must be generated programmatically.

The Python source files are the authoritative definition of the model.

Generated CAD files are outputs, not primary source files.

### Modelling conventions

Use millimetres as the standard modelling unit.

Use a consistent global coordinate system.

Model convention (preserved from the Onshape model):

- X: Across the vehicle, from the long-bench wall toward the cabinet wall
- Y: Along the vehicle, from the rear doors toward the cab
- Z: Vertical direction

The nominal rear-left floor corner is `(0, 0, 0)`.

Prefer meaningful dimensions and reference positions rather than unexplained numeric constants.

Each physical component should have:

- Stable component identifier
- Human-readable name
- Geometry
- Material
- Manufacturing category
- Relevant dimensions
- Position and orientation
- Visibility state
- Optional manufacturing metadata

Where practical, separate the geometry of a component from its placement.

This allows drawers, lids, doors and bed sections to move without unnecessarily rebuilding their underlying geometry.

---

## 4.2 Visualization: Standalone OCP CAD Viewer

Documentation:
https://bernhard-42.github.io/ocp_viewer_docs/

Installation:
https://bernhard-42.github.io/ocp_viewer_docs/viewers/ocp_viewer/installation/

OCP CAD Viewer provides the interactive 3D visualization environment.

It runs locally and exposes a browser-based viewer.

Required capabilities:

- Rotate
- Pan
- Zoom
- Fit model to viewport
- Display assemblies and multiple components
- Show/hide objects
- Display component names
- Preserve useful visual state between updates where possible
- Refresh the displayed model after successful Python execution

The initial implementation should use the existing standalone OCP viewer.

Do NOT build a custom WebGL renderer.

Do NOT immediately replace OCP Viewer with a custom three-cad-viewer integration.

### Viewer integration

The standalone viewer should run as a separate local service.

The FastAPI frontend may embed it using an iframe.

The CAD execution process sends geometry to the running OCP Viewer using its supported Python API.

The exact integration must follow the installed OCP Viewer version's documented API.

Model execution must trigger viewer updates without requiring:

- A manual browser refresh
- A manual file import
- Restarting the viewer
- Restarting the backend

### Camera state

The desired behaviour is to preserve the user's current camera orientation and zoom when the model updates.

This must be verified against the standalone viewer API.

If necessary, implement camera-state preservation through supported viewer options.

Do not assume that every model update automatically preserves the camera.

---

# 5. Backend: FastAPI

Documentation:
https://fastapi.tiangolo.com/

FastAPI provides the application backend.

Its responsibilities are:

1. Manage model parameters.
2. Manage configuration presets.
3. Trigger model regeneration.
4. Track execution status.
5. Maintain model metadata.
6. Expose component information.
7. Support visibility and positioning controls.
8. Generate BOM data.
9. Generate cut lists.
10. Coordinate updates to OCP Viewer.

The backend must remain independent of the CAD viewer's frontend implementation.

## 5.1 Model Execution

The backend should invoke a dedicated model-building function.

Conceptual interface:

```python
def build_campervan(
    parameters: CampervanParameters,
    configuration: CampervanConfiguration,
) -> CampervanModel:
    ...
```

The function returns a structured model containing:

- CAD geometry
- Component hierarchy
- Component metadata
- Manufacturing metadata
- Configuration state

Avoid generating the entire model as an unstructured collection of anonymous solids.

## 5.2 Execution Isolation

Model execution may be computationally expensive.

Do not execute heavy CAD operations directly on FastAPI's event loop.

Use a dedicated execution worker or subprocess.

Requirements:

- Only one authoritative model-generation job should commit results at a time.
- New parameter changes may supersede obsolete pending jobs.
- Failed executions must not destroy the last successful model.
- Exceptions must be captured and displayed to the user.
- Model execution must not require restarting FastAPI.
- The backend must report whether the current model is building, ready or failed.

For an initial implementation, a simple single-worker process is sufficient.

A distributed job queue is unnecessary.

## 5.3 API Endpoints

Suggested API:

```text
GET    /api/parameters
PUT    /api/parameters

GET    /api/configurations
POST   /api/configurations/apply

GET    /api/components
PATCH  /api/components/{id}

POST   /api/model/rebuild
GET    /api/model/status

GET    /api/bom
GET    /api/cut-list

GET    /api/export/step
GET    /api/export/stl
```

The exact API may evolve during implementation.

Prefer straightforward REST endpoints.

WebSockets are optional for backend status notifications.

The OCP Viewer already provides its own mechanism for receiving geometry updates.

Do not unnecessarily duplicate that transport.

---

# 6. Frontend

## 6.1 General Requirements

Build a lightweight browser-based interface.

The application should have:

- Parameter panel
- Configuration panel
- Component visibility controls
- Large interactive 3D viewport
- Model execution status
- Optional BOM and cut-list panels

The frontend may use React, Vue or lightweight HTML/JavaScript.

Choose the simplest solution that meets the requirements.

Avoid unnecessary frontend frameworks and infrastructure.

## 6.2 Layout

Suggested layout:

```text
+-----------------------------------------------------------+
| Campervan CAD                                             |
+--------------------+--------------------------------------+
| PARAMETERS         |                                      |
|                    |                                      |
| Vehicle            |                                      |
|   Length           |                                      |
|   Width            |                                      |
|                    |                                      |
| Furniture          |                                      |
|   Height           |                                      |
|   Depth            |                                      |
|                    |                                      |
| Bed                |                                      |
|   Width            |                                      |
|   Slat count       |                                      |
|                    |             3D VIEWER                |
+--------------------+                                      |
| CONFIGURATION      |                                      |
|                    |                                      |
| Day / Night        |                                      |
| Bed extension      |                                      |
| Drawer positions   |                                      |
| Door positions     |                                      |
+--------------------+                                      |
| VISIBILITY         |                                      |
|                    |                                      |
| [x] Cushions       |                                      |
| [x] Furniture      |                                      |
| [ ] Van shell      |                                      |
+--------------------+--------------------------------------+
| BOM | Cut List     | Model ready                          |
+-----------------------------------------------------------+
```

The viewport should receive most of the available screen space.

## 6.3 Parameter Controls

Support:

- Numeric inputs
- Checkboxes
- Sliders
- Dropdowns
- Grouped parameters
- Default values
- Minimum and maximum constraints
- Parameter descriptions

The UI should be generated from parameter metadata wherever practical.

Avoid separately hardcoding the same parameter definitions in both Python and JavaScript.

For example:

```python
class ParameterDefinition:
    name: str
    label: str
    type: str
    default: object
    minimum: float | None
    maximum: float | None
    step: float | None
    unit: str | None
    group: str
```

Pydantic models or a schema-driven approach may be used.

The backend remains the authoritative source of parameter definitions and validation.

## 6.4 Parameter Updates

When a user modifies a parameter:

1. The frontend sends the updated value to FastAPI.
2. FastAPI validates the parameter.
3. The new configuration is saved.
4. The model is regenerated.
5. The updated geometry is sent to OCP Viewer.
6. The viewer displays the new model.

Debounce rapidly changing controls to avoid unnecessary CAD recomputations.

For expensive geometry changes, rebuilding on slider release may be preferable to rebuilding on every movement.

---

# 7. Parametric Model Architecture

## 7.1 Parameter Definitions

All configurable dimensions should be centralised.

Example:

```python
from pydantic import BaseModel, Field


class CampervanParameters(BaseModel):
    van_length: float = Field(default=2850, gt=0)
    van_width: float = Field(default=1750, gt=0)

    floor_thickness: float = Field(default=18, gt=0)

    furniture_height: float = Field(default=730, gt=0)
    furniture_depth: float = Field(default=500, gt=0)

    plywood_thickness: float = Field(default=15, gt=0)

    bed_width: float = Field(default=1200, gt=0)
    bed_slat_count: int = Field(default=14, ge=1)
```

These are illustrative values only.

Actual values must be migrated from the existing FeatureScript implementation.

No dimensions should be invented during migration when existing values are available.

## 7.2 Derived Dimensions

Derived dimensions should be calculated from primary parameters.

Example:

```python
internal_width = (
    parameters.van_width
    - 2 * wall_clearance
)
```

Maintain a clear distinction between:

- User-configurable parameters
- Derived dimensions
- Component placement calculations
- Manufacturing tolerances

Avoid duplicating derived calculations across components.

## 7.3 Component Modularity

Each significant component should have a dedicated Python module.

For example:

```text
cad/
    floor.py
    vehicle_shell.py
    furniture.py
    drawers.py
    bed.py
    doors.py
    cushions.py
```

Each module should expose functions that create its geometry.

Example:

```python
def create_floor(parameters) -> Component:
    ...

def create_drawer(parameters, drawer_config) -> Component:
    ...

def create_bed(parameters, bed_config) -> Component:
    ...
```

Components should use stable identifiers so they can be tracked across model regenerations.

---

# 8. Configurations

The model must support multiple physical arrangements without duplicating the underlying design.

## 8.1 Configuration State

Separate configuration state from dimensional parameters.

Example:

```python
from pydantic import BaseModel


class CampervanConfiguration(BaseModel):
    mode: str = "day"

    bed_extension: float = 0.0

    left_drawer_extension: float = 0.0
    right_drawer_extension: float = 0.0

    rear_door_angle: float = 0.0

    show_cushions: bool = True
    show_vehicle_shell: bool = True
    show_furniture: bool = True
```

Extension values should have clearly defined units or normalised ranges.

Angles should use a consistent convention.

## 8.2 Named Presets

Support named configurations such as:

```text
Day
Night
Storage Access
Cooking
All Components
```

Presets should be stored as JSON or another simple local format.

The user should be able to:

- Apply a preset
- Modify individual configuration values
- Save a new preset
- Update an existing preset

## 8.3 Moving Components

Moving components should preferably be implemented through geometric transformations.

Examples:

- Drawer extension: translation along drawer travel axis
- Bed extension: translation of moving bed elements
- Hinged door: rotation around hinge axis
- Lid opening: rotation around hinge axis

Avoid rebuilding component geometry merely to change its position when a transformation is sufficient.

## 8.4 Visibility

Visibility should be managed independently of geometry wherever possible.

Hiding cushions should not require rebuilding the cushions.

The model should retain stable object identifiers to support component-level visibility.

Initial visibility implementation may use viewer-side object controls.

The custom frontend can later expose those controls through its own interface.

---

# 9. Component Data Model

The CAD geometry must be associated with structured component metadata.

Conceptual structure:

```python
@dataclass
class Component:
    id: str
    name: str

    geometry: object

    material: str | None
    category: str

    visible: bool

    metadata: dict
```

The actual implementation may use dataclasses, Pydantic models or other suitable structures.

A component may contain subcomponents.

For example:

```text
Campervan
├── Vehicle Shell
├── Floor
├── Left Furniture
│   ├── Side Panels
│   ├── Shelves
│   ├── Drawer 1
│   │   ├── Front
│   │   ├── Back
│   │   ├── Left Side
│   │   ├── Right Side
│   │   └── Bottom
│   └── Drawer 2
├── Right Furniture
├── Bed
│   ├── Fixed Frame
│   ├── Sliding Frame
│   └── Slats
└── Cushions
```

Component identifiers must remain stable even when dimensions change.

---

# 10. Bill of Materials

The project must eventually generate a bill of materials directly from model metadata.

Suggested fields:

```text
Part ID
Part Name
Assembly
Material
Quantity
Length
Width
Thickness
Volume
Notes
```

The BOM should distinguish:

- Manufactured wooden parts
- Hardware
- Purchased components
- Cushions and upholstery
- Structural components

Identical manufactured parts should be grouped where appropriate.

Support CSV export initially.

Other formats may be added later.

The BOM must be generated from the authoritative component model rather than manually maintained separately.

---

# 11. Manufacturing Cut Lists

A future cut-list generator should support sheet materials such as plywood.

Required information:

- Part identifier
- Part name
- Material
- Thickness
- Length
- Width
- Quantity
- Grain direction
- Edge treatment
- Manufacturing notes

The system must distinguish finished dimensions from cutting dimensions where necessary.

For rectangular panels, dimensions can be derived from explicit panel metadata.

Do not rely exclusively on world-axis bounding boxes, because rotated parts can produce misleading dimensions.

The component definitions should preserve manufacturing orientation and nominal cut dimensions.

Future enhancements may include:

- Sheet nesting
- Material utilisation
- Kerf allowance
- Edge banding
- CNC exports

These are not required for the initial migration.

---

# 12. Codex Integration

## 12.1 Intended Workflow

Codex is the primary development agent.

It should be able to:

1. Inspect the existing Python CAD code.
2. Modify parameters and geometry.
3. Add components.
4. Refactor the model.
5. Execute model-generation scripts.
6. Detect and correct Python exceptions.
7. Trigger viewer updates.
8. Run automated tests.
9. Generate exports.

No CAD-specific MCP server is required.

Codex works directly with the Python source files and local execution commands.

## 12.2 Development Commands

Provide simple commands for Codex.

For example:

```bash
python -m campervan.build
```

Or:

```bash
make build
```

This command should:

1. Load the current parameters.
2. Load the selected configuration.
3. Generate the build123d model.
4. Validate successful execution.
5. Publish the updated model to OCP Viewer.
6. Report errors if generation fails.

Prefer one clear entry point rather than requiring Codex to understand multiple unrelated execution commands.

## 12.3 Source Code Changes

Codex should modify the source files directly.

FastAPI development auto-reload may be used for application-code changes, but the CAD model must also support explicit rebuilding without restarting the frontend or viewer.

A file watcher may optionally regenerate the model after changes to CAD source files.

This is useful when Codex edits code without explicitly invoking the build command.

However, explicit execution should remain supported.

## 12.4 Error Handling

If model generation fails:

- Retain the last successfully generated model in the viewer.
- Capture the full Python traceback.
- Report the failing component or modelling stage where possible.
- Do not overwrite valid exports with failed outputs.
- Allow Codex to inspect the failure and retry.

---

# 13. Project Directory Structure

Suggested initial layout:

```text
campervan-cad/
│
├── README.md
├── AGENTS.md
├── pyproject.toml
├── Makefile
│
├── src/
│   └── campervan/
│       │
│       ├── __init__.py
│       │
│       ├── app.py
│       ├── build.py
│       │
│       ├── parameters.py
│       ├── configurations.py
│       ├── components.py
│       │
│       ├── cad/
│       │   ├── __init__.py
│       │   ├── assembly.py
│       │   ├── floor.py
│       │   ├── vehicle_shell.py
│       │   ├── furniture.py
│       │   ├── drawers.py
│       │   ├── bed.py
│       │   ├── doors.py
│       │   └── cushions.py
│       │
│       ├── services/
│       │   ├── model_runner.py
│       │   ├── viewer.py
│       │   ├── bom.py
│       │   ├── cut_list.py
│       │   └── exports.py
│       │
│       └── api/
│           ├── parameters.py
│           ├── configurations.py
│           ├── components.py
│           └── model.py
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── config/
│   ├── parameters.json
│   └── presets/
│       ├── day.json
│       └── night.json
│
├── migration/
│   ├── featurescript/
│   ├── parameter_mapping.md
│   ├── component_mapping.md
│   └── migration_notes.md
│
├── exports/
│   ├── step/
│   ├── stl/
│   ├── bom/
│   └── cut_lists/
│
└── tests/
    ├── test_parameters.py
    ├── test_geometry.py
    ├── test_configurations.py
    └── test_components.py
```

Keep the structure pragmatic.

Do not create unnecessary abstractions before they are required.

---

# 14. Migration from Onshape FeatureScript

## 14.1 Migration Strategy

The existing FeatureScript source is the authoritative reference for the current design.

The migration must preserve:

- Parametric dimensions
- Derived calculations
- Geometric relationships
- Component hierarchy
- Feature behaviour
- Configuration logic
- Visibility options
- Moving component behaviour
- Design intent

The goal is to reproduce the existing campervan model using native Python and build123d.

Do NOT attempt to build a general-purpose FeatureScript interpreter.

Do NOT translate FeatureScript syntax mechanically without understanding the geometry.

Use a component-by-component semantic migration.

## 14.2 Required Source Material

Collect the following from Onshape before migration:

1. Complete FeatureScript source code.
2. Current parameter names and values.
3. Parameter types and allowed ranges.
4. Parameter descriptions.
5. Derived dimension calculations.
6. Configuration definitions.
7. Component names and hierarchy.
8. Reference screenshots.
9. Relevant exported STEP files.
10. Known model dimensions and measurements.

Where possible, export a STEP model for each important configuration.

At minimum:

- Day configuration
- Night configuration
- Bed extended
- Bed retracted
- Relevant drawer/door states

These exports provide geometric reference models for validating the Python implementation.

STEP imports should be treated as validation references, not the permanent parametric model.

## 14.3 Phase 1: FeatureScript Analysis

Codex should analyse the FeatureScript source before translating geometry.

Extract:

- All user-facing parameters
- Parameter default values
- Parameter bounds
- Parameter dependencies
- Derived calculations
- Geometry-generating operations
- Component identities
- Transformations
- Conditional geometry
- Visibility logic
- Configuration rules

Document these in:

```text
migration/parameter_mapping.md
migration/component_mapping.md
```

Produce a dependency map showing which parameters affect which components.

Do not begin implementing the full model until the parameter and component structures are understood.

## 14.4 Phase 2: Parameter Migration

Translate FeatureScript parameter definitions into Python models.

Preserve existing parameter names where practical.

Where Python naming conventions require changes, maintain an explicit mapping.

Example:

```text
FeatureScript                 Python

bedWidth                     bed_width
bedLength                    bed_length
plywoodThickness             plywood_thickness
drawerExtension              drawer_extension
showCushions                 show_cushions
```

Preserve the original:

- Default values
- Units
- Limits
- Descriptions
- Dependencies

Verify that derived parameters produce equivalent values.

Unit conversions must be explicit and tested.

## 14.5 Phase 3: Geometry Migration

Translate geometry component by component.

Suggested order:

1. Global coordinate system
2. Floor
3. Vehicle interior reference geometry
4. Fixed furniture
5. Cabinets and shelves
6. Drawers
7. Bed support structure
8. Sliding bed elements
9. Doors and lids
10. Cushions
11. Remaining details

For each component:

1. Identify its FeatureScript construction logic.
2. Identify input parameters.
3. Identify derived dimensions.
4. Implement equivalent build123d operations.
5. Generate the geometry.
6. Display it in OCP Viewer.
7. Compare with the Onshape reference.
8. Add validation tests.
9. Proceed to the next component.

Preserve component identity throughout migration.

Avoid combining all parts into a single Boolean union.

The assembly must retain individual components for visibility, movement, BOM and cut-list generation.

## 14.6 Phase 4: Configuration Migration

Translate the existing Onshape configuration logic into Python.

Separate:

- Dimensional parameters
- Physical configuration state
- Viewer visibility state

Implement the existing configuration presets.

Verify the following behaviours:

- Day/night switching
- Bed extension/retraction
- Drawer movement
- Door movement
- Lid movement
- Cushion visibility
- Furniture visibility
- Vehicle shell visibility

Moving parts must retain correct alignment and relationships.

## 14.7 Phase 5: Geometric Validation

Compare the build123d model against exported Onshape reference geometry.

Validation should include:

- Overall bounding dimensions
- Component dimensions
- Relative component positions
- Component volumes
- Critical clearances
- Alignment of moving components
- Configuration-specific geometry

Where feasible, use OpenCascade geometric comparison operations.

Validation tolerances should be explicitly defined.

Do not require exact binary geometric identity between CAD systems.

The objective is geometrically equivalent parts within appropriate tolerances.

## 14.8 Phase 6: Manufacturing Metadata

Once geometry and configurations are validated:

1. Assign material metadata to components.
2. Identify manufactured versus purchased components.
3. Associate nominal manufacturing dimensions.
4. Assign stable part identifiers.
5. Generate an initial BOM.
6. Generate rectangular panel cut lists.

Manufacturing metadata should be incorporated into the component architecture rather than added as an unrelated external spreadsheet.

## 14.9 FeatureScript Migration Principles

Codex must follow these rules:

- Preserve existing design intent.
- Preserve dimensions unless explicitly instructed otherwise.
- Do not invent missing geometry.
- Do not silently simplify complex features.
- Maintain parametric relationships.
- Identify unsupported or ambiguous FeatureScript operations.
- Prefer readable Python implementations.
- Avoid unnecessary dependence on imported STEP geometry.
- Keep physical parts individually addressable.
- Validate each migrated component.
- Maintain a record of migration discrepancies.

---

# 15. Implementation Phases

## Phase A: Minimal Working Prototype

Goal: Prove the complete local modelling-to-viewer workflow.

Implement:

- Python environment
- build123d installation
- Standalone OCP Viewer
- Simple test geometry
- Model execution command
- Automatic viewer update after execution

Acceptance criteria:

1. Start OCP Viewer.
2. Run a Python CAD script.
3. See the model in the browser.
4. Rotate, pan and zoom.
5. Ask Codex to modify the script.
6. Codex runs the modified script.
7. The existing viewer displays the updated geometry.
8. No browser refresh or manual import is required.

This phase is the highest priority.

Do not proceed with the full application until it works reliably.

## Phase B: FastAPI Integration

Goal: Connect model generation to a browser application.

Implement:

- FastAPI server
- Model execution worker
- Model status endpoint
- Embedded standalone viewer
- Basic parameter form

Acceptance criteria:

Changing a numeric parameter in the frontend regenerates and displays the model.

## Phase C: Parametric Architecture

Goal: Establish the production model structure.

Implement:

- Parameter schemas
- Derived dimensions
- Component data model
- Assembly hierarchy
- Configuration state
- Stable component identifiers

Acceptance criteria:

A multi-component test assembly can be rebuilt from parameters without losing component identity.

## Phase D: FeatureScript Migration

Goal: Reproduce the existing campervan design.

Migrate components incrementally.

Validate against the existing Onshape model.

Acceptance criteria:

Major geometry and configuration states match the existing implementation within agreed tolerances.

## Phase E: Configuration UX

Goal: Reproduce the existing configuration workflow.

Implement:

- Day/night presets
- Visibility controls
- Drawer sliders
- Bed extension controls
- Door/lid controls
- Saved configurations

Acceptance criteria:

All existing important Onshape configurations can be reproduced through the new web interface.

## Phase F: Manufacturing Outputs

Goal: Produce useful manufacturing data.

Implement:

- Component metadata
- BOM
- Panel cut lists
- CSV export
- STEP export

Acceptance criteria:

The model can generate a consistent component list and manufacturing dimensions.

---

# 16. Technical Risks and Design Constraints

## 16.1 Viewer API Compatibility

OCP Viewer APIs may change between versions.

Pin compatible package versions.

Validate the exact standalone viewer API during Phase A.

Avoid relying on undocumented internal interfaces.

## 16.2 Viewer Embedding

Embedding the standalone viewer in an iframe must be tested.

Potential issues include:

- Browser framing restrictions
- WebSocket connectivity
- Different local ports
- Camera state persistence
- Component selection synchronisation

If iframe embedding proves restrictive, the fallback is to integrate three-cad-viewer directly into the frontend.

That fallback is not part of the initial implementation.

## 16.3 Geometry Regeneration Performance

Large parametric assemblies can be expensive to rebuild.

Prefer:

- Modular component generation
- Reuse of unchanged geometry
- Transformations for moving parts
- Debounced parameter updates
- Minimal unnecessary Boolean operations

Optimise only after measuring actual performance.

## 16.4 Code Reloading

Python imports are cached within a running interpreter.

The implementation must ensure Codex's source changes are actually used during regeneration.

A dedicated subprocess for each build is one straightforward solution.

A persistent worker with explicit module reloading is another option, but requires greater care.

Prefer correctness and predictability over premature optimisation.

## 16.5 Model Consistency

Do not publish partially generated or invalid models.

The system should preserve the last successful viewer state if a build fails.

Generated metadata and exports must correspond to the same successful model version.

## 16.6 Camera Preservation

Ideally, a model update should not reset the user's viewpoint.

This behaviour must be explicitly tested.

If supported, disable automatic camera fitting after the initial model display.

## 16.7 Parameter Validation

Invalid dimensions can produce failed or geometrically impossible models.

Validate parameter ranges and cross-parameter constraints before geometry generation.

Report validation errors through FastAPI.

Do not silently clamp values without informing the user.

---

# 17. Development Principles

1. **Python is the source of truth.**

   The parametric CAD source defines the model.

2. **Keep geometry independent of presentation.**

   CAD generation must not depend on the web frontend.

3. **Use existing CAD libraries.**

   Do not implement custom solid modelling or WebGL rendering.

4. **Keep the architecture local.**

   No external CAD services or metered APIs.

5. **Prefer simple interfaces.**

   Avoid unnecessary message brokers, databases and distributed infrastructure.

6. **Preserve component identity.**

   Individual physical parts must remain identifiable.

7. **Separate parameters from configurations.**

   Dimensions and operational states are conceptually different.

8. **Make builds deterministic.**

   The same source, parameters and configuration should produce equivalent geometry.

9. **Make builds repeatable.**

   Codex must be able to execute a single command to regenerate the model.

10. **Prioritise visual feedback.**

    The interactive browser viewer is central to the development workflow.

11. **Preserve manufacturing intent.**

    Components should retain materials, dimensions and identifiers needed for fabrication.

12. **Migrate incrementally.**

    Validate components before implementing subsequent assemblies.

---

# 18. Immediate Next Steps for Codex

Begin with Phase A only.

Tasks:

1. Inspect the Python development environment.
2. Create a project-local Python virtual environment.
3. Install compatible versions of build123d and OCP Viewer.
4. Verify the documented standalone OCP Viewer startup procedure.
5. Start the standalone browser viewer.
6. Create a simple parametric assembly containing several individually named solids.
7. Write a Python entry point that generates and publishes the assembly.
8. Execute the entry point.
9. Confirm that the geometry appears in the running browser viewer.
10. Modify one dimension in the source code.
11. Execute the entry point again.
12. Confirm that the viewer updates without a manual refresh.
13. Confirm that the model remains interactive.
14. Document the exact commands and installed package versions.

Use the official OCP Viewer documentation as the authority for installation and API details:

https://bernhard-42.github.io/ocp_viewer_docs/viewers/ocp_viewer/installation/

Do not build FastAPI, the configuration UI or the complete campervan model until this end-to-end workflow is proven.

After Phase A succeeds, proceed to FastAPI integration.

---

# 19. Definition of Success

The completed system allows the following workflow:

The user opens a local campervan CAD web application.

The application displays a detailed, dimensionally accurate 3D model of the campervan interior.

The user can rotate, pan and zoom freely.

A sidebar provides controls for all important dimensions and configurations.

The user can switch between day and night layouts, extend the bed, open drawers, operate doors and lids, and show or hide components.

Changes to parameters regenerate the appropriate geometry.

Separately, the user can instruct Codex in natural language to modify the model.

Codex edits Python source files and executes the model builder.

The updated geometry appears automatically in the already-open browser viewer.

The user can immediately inspect the result.

All components retain structured identities and manufacturing metadata.

The system can generate bills of materials, woodworking cut lists and CAD exports.

Everything runs locally.

There are no CAD API quotas, no proprietary CAD subscriptions and no dependency on Onshape.

**The primary deliverable is a maintainable, fully parametric, AI-driven campervan CAD application with an interactive browser-based 3D viewer.**
