"""
VetKnowledge v2.1 — База знаний с референсами для собак и кошек
"""
import urllib.request
import urllib.parse
import json
import ssl
import os
import re
import time
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context

KNOWLEDGE_FILE = r"C:\Users\пользователь\pilot-pulmoscan\vet_knowledge_base.json"

# ==========================================
# РАСШИРЕННЫЕ РЕФЕРЕНСНЫЕ ЗНАЧЕНИЯ
# ==========================================
REFERENCE_VALUES = {
    "dog": {
        "hr_resting": [60, 140],
        "hr_tachycardia": 140,
        "hr_bradycardia": 60,
        "rr_resting": [10, 30],
        "rr_tachypnea": 30,
        "rr_bradypnea": 10,
        "temp_c": [37.5, 39.2],
        "temp_fever": 39.2,
        "temp_hypothermia": 37.5,
        "spo2_min": 95,
        "spo2_critical": 90,
        "weight_kg_by_size": {"small": [1, 10], "medium": [10, 25], "large": [25, 45], "giant": [45, 100]},
        "common_diseases_by_age": {
            "puppy": ["парвовирус", "чума", "глисты", "инородные тела"],
            "adult": ["аллергия", "травмы", "пиодерма", "гастрит"],
            "senior": ["артрит", "сердечная недостаточность", "ХБП", "онкология", "стоматология"]
        }
    },
    "cat": {
        "hr_resting": [140, 220],
        "hr_tachycardia": 220,
        "hr_bradycardia": 140,
        "rr_resting": [20, 30],
        "rr_tachypnea": 30,
        "rr_bradypnea": 20,
        "temp_c": [38.0, 39.2],
        "temp_fever": 39.2,
        "temp_hypothermia": 38.0,
        "spo2_min": 95,
        "spo2_critical": 90,
        "weight_kg_by_size": {"small": [2, 4], "medium": [4, 6], "large": [6, 10]},
        "common_diseases_by_age": {
            "kitten": ["панлейкопения", "калицивироз", "глисты", "конъюнктивит"],
            "adult": ["цистит", "астма", "гингивостоматит", "травмы"],
            "senior": ["ХБП", "гипертиреоз", "HCM", "артрит", "стоматология"]
        },
        "special_notes": [
            "Кошки — облигатные хищники. НЕЛЬЗЯ голодание >48 часов (липидоз печени)",
            "Парацетамол СМЕРТЕЛЕН для кошек",
            "Лилии СМЕРТЕЛЬНО ТОКСИЧНЫ (ОПП)",
            "Кошкам нужен ТАУРИН в пище (иначе дилатационная кардиомиопатия + слепота)",
            "Кошкам нужен АРГИНИН (иначе гипераммониемия за 2-3 часа)"
        ]
    }
}

# ==========================================
# БАЗА ПОРОД (сокращённая — дополняется из breeds_extra.json)
# ==========================================
DEFAULT_BREEDS = {
    "кавалер-кинг-чарльз": {"size":"small","weight":[5.9,8.2],"life":[9,14],
        "risks":{"heart":{"mitral_valve_disease":0.9,"chf":0.5},"neuro":{"syringomyelia":0.25},"ortho":{"patellar_luxation":0.2}}},
    "такса": {"size":"small","weight":[7,14],"life":[12,16],
        "risks":{"ortho":{"ivdd":0.4},"heart":{"mitral_valve_disease":0.3},"eyes":{"pra":0.1}}},
    "мопс": {"size":"small","weight":[6.3,8.1],"life":[12,15],
        "risks":{"resp":{"baos":0.8},"eyes":{"corneal_ulcer":0.3},"ortho":{"hip_dysplasia":0.2}}},
    "лабрадор": {"size":"large","weight":[25,36],"life":[10,14],
        "risks":{"ortho":{"hip_dysplasia":0.2,"elbow_dysplasia":0.15},"endocrine":{"obesity":0.4}}},
    "немецкая овчарка": {"size":"large","weight":[30,40],"life":[9,13],
        "risks":{"ortho":{"hip_dysplasia":0.35,"elbow_dysplasia":0.2},"neuro":{"degenerative_myelopathy":0.15}}},
    "доберман": {"size":"large","weight":[32,45],"life":[10,13],
        "risks":{"heart":{"dcm":0.5,"arrhythmia":0.3}}},
    "боксёр": {"size":"large","weight":[25,32],"life":[10,12],
        "risks":{"heart":{"arvc":0.4,"aortic_stenosis":0.15},"cancer":{"mast_cell":0.2}}},
}

# ==========================================
# ФУНКЦИИ
# ==========================================
def search_pubmed(query, max_results=5):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    search_url = f"{base_url}esearch.fcgi?db=pubmed&term={urllib.parse.quote(query)}&retmax={max_results}&retmode=json"
    try:
        resp = urllib.request.urlopen(search_url, timeout=10)
        data = json.loads(resp.read())
        return data.get("esearchresult", {}).get("idlist", [])
    except:
        return []

def load_or_create_kb():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            kb = json.load(f)
        print(f"📚 Загружена база: {kb['metadata'].get('total_breeds',0)} собак, {kb['metadata'].get('total_cats',0)} кошек")
    else:
        kb = {
            "breeds": DEFAULT_BREEDS,
            "cats": {},
            "diseases": {},
            "drug_interactions": {},
            "reference_values": REFERENCE_VALUES,
            "metadata": {"version": "2.1", "total_breeds": len(DEFAULT_BREEDS), "total_cats": 0, "last_updated": datetime.now().isoformat()}
        }
        print("Создана новая база знаний с референсами")
    
    # Всегда обновляем референсы до актуальной версии
    kb["reference_values"] = REFERENCE_VALUES
    return kb

def save_kb(kb):
    kb["metadata"]["last_updated"] = datetime.now().isoformat()
    kb["metadata"]["total_breeds"] = len(kb.get("breeds", {}))
    kb["metadata"]["total_cats"] = len(kb.get("cats", {}))
    with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Сохранено: {KNOWLEDGE_FILE}")
    print(f"   Собак: {kb['metadata']['total_breeds']}, Кошек: {kb['metadata']['total_cats']}")

def update_knowledge_base(kb, force=False):
    last_update = kb.get("metadata", {}).get("last_updated", "")
    if last_update and not force:
        try:
            days_ago = (datetime.now() - datetime.fromisoformat(last_update)).days
            if days_ago < 7:
                print(f"  База обновлялась {days_ago} дн. назад. Пропускаю.")
                return kb
        except:
            pass
    
    print("\n🔄 АВТООБНОВЛЕНИЕ")
    print("─" * 50)
    
    kb["metadata"]["last_updated"] = datetime.now().isoformat()
    kb["metadata"]["version"] = "2.1"
    
    # Пробуем PubMed для пары пород
    if force:
        for breed in list(kb.get("breeds", {}).keys())[:2]:
            print(f"\n  🔬 PubMed: '{breed} dog disease'")
            pmids = search_pubmed(f"{breed} dog disease predisposition")
            if pmids:
                print(f"     Найдено статей: {len(pmids)}")
            time.sleep(1)
    
    return kb

def main():
    print("=" * 70)
    print("  🧠 VET KNOWLEDGE v2.1 — Референсы + Автообновление")
    print("=" * 70)
    
    import sys
    force = "--force" in sys.argv
    
    kb = load_or_create_kb()
    kb = update_knowledge_base(kb, force=force)
    
    # Покажем референсы
    print(f"\n{'─'*50}")
    print("  РЕФЕРЕНСНЫЕ ЗНАЧЕНИЯ")
    print(f"{'─'*50}")
    for species in ["dog", "cat"]:
        ref = kb["reference_values"].get(species, {})
        print(f"\n  {species.upper()}:")
        print(f"    ЧСС: {ref.get('hr_resting', '?')} уд/мин")
        print(f"    ЧДД: {ref.get('rr_resting', '?')} в мин")
        print(f"    Температура: {ref.get('temp_c', '?')} °C")
        print(f"    SpO2 min: {ref.get('spo2_min', '?')}%")
    
    save_kb(kb)

if __name__ == "__main__":
    main()