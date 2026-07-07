"""
DataMole v1.1 — Крот-чистюля
Сканирует loot/, распаковывает zip, сортирует, конвертирует, валидирует
"""
import os
import shutil
import json
import zipfile
import glob
from datetime import datetime

# ==========================================
# НАСТРОЙКИ
# ==========================================
LOOT_DIR = r"C:\Users\пользователь\pilot-pulmoscan\loot"
SORTED_DIR = r"C:\Users\пользователь\pilot-pulmoscan\sorted_data"

# Категории для сортировки
CATEGORIES = {
    "cardiac_normal": ["normal", "norm", "healthy"],
    "cardiac_murmur": ["murmur", "systolic", "diastolic", "abnormal"],
    "cardiac_extrahls": ["extrahls", "extrasystole", "arrhythmia"],
    "cardiac_artifact": ["artifact", "noise"],
    "lung_normal": ["lung_normal", "clear", "vesicular"],
    "lung_wheeze": ["wheeze", "crackles", "crepitation", "rhonchi"],
    "clinical_csv": [],
    "unknown": []
}

os.makedirs(SORTED_DIR, exist_ok=True)
for cat in CATEGORIES:
    os.makedirs(os.path.join(SORTED_DIR, cat), exist_ok=True)

# ==========================================
# ШАГ 0: РАСПАКОВКА ZIP
# ==========================================
def extract_zips():
    """Распаковывает все zip в loot"""
    zips = glob.glob(os.path.join(LOOT_DIR, "*.zip"))
    if not zips:
        print("📭 Zip-архивов не найдено")
        return
    
    print(f"\n📦 Распаковываю {len(zips)} архивов...")
    for zpath in zips:
        zname = os.path.basename(zpath)
        extract_dir = os.path.join(LOOT_DIR, zname.replace('.zip', ''))
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zpath, 'r') as z:
                files = z.namelist()
                print(f"  📦 {zname} ({len(files)} файлов) → {extract_dir}")
                z.extractall(extract_dir)
            os.remove(zpath)
            print(f"  ✅ Распакован, архив удалён")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")

# ==========================================
# ШАГ 1: СКАНИРОВАНИЕ
# ==========================================
def scan_loot():
    """Сканирует папку loot и возвращает список всех файлов"""
    print(f"\n🔍 Сканирую {LOOT_DIR}...")
    all_files = []
    
    for root, dirs, files in os.walk(LOOT_DIR):
        for f in files:
            fpath = os.path.join(root, f)
            fname = f.lower()
            size_kb = os.path.getsize(fpath) / 1024
            
            ftype = "unknown"
            if fname.endswith('.wav'):
                ftype = "audio_wav"
            elif fname.endswith('.mp3'):
                ftype = "audio_mp3"
            elif fname.endswith('.csv'):
                ftype = "csv"
            elif fname.endswith('.hea'):
                ftype = "physionet_header"
            elif fname.endswith('.dat'):
                ftype = "physionet_data"
            elif fname.endswith('.zip'):
                ftype = "archive_zip"
            elif fname.endswith('.txt'):
                ftype = "text"
            
            all_files.append({
                'path': fpath,
                'name': f,
                'type': ftype,
                'size_kb': round(size_kb, 1)
            })
    
    return all_files

# ==========================================
# ШАГ 2: КЛАССИФИКАЦИЯ
# ==========================================
def classify_file(fpath, fname):
    """Определяет категорию файла по имени и пути"""
    fname_lower = fname.lower()
    
    # Проверяем ключевые слова в имени
    for cat, keywords in CATEGORIES.items():
        if cat == "unknown":
            continue
        for kw in keywords:
            if kw in fname_lower:
                return cat
    
    # Проверяем CSV
    if fname_lower.endswith('.csv'):
        return "clinical_csv"
    
    # Проверяем путь (veterinary/dog/canine)
    path_lower = fpath.lower()
    if 'veterinary' in path_lower or 'dog' in path_lower or 'canine' in path_lower:
        if 'murmur' in path_lower or 'abnormal' in path_lower:
            return "cardiac_murmur"
        if 'normal' in path_lower:
            return "cardiac_normal"
        return "cardiac_normal"  # по умолчанию собаки → сердечные
    
    # WAV без метки → пытаемся угадать по пути
    if fname_lower.endswith('.wav'):
        if 'heart' in path_lower or 'cardiac' in path_lower:
            return "cardiac_normal"
        if 'lung' in path_lower or 'respiratory' in path_lower:
            return "lung_normal"
    
    return "unknown"

def sort_files(files):
    """Сортирует файлы по категориям"""
    print(f"\n📦 Сортирую {len(files)} файлов...")
    stats = {cat: 0 for cat in CATEGORIES}
    
    for f in files:
        fpath = f['path']
        fname = f['name']
        category = classify_file(fpath, fname)
        
        dest_dir = os.path.join(SORTED_DIR, category)
        dest_path = os.path.join(dest_dir, fname)
        
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(fname)
            dest_path = os.path.join(dest_dir, f"{base}_copy{ext}")
        
        try:
            shutil.copy2(fpath, dest_path)
            stats[category] += 1
        except Exception as e:
            print(f"  ⚠️ Ошибка копирования {fname}: {e}")
    
    return stats

# ==========================================
# ШАГ 3: ВАЛИДАЦИЯ
# ==========================================
def validate_wav_files():
    """Проверяет целостность WAV файлов"""
    print(f"\n🔬 Валидация WAV файлов...")
    from scipy.io import wavfile
    
    wav_files = glob.glob(os.path.join(SORTED_DIR, "**", "*.wav"), recursive=True)
    ok = 0
    broken = 0
    
    for wf in wav_files:
        try:
            fs, data = wavfile.read(wf)
            if len(data) > 0:
                ok += 1
            else:
                print(f"  ⚠️ Пустой файл: {os.path.basename(wf)}")
                broken += 1
        except Exception as e:
            print(f"  💀 Битый файл: {os.path.basename(wf)} — {str(e)[:50]}")
            broken += 1
    
    print(f"  ✅ Целых: {ok}")
    print(f"  💀 Битых: {broken}")
    return ok, broken

# ==========================================
# ШАГ 4: ОТЧЁТ
# ==========================================
def generate_report(stats, ok, broken):
    """Генерирует отчёт о работе крота"""
    total = sum(stats.values())
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'loot_dir': LOOT_DIR,
        'sorted_dir': SORTED_DIR,
        'total_files': total,
        'by_category': stats,
        'wav_validation': {'ok': ok, 'broken': broken}
    }
    
    report_path = os.path.join(SORTED_DIR, 'mole_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("  🐹 DATA MOLE — ОТЧЁТ")
    print(f"{'='*60}")
    print(f"  Всего файлов: {total}")
    print(f"  Распределение по категориям:")
    for cat, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            bar = "█" * min(count, 40)
            print(f"  {cat:<25} {count:>4} {bar}")
    print(f"\n  WAV валидация: {ok} целых, {broken} битых")
    print(f"  📁 Отсортированные данные: {SORTED_DIR}")
    print(f"  📝 Отчёт: {report_path}")
    
    usable = stats.get('cardiac_normal', 0) + stats.get('cardiac_murmur', 0) + \
             stats.get('cardiac_extrahls', 0) + stats.get('cardiac_artifact', 0) + \
             stats.get('lung_normal', 0) + stats.get('lung_wheeze', 0)
    print(f"\n  🎯 Готово к обучению: {usable} файлов")
    if usable > 0:
        print(f"     Можно запускать дообучение!")

# ==========================================
# ГЛАВНАЯ
# ==========================================
def main():
    print("=" * 60)
    print("  🐹 DATA MOLE v1.1 — Крот-чистюля")
    print("=" * 60)
    
    # 0. Распаковываем zip
    extract_zips()
    
    # 1. Сканируем
    files = scan_loot()
    print(f"  Найдено: {len(files)} файлов")
    
    types = {}
    for f in files:
        t = f['type']
        types[t] = types.get(t, 0) + 1
    for t, c in sorted(types.items()):
        print(f"    {t}: {c}")
    
    # 2. Сортируем
    stats = sort_files(files)
    
    # 3. Валидируем
    ok, broken = validate_wav_files()
    
    # 4. Отчёт
    generate_report(stats, ok, broken)

if __name__ == "__main__":
    main()