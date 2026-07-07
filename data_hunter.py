"""
DataHunter v5.0 — Ищейка с защитой от дубликатов
Проверяет что уже скачано, не качает повторно
"""
import os, json, subprocess, webbrowser, time, shutil, zipfile, glob
from datetime import datetime

# ==========================================
# НАСТРОЙКИ
# ==========================================
LOOT_DIR = r"C:\Users\пользователь\pilot-pulmoscan\loot"
SORTED_DIR = r"C:\Users\пользователь\pilot-pulmoscan\sorted_data"
os.makedirs(LOOT_DIR, exist_ok=True)

# ==========================================
# БАЗА ИСТОЧНИКОВ
# ==========================================
SOURCES = {
    "kaggle_heartbeat": {
        "name": "Kaggle Heartbeat Sounds (veterinary)",
        "type": "kaggle_cli",
        "command": 'kaggle datasets download kinguistics/heartbeat-sounds -p "{loot}"',
        "output_name": "heartbeat-sounds.zip",
        "extract_dir": "heartbeat-sounds",
        "size_mb": 150,
        "notes": "Собаки/кошки в папке veterinary/",
        "already_downloaded": False,
        "already_extracted": False
    },
    "physionet_cardiac": {
        "name": "PhysioNet 2016 Heart Sounds",
        "type": "manual",
        "url": "https://physionet.org/content/challenge-2016/1.0.0/",
        "size_mb": 1500,
        "notes": "Нужен VPN. Откроется браузер. Скачай ZIP в Downloads.",
        "already_downloaded": False
    },
    "mendeley_canine": {
        "name": "Mendeley Canine Cardiac (87 записей)",
        "type": "manual",
        "url": "https://data.mendeley.com/datasets/y5h3k8t7n2/1",
        "size_mb": 50,
        "notes": "Откроется браузер. Скачай вручную.",
        "already_downloaded": False
    },
}

# ==========================================
# ПРОВЕРКА ЧТО УЖЕ СКАЧАНО
# ==========================================
def check_existing():
    """Проверяет что уже есть в loot/ и sorted_data/"""
    print("🔍 Проверяю что уже добыто...")
    
    # Проверяем zip-файлы в loot
    if os.path.exists(LOOT_DIR):
        for item in os.listdir(LOOT_DIR):
            item_path = os.path.join(LOOT_DIR, item)
            if item.endswith('.zip'):
                for key, src in SOURCES.items():
                    if src.get("output_name") == item or item.startswith(src.get("extract_dir", "")):
                        src["already_downloaded"] = True
                        print(f"  ✅ {src['name']} — уже скачан")
            elif os.path.isdir(item_path):
                for key, src in SOURCES.items():
                    if item == src.get("extract_dir", ""):
                        src["already_extracted"] = True
                        print(f"  ✅ {src['name']} — уже распакован")
    
    # Проверяем sorted_data
    if os.path.exists(SORTED_DIR):
        wav_count = len(glob.glob(os.path.join(SORTED_DIR, "**", "*.wav"), recursive=True))
        if wav_count > 0:
            print(f"  ✅ Сортированных WAV: {wav_count}")

# ==========================================
# ФУНКЦИИ СКАЧИВАНИЯ
# ==========================================
def run_kaggle(command, loot_dir):
    """Запускает Kaggle CLI"""
    cmd = command.replace("{loot}", loot_dir)
    print(f"  🏃 {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"  ✅ Скачано")
            return True
        else:
            err = result.stderr.strip()
            if "already" in err.lower():
                print(f"  ⚠️ Уже существует")
                return True
            print(f"  ❌ {err[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ {e}")
        return False

def watch_downloads(timeout=120):
    """Ждёт появления нового zip в Downloads"""
    downloads = r"C:\Users\пользователь\Downloads"
    before = set(os.listdir(downloads))
    
    print(f"  ⏳ Жду скачивания ({timeout} сек)...")
    
    for i in range(timeout // 2):
        time.sleep(2)
        after = set(os.listdir(downloads))
        new = after - before
        
        for f in new:
            if f.endswith('.zip'):
                fpath = os.path.join(downloads, f)
                # Ждём пока допишется
                s1 = os.path.getsize(fpath)
                time.sleep(3)
                s2 = os.path.getsize(fpath)
                if s1 == s2 and s1 > 1000:
                    print(f"  🎯 Обнаружен: {f} ({s1/(1024*1024):.1f} MB)")
                    return fpath
        
        if i % 15 == 0 and i > 0:
            print(f"  ⏳ Жду... ({i*2} сек)")
    
    return None

def move_to_loot(filepath):
    """Переносит файл в loot"""
    if not filepath or not os.path.exists(filepath):
        return None
    dest = os.path.join(LOOT_DIR, os.path.basename(filepath))
    shutil.move(filepath, dest)
    print(f"  📦 Перемещён: {dest}")
    return dest

def extract_all():
    """Распаковывает все zip в loot"""
    zips = glob.glob(os.path.join(LOOT_DIR, "*.zip"))
    if not zips:
        return
    
    print(f"\n📦 Распаковка {len(zips)} архивов...")
    for zpath in zips:
        zname = os.path.basename(zpath)
        extract_dir = os.path.join(LOOT_DIR, zname.replace('.zip', ''))
        
        if os.path.exists(extract_dir):
            # Уже распакован — проверяем количество файлов
            existing = len(glob.glob(os.path.join(extract_dir, "**", "*"), recursive=True))
            if existing > 10:
                print(f"  ⏭️ {zname} уже распакован ({existing} файлов)")
                os.remove(zpath)
                continue
        
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zpath, 'r') as z:
                files = z.namelist()
                print(f"  📦 {zname} ({len(files)} файлов)")
                z.extractall(extract_dir)
            os.remove(zpath)
            print(f"  ✅ Готово: {extract_dir}")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")

# ==========================================
# ГЛАВНЫЙ ЦИКЛ
# ==========================================
def main():
    print("=" * 70)
    print("  🐕 DATAHUNTER v5.0 — Умная охота (без дубликатов)")
    print(f"  📂 Добыча: {LOOT_DIR}")
    print("=" * 70)
    
    # Проверяем что уже есть
    check_existing()
    
    # Считаем что нового
    new_sources = [s for s in SOURCES.values() if not s.get("already_downloaded") and not s.get("already_extracted")]
    
    if not new_sources:
        print("\n✅ Все источники уже добыты! Нового ничего нет.")
        extract_all()
        show_summary()
        return
    
    print(f"\n🎯 Доступно нового: {len(new_sources)} источников")
    for s in new_sources:
        print(f"  • {s['name']} (~{s['size_mb']} MB)")
    
    print("\n  [A] Скачать всё новое")
    print("  [1..N] Выбрать конкретный")
    print("  [S] Пропустить (только распаковать)")
    print("  [Q] Выход")
    
    choice = input("\n  ▶ Выбор: ").strip().upper()
    
    if choice == 'Q':
        return
    elif choice == 'S':
        extract_all()
        show_summary()
        return
    
    for key, src in SOURCES.items():
        if src.get("already_downloaded") or src.get("already_extracted"):
            continue
        
        if choice == 'A' or choice == str(list(SOURCES.keys()).index(key) + 1):
            print(f"\n{'─'*60}")
            print(f"  🎯 {src['name']}")
            print(f"{'─'*60}")
            
            if src['type'] == 'kaggle_cli':
                run_kaggle(src['command'], LOOT_DIR)
            elif src['type'] == 'manual':
                print(f"  🌐 Открываю браузер...")
                print(f"  📝 {src['notes']}")
                webbrowser.open(src['url'])
                ans = input(f"  Скачать {src['name']}? [Y/N]: ").strip().upper()
                if ans == 'Y':
                    fpath = watch_downloads(timeout=180)
                    if fpath:
                        move_to_loot(fpath)
    
    # Распаковываем всё что есть
    extract_all()
    show_summary()

def show_summary():
    """Показывает итоги"""
    print(f"\n{'='*70}")
    print("  🏆 ИТОГИ ОХОТЫ")
    print(f"{'='*70}")
    
    total_size = 0
    if os.path.exists(LOOT_DIR):
        items = os.listdir(LOOT_DIR)
        for item in items:
            item_path = os.path.join(LOOT_DIR, item)
            if os.path.isdir(item_path):
                size = 0
                for root, dirs, files in os.walk(item_path):
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.exists(fp):
                            size += os.path.getsize(fp)
                total_size += size
                file_count = len(glob.glob(os.path.join(item_path, "**", "*"), recursive=True))
                print(f"  📁 {item:<40} {size/(1024*1024):.1f} MB ({file_count} файлов)")
            elif os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                total_size += size
                print(f"  📄 {item:<40} {size/(1024*1024):.1f} MB")
    
    print(f"  💾 Всего: {total_size/(1024*1024):.1f} MB")
    
    # Что готово к сортировке
    wavs = glob.glob(os.path.join(LOOT_DIR, "**", "*.wav"), recursive=True)
    print(f"  🎯 WAV файлов к сортировке: {len(wavs)}")

if __name__ == "__main__":
    main()