"""
PulmoScan PRO — Умный анализатор лёгких с врачебными заключениями
"""
import numpy as np
import tensorflow as tf
from scipy.io import wavfile
from scipy.signal import butter, filtfilt, resample, find_peaks, spectrogram
from collections import Counter
import json, os, sys, warnings
warnings.filterwarnings('ignore')

# ==========================================
# БАЗА ЗНАНИЙ
# ==========================================
LUNG_PATTERNS = {
    'normal': {
        'description': 'Дыхание везикулярное, проводится по всем полям',
        'recommendation': 'Патологии не выявлено. Плановое наблюдение.',
        'differential': [],
        'drugs': []
    },
    'wheeze_dry': {
        'description': 'Сухие свистящие хрипы, преимущественно на выдохе',
        'differential': ['Бронхит', 'Астма', 'Коллапс трахеи', 'Инородное тело'],
        'recommendation': 'Рентген ОГК, бронхоскопия. Исключить инородное тело.',
        'drugs': ['Преднизолон', 'Теофиллин', 'Доксициклин']
    },
    'wheeze_wet': {
        'description': 'Влажные хрипы (крепитация), преимущественно на вдохе',
        'differential': ['Пневмония', 'Отёк лёгких', 'Бронхопневмония'],
        'recommendation': 'Рентген ОГК, анализ крови. Исключить кардиогенный отёк!',
        'drugs': ['Амоксициллин', 'Марбофлоксацин', 'Фуросемид (при отёке)']
    },
    'wheeze_mixed': {
        'description': 'Смешанные хрипы (сухие + влажные)',
        'differential': ['Бронхопневмония', 'ХОБЛ', 'Тяжёлый бронхит'],
        'recommendation': 'Рентген ОГК, бронхоальвеолярный лаваж. Антибиотики + бронходилататоры.',
        'drugs': ['Марбофлоксацин', 'Теофиллин', 'Амоксициллин']
    }
}

BREED_RISKS = {
    'кавалер-кинг-чарльз': {'heart': 0.9, 'notes': 'Группа риска по митральной недостаточности'},
    'доберман': {'heart': 0.8, 'notes': 'Риск ДКМП'},
    'боксёр': {'heart': 0.7, 'notes': 'Риск аритмогенной кардиомиопатии'},
    'мопс': {'respiratory': 0.9, 'notes': 'Брахицефалический синдром'},
    'бульдог': {'respiratory': 0.9, 'notes': 'Брахицефалический синдром'},
    'такса': {'heart': 0.6, 'notes': 'Риск митральной недостаточности'},
}

# ==========================================
# DSP
# ==========================================
def butter_bandpass(lowcut, highcut, fs, order=4):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

def clean_lung_signal(signal, fs):
    b, a = butter_bandpass(200, 1800, fs, order=4)
    return filtfilt(b, a, signal)

def analyze_wheeze_character(segment, fs):
    """Определяет характер хрипов: dry, wet, mixed, none"""
    try:
        f, t, Sxx = spectrogram(segment, fs, nperseg=256, noverlap=200)
        
        low_mask = (f >= 100) & (f <= 400)
        high_mask = (f >= 400) & (f <= 800)
        vh_mask = (f >= 800) & (f <= 1500)
        
        low_energy = np.mean(Sxx[low_mask, :]) if np.any(low_mask) else 0
        high_energy = np.mean(Sxx[high_mask, :]) if np.any(high_mask) else 0
        vh_energy = np.mean(Sxx[vh_mask, :]) if np.any(vh_mask) else 0
        
        total = low_energy + high_energy + vh_energy + 1e-10
        low_ratio = low_energy / total
        high_ratio = high_energy / total
        vh_ratio = vh_energy / total
        
        if vh_ratio > 0.4 and high_ratio > 0.3:
            return 'dry'
        elif low_ratio > 0.4:
            return 'wet'
        elif high_ratio > 0.3 and low_ratio > 0.3:
            return 'mixed'
        else:
            return 'none'
    except:
        return 'none'

def estimate_respiratory_rate(signal, fs):
    """Оценка частоты дыхания по огибающей амплитуды"""
    envelope = np.abs(signal)
    window_size = int(0.5 * fs)
    if len(envelope) > window_size:
        envelope = np.convolve(envelope, np.ones(window_size)/window_size, mode='same')
    threshold = np.mean(envelope) * 1.5
    distance = int(1.0 * fs)
    peaks, _ = find_peaks(envelope, distance=distance, height=threshold)
    if len(peaks) >= 2:
        intervals = np.diff(peaks) / fs
        rr = 60.0 / np.median(intervals)
        return max(5, min(80, rr))
    return 0

# ==========================================
# ЗАГРУЗКА МОДЕЛИ
# ==========================================
print("Загрузка PulmoNet...")
MODEL_PATH = r"C:\Users\пользователь\PulmoScan\pulmonet_precise_v2.h5"
pulmonet = tf.keras.models.load_model(MODEL_PATH)

# ==========================================
# АНАЛИЗ
# ==========================================
def analyze_lungs_pro(wav_path, patient_info=None):
    """Полный анализ лёгких с врачебным заключением"""
    if patient_info is None:
        patient_info = {'species': 'dog', 'breed': 'неизвестно', 'age': 5, 'weight_kg': 10}
    
    print("=" * 70)
    print("  🫁 PULMOSCAN PRO — Анализ дыхательной системы")
    print("=" * 70)
    
    # Загрузка аудио
    fs, audio = wavfile.read(wav_path)
    if len(audio.shape) > 1:
        audio = audio[:, 0]
    audio = audio.astype(np.float32)
    original_dur = len(audio) / fs
    
    print(f"\n  📂 Файл: {os.path.basename(wav_path)}")
    print(f"  ⏱️ Длительность: {original_dur:.1f} сек, {fs} Гц")
    
    # Ресемплинг
    if fs != 4000:
        new_len = int(len(audio) * 4000 / fs)
        audio = resample(audio, new_len)
        fs = 4000
    
    # Фильтрация
    audio_clean = clean_lung_signal(audio, fs)
    
    # Нарезка на окна
    window = 3 * fs
    step = window // 2
    segments = []
    for start in range(0, len(audio_clean) - window + 1, step):
        seg = audio_clean[start:start + window]
        rms = np.sqrt(np.mean(seg**2))
        if rms > 1e-8:
            seg = seg / rms
        segments.append(seg)
    
    if not segments:
        print("  ❌ Сигнал слишком короткий!")
        return None
    
    segments = np.array(segments, dtype=np.float32)
    
    # Прогон через модель
    preds = pulmonet.predict(segments, verbose=0)
    wheeze_scores = preds[:, 1]
    mean_wheeze = np.mean(wheeze_scores)
    
    # Частота дыхания
    rr = estimate_respiratory_rate(audio_clean, fs)
    
    # Характер хрипов
    wheeze_mask = wheeze_scores > 0.5
    character = 'none'
    if np.sum(wheeze_mask) > 0:
        wheeze_segs = segments[wheeze_mask]
        chars = [analyze_wheeze_character(s, fs) for s in wheeze_segs[:10]]
        char_counts = Counter(chars)
        if 'none' in char_counts:
            del char_counts['none']
        if char_counts:
            character = char_counts.most_common(1)[0][0]
    
    # Определение паттерна
    if mean_wheeze > 0.7:
        severity = 'ВЫСОКАЯ'
        alert = '🔴'
        if character == 'dry':
            pattern_key = 'wheeze_dry'
        elif character == 'wet':
            pattern_key = 'wheeze_wet'
        else:
            pattern_key = 'wheeze_mixed'
    elif mean_wheeze > 0.5:
        severity = 'СРЕДНЯЯ'
        alert = '🟡'
        pattern_key = 'wheeze_mixed' if character != 'none' else 'wheeze_dry'
    else:
        severity = 'НИЗКАЯ'
        alert = '🟢'
        pattern_key = 'normal'
    
    pattern = LUNG_PATTERNS[pattern_key]
    
    # === ВЫВОД ===
    print(f"\n  🐶 ПАЦИЕНТ:")
    print(f"     Вид: {patient_info.get('species', 'dog')}")
    print(f"     Порода: {patient_info.get('breed', 'неизвестно')}")
    print(f"     Возраст: {patient_info.get('age', '?')} лет")
    print(f"     Вес: {patient_info.get('weight_kg', '?')} кг")
    
    print(f"\n  📊 РЕЗУЛЬТАТЫ:")
    print(f"  ┌─────────────────────────────────────┐")
    print(f"  │ Вероятность хрипов:  {mean_wheeze:.1%}          │")
    print(f"  │ Характер хрипов:     {character:<14} │")
    print(f"  │ Тяжесть:             {severity:<14} │")
    if rr > 0:
        print(f"  │ Частота дыхания:     {rr:.0f} в мин          │")
    print(f"  └─────────────────────────────────────┘")
    print(f"  {alert} {severity} ВЕРОЯТНОСТЬ ПАТОЛОГИИ")
    
    # Заключение
    print(f"\n  📝 ЗАКЛЮЧЕНИЕ:")
    print(f"  {pattern['description']}")
    
    if pattern_key != 'normal':
        print(f"\n  🩺 ДИФФЕРЕНЦИАЛЬНЫЙ ДИАГНОЗ:")
        for i, d in enumerate(pattern['differential'], 1):
            print(f"     {i}. {d}")
        
        # Проверка породных рисков
        breed = patient_info.get('breed', '').lower()
        if breed in BREED_RISKS:
            risks = BREED_RISKS[breed]
            if risks.get('respiratory', 0) > 0.5:
                print(f"\n  ⚠️ ВНИМАНИЕ: {risks['notes']}")
            if risks.get('heart', 0) > 0.5 and pattern_key in ['wheeze_wet', 'wheeze_mixed']:
                print(f"  💔 {risks['notes']} — исключить кардиогенный отёк!")
        
        print(f"\n  📋 РЕКОМЕНДАЦИИ:")
        print(f"  {pattern['recommendation']}")
        
        if pattern['drugs']:
            print(f"\n  💊 ПРЕПАРАТЫ (по показаниям):")
            for drug in pattern['drugs']:
                print(f"     • {drug}")
    else:
        print(f"\n  ✅ {pattern['recommendation']}")
    
    # Сводка по сегментам
    wheezy = [(i, s) for i, s in enumerate(wheeze_scores) if s > 0.5]
    print(f"\n  📊 СЕГМЕНТЫ С ХРИПАМИ ({len(wheezy)}/{len(segments)}):")
    if wheezy:
        for i, s in wheezy[:5]:
            bar = "█" * int(s * 15) + "░" * (15 - int(s * 15))
            print(f"     #{i+1}: {s:.0%} [{bar}]")
        if len(wheezy) > 5:
            print(f"     ... и ещё {len(wheezy)-5}")
    else:
        print(f"     ✅ Хрипы не обнаружены")
    
    print(f"\n{'='*70}")
    print("  Анализ завершён.")
    print(f"{'='*70}")
    
    return {
        'wheeze_prob': float(mean_wheeze),
        'character': character,
        'severity': severity,
        'pattern': pattern_key,
        'respiratory_rate': float(rr),
        'conclusion': pattern['description'],
        'recommendation': pattern['recommendation'],
        'drugs': pattern['drugs']
    }

# ==========================================
# ЗАПУСК
# ==========================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        wav_file = sys.argv[1]
    else:
        wav_file = r"C:\Users\пользователь\PulmoScan\icbhi_data\wheezes\107_2b3_Ar_mc_AKGC417L.wav"
        print("Использую тестовый файл с хрипами.")
        print("Для своего: python pulmoscan_pro.py путь_к_файлу.wav\n")
    
    if not os.path.exists(wav_file):
        print(f"Файл не найден: {wav_file}")
        sys.exit(1)
    
    patient = {
        'species': 'dog',
        'breed': 'кавалер-кинг-чарльз',
        'age': 8,
        'weight_kg': 12,
        'symptoms': 'кашель, одышка, вялость'
    }
    
    result = analyze_lungs_pro(wav_file, patient)