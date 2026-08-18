# Atelier — 3-Minute Timed Demo Video Script

> **Target Duration**: Exactly 3:00 (180 seconds)  
> **Speaker**: Hugo Valer  
> **Structure**: 3 Acts (1. The Problem & Vision; 2. The Live Magic & Multimodal UX; 3. Under the Hood & Future)

---

### ⏱️ Act 1: The Problem & The Core Invariant (0:00 - 0:45)

**[Visual: Camera on speaker, holding tester's sketchbook with a drawn cube; then screen share on Atelier Studio]**

> *"Hi everyone, I'm Hugo. When our youngest tester (age 9, drawings used with permission) started practicing 3D perspective boxes, she ran into a classic problem every remote art student faces: you know your box looks slightly deformed or 'off', but you cannot see the invisible 4-degree angle error causing it.*  
>  
> *If you ask standard AI chatbots, they hallucinate visual measurements. That's why we created **Atelier** around one golden architectural invariant:*  
>  
> ***'The geometry measures, the AI teaches, the student grows.'***  
>  
> *Atelier pairs deterministic OpenCV computer vision with Gemini on Google Cloud Vertex AI to deliver empathetic, zero-hallucination studio master tutoring."*

---

### ⏱️ Act 2: Live Demo — The 4 Verbs in Action (0:45 - 2:05)

**[Visual: Screen recording of `Atelier.Web` UI]**

> **1. Multi-Student & Level-Aware Switching (0:45 - 1:00)**  
> *"Here in the Studio Workspace, Atelier supports independent students from day one. Let's start with our 9-year-old beginner. Notice how Atelier begins by **ASKING** clarifying questions before analyzing: 'What kind of 3D box were you practicing today? Which corner felt hardest?'"*  
>  
> **2. The Multimodal Overlay — The Star Experience (1:00 - 1:30)**  
> *"When we analyze the drawing, the OpenCV engine deskews the notebook, runs RANSAC clustering, detects the exact vanishing point on the horizon, and measures convergence error per line in degrees.*  
>  
> *Look at our **Multimodal Overlay**: with one click, we toggle between the original student sketch, the color-coded annotated overlay (green for accurate lines, yellow for slight drift, red for diverging lines), and a side-by-side comparison.*  
>  
> *Now check out the **Two-Plane Critique**: Plane A shows strictly measured findings with zero hallucinations. Plane B delivers qualitative studio master feedback on line weight and spatial depth, speaking to the beginner in gentle, encouraging language!"*  
>  
> **3. Feedback Capture & Dynamic Adaptation (1:30 - 2:05)**  
> *"Next, we **CAPTURE** student feedback. She clicks 'Helpful 👍'. Atelier immediately **ADAPTS** her learning profile in an append-only Firestore store.*  
>  
> *If we switch to Sofia—an advanced animation university student—Atelier instantly shifts vocabulary to technical studio terms: Line of Horizon ($LH$), Ground Line ($LT$), $F_1/F_2$ convergence, and true magnitude dimensions! In the **Progression Tab**, we can see Sofia's angular error dropping from 4.8° down to 1.8° across sessions, alongside her weekly practice plan generated automatically by Cloud Scheduler."*

---

### ⏱️ Act 3: Under the Hood, Google Cloud Stack & Wrap-up (2:05 - 3:00)

**[Visual: Architecture diagram slide and GitHub repository overview]**

> *"Under the hood, Atelier is built with:*  
> - *A **Gemma** pre-router on Vertex AI for cheap drawing classification.*  
> - ***Gemini Flash** for level-aware pedagogical critiques.*  
> - *An **Anti-Hallucination Validator** that guarantees metrics integrity.*  
> - ***Google Cloud Run** running our .NET 10 Blazor frontend and Python microservices.*  
> - ***Google Cloud Storage + Eventarc** for background photo ingestion, and **Cloud Scheduler** for weekly progress digests.*  
>  
> *The entire codebase is open-source, fully tested with 26 Python tests and 7 .NET integration tests, and deployed to Cloud Run.*  
>  
> *Atelier makes invisible perspective errors visible, empowering art students everywhere to grow with confidence. Thank you!"*
