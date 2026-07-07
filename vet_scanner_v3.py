"""
VetScanner v3.0 — АВТОНОМНЫЙ АНАЛИЗАТОР (собаки + кошки)
Запуск: python vet_scanner_v3.py путь_к_wav
"""
import numpy as np
import tensorflow as tf
import joblib
import json
import os
import sys
from datetime import datetime
from scipy.io import wavfile
from scipy.signal import butter, filtfilt, resample, find_peaks
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# ПУТИ
# ==========================================
MODELS = {
    "pulmonet": r"C:\Users\пользователь\PulmoScan\pulmonet_precise_v2.h5",
    "cardionet_vet": r"C:\Users\пользователь\cardioflow\cardionet_veterinary.h5",
    "chf_model": r"C:\Users\пользователь\cardioflow\chf_risk_model.joblib",
    "chf_scaler": r"C:\Users\пользователь\cardioflow\chf_scaler.joblib",
}
KNOWLEDGE_FILE = r"C:\Users\пользователь\pilot-pulmoscan\vet_knowledge_base.json"
PHARMA_FILE = r"C:\Users\пользователь\pharma_base_enriched.json"

# ==========================================
# ЗАГРУЗКА
# ==========================================
print("🔄 Загрузка моделей...")
pulmonet = tf.keras.models.load_model(MODELS["pulmonet"])
cardionet = tf.keras.models.load_model(MODELS["cardionet_vet"])
chf_model = joblib.load(MODELS["chf_model"])
chf_scaler = joblib.load(MODELS["chf_scaler"])
print("✅ Модели загружены")

if os.path.exists(KNOWLEDGE_FILE):
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        KB = json.load(f)
else:
    KB = {"breeds": {}, "cats": {}, "reference_values": {}, "drug_interactions": {}}

if os.path.exists(PHARMA_FILE):
    with open(PHARMA_FILE, 'r', encoding='utf-8') as f:
        PHARMA = json.load(f)
else:
    PHARMA = []

# ==========================================
# DSP
# ==========================================
def butter_bandpass(lowcut, highcut, fs, order=4):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

def clean_signal(signal, fs, band='lung'):
    if band == 'lung':
        b, a = butter_bandpass(200, 1800, fs)
    else:
        b, a = butter_bandpass(20, 500, fs)
    return filtfilt(b, a, signal)

def estimate_rate(signal, fs, mode='rr'):
    envelope = np.abs(signal)
    win = int(0.5 * fs) if mode == 'rr' else int(0.2 * fs)
    if len(envelope) > win:
        envelope = np.convolve(envelope, np.ones(win)/win, mode='same')
    dist = int(1.0 * fs) if mode == 'rr' else int(0.3 * fs)
    threshold = np.mean(envelope) * 1.5
    peaks, _ = find_peaks(envelope, distance=dist, height=threshold)
    if len(peaks) >= 2:
        return 60.0 / np.median(np.diff(peaks) / fs)
    return 0

def analyze_wheeze_type(segments, fs):
    from scipy.signal import spectrogram
    types = []
    for seg in segments:
        try:
            f, t, Sxx = spectrogram(seg, fs, nperseg=256, noverlap=200)
            low = np.mean(Sxx[(f>=100)&(f<=400),:]) if np.any((f>=100)&(f<=400)) else 0
            high = np.mean(Sxx[(f>=400)&(f<=800),:]) if np.any((f>=400)&(f<=800)) else 0
            vh = np.mean(Sxx[(f>=800)&(f<=1500),:]) if np.any((f>=800)&(f<=1500)) else 0
            total = low + high + vh + 1e-10
            if vh/total > 0.4 and high/total > 0.3:
                types.append('dry')
            elif low/total > 0.4:
                types.append('wet')
            elif high/total > 0.3 and low/total > 0.3:
                types.append('mixed')
            else:
                types.append('none')
        except:
            types.append('none')
    c = Counter([t for t in types if t != 'none'])
    return c.most_common(1)[0][0] if c else 'none'

# ==========================================
# АНАЛИЗ ЛЁГКИХ
# ==========================================
def analyze_lungs(wav_path):
    fs, audio = wavfile.read(wav_path)
    if len(audio.shape) > 1:
        audio = audio[:, 0]
    audio = audio.astype(np.float32)
    if fs != 4000:
        audio = resample(audio, int(len(audio)*4000/fs))
        fs = 4000
    
    audio = clean_signal(audio, fs, 'lung')
    window = 3 * fs
    segments = []
    for start in range(0, len(audio) - window + 1, window // 2):
        seg = audio[start:start+window]
        rms = np.sqrt(np.mean(seg**2))
        if rms > 1e-8:
            seg = seg / rms
        segments.append(seg)
    
    if not segments:
        return {"wheeze_prob": 0, "rr": 0, "character": "none", "verdict": "error"}
    
    segments = np.array(segments, dtype=np.float32)
    preds = pulmonet.predict(segments, verbose=0)
    wheeze_prob = float(np.mean(preds[:, 1]))
    rr = estimate_rate(audio, fs, 'rr')
    
    wheeze_mask = preds[:, 1] > 0.5
    character = 'none'
    if np.sum(wheeze_mask) > 0:
        character = analyze_wheeze_type(segments[wheeze_mask][:10], fs)
    
    if wheeze_prob > 0.7:
        verdict = "HIGH"
    elif wheeze_prob > 0.5:
        verdict = "SUSPECT"
    else:
        verdict = "NORMAL"
    
    return {
        "wheeze_prob": wheeze_prob,
        "rr": float(rr),
        "character": character,
        "verdict": verdict,
        "n_segments": len(segments),
        "n_wheezy": int(np.sum(wheeze_mask))
    }

# ==========================================
# АНАЛИЗ СЕРДЦА
# ==========================================
def analyze_heart(wav_path):
    fs, audio = wavfile.read(wav_path)
    if len(audio.shape) > 1:
        audio = audio[:, 0]
    audio = audio.astype(np.float32)
    if fs != 4000:
        audio = resample(audio, int(len(audio)*4000/fs))
        fs = 4000
    
    audio = clean_signal(audio, fs, 'heart')
    window = 6000
    segments = []
    for start in range(0, len(audio) - window + 1, window):
        seg = audio[start:start+window]
        rms = np.sqrt(np.mean(seg**2))
        if rms > 1e-8:
            seg = seg / rms
        segments.append(seg)
    
    if not segments:
        return {"abnormal_prob": 0, "hr": 0, "class": "unknown", "verdict": "error"}
    
    segments = np.array(segments, dtype=np.float32)
    preds = cardionet.predict(segments, verbose=0)
    
    class_names = ['normal', 'murmur', 'extrahls', 'artifact']
    class_idx = np.argmax(np.mean(preds, axis=0))
    abnormal_prob = float(1 - np.mean(preds[:, 0]))
    hr = estimate_rate(audio, fs, 'hr')
    
    if abnormal_prob > 0.7:
        verdict = "HIGH"
    elif abnormal_prob > 0.5:
        verdict = "SUSPECT"
    else:
        verdict = "NORMAL"
    
    return {
        "abnormal_prob": abnormal_prob,
        "hr": float(hr),
        "class": class_names[class_idx],
        "verdict": verdict,
        "class_probs": {name: float(p) for name, p in zip(class_names, np.mean(preds, axis=0))}
    }

# ==========================================
# АНАЛИЗ ПОРОДЫ (СОБАКИ + КОШКИ)
# ==========================================
def _parse_risk_value(val):
    """Безопасно извлекает probability из значения (dict или float)"""
    if isinstance(val, dict):
        return val.get("probability", 0), val.get("age_onset"), val.get("notes", "")
    elif isinstance(val, (int, float)):
        return float(val), None, ""
    return 0, None, ""

def analyze_breed(breed_name, species, lung_result, heart_result):
    breed_lower = breed_name.lower().strip()
    breed_info = None
    breed_found_name = breed_name
    is_cat = species.lower() == 'cat'
    
    search_in = KB.get("cats", {}) if is_cat else KB.get("breeds", {})
    
    for key, info in search_in.items():
        if key.lower() in breed_lower or breed_lower in key.lower():
            breed_info = info
            breed_found_name = key
            break
    
    if not breed_info:
        return {"found": False, "warnings": [], "risks": [], "breed": breed_name}
    
    warnings_list = []
    risks = []
    
    for system in ["heart", "respiratory", "kidney", "ortho", "neuro", "cancer", "eyes", "endocrine", "gi"]:
        system_risks = breed_info.get("risks", {}).get(system, {})
        if isinstance(system_risks, dict):
            for condition, details in system_risks.items():
                prob, age, notes = _parse_risk_value(details)
                if prob > 0.1:
                    risks.append({"system": system, "condition": condition, "probability": prob})
                    msg = f"Риск {condition} ({prob:.0%})"
                    if age:
                        msg = f"Риск {condition} с {age} лет ({prob:.0%})"
                    if notes:
                        msg += f" — {notes}"
                    warnings_list.append(msg)
    
    # Связываем симптомы с породными рисками
    if lung_result.get("verdict") in ["HIGH", "SUSPECT"]:
        if any(r['system'] == 'heart' for r in risks):
            warnings_list.append("🚨 Исключить кардиогенный отёк! Порода в группе риска.")
    
    if heart_result.get("class") == "murmur":
        if any(r['system'] == 'heart' for r in risks):
            suffix = "ЭХО" if is_cat else "ЭХО сердца"
            warnings_list.append(f"Сердечный шум + породный риск — рекомендовано {suffix}.")
    
    return {
        "found": True,
        "breed": breed_found_name,
        "is_cat": is_cat,
        "size": breed_info.get("size", "?"),
        "weight_range": breed_info.get("weight_range_kg", breed_info.get("weight", [])),
        "warnings": warnings_list,
        "risks": risks
    }

# ==========================================
# ПРОВЕРКА ТОКСИЧНОСТИ
# ==========================================
def check_toxicity(drugs_list, species):
    if species.lower() != 'cat':
        return []
    toxic = []
    for drug_name in drugs_list:
        for d in PHARMA:
            if d.get('toxic_cat') and drug_name.upper() in d.get('name', '').upper():
                toxic.append({'drug': drug_name, 'warning': d.get('indications', ['ТОКСИЧЕН'])[0]})
    return toxic

def find_drugs_for_condition(condition, species, weight_kg):
    results = []
    for d in PHARMA:
        indications = d.get('indications', [])
        drug_species = d.get('species', [])
        if species.lower() in drug_species or not drug_species:
            for ind in indications:
                if condition.lower() in ind.lower():
                    dose = d.get('dose_mg_kg', 0)
                    total = round(dose * weight_kg, 1) if dose else 0
                    results.append({
                        'name': d.get('name', '?'),
                        'dose_mg_kg': dose,
                        'dose_total': total,
                        'route': d.get('route', 'oral'),
                        'frequency_h': d.get('frequency_h', '?'),
                        'indication': ind,
                        'toxic_cat': d.get('toxic_cat', False),
                        'notes': d.get('notes', '')
                    })
    return results[:5]

# ==========================================
# ГЛАВНЫЙ АНАЛИЗ
# ==========================================
def full_analysis(wav_path, patient_info=None):
    if patient_info is None:
        patient_info = {"name": "Пациент", "species": "dog", "breed": "метис", "age": 5, "weight_kg": 10}
    
    species = patient_info.get('species', 'dog').lower()
    is_cat = species == 'cat'
    species_label = "Кошка" if is_cat else "Собака"
    
    print("\n" + "=" * 70)
    print("  🧠 VETSCANNER v3.0 — АВТОНОМНЫЙ АНАЛИЗ")
    print("=" * 70)
    print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  📂 {os.path.basename(wav_path)}")
    print(f"  🐶🐱 {patient_info.get('name', '?')}: {species_label}, "
          f"{patient_info.get('breed', '?')}, {patient_info.get('age', '?')} лет, "
          f"{patient_info.get('weight_kg', '?')} кг")
    
    refs = KB.get("reference_values", {}).get(species, {})
    
    lung = analyze_lungs(wav_path)
    heart = analyze_heart(wav_path)
    breed = analyze_breed(patient_info.get("breed", ""), species, lung, heart)
    
    # === ДЫХАТЕЛЬНАЯ ===
    print(f"\n{'─'*70}")
    print(f"  🫁 ДЫХАТЕЛЬНАЯ СИСТЕМА")
    print(f"{'─'*70}")
    
    lv = lung['verdict']
    icon = "🔴" if lv == "HIGH" else "🟡" if lv == "SUSPECT" else "🟢"
    print(f"  {icon} Вероятность хрипов: {lung['wheeze_prob']:.1%} ({lv})")
    if lung['character'] != 'none':
        print(f"     Характер: {lung['character']}")
    if lung['rr'] > 0:
        rr = lung['rr']
        rr_range = refs.get('rr_resting', [10, 30])
        rr_status = "⚠️ ТАХИПНОЭ" if rr > rr_range[1] else "✅ НОРМА"
        print(f"     ЧДД: {rr:.0f} в мин ({rr_status}, норма {rr_range[0]}-{rr_range[1]})")
    print(f"     Хрипы в {lung['n_wheezy']}/{lung['n_segments']} сегментов")
    
    # === СЕРДЕЧНАЯ ===
    print(f"\n{'─'*70}")
    print(f"  ❤️ СЕРДЕЧНО-СОСУДИСТАЯ СИСТЕМА")
    print(f"{'─'*70}")
    
    hv = heart['verdict']
    icon_h = "🔴" if hv == "HIGH" else "🟡" if hv == "SUSPECT" else "🟢"
    print(f"  {icon_h} Патология: {heart['abnormal_prob']:.1%} ({hv})")
    print(f"     Класс: {heart['class']}")
    if heart['hr'] > 0:
        hr = heart['hr']
        hr_range = refs.get('hr_resting', [60, 140])
        if hr > hr_range[1]:
            hr_status = "⚠️ ТАХИКАРДИЯ"
        elif hr < hr_range[0]:
            hr_status = "⚠️ БРАДИКАРДИЯ"
        else:
            hr_status = "✅ НОРМА"
        print(f"     ЧСС: {hr:.0f} уд/мин ({hr_status}, норма {hr_range[0]}-{hr_range[1]})")
    
    print(f"     Детально: норма {heart['class_probs'].get('normal',0):.0%}, "
          f"шум {heart['class_probs'].get('murmur',0):.0%}, "
          f"экстра {heart['class_probs'].get('extrahls',0):.0%}, "
          f"артефакт {heart['class_probs'].get('artifact',0):.0%}")
    
    # Особые примечания для кошек
    if is_cat:
        special = KB.get("reference_values", {}).get("cat", {}).get("special_notes", [])
        if special:
            print(f"\n{'─'*70}")
            print(f"  🐱 ОСОБЫЕ ПРИМЕЧАНИЯ ДЛЯ КОШЕК")
            print(f"{'─'*70}")
            for note in special:
                print(f"  • {note}")
    
    # Породные риски
    if breed['found'] and breed['warnings']:
        print(f"\n{'─'*70}")
        print(f"  ⚠️ ПОРОДНЫЕ РИСКИ: {breed['breed']}")
        print(f"{'─'*70}")
        for w in breed['warnings']:
            print(f"  • {w}")
    
    # Рекомендации
    print(f"\n{'─'*70}")
    print(f"  📋 РЕКОМЕНДАЦИИ")
    print(f"{'─'*70}")
    
    recommendations = []
    drugs = []
    
    if lv in ["HIGH", "SUSPECT"]:
        recommendations.append("🔴 Рентген грудной клетки")
        if lung['character'] == 'wet':
            antibiotics = find_drugs_for_condition("пневмония", species, patient_info.get('weight_kg', 10))
            for a in antibiotics[:2]:
                if a['dose_total'] > 0:
                    recommendations.append(f"💊 {a['name']} — {a['dose_total']} мг {a['route']}")
                else:
                    recommendations.append(f"💊 {a['name']} — {a['dose_mg_kg']} мг/кг {a['route']}")
                drugs.append(a['name'])
            if breed['found'] and any(r['system'] == 'heart' for r in breed.get('risks', [])):
                recommendations.append("💔 Исключить кардиогенный отёк (фуросемид 2 мг/кг)")
                drugs.append("фуросемид")
        elif lung['character'] == 'dry':
            recommendations.append("💊 Бронходилататоры (теофиллин)")
            drugs.append("теофиллин")
    
    if hv in ["HIGH", "SUSPECT"]:
        recommendations.append("🔴 ЭХО сердца")
        if heart['class'] == 'murmur':
            pimo = find_drugs_for_condition("сердечная недостаточность", species, patient_info.get('weight_kg', 10))
            for p in pimo[:1]:
                if p['dose_total'] > 0:
                    recommendations.append(f"💊 {p['name']} — {p['dose_total']} мг")
                drugs.append(p['name'])
    
    if not recommendations:
        recommendations.append("✅ Плановое наблюдение. Патологий не выявлено.")
    
    # Проверка токсичности
    if is_cat and drugs:
        toxic = check_toxicity(drugs, species)
        if toxic:
            print(f"\n  🚨 ТОКСИЧНОСТЬ ДЛЯ КОШЕК!")
            for t in toxic:
                print(f"  ☠️ {t['drug']}: {t['warning']}")
    
    for r in recommendations:
        print(f"  {r}")
    
    print(f"\n{'='*70}")
    print("  ✅ Анализ завершён.")
    print(f"{'='*70}\n")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "patient": patient_info,
        "lungs": lung,
        "heart": heart,
        "breed_risks": breed,
        "recommendations": recommendations
    }

# ==========================================
# ЗАПУСК
# ==========================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        wav_file = sys.argv[1]
    else:
        wav_file = r"C:\Users\пользователь\PulmoScan\raw_icbhi\ICBHI_final_database\120_1b1_Pl_sc_Meditron.wav"
        print("Использую тестовый файл.\n")
    
    if not os.path.exists(wav_file):
        print(f"❌ Файл не найден: {wav_file}")
        sys.exit(1)
    
    # Тест с собакой
    patient_dog = {"name": "Шарик", "species": "dog", "breed": "кавалер-кинг-чарльз", "age": 8, "weight_kg": 12}
    result_dog = full_analysis(wav_file, patient_dog)
    
    # Тест с кошкой
    print("\n" + "=" * 70)
    print("  ТЕСТ С КОШКОЙ")
    print("=" * 70)
    patient_cat = {"name": "Мурка", "species": "cat", "breed": "мейн-кун", "age": 5, "weight_kg": 6}
    result_cat = full_analysis(wav_file, patient_cat)