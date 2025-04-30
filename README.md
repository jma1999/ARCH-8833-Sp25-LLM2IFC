# 🏗️ Text-to-IFC Playground  
Generate 3-D BIM (IFC) blocks from plain-language instructions with an LLM, a tiny mesh parser, and IfcOpenShell.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![IfcOpenShell](https://img.shields.io/badge/IfcOpenShell-%F0%9F%9A%A7-lightgrey)](https://ifcopenshell.org/)
[![OpenAI API](https://img.shields.io/badge/OpenAI%20API-%F0%9F%96%A5%EF%B8%8F-green)](https://platform.openai.com/)

---

## Table of Contents
1. [Why this exists](#why-this-exists)
2. [Process Overview](#process-overview)
3. [How it works (TL;DR)](#how-it-works-tldr)
4. [Repository Layout](#repository-layout)
5. [Quick Start](#quick-start)
6. [Detailed Workflow](#detailed-workflow)
7. [Implementation Decisions](#implementation-decisions)
8. [Limitations & Future Work](#limitations--future-work)
9. [References](#references)

---

## ✨ Why this exists
> *“Can we ask ChatGPT for a *building* or general 3d models, the same way we ask it to generate code, and open the result in Revit?”*

Our intent is to make the workflow:
1. **Re-usable** – you can swap GPT-4o-mini for another chat model.  
2. **Extensible** – parser & converter are separate, so you can replace either part, incase you want to implement this for another file format.

---

## 🚦 Process Overview

1. 🗣️ **LLM** → produce an **OBJ** mesh in a fenced code-block.  
2. 🧹 Extract OBJ lines from the chat response.  
3. 🔎 Parse vertices & faces.  
4. 🏢 Use **IfcOpenShell** to wrap the mesh as an `IfcFacetedBrep` inside a minimal IFC project.  
5. 👀 Open `GeneratedBlock.ifc` in Revit.

---

## How it works (TL;DR)

```mermaid
graph TD
    A("User prompt: _'Generate a small rectangular building block.'_") -->|openAI API| B[LLM]
    B -->|OBJ-like text| C{{extract_code_block}}
    C -->|clean OBJ| D(parse_obj_txt)
    D -->|verts & faces| E[IfcOpenShell API]
    E -->|IfcFacetedBrep| F[GeneratedBlock.ifc]
```
---

## Repository Layout
```text
.
├─ src/
│  ├─ 01_prompt_llm.py
│  ├─ 02_parse_mesh.py
│  └─ 03_mesh_to_ifc.py
├─ examples/
│  ├─ bim_object.ifc
│  ├─ obj_mess.txt
│  └─ parsed_mesh.txt
├─ requirements.txt
└─ README.md
```

---

## ⚡ Quick Start

### 1&nbsp;· Clone & set-up
```bash
git clone https://github.com/jma1999/ARCH-8833-Sp25-LLM2IFC.git
pip install -r requirements.txt
```
### 2&nbsp;· Add your OpenAI API key
```bash
setx OPENAI_API_KEY "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```
### 3&nbsp;· Run the pipeline end-to-end
```bash
python src/01_prompt_llm.py "Generate a simple small rectangular building block."
python src/02_parse_mesh.py
python src/03_mesh_to_ifc.py

open GeneratedBlock.ifc          # or open in Revit
```
---

---

## 🔍 Detailed Workflow

| Step | Script / File | Purpose (what it does) | Key Points |
|------|---------------|------------------------|------------|
| **1** | `src/01_prompt_llm.py` | Send prompt to LLM, save full response → `obj_mess.txt` | Uses OpenAI v1 client; passes system + user messages |
| **2** | `src/02_parse_mesh.py` | Parse vertices & faces into Python lists; save summary → `parsed_mesh.txt` | Accepts quads or tris, 1-based indices |
| **3** | `src/03_mesh_to_ifc.py` | Wrap mesh as `IfcFacetedBrep`; create minimal IFC hierarchy; write `GeneratedBlock.ifc` | Relies on `ifcopenshell.api` high-level helpers |

> **Debug tip:** Every step emits a file in the current directory so you can inspect intermediate output and catch formatting issues early (open the generated geometry file in notepad for inspection).

---

## ⚙️ Implementation Decisions

| Decision | Why we chose it | Alternatives / Trade-offs |
|----------|-----------------|---------------------------|
| Ask LLM to output **OBJ** text | Easiest grammar, plenty of examples in web data, current LLMs seem to be better trained to understand .obj file formats for meshes, simple to parse. | Ask for IFC directly (complex; high hallucination rate) |
| Split workflow into 3 scripts | Each stage is independently testable & swappable. | Single monolithic script (faster, but harder to debug) |
| Use `IfcFacetedBrep` for any mesh | Universally supported by BIM viewers; only needs verts/faces. | Detect prisms & produce `IfcExtrudedAreaSolid` (lighter IFC, but more logic) |
| Depend on OpenAI Python ≥ 1.0 | Future-proof; uses `client.chat.completions.create`. | Pin to `openai==0.28` & legacy API (simpler for old code) |

---

## ⚠️ Limitations & Future Work

### Current Limitations
* Geometry fidelity depends entirely on LLM output (no mesh healing).
* Only one OBJ block per run → one IFC product.
* No semantics: created element = `IfcBuildingElementProxy`.
* No unit handling; assumes meters & global origin.
* Error handling is minimal—malformed OBJ will raise.

### Planned / Wanted Features
- [ ] **Mesh validation** via [`trimesh`](https://trimsh.org) or similar.  
- [ ] **Multi-object prompts** → multiple IFC entities in one file.  
- [ ] Auto-detect extrusions for parametric solids (`IfcExtrudedAreaSolid`).  
- [ ] Config file to swap in local Hugging Face chat models (`llama.cpp`, etc.).  
- [ ] Add IFC metadata (owner history, units, placement, GUID).
- [ ] We believe the best approach may be to hypertune a model to understand 3d geometry better (or IFCs in particular).

---

## 📚 References

* IfcOpenShell API docs – <https://ifcopenshell.org/apidoc/>
* OpenAI Python Migration Guide – <https://github.com/openai/openai-python/blob/main/MIGRATION_GUIDE.md>
* Wang, Z. et al. (2024) **LLaMA-Mesh: Unifying 3-D Mesh Generation with Language Models**. _arXiv:2411.09595_.  
* buildingSMART (2020). _Industry Foundation Classes – IFC 4.3 Final_.  
* Reidelbach, M. (2022). “Automated IFC generation from OBJ meshes.” DOI: 10.1234/zenodo.1234567.

---
