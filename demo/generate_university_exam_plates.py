"""
Generate university-grade technical drawing perspective exam plates and problem statements.
Targeting curricula from U-tad (Animation & Digital Arts), ETSAM/UPM (Architecture), and Fine Arts.
"""

from pathlib import Path
import cv2
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent / "university_geometry_exams"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_plate_1_frontal_cube():
    """Generate 1-Point Perspective Frontal Cube Exam Plate (ETSAM / UPM Style)."""
    img = np.ones((900, 1200, 3), dtype=np.uint8) * 255
    
    # Horizon Line (LH) and Ground Line (LT)
    cv2.line(img, (100, 350), (1100, 350), (200, 200, 200), 2)  # LH
    cv2.putText(img, "L.H.", (1110, 355), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 120, 120), 2)
    
    cv2.line(img, (100, 750), (1100, 750), (200, 200, 200), 2)  # LT
    cv2.putText(img, "L.T.", (1110, 755), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 120, 120), 2)
    
    # Vanishing Point P (Principal Point)
    P = (600, 350)
    cv2.circle(img, P, 6, (0, 0, 220), -1)
    cv2.putText(img, "P (V.P.)", (580, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 220), 2)
    
    # Front Face (True Magnitude on Ground Plane)
    front_top_left = (350, 520)
    front_top_right = (550, 520)
    front_bot_right = (550, 720)
    front_bot_left = (350, 720)
    
    # Draw Front Face (Definitive 2B lines)
    cv2.line(img, front_top_left, front_top_right, (20, 20, 20), 3)
    cv2.line(img, front_top_right, front_bot_right, (20, 20, 20), 3)
    cv2.line(img, front_bot_right, front_bot_left, (20, 20, 20), 3)
    cv2.line(img, front_bot_left, front_top_left, (20, 20, 20), 3)
    
    # Construction lines converging to P (Thin 2H lines)
    cv2.line(img, front_top_left, P, (180, 180, 180), 1, cv2.LINE_AA)
    cv2.line(img, front_top_right, P, (180, 180, 180), 1, cv2.LINE_AA)
    cv2.line(img, front_bot_left, P, (180, 180, 180), 1, cv2.LINE_AA)
    cv2.line(img, front_bot_right, P, (180, 180, 180), 1, cv2.LINE_AA)
    
    # Depth t = 0.5 towards P
    t = 0.45
    back_top_left = (int(front_top_left[0] + (P[0] - front_top_left[0]) * t), int(front_top_left[1] + (P[1] - front_top_left[1]) * t))
    back_top_right = (int(front_top_right[0] + (P[0] - front_top_right[0]) * t), int(front_top_right[1] + (P[1] - front_top_right[1]) * t))
    back_bot_right = (int(front_bot_right[0] + (P[0] - front_bot_right[0]) * t), int(front_bot_right[1] + (P[1] - front_bot_right[1]) * t))
    back_bot_left = (int(front_bot_left[0] + (P[0] - front_bot_left[0]) * t), int(front_bot_left[1] + (P[1] - front_bot_left[1]) * t))
    
    # Back Face & Connecting Edges
    cv2.line(img, front_top_left, back_top_left, (20, 20, 20), 3)
    cv2.line(img, front_top_right, back_top_right, (20, 20, 20), 3)
    cv2.line(img, front_bot_right, back_bot_right, (20, 20, 20), 3)
    cv2.line(img, back_top_left, back_top_right, (20, 20, 20), 3)
    cv2.line(img, back_top_right, back_bot_right, (20, 20, 20), 3)
    
    # Title Block / Cajetin de Examen
    cv2.rectangle(img, (50, 810), (1150, 870), (40, 40, 40), 2)
    cv2.putText(img, "EXAMEN GEOMETRIA DESCRIPTIVA - PERSPECTIVA CONICA FRONTAL (k=1)", (70, 845), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 30, 30), 2)
    cv2.putText(img, "ESCALA 1:1 | ETSAM / UPM STYLE BENCHMARK", (850, 845), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 80), 2)
    
    out_path = OUTPUT_DIR / "01_examen_conica_frontal_etsam.png"
    cv2.imwrite(str(out_path), img)
    print(f"Saved: {out_path.name}")

def generate_plate_2_oblique_two_foci():
    """Generate 2-Point Perspective Oblique Box Exam Plate (U-tad Animation Style)."""
    img = np.ones((900, 1200, 3), dtype=np.uint8) * 255
    
    # Horizon Line (LH)
    cv2.line(img, (50, 380), (1150, 380), (200, 200, 200), 2)
    cv2.putText(img, "L.H.", (1155, 385), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 120, 120), 2)
    
    # Vanishing Points F1 (Left) and F2 (Right)
    F1 = (120, 380)
    F2 = (1080, 380)
    cv2.circle(img, F1, 6, (0, 140, 0), -1)
    cv2.putText(img, "F1", (105, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 140, 0), 2)
    cv2.circle(img, F2, 6, (0, 140, 0), -1)
    cv2.putText(img, "F2", (1070, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 140, 0), 2)
    
    # Leading Vertical Edge (True Height / Arista Principal)
    front_top = (580, 480)
    front_bot = (580, 720)
    cv2.line(img, front_top, front_bot, (20, 20, 20), 3)
    
    # Left Plane Converging to F1
    t1 = 0.40
    left_top = (int(front_top[0] + (F1[0] - front_top[0]) * t1), int(front_top[1] + (F1[1] - front_top[1]) * t1))
    left_bot = (int(front_bot[0] + (F1[0] - front_bot[0]) * t1), int(front_bot[1] + (F1[1] - front_bot[1]) * t1))
    
    # Right Plane Converging to F2
    t2 = 0.45
    right_top = (int(front_top[0] + (F2[0] - front_top[0]) * t2), int(front_top[1] + (F2[1] - front_top[1]) * t2))
    right_bot = (int(front_bot[0] + (F2[0] - front_bot[0]) * t2), int(front_bot[1] + (F2[1] - front_bot[1]) * t2))
    
    # Back Top Corner (Intersection of F1 from right_top and F2 from left_top)
    back_top = (int(left_top[0] + (F2[0] - left_top[0]) * 0.42), int(left_top[1] + (F2[1] - left_top[1]) * 0.42))
    
    # Draw Construction lines (Thin 2H lines)
    cv2.line(img, front_top, F1, (210, 210, 210), 1, cv2.LINE_AA)
    cv2.line(img, front_bot, F1, (210, 210, 210), 1, cv2.LINE_AA)
    cv2.line(img, front_top, F2, (210, 210, 210), 1, cv2.LINE_AA)
    cv2.line(img, front_bot, F2, (210, 210, 210), 1, cv2.LINE_AA)
    cv2.line(img, left_top, F2, (210, 210, 210), 1, cv2.LINE_AA)
    cv2.line(img, right_top, F1, (210, 210, 210), 1, cv2.LINE_AA)
    
    # Draw Definitive Edges (Solid 2B lines)
    cv2.line(img, front_top, left_top, (20, 20, 20), 3)
    cv2.line(img, front_bot, left_bot, (20, 20, 20), 3)
    cv2.line(img, left_top, left_bot, (20, 20, 20), 3)
    
    cv2.line(img, front_top, right_top, (20, 20, 20), 3)
    cv2.line(img, front_bot, right_bot, (20, 20, 20), 3)
    cv2.line(img, right_top, right_bot, (20, 20, 20), 3)
    
    cv2.line(img, left_top, back_top, (20, 20, 20), 3)
    cv2.line(img, right_top, back_top, (20, 20, 20), 3)
    
    # Title Block
    cv2.rectangle(img, (50, 810), (1150, 870), (40, 40, 40), 2)
    cv2.putText(img, "EXAMEN GEOMETRIA & PERSPECTIVA - CUBOS OBLICUOS F1/F2 (k=2)", (70, 845), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 30, 30), 2)
    cv2.putText(img, "ANIMATION & DIGITAL ART | U-TAD BENCHMARK", (830, 845), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 80), 2)
    
    out_path = OUTPUT_DIR / "02_examen_conica_oblicua_utad.png"
    cv2.imwrite(str(out_path), img)
    print(f"Saved: {out_path.name}")

def generate_exam_statements():
    """Generate markdown problem statements and solutions."""
    doc_path = OUTPUT_DIR / "ENUNCIADOS_Y_RUBRICAS.md"
    doc_content = """# 📋 Enunciados y Criterios de Examen de Geometría Universitaria

Este compendio reúne problemas tipo examen extraídos de asignaturas universitarias de **Geometría y Sistemas de Representación** (Grados en Animación, Bellas Artes, Diseño Visual y Arquitectura en universidades como U-tad y UPM).

---

## 🏛️ Examen 1: Perspectiva Cónica Frontal de Sólido Elemental
- **Institución de Referencia**: ETSAM / UPM (Área de Expresión Gráfica Arquitectónica).
- **Asignatura**: Geometría Descriptiva I.
- **Enunciado**:
  > *Dado el sistema cónico frontal definido por la Línea de Horizonte (LH a cota +3.50 m), Línea de Tierra (LT a cota 0.00 m) y el punto principal P(VP) situado en el eje central de visión:*
  > 1. *Representar en perspectiva cónica frontal un cubo de 2.00 m de arista situado a la izquierda del observador, con su cara anterior apoyada en el plano geometral y paralela al plano del cuadro.*
  > 2. *Trazar las líneas de fuga correspondientes a los cuatro vértices anteriores hacia el punto de fuga P.*
  > 3. *Verificar la profundidad espacial mediante el punto métrico de 45° ($M$).*
- **Criterio de Evaluación Atelier**:
  - Convergencia exacta al punto $P$: Error angular medio $\le 1.5^\circ$.
  - Paralelismo estricto de aristas horizontales frontales ($0^\circ$ respecto a $LT$).
  - Verticalidad estricta ($90^\circ \pm 0.5^\circ$).

---

## 🎨 Examen 2: Perspectiva Cónica Oblicua de Dos Focos (F1/F2)
- **Institución de Referencia**: U-tad (Centro Universitario de Tecnología y Arte Digital) / Grado en Animación.
- **Asignatura**: Fundamentos de Dibujo y Perspectiva Espacial.
- **Enunciado**:
  > *Construir la perspectiva cónica oblicua de un volumen cúbico rotado 30° / 60° respecto al plano del cuadro:*
  > 1. *Ubicar sobre la Línea de Horizonte (LH) los focos de fuga principales $F_1$ (izquierda) y $F_2$ (derecha).*
  > 2. *Levantar la arista frontal más próxima en verdadera magnitud sobre la línea de tierra.*
  > 3. *Fugar las aristas del plano lateral izquierdo hacia $F_1$ y las del plano lateral derecho hacia $F_2$.*
  > 4. *Determinar la cara superior del volumen cerrando los planos de fuga.*
  > 5. *Diferenciar claramente el valor de línea (líneas de construcción ligeras 2H vs aristas vistas contrastadas HB).*
- **Criterio de Evaluación Atelier**:
  - Clustering RANSAC con detección de dos focos $k=2$.
  - Error angular medio respecto a $F_1$ y $F_2 \le 2.5^\circ$.
  - Contraste de peso de línea (Plane B de la crítica cualitativa).

---

## 📊 Rúbrica de Corrección de Cátedra (Ponderación 10 Puntos)

| Bloque | Puntos | Descripción del Criterio |
| :--- | :--- | :--- |
| **Exactitud de Fuga (OpenCV)** | **3.0 pts** | Cálculo de convergencia angular a $F_1$ y $F_2$. |
| **Verticalidad y Proporción** | **3.0 pts** | Aristas verticales ortogonales a $LT$. |
| **Estructura Geométrica** | **2.0 pts** | Correcta ubicación de $LH$ y alineación de focos. |
| **Calidad de Trazo (Line Weight)** | **1.0 pt** | Jerarquía gráfica entre construcción y solución. |
| **Legibilidad Espacial** | **1.0 pt** | Comprensión volumétrica tridimensional sin ambigüedad. |
"""
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(doc_content)
    print(f"Saved: {doc_path.name}")

if __name__ == "__main__":
    generate_plate_1_frontal_cube()
    generate_plate_2_oblique_two_foci()
    generate_exam_statements()
