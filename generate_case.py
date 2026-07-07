"""
Генератор корпуса PulmoScan
Создаёт:
  - case_drawing.svg (2D чертёж для вырезания)
  - case_3d.step (3D-модель для печати)
"""

import cadquery as cq
import math

# ==========================================
# ПАРАМЕТРЫ КОРПУСА (можно менять!)
# ==========================================
CASE_LENGTH = 120      # длина корпуса (мм)
CASE_WIDTH = 35        # ширина (мм) 
CASE_HEIGHT = 25       # высота (мм)
WALL_THICKNESS = 2     # толщина стенок (мм)

MIC_HOLE_DIAM = 10     # отверстие под микрофон (мм)
USB_HOLE_WIDTH = 9     # отверстие USB-C (мм)
USB_HOLE_HEIGHT = 4    # высота USB-C (мм)
BUTTON_HOLE_DIAM = 7   # отверстие под кнопку (мм)
LED_HOLE_DIAM = 5      # отверстие под светодиод (мм)

# ==========================================
# 1. ГЕНЕРАЦИЯ SVG-ЧЕРТЕЖА
# ==========================================
def generate_svg():
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <style>
    text {{ font-family: Arial, sans-serif; font-size: 12px; }}
    .dim {{ stroke: #666; stroke-width: 0.5; stroke-dasharray: 4,4; }}
    .cut {{ stroke: #000; stroke-width: 2; fill: none; }}
    .hole {{ stroke: #f00; stroke-width: 1.5; fill: #fee; }}
    .label {{ font-size: 14px; font-weight: bold; fill: #333; }}
  </style>
  
  <!-- Заголовок -->
  <text x="400" y="30" text-anchor="middle" class="label">PULMOSCAN v1.0 — Чертеж корпуса</text>
  <text x="400" y="50" text-anchor="middle">Размеры: {CASE_LENGTH}×{CASE_WIDTH}×{CASE_HEIGHT} мм | Толщина стенки: {WALL_THICKNESS} мм</text>
  
  <!-- Вид сверху -->
  <text x="150" y="90" text-anchor="middle" class="label">ВИД СВЕРХУ</text>
  <rect x="50" y="110" width="{CASE_LENGTH}" height="{CASE_WIDTH}" class="cut"/>
  
  <!-- Отверстие микрофона (сверху, по центру) -->
  <circle cx="{50 + CASE_LENGTH//2}" cy="{110 + CASE_WIDTH//2}" r="{MIC_HOLE_DIAM//2}" class="hole"/>
  <text x="{50 + CASE_LENGTH//2}" y="{110 + CASE_WIDTH//2 + MIC_HOLE_DIAM//2 + 15}" text-anchor="middle">Микрофон ∅{MIC_HOLE_DIAM}мм</text>
  
  <!-- Размеры -->
  <line x1="50" y1="{110 + CASE_WIDTH + 10}" x2="{50 + CASE_LENGTH}" y2="{110 + CASE_WIDTH + 10}" class="dim"/>
  <text x="{50 + CASE_LENGTH//2}" y="{110 + CASE_WIDTH + 25}" text-anchor="middle">{CASE_LENGTH} мм</text>
  
  <!-- Вид сбоку -->
  <text x="550" y="90" text-anchor="middle" class="label">ВИД СБОКУ</text>
  <rect x="450" y="110" width="{CASE_LENGTH}" height="{CASE_HEIGHT}" class="cut"/>
  
  <!-- Отверстие USB (слева) -->
  <rect x="450" y="{110 + CASE_HEIGHT//2 - USB_HOLE_HEIGHT//2}" width="{USB_HOLE_WIDTH}" height="{USB_HOLE_HEIGHT}" class="hole"/>
  <text x="450" y="{110 + CASE_HEIGHT//2 + USB_HOLE_HEIGHT//2 + 12}" text-anchor="middle" font-size="10">USB-C</text>
  
  <!-- Отверстие кнопки (справа) -->
  <circle cx="{450 + CASE_LENGTH - 10}" cy="{110 + CASE_HEIGHT//2}" r="{BUTTON_HOLE_DIAM//2}" class="hole"/>
  <text x="{450 + CASE_LENGTH - 10}" y="{110 + CASE_HEIGHT//2 + BUTTON_HOLE_DIAM//2 + 12}" text-anchor="middle" font-size="10">Кнопка</text>
  
  <!-- Отверстие LED (рядом с кнопкой) -->
  <circle cx="{450 + CASE_LENGTH - 25}" cy="{110 + CASE_HEIGHT//2 - 5}" r="{LED_HOLE_DIAM//2}" class="hole"/>
  
  <!-- Вид спереди -->
  <text x="150" y="400" text-anchor="middle" class="label">ВИД СПЕРЕДИ (головка щупа)</text>
  <rect x="50" y="420" width="{CASE_WIDTH}" height="{CASE_HEIGHT}" class="cut"/>
  
  <!-- Отверстие микрофона -->
  <circle cx="{50 + CASE_WIDTH//2}" cy="{420 + CASE_HEIGHT//2}" r="{MIC_HOLE_DIAM//2}" class="hole"/>
  <text x="{50 + CASE_WIDTH//2}" y="{420 + CASE_HEIGHT//2 + MIC_HOLE_DIAM//2 + 15}" text-anchor="middle">∅{MIC_HOLE_DIAM}мм</text>
  
  <!-- Примечания -->
  <text x="400" y="530" text-anchor="middle" font-size="12" fill="#666">
    Материал: ABS/PLA пластик | Сборка на винтах M2×6мм (4 шт по углам) | 
    Все отверстия под компоненты согласно спецификации
  </text>
  <text x="400" y="550" text-anchor="middle" font-size="10" fill="#999">
    PulmoScan v1.0 © 2026 | Сгенерировано Python + CadQuery
  </text>
</svg>'''
    
    with open('case_drawing.svg', 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print("✅ SVG чертёж сохранён: case_drawing.svg")

# ==========================================
# 2. ГЕНЕРАЦИЯ 3D-МОДЕЛИ (STEP)
# ==========================================
def generate_3d():
    # Корпус — полая коробка
    case = (
        cq.Workplane("XY")
        .box(CASE_LENGTH, CASE_WIDTH, CASE_HEIGHT)
        .faces(">Z")
        .shell(-WALL_THICKNESS)
    )
    
    # Отверстие для микрофона на верхней грани
    case = (
        case
        .faces(">Z")
        .workplane()
        .center(0, 0)
        .hole(MIC_HOLE_DIAM)
    )
    
    # Отверстие USB-C на переднем торце
    case = (
        case
        .faces("<X")
        .workplane()
        .center(0, 0)
        .rect(USB_HOLE_WIDTH, USB_HOLE_HEIGHT)
        .cutBlind(-10)
    )
    
    # Отверстие кнопки на заднем торце
    case = (
        case
        .faces(">X")
        .workplane()
        .center(-5, 0)
        .hole(BUTTON_HOLE_DIAM)
    )
    
    # Отверстие светодиода
    case = (
        case
        .faces(">X")
        .workplane()
        .center(10, 5)
        .hole(LED_HOLE_DIAM)
    )
    
    # Сохраняем
    cq.exporters.export(case, 'case_3d.step')
    print("✅ 3D-модель сохранена: case_3d.step")
    print(f"   Размеры: {CASE_LENGTH}×{CASE_WIDTH}×{CASE_HEIGHT} мм")
    print(f"   Толщина стенок: {WALL_THICKNESS} мм")
    print(f"   Можно открыть в FreeCAD, Fusion360, или отдать на 3D-печать")

# ==========================================
# ЗАПУСК
# ==========================================
if __name__ == "__main__":
    print("=" * 50)
    print("  PULMOSCAN CASE GENERATOR v1.0")
    print("=" * 50)
    
    generate_svg()
    generate_3d()
    
    print("\n" + "=" * 50)
    print("  ГОТОВО!")
    print("  Чертеж: case_drawing.svg (откройте в браузере)")
    print("  3D модель: case_3d.step (для печати)")
    print("=" * 50)