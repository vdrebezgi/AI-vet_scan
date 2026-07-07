"""Импорт пород собак и кошек в vet_knowledge_base.json"""
import json
import os

KB_FILE = r"C:\Users\пользователь\pilot-pulmoscan\vet_knowledge_base.json"
EXTRA_FILES = [
    r"C:\Users\пользователь\pilot-pulmoscan\breeds_extra.json",
    r"C:\Users\пользователь\pilot-pulmoscan\breeds_cats.json"
]

with open(KB_FILE, 'r', encoding='utf-8') as f:
    kb = json.load(f)

if "cats" not in kb:
    kb["cats"] = {}

total_added = 0
for extra_file in EXTRA_FILES:
    if not os.path.exists(extra_file):
        print(f"⚠️ Файл не найден: {extra_file}")
        continue
    
    with open(extra_file, 'r', encoding='utf-8') as f:
        extra = json.load(f)
    
    is_cat = "cat" in extra_file or "кош" in extra_file
    target = kb["cats"] if is_cat else kb["breeds"]
    
    added = 0
    for name, info in extra.items():
        if name not in target:
            target[name] = info
            added += 1
    
    label = "кошек" if is_cat else "собак"
    print(f"✅ {label}: +{added} пород из {os.path.basename(extra_file)}")
    total_added += added

kb["metadata"]["total_breeds"] = len(kb.get("breeds", {}))
kb["metadata"]["total_cats"] = len(kb.get("cats", {}))
kb["metadata"]["last_updated"] = "2026-06-21"

with open(KB_FILE, 'w', encoding='utf-8') as f:
    json.dump(kb, f, indent=2, ensure_ascii=False)

print(f"\n📊 Итого: {kb['metadata']['total_breeds']} собак + {kb['metadata']['total_cats']} кошек = {kb['metadata']['total_breeds'] + kb['metadata']['total_cats']} пород")