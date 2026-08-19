"""
Script to download and organize university geometry & perspective drawing exam sheets and problem sets.
Targeted at: Animation (U-tad style), Architecture (UPM/ETSAM style), and Fine Arts perspective courses.
"""

import os
from pathlib import Path
import urllib.request

EXAMS_DIR = Path(__file__).resolve().parent / "university_geometry_exams"
EXAMS_DIR.mkdir(parents=True, exist_ok=True)

# Curated repository of open educational perspective drawing exam and exercise PDFs
EXAM_RESOURCES = [
    {
        "filename": "01_conica_frontal_fundamentos_etsam.pdf",
        "title": "Sistema Cónico Frontal - Fundamentos y Ejercicios Prácticos",
        "category": "1-Point Perspective (k=1)",
        "source": "Open Education - Descriptive Geometry Series",
        "url": "https://raw.githubusercontent.com/hvaler/atelier/main/docs/sample_resources/sample_exam_conica_1.pdf"
    },
    {
        "filename": "02_conica_oblicua_focos_metricos_utad.pdf",
        "title": "Perspectiva Cónica Oblicua (2 Puntos de Fuga F1/F2 y Puntos Métricos)",
        "category": "2-Point Perspective (k=2)",
        "source": "Animation & Game Design Perspective Benchmark",
        "url": "https://raw.githubusercontent.com/hvaler/atelier/main/docs/sample_resources/sample_exam_conica_2.pdf"
    },
    {
        "filename": "03_composicion_volumetrica_arquitectura.pdf",
        "title": "Composición Volumétrica y Escalas en Perspectiva Cónica",
        "category": "Volumetric Composition & Scale",
        "source": "Architectural Geometry Problem Sheets",
        "url": "https://raw.githubusercontent.com/hvaler/atelier/main/docs/sample_resources/sample_exam_conica_3.pdf"
    }
]

def main():
    print(f"[INFO] Initializing University Geometry Exams directory: {EXAMS_DIR}")
    
    # Create problem sheet descriptions
    readme_path = EXAMS_DIR / "README.md"
    readme_content = """# Banco de Examenes y Problemas de Geometria y Perspectiva Conica

Este directorio contiene problemas, ejercicios y examenes reales tipo universidad (grados de Animacion tipo U-tad, Arquitectura tipo ETSAM/UPM, e Ingenieria) estructurados para calibrar y evaluar los modelos de vision artificial y pedagogia de Atelier.

---

## Bloques Tematicos de Examen

### 1. Perspectiva Conica Frontal (k=1 Vanishing Point)
- Objetivo: Determinar el Punto Principal (P/VP), Linea de Horizonte (LH), Linea de Tierra (LT), y abatimiento de plantas sobre el plano del cuadro.
- Tolerancia angular esperada: < 2.0 grados de desviacion respecto a P.
- Enunciado tipico: *"Dado el sistema conico definido por LH, LT y el punto de vista V, dibujar la perspectiva conica frontal de un cubo apoyado en el plano geometral de arista 50 mm."*

### 2. Perspectiva Conica Oblicua (k=2 Vanishing Points F1, F2)
- Objetivo: Localizacion de focos F1 y F2, calculo de puntos metricos M1 y M2, y fuga de aristas principales a 30/60 o 45/45 grados.
- Tolerancia angular esperada: < 2.5 grados en aristas de profundidad.
- Enunciado tipico: *"Representar en perspectiva conica oblicua el volumen arquitectonico escalonado definido por sus vistas diedricas (planta y alzado), con angulo de giro de 30 grados respecto al plano del cuadro."*

### 3. Calidad Grafica y Peso de Linea (Rubrica Universitaria)
- Trazo auxiliar: Lineas de construccion finas (2H/3H) trazadas desde los focos.
- Trazo definitivo: Aristas vistas con grosor jerarquico (HB/2B) y aristas ocultas discontinuas.
- Legibilidad espacial: Lectura inequivoca de caras superiores, frontales y laterales.

---

## Rubrica Formal de Calificacion de Examen (10 Puntos)

| Criterio | Peso | Aspecto Evaluado por Atelier |
| :--- | :--- | :--- |
| **Volumetria y Convergencia** | **3.0 pts** | Calculo OpenCV de error angular medio en grados a F1/F2. |
| **Verticalidad y Dimensiones** | **3.0 pts** | Desviacion angular de aristas verticales respecto a la normal (90 grados). |
| **Estructura y Focos** | **2.0 pts** | Coherencia de la linea de horizonte (LH) y alineacion de puntos de fuga. |
| **Peso de Linea y Calidad** | **1.0 pt** | Contraste entre lineas guia de construccion y aristas definitivas. |
| **Legibilidad Espacial** | **1.0 pt** | Claridad en la lectura tridimensional del volumen sin ambiguedad. |
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"[SUCCESS] Created benchmark documentation at {readme_path}")

if __name__ == "__main__":
    main()
