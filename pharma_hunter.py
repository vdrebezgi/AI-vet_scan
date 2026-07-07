"""
PharmaHunter v2.0 — Охотник за дозировками (собаки + кошки)
Парсит открытые базы и пополняет pharma_base_enriched.json
"""
import json
import os
from datetime import datetime

PHARMA_FILE = r"C:\Users\пользователь\pharma_base_enriched.json"

# ==========================================
# ПОЛНАЯ БАЗА ДОЗИРОВОК (СОБАКИ + КОШКИ)
# ==========================================
VET_DOSAGES = {
    # ========== АНТИБИОТИКИ ==========
    "AMOXICILLIN": {"dose_mg_kg": 15, "species": ["dog", "cat"], "route": "oral", "frequency_h": 12, "indications": ["инфекции дыхательных путей", "пневмония", "пиодерма"]},
    "AMOXICILLIN/CLAVULANATE": {"dose_mg_kg": 13.75, "species": ["dog", "cat"], "route": "oral", "frequency_h": 12, "indications": ["инфекции", "пиодерма", "пародонтит"]},
    "DOXYCYCLINE": {"dose_mg_kg": 10, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["боррелиоз", "анаплазмоз", "питомниковый кашель"]},
    "DOXYCYCLINE_CAT": {"dose_mg_kg": 5, "species": ["cat"], "route": "oral", "frequency_h": 12, "indications": ["инфекции", "боррелиоз", "микоплазмоз"]},
    "ENROFLOXACIN": {"dose_mg_kg": 5, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["инфекции", "пневмония", "пиодерма"]},
    "ENROFLOXACIN_CAT": {"dose_mg_kg": 2.5, "species": ["cat"], "route": "oral", "frequency_h": 24, "indications": ["инфекции"], "notes": "Риск острой слепоты у кошек при высоких дозах!"},
    "MARBOFLOXACIN": {"dose_mg_kg": 2.75, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["пневмония", "инфекции мягких тканей"]},
    "MARBOFLOXACIN_CAT": {"dose_mg_kg": 2, "species": ["cat"], "route": "oral", "frequency_h": 24, "indications": ["инфекции кожи", "инфекции дыхательных путей"]},
    "CEFALEXIN": {"dose_mg_kg": 22, "species": ["dog"], "route": "oral", "frequency_h": 12, "indications": ["пиодерма", "инфекции кожи"]},
    "CEFALEXIN_CAT": {"dose_mg_kg": 22, "species": ["cat"], "route": "oral", "frequency_h": 12, "indications": ["инфекции кожи", "инфекции мочевыводящих путей"]},
    "CLINDAMYCIN": {"dose_mg_kg": 11, "species": ["dog", "cat"], "route": "oral", "frequency_h": 12, "indications": ["стоматит", "инфекции", "остеомиелит"]},
    "METRONIDAZOLE": {"dose_mg_kg": 15, "species": ["dog"], "route": "oral", "frequency_h": 12, "indications": ["диарея", "лямблиоз", "анаэробные инфекции"]},
    "METRONIDAZOLE_CAT": {"dose_mg_kg": 10, "species": ["cat"], "route": "oral", "frequency_h": 12, "indications": ["диарея", "лямблиоз"]},
    "AZITHROMYCIN": {"dose_mg_kg": 10, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["респираторные инфекции", "бартонеллёз"]},
    "AZITHROMYCIN_CAT": {"dose_mg_kg": 5, "species": ["cat"], "route": "oral", "frequency_h": 24, "indications": ["респираторные инфекции"]},
    
    # ========== СЕРДЕЧНЫЕ ==========
    "PIMOBENDAN": {"dose_mg_kg": 0.5, "species": ["dog"], "route": "oral", "frequency_h": 12, "indications": ["сердечная недостаточность", "митральная недостаточность", "ДКМП"]},
    "PIMOBENDAN_CAT": {"dose_mg_kg": 0.3, "species": ["cat"], "route": "oral", "frequency_h": 12, "indications": ["сердечная недостаточность", "HCM с обструкцией"]},
    "BENAZEPRIL": {"dose_mg_kg": 0.5, "species": ["dog", "cat"], "route": "oral", "frequency_h": 24, "indications": ["сердечная недостаточность", "гипертензия", "ХБП"]},
    "ENALAPRIL": {"dose_mg_kg": 0.5, "species": ["dog", "cat"], "route": "oral", "frequency_h": 24, "indications": ["сердечная недостаточность", "гипертензия"]},
    "FUROSEMIDE": {"dose_mg_kg": 2, "species": ["dog", "cat"], "route": "oral", "frequency_h": 12, "indications": ["отёк лёгких", "сердечная недостаточность", "асцит"]},
    "SPIRONOLACTONE": {"dose_mg_kg": 2, "species": ["dog", "cat"], "route": "oral", "frequency_h": 24, "indications": ["сердечная недостаточность", "асцит"]},
    "CLOPIDOGREL": {"dose_mg_kg": 2, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["тромбоэмболия", "профилактика тромбозов"]},
    "CLOPIDOGREL_CAT": {"dose_mg_kg": 18.75, "species": ["cat"], "route": "oral", "frequency_h": 24, "indications": ["профилактика тромбоэмболии при HCM"], "notes": "1/4 таблетки 75 мг на кота"},
    "SOTALOL": {"dose_mg_kg": 2, "species": ["dog"], "route": "oral", "frequency_h": 12, "indications": ["аритмия", "желудочковая тахикардия"]},
    "DILTIAZEM": {"dose_mg_kg": 1.5, "species": ["dog"], "route": "oral", "frequency_h": 8, "indications": ["аритмия", "гипертензия"]},
    "DILTIAZEM_CAT": {"dose_mg_kg": 7.5, "species": ["cat"], "route": "oral", "frequency_h": 8, "indications": ["HCM", "гипертензия"]},
    "ATENOLOL": {"dose_mg_kg": 1, "species": ["dog"], "route": "oral", "frequency_h": 12, "indications": ["аритмия", "гипертензия"]},
    "ATENOLOL_CAT": {"dose_mg_kg": 6.25, "species": ["cat"], "route": "oral", "frequency_h": 12, "indications": ["HCM", "гипертиреоз", "гипертензия"]},
    "AMLODIPINE": {"dose_mg_kg": 0.1, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["гипертензия"]},
    "AMLODIPINE_CAT": {"dose_mg_kg": 0.625, "species": ["cat"], "route": "oral", "frequency_h": 24, "indications": ["гипертензия", "ХБП"], "notes": "1/4 таблетки 2.5 мг"},
    
    # ========== НПВС / ОБЕЗБОЛИВАНИЕ ==========
    "CARPROFEN": {"dose_mg_kg": 4.4, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["боль", "воспаление", "артрит"]},
    "MELOXICAM": {"dose_mg_kg": 0.2, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["боль", "воспаление", "артрит"]},
    "MELOXICAM_CAT": {"dose_mg_kg": 0.05, "species": ["cat"], "route": "oral", "frequency_h": 24, "indications": ["боль", "воспаление"], "notes": "Только кратковременно! Риск ОПП у кошек."},
    "FIROCOXIB": {"dose_mg_kg": 5, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["остеоартрит", "послеоперационная боль"]},
    "ROBENACOXIB": {"dose_mg_kg": 2, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["боль", "воспаление"]},
    "ROBENACOXIB_CAT": {"dose_mg_kg": 1, "species": ["cat"], "route": "oral", "frequency_h": 24, "indications": ["боль", "послеоперационная боль"]},
    "GABAPENTIN": {"dose_mg_kg": 10, "species": ["dog", "cat"], "route": "oral", "frequency_h": 8, "indications": ["нейропатическая боль", "судороги", "тревожность"]},
    "TRAMADOL": {"dose_mg_kg": 4, "species": ["dog"], "route": "oral", "frequency_h": 8, "indications": ["боль", "послеоперационная боль"]},
    "TRAMADOL_CAT": {"dose_mg_kg": 2, "species": ["cat"], "route": "oral", "frequency_h": 12, "indications": ["боль"]},
    "BUPRENORPHINE_CAT": {"dose_mg_kg": 0.02, "species": ["cat"], "route": "oral", "frequency_h": 8, "indications": ["боль", "послеоперационная боль"], "notes": "Трансмукозально (за щеку)"},
    
    # ========== ГОРМОНЫ / ЭНДОКРИННЫЕ ==========
    "LEVOTHYROXINE": {"dose_mg_kg": 0.02, "species": ["dog"], "route": "oral", "frequency_h": 12, "indications": ["гипотиреоз"]},
    "LEVOTHYROXINE_CAT": {"dose_mg_kg": 0.05, "species": ["cat"], "route": "oral", "frequency_h": 12, "indications": ["гипотиреоз (редко)"]},
    "TRILOSTANE": {"dose_mg_kg": 2, "species": ["dog"], "route": "oral", "frequency_h": 12, "indications": ["гиперадренокортицизм (Кушинга)"]},
    "TRILOSTANE_CAT": {"dose_mg_kg": 1, "species": ["cat"], "route": "oral", "frequency_h": 12, "indications": ["гиперадренокортицизм"]},
    "METHIMAZOLE": {"dose_mg_kg": 2.5, "species": ["cat"], "route": "oral", "frequency_h": 12, "indications": ["гипертиреоз"]},
    "CARBIMAZOLE_CAT": {"dose_mg_kg": 5, "species": ["cat"], "route": "oral", "frequency_h": 8, "indications": ["гипертиреоз"]},
    "INSULIN_CANINE": {"dose_mg_kg": 0.5, "species": ["dog"], "route": "injection", "frequency_h": 12, "indications": ["сахарный диабет"], "notes": "Ед/кг, не мг/кг"},
    "INSULIN_FELINE": {"dose_mg_kg": 1, "species": ["cat"], "route": "injection", "frequency_h": 12, "indications": ["сахарный диабет"], "notes": "Ед/кг, не мг/кг. Гларгин или детемир"},
    
    # ========== ЖКТ / ПРОТИВОРВОТНЫЕ ==========
    "MAROPITANT": {"dose_mg_kg": 2, "species": ["dog"], "route": "oral", "frequency_h": 24, "indications": ["рвота", "укачивание"]},
    "MAROPITANT_CAT": {"dose_mg_kg": 1, "species": ["cat"], "route": "oral", "frequency_h": 24, "indications": ["рвота", "укачивание"]},
    "OMEPRAZOLE": {"dose_mg_kg": 1, "species": ["dog", "cat"], "route": "oral", "frequency_h": 12, "indications": ["гастрит", "рефлюкс", "язва"]},
    "FAMOTIDINE": {"dose_mg_kg": 1, "species": ["dog", "cat"], "route": "oral", "frequency_h": 12, "indications": ["гастрит", "рефлюкс"]},
    "METOCLOPRAMIDE": {"dose_mg_kg": 0.5, "species": ["dog", "cat"], "route": "oral", "frequency_h": 8, "indications": ["рвота", "гастропарез"]},
    "SUCRALFATE": {"dose_mg_kg": 500, "species": ["dog"], "route": "oral", "frequency_h": 8, "indications": ["язва", "эзофагит"]},
    "SUCRALFATE_CAT": {"dose_mg_kg": 250, "species": ["cat"], "route": "oral", "frequency_h": 8, "indications": ["язва", "эзофагит"], "notes": "1/4 таблетки 1 г"},
    
    # ========== ПРОТИВОСУДОРОЖНЫЕ ==========
    "PHENOBARBITAL": {"dose_mg_kg": 2.5, "species": ["dog", "cat"], "route": "oral", "frequency_h": 12, "indications": ["эпилепсия", "судороги"]},
    "LEVETIRACETAM": {"dose_mg_kg": 20, "species": ["dog", "cat"], "route": "oral", "frequency_h": 8, "indications": ["эпилепсия", "судороги"]},
    "ZONISAMIDE": {"dose_mg_kg": 10, "species": ["dog", "cat"], "route": "oral", "frequency_h": 12, "indications": ["эпилепсия"]},
    
    # ========== АЛЛЕРГИЯ / ИММУННЫЕ ==========
    "PREDNISONE": {"dose_mg_kg": 1, "species": ["dog"], "route": "oral", "frequency_h": 12, "indications": ["аллергия", "воспаление", "иммуносупрессия"]},
    "PREDNISOLONE_CAT": {"dose_mg_kg": 2, "species": ["cat"], "route": "oral", "frequency_h": 12, "indications": ["астма", "аллергия", "воспаление"], "notes": "Кошки не конвертируют преднизон в преднизолон!"},
    "CYCLOSPORINE": {"dose_mg_kg": 5, "species": ["dog", "cat"], "route": "oral", "frequency_h": 24, "indications": ["атопия", "иммуноопосредованные заболевания"]},
    "OCLACITINIB": {"dose_mg_kg": 0.5, "species": ["dog"], "route": "oral", "frequency_h": 12, "indications": ["атопия", "аллергический дерматит"]},
    "DIPHENHYDRAMINE": {"dose_mg_kg": 2, "species": ["dog", "cat"], "route": "oral", "frequency_h": 8, "indications": ["аллергия", "анафилаксия"]},
    
    # ========== АНТИПАРАЗИТАРНЫЕ ==========
    "IVERMECTIN": {"dose_mg_kg": 0.006, "species": ["dog"], "route": "oral", "frequency_h": "monthly", "indications": ["профилактика дирофиляриоза"]},
    "MILBEMYCIN": {"dose_mg_kg": 0.5, "species": ["dog", "cat"], "route": "oral", "frequency_h": "monthly", "indications": ["профилактика дирофиляриоза", "глисты"]},
    "PRAZIQUANTEL": {"dose_mg_kg": 5, "species": ["dog", "cat"], "route": "oral", "frequency_h": "single", "indications": ["цестоды"]},
    "FENBENDAZOLE": {"dose_mg_kg": 50, "species": ["dog", "cat"], "route": "oral", "frequency_h": 24, "indications": ["глисты", "лямблиоз"]},
    "SELAMECTIN": {"dose_mg_kg": 6, "species": ["dog", "cat"], "route": "topical", "frequency_h": "monthly", "indications": ["блохи", "глисты", "чесоточные клещи"]},
    "FLURALANER": {"dose_mg_kg": 25, "species": ["dog"], "route": "oral", "frequency_h": "12 weeks", "indications": ["блохи", "клещи"]},
    "MOXIDECTIN": {"dose_mg_kg": 0.003, "species": ["dog", "cat"], "route": "topical", "frequency_h": "monthly", "indications": ["профилактика дирофиляриоза", "блохи"]},
    
    # ========== БРОНХОДИЛАТАТОРЫ ==========
    "THEOPHYLLINE": {"dose_mg_kg": 10, "species": ["dog"], "route": "oral", "frequency_h": 12, "indications": ["бронхит", "коллапс трахеи", "астма"]},
    "THEOPHYLLINE_CAT": {"dose_mg_kg": 20, "species": ["cat"], "route": "oral", "frequency_h": 24, "indications": ["астма", "бронхит"], "notes": "Пролонгированная форма"},
    "TERBUTALINE": {"dose_mg_kg": 0.01, "species": ["dog", "cat"], "route": "injection", "frequency_h": 4, "indications": ["бронхоспазм", "астма"]},
    "SALBUTAMOL_CAT": {"dose_mg_kg": 0.1, "species": ["cat"], "route": "inhalation", "frequency_h": 6, "indications": ["астма"], "notes": "Ингаляционно через спейсер"},
    
    # ========== ТОКСИЧНЫЕ ДЛЯ КОШЕК ==========
    "ACETAMINOPHEN": {"dose_mg_kg": 0, "species": [], "route": "TOXIC", "frequency_h": 0, "indications": ["☠️ СМЕРТЕЛЬНО ТОКСИЧЕН ДЛЯ КОШЕК! НЕ ПРИМЕНЯТЬ!"], "toxic_cat": True},
    "IBUPROFEN": {"dose_mg_kg": 0, "species": [], "route": "TOXIC", "frequency_h": 0, "indications": ["☠️ ТОКСИЧЕН ДЛЯ КОШЕК! ВЫЗЫВАЕТ ОПП!"], "toxic_cat": True},
    "PERMETHRIN": {"dose_mg_kg": 0, "species": [], "route": "TOXIC", "frequency_h": 0, "indications": ["☠️ СМЕРТЕЛЬНО ТОКСИЧЕН ДЛЯ КОШЕК! НЕ ДОПУСКАТЬ КОНТАКТА!"], "toxic_cat": True},
    "ESSENTIAL_OILS": {"dose_mg_kg": 0, "species": [], "route": "TOXIC", "frequency_h": 0, "indications": ["☠️ Эфирные масла (чайное дерево, цитрус) ТОКСИЧНЫ ДЛЯ КОШЕК!"], "toxic_cat": True},
    "LILY": {"dose_mg_kg": 0, "species": [], "route": "TOXIC", "frequency_h": 0, "indications": ["☠️ ЛИЛИИ СМЕРТЕЛЬНО ТОКСИЧНЫ ДЛЯ КОШЕК! Острая почечная недостаточность!"], "toxic_cat": True},
}

# ==========================================
# ФУНКЦИИ
# ==========================================
def load_pharma_base():
    if os.path.exists(PHARMA_FILE):
        with open(PHARMA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_pharma_base(db):
    with open(PHARMA_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def enrich_with_dosages(db):
    """Добавляет дозировки из VET_DOSAGES в существующую базу"""
    added = 0
    updated = 0
    
    for drug in db:
        name = drug.get('name', '').upper()
        for key, info in VET_DOSAGES.items():
            base_key = key.replace("_CAT", "").replace("_CANINE", "").replace("_FELINE", "")
            if base_key in name or name in base_key:
                if 'dose_mg_kg' not in drug or drug.get('source') != 'vet_dosages':
                    drug['dose_mg_kg'] = info['dose_mg_kg']
                    drug['species'] = info['species']
                    drug['route'] = info['route']
                    drug['frequency_h'] = info['frequency_h']
                    drug['indications'] = info['indications']
                    drug['source'] = 'vet_dosages'
                    if info.get('toxic_cat'):
                        drug['toxic_cat'] = True
                    if info.get('notes'):
                        drug['notes'] = info.get('notes')
                    updated += 1
                break
    
    # Добавляем новые препараты
    existing_names = {d.get('name', '').upper() for d in db}
    for key, info in VET_DOSAGES.items():
        if key not in existing_names:
            db.append({
                'name': key,
                'dose_mg_kg': info['dose_mg_kg'],
                'species': info['species'],
                'route': info['route'],
                'frequency_h': info['frequency_h'],
                'indications': info['indications'],
                'source': 'vet_dosages',
                'toxic_cat': info.get('toxic_cat', False),
                'notes': info.get('notes', '')
            })
            added += 1
    
    return db, added, updated

def main():
    print("=" * 60)
    print("  💊 PHARMA HUNTER v2.0 — Дозировки (собаки + кошки)")
    print("=" * 60)
    
    print(f"\n📂 База: {PHARMA_FILE}")
    db = load_pharma_base()
    print(f"   Загружено препаратов: {len(db)}")
    
    with_dose = sum(1 for d in db if d.get('dose_mg_kg'))
    toxic = sum(1 for d in db if d.get('toxic_cat'))
    print(f"   С дозировками: {with_dose}")
    print(f"   Токсичных для кошек: {toxic}")
    
    print(f"\n🔍 Обогащаю...")
    db, added, updated = enrich_with_dosages(db)
    print(f"   ✅ Добавлено новых: {added}")
    print(f"   ✅ Обновлено: {updated}")
    
    save_pharma_base(db)
    
    with_dose_after = sum(1 for d in db if d.get('dose_mg_kg'))
    toxic_after = sum(1 for d in db if d.get('toxic_cat'))
    
    print(f"\n{'─'*50}")
    print(f"   Всего препаратов: {len(db)}")
    print(f"   С дозировками: {with_dose_after} (+{with_dose_after - with_dose})")
    print(f"   Токсичных для кошек: {toxic_after}")
    print(f"   💾 Сохранено: {PHARMA_FILE}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()