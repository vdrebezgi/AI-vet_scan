
---

# 🇬🇧 English version

```md
# AI VetScan — Veterinary AI Diagnostic System

## About the Project

AI VetScan is a prototype Clinical Decision Support System (CDSS) designed for rapid screening of respiratory and cardiovascular abnormalities in dogs and cats.

The project combines machine learning, medical data processing, and veterinary knowledge bases to support preliminary diagnostic decision-making.

## Project Goal

The main goal is to explore how AI can support veterinary medicine through:

- respiratory sound analysis;
- cardiac sound classification;
- structured veterinary data processing;
- decision support tools.

## My Role

Project author and developer.

Responsibilities included:
- researching the domain area;
- collecting and structuring datasets;
- preparing and validating data;
- developing ML-based solutions;
- testing model outputs;
- organizing project structure and documentation.

---

# Features

## 🫁 PulmoScan

Respiratory sound analysis:
- detection of abnormal sounds;
- respiratory pattern evaluation;
- preliminary localization of possible issues.

## ❤️ CardioFlow

Heart sound analysis:
- classification of:
  - normal sounds;
  - murmurs;
  - arrhythmia-related patterns;
  - artifacts.

## 💊 PharmaDSS

Veterinary medication knowledge base:
- 323 medications;
- dosage calculation by species and weight;
- structured drug information.

## 🧠 VetKnowledge

Veterinary knowledge base:
- 75 dog breeds;
- 23 cat breeds;
- genetic risks;
- reference values;
- medication safety information.

## 🔍 DataHunter

Dataset preparation tools:
- automated dataset collection;
- Kaggle CLI integration;
- file monitoring.

## 🐹 DataMole

Audio data preparation:
- sorting;
- validation;
- preprocessing.

---

# Model Results

| Model | Dataset | Accuracy |
|---|---|---|
| PulmoNet v2 | ICBHI 2017 (920 recordings) | 80.6% |
| CardioNet Vet | PhysioNet + PASCAL + Kaggle Heartbeat (4000+ recordings) | 85.8% |
| CHF Risk Scorer | Heart Failure Clinical Records (299 patients) | 83.3% |

---

# Tech Stack

Python • TensorFlow/Keras • Scikit-learn • SciPy • Matplotlib • Kaggle API • PubMed API

---

# Project Status

The project is actively under development.

Future plans include preparing an autonomous device version based on ESP32.
