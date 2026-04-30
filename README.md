# A UAV Dataset for Crop Monitoring, Weed Mapping, and Field Analysis in *Camelina sativa*

<p align="center">
  <b>RGB and multispectral UAV imagery with polygon-based weed annotations for precision agriculture research.</b>
</p>

<p align="center">
  <a href="DATASET_DOWNLOAD_LINK"><b>Dataset</b></a> ·
  <a href="PAPER_LINK"><b>Paper</b></a> ·
  <a href="DOI_LINK"><b>DOI</b></a>
</p>

---

## Overview

This repository provides documentation for a UAV-based dataset collected in *Camelina sativa* fields in Greece.

The dataset includes RGB and multispectral UAV imagery acquired from agricultural fields in Thessaloniki and Chalkidiki during summer 2025 and winter 2025–2026. It contains manually annotated RGB images with polygon-based weed annotations, as well as unannotated RGB images, multispectral images, raw UAV images, and orthomosaic products.

The dataset was created to support research in computer vision, precision agriculture, weed detection, crop monitoring, and field-level analysis under realistic agricultural conditions.

---

## Annotation Preview

<p align="center">
  <img src="figures/Roboflow-Polygons.png" width="45%" alt="Polygon-based weed annotations">
  <img src="figures/Roboflow-labels.png" width="45%" alt="Weed annotation labels">
</p>

<p align="center">
  <i>Examples of polygon-based weed annotations generated in Roboflow. The dataset includes class-specific labels and manually annotated weed instances.</i>
</p>

---


## UAV Data Summary

| Season | Location | Acquisition setting | Annotated | Unannotated | Orthomosaic |
|---|---|---|---:|---:|:---:|
| Summer 2025 | Thessaloniki | Phantom flight at 5 m altitude | 34 | 32 | ✗ |
| Summer 2025 | Thessaloniki | Phantom flight at 10 m altitude | 297 | 46 | ✗ |
| Winter 2025–2026 | Thessaloniki | Phantom flight at 3 m altitude | 17 | 32 | ✗ |
| Winter 2025–2026 | Thessaloniki | Mavic 3M flight 1 at 2 m altitude | 627 | 215 | ✗ |
| Winter 2025–2026 | Thessaloniki | Mavic 3M flight 1 at 2 m altitude MS | — | 842 | ✗ |
| Winter 2025–2026 | Thessaloniki | Mavic 3M flight 2 at 2 m altitude | 47 | 193 | ✗ |
| Winter 2025–2026 | Thessaloniki | Mavic 3M flight 2 at 2 m altitude MS | — | 240 | ✗ |
| Winter 2025–2026 | Thessaloniki | Mavic 3M Orthomosaic 20 m Altitude RGB | — | 227 | ✓ |
| Winter 2025–2026 | Thessaloniki | Mavic 3M Orthomosaic 20 m Altitude MS | — | 908 | ✓ |
| Winter 2025–2026 | Chalkidiki | Phantom flight at 3 m altitude | 43 | 159 | ✗ |
| Winter 2025–2026 | Chalkidiki | Phantom flight at 5 m altitude | 55 | 144 | ✗ |
| Winter 2025–2026 | Chalkidiki | Mavic 3M Orthomosaic 20 m Altitude RGB | — | 1351 | ✓ |
| Winter 2025–2026 | Chalkidiki | Mavic 3M Orthomosaic 20 m Altitude MS | — | 5404 | ✓ |

---

## Dataset Structure

The dataset is organized hierarchically by acquisition season, location, UAV flight/acquisition setting, and data type.

```text
dataset/
├── Summer 2025/
│   └── Thessaloniki/
│       ├── Phantom Flight at 5 m Altitude/
│       │   ├── Annotated/
│       │   │   ├── images/
│       │   │   └── annotations.json
│       │   └── Unannotated/
│       │       └── images/
│       └── ...
│
└── Winter 2025-2026/
    ├── Thessaloniki/
    │   ├── Phantom Flight at 3 m Altitude/
    │   │   ├── Annotated/
    │   │   │   ├── images/
    │   │   │   └── annotations.json
    │   │   └── Unannotated/
    │   │       └── images/
    │   ├── ...
    │   ├── Orthomosaic_RGB.tif
    │   └── Orthomosaic_MS.tif
    │
    └── Chalkidiki/
        ├── Phantom Flight at 3 m Altitude/
        │   ├── Annotated/
        │   │   ├── images/
        │   │   └── annotations.json
        │   └── Unannotated/
        │       └── images/
        ├── ...
        ├── Orthomosaic_RGB.tif
        └── Orthomosaic_MS.tif
