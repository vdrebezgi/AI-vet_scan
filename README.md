# AI VetScan — Ветеринарный AI-диагностический комплекс

Система поддержки врачебных решений (CDSS) для скоростного скрининга патологий дыхательной и сердечно-сосудистой систем у собак и кошек.

## Возможности

- 🫁 **PulmoScan** — анализ аудиозаписей дыхания: выявление хрипов (сухих/влажных/смешанных), оценка частоты дыхания, локализация патологии
- ❤️ **CardioFlow** — анализ сердечных звуков: классификация нормы, шумов, экстрасистол, артефактов (4 класса)
- 💊 **PharmaDSS** — база из 323 ветеринарных препаратов с авторасчётом дозировок по виду и весу
- 🧠 **VetKnowledge** — база знаний: 75 пород собак + 23 породы кошек с генетическими рисками, референсные значения, проверка лекарственной токсичности
- 🔍 **DataHunter** — автосборщик датасетов (Kaggle CLI, мониторинг файловой системы)
- 🐹 **DataMole** — сортировщик и валидатор аудиоданных

## Точность моделей

| Модель | Данные | Точность |
|:---|:---|:---|
| PulmoNet v2 | ICBHI 2017 (920 записей) | 80.6% |
| CardioNet Vet | PhysioNet + PASCAL + Kaggle Heartbeat (4000+ записей) | 85.8% |
| CHF Risk Scorer | Heart Failure Clinical Records (299 пациентов) | 83.3% |

## Быстрый старт

```bash
git clone [https://github.com/vdrebezgi/AI-vet_scan.git](https://github.com/vdrebezgi/AI-vet_scan.git)
cd AI-vet_scan
pip install tensorflow scipy scikit-learn matplotlib joblib
python vet_station.py
Выбрать [4] для тестового анализа или [6] для своего WAV-файла.
```

## Структура проекта
pilot-pulmoscan/
├── vet_station.py          # Центр управления (главный файл для запуска)
├── vet_scanner_v3.py       # Автономный анализатор (собаки + кошки)
├── vet_knowledge_v2.py     # База знаний с автообновлением из PubMed
├── pharma_hunter.py        # Охотник за дозировками
├── data_hunter.py          # Автосборщик датасетов
├── data_mole.py            # Сортировщик аудиоданных
├── pulmoscan_pro.py        # Анализатор лёгких с врачебным заключением
├── import_breeds.py        # Импорт пород в базу знаний
├── generate_case.py        # Генератор 3D-корпуса прибора
├── vet_knowledge_base.json # База знаний (породы + референсы)
├── pharma_base_enriched.json # База лекарств
├── breeds_extra.json       # Расширенная база пород собак
├── breeds_cats.json        # База пород кошек
├── case_drawing.svg        # Чертёж корпуса
└── case_3d.step            # 3D-модель корпуса

## Технологический стек
Python TensorFlow/Keras scikit-learn SciPy Matplotlib Kaggle CLI PubMed API

## Статус
Проект в активной разработке. Готовится версия для ESP32 (автономный прибор).
