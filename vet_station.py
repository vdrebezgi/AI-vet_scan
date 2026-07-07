"""
VetStation v1.0 — ЕДИНЫЙ ЦЕНТР УПРАВЛЕНИЯ
Объединяет: DataHunter + DataMole + VetKnowledge + VetScanner
Запуск: python vet_station.py
"""
import os
import sys
import json
import subprocess
from datetime import datetime

# ==========================================
# ПУТИ К МОДУЛЯМ
# ==========================================
BASE_DIR = r"C:\Users\пользователь\pilot-pulmoscan"
MODULES = {
    "hunter": os.path.join(BASE_DIR, "data_hunter.py"),
    "mole": os.path.join(BASE_DIR, "data_mole.py"),
    "knowledge": os.path.join(BASE_DIR, "vet_knowledge_v2.py"),
    "scanner": os.path.join(BASE_DIR, "vet_scanner_v2.py"),
    "pulmoscan": os.path.join(BASE_DIR, "pulmoscan_pro.py"),
}

# ==========================================
# ФУНКЦИИ
# ==========================================
def banner():
    print("\n" + "=" * 70)
    print("  🏥 VET STATION v1.0 — Центр управления")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 70)

def run_module(name, description, extra_args=""):
    """Запускает модуль Python"""
    if name not in MODULES:
        print(f"  ❌ Модуль '{name}' не найден")
        return False
    
    path = MODULES[name]
    if not os.path.exists(path):
        print(f"  ❌ Файл не найден: {path}")
        return False
    
    print(f"\n{'─'*70}")
    print(f"  ▶ {description}")
    print(f"{'─'*70}")
    
    cmd = f'python "{path}" {extra_args}'
    try:
        result = subprocess.run(cmd, shell=True, cwd=BASE_DIR)
        if result.returncode == 0:
            print(f"\n  ✅ {name} завершён успешно")
            return True
        else:
            print(f"\n  ⚠️ {name} завершён с кодом {result.returncode}")
            return False
    except KeyboardInterrupt:
        print(f"\n  ⏹️ {name} прерван пользователем")
        return False

def full_pipeline(wav_file=None):
    """Полный конвейер: охота → сортировка → знания → анализ"""
    banner()
    results = {}
    
    # ШАГ 1: Ищейка — поиск новых данных
    print("\n  🎯 ШАГ 1/4: Поиск новых датасетов (DataHunter)")
    print("  " + "─" * 50)
    hunter_ok = run_module("hunter", "DataHunter — охота за датасетами")
    results["hunter"] = hunter_ok
    
    # ШАГ 2: Крот — сортировка добычи
    print("\n  🎯 ШАГ 2/4: Сортировка данных (DataMole)")
    print("  " + "─" * 50)
    mole_ok = run_module("mole", "DataMole — распаковка и сортировка")
    results["mole"] = mole_ok
    
    # ШАГ 3: База знаний — автообновление
    print("\n  🎯 ШАГ 3/4: Обновление базы знаний (VetKnowledge)")
    print("  " + "─" * 50)
    knowledge_ok = run_module("knowledge", "VetKnowledge — автообновление из PubMed", "--force")
    results["knowledge"] = knowledge_ok
    
    # ШАГ 4: Анализ
    print("\n  🎯 ШАГ 4/4: Комплексный анализ (VetScanner)")
    print("  " + "─" * 50)
    
    if wav_file and os.path.exists(wav_file):
        scanner_ok = run_module("scanner", f"VetScanner — анализ {os.path.basename(wav_file)}", f'"{wav_file}"')
    else:
        scanner_ok = run_module("scanner", "VetScanner — тестовый анализ")
    results["scanner"] = scanner_ok
    
    # ИТОГИ
    print("\n" + "=" * 70)
    print("  🏆 РЕЗУЛЬТАТЫ КОНВЕЙЕРА")
    print("=" * 70)
    for step, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {step}")
    
    print(f"\n  📁 Добыча: {os.path.join(BASE_DIR, 'loot')}")
    print(f"  📁 Сортированные: {os.path.join(BASE_DIR, 'sorted_data')}")
    print(f"  📚 База знаний: {os.path.join(BASE_DIR, 'vet_knowledge_base.json')}")
    print("=" * 70)

def menu():
    """Интерактивное меню"""
    while True:
        banner()
        print("\n  📋 МЕНЮ:")
        print("  ─────────────────────────────────────")
        print("  [1] 🔍 Только поиск данных (DataHunter)")
        print("  [2] 🐹 Только сортировка (DataMole)")
        print("  [3] 🧠 Только обновление знаний (VetKnowledge)")
        print("  [4] 🫁❤️ Только анализ (VetScanner)")
        print("  [5] 🚀 ПОЛНЫЙ КОНВЕЙЕР (всё сразу)")
        print("  [6] 📊 Анализ конкретного WAV файла")
        print("  [7] 💊 Проверка базы лекарств")
        print("  [0] 🚪 Выход")
        print("  ─────────────────────────────────────")
        
        choice = input("  ▶ Выбор: ").strip()
        
        if choice == "1":
            run_module("hunter", "DataHunter")
        elif choice == "2":
            run_module("mole", "DataMole")
        elif choice == "3":
            run_module("knowledge", "VetKnowledge", "--force")
        elif choice == "4":
            run_module("scanner", "VetScanner")
        elif choice == "5":
            full_pipeline()
        elif choice == "6":
            wav = input("  📂 Путь к WAV файлу: ").strip().strip('"')
            if wav and os.path.exists(wav):
                run_module("scanner", f"Анализ {os.path.basename(wav)}", f'"{wav}"')
            else:
                print(f"  ❌ Файл не найден: {wav}")
        elif choice == "7":
            show_drugs()
        elif choice == "0":
            print("\n  🚪 До свидания!")
            break
        else:
            print("  ❌ Неизвестная команда")
        
        input("\n  Нажми Enter для продолжения...")

def show_drugs():
    """Показывает статистику базы лекарств"""
    pharma_file = r"C:\Users\пользователь\pharma_base_enriched.json"
    if os.path.exists(pharma_file):
        with open(pharma_file, 'r', encoding='utf-8') as f:
            drugs = json.load(f)
        with_dose = sum(1 for d in drugs if d.get('dose_mg_kg'))
        print(f"\n  💊 БАЗА ЛЕКАРСТВ:")
        print(f"  ──────────────────────────────")
        print(f"  Всего препаратов: {len(drugs)}")
        print(f"  С дозировками: {with_dose}")
        print(f"  Примеры:")
        for d in drugs[:5]:
            dose = d.get('dose_mg_kg', '?')
            print(f"    • {d.get('name', '?')} — {dose} мг/кг ({d.get('route', '?')})")
    else:
        print(f"  ❌ База лекарств не найдена: {pharma_file}")

# ==========================================
# ЗАПУСК
# ==========================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--full":
            full_pipeline(sys.argv[2] if len(sys.argv) > 2 else None)
        elif sys.argv[1] == "--scan" and len(sys.argv) > 2:
            run_module("scanner", f"Анализ {os.path.basename(sys.argv[2])}", f'"{sys.argv[2]}"')
        elif sys.argv[1] == "--hunt":
            run_module("hunter", "DataHunter")
        elif sys.argv[1] == "--mole":
            run_module("mole", "DataMole")
        elif sys.argv[1] == "--knowledge":
            run_module("knowledge", "VetKnowledge", "--force")
    else:
        menu()