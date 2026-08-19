# 📋 Enunciados y Criterios de Examen de Geometría Universitaria

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
