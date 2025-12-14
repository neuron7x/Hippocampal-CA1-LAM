# Тема та Мета Проекту / Project Theme and Goal

---

## 🎯 ТЕМА ПРОЕКТУ

**Обчислювальна модель ламінарної архітектури гіпокампальної області CA1 для нейробіологічних досліджень та інтеграції штучного інтелекту**

> Computational Model of Hippocampal CA1 Laminar Architecture for Neurobiological Research and AI Integration

### Ключові аспекти теми:

1. **Біофізична точність** — модель базується на реальних експериментальних даних (58,065 клітин, smFISH транскриптоміка)
2. **Ламінарна структура** — чотиришарова організація CA1 (stratum oriens, pyramidale, radiatum, lacunosum-moleculare)
3. **Пластичність** — уніфікована система ваг з Ca²⁺-залежною пластичністю (LTP/LTD)
4. **Динамічні стани** — перемикання Theta-SWR (Sharp-Wave Ripple) режимів
5. **ШІ-інтеграція** — модуль пам'яті для великих мовних моделей (LLM)

---

## 🎯 МЕТА ПРОЕКТУ

**Створення виробничо-готової (production-ready), науково-обґрунтованої обчислювальної моделі CA1 гіпокампу для:**

### 1. Фундаментальних нейронаукових досліджень
- Моделювання механізмів пам'яті та навчання
- Дослідження фазової прецесії та theta-ритмів
- Аналіз replay-механізмів консолідації пам'яті
- Валідація біофізичних параметрів

### 2. Застосувань штучного інтелекту
- Біологічно натхненна довготривала пам'ять для LLM
- Покращення retrieval-augmented generation (RAG) систем
- Механізми novelty-фільтрації для ефективного зберігання
- Theta-phase кодування для семантичного пошуку

### 3. Освітніх цілей
- Демонстрація принципів обчислювальної нейронауки
- Практичне розуміння синаптичної пластичності
- Вивчення взаємодії біології та штучного інтелекту

---

## 📊 Наукова база проекту

| Компонент | Джерело | Дані | DOI |
|-----------|---------|------|-----|
| Ламінарні маркери | Pachicano 2025 | 58,065 клітин | 10.1038/s41467-025-66613-y |
| Ca²⁺ пластичність | Graupner 2012 | Експериментальна калібрація | 10.1073/pnas.1109359109 |
| BTSP | Bittner 2017 | Поведінковий тайминг | 10.1126/science.aan3846 |
| OLM контроль | Udakis 2025 | Записи нейронних ланцюгів | 10.1038/s41467-025-64859-0 |
| HippoRAG | Gutiérrez 2025 | Multi-hop QA | 10.48550/arXiv.2405.14831 |

---

## ✅ Критерії успіху

Проект вважається успішним, якщо:

1. **Ламінарна структура**: I(L;z) > 0.1 (інформаційний виграш)
2. **Динамічна стабільність**: ρ(W) < 1.0 (спектральний радіус)
3. **Фазова прецесія**: |κ| > 0.5 (значущий нахил)
4. **Якість replay**: кореляція > 0.5
5. **Відтворюваність**: 5/5 golden тестів проходять (seed=42)

---

## 📁 Структура проекту

```
Hippocampal-CA1-LAM/
├── core/           # Core: laminar structure, neuron model
├── plasticity/     # Plasticity: Ca²⁺, BTSP, OLM
├── ai_integration/ # AI: memory module for LLM
├── validation/     # Validation: 5 biological criteria
├── data/           # Data: biophysical parameters
├── examples/       # Usage examples
└── docs/           # Documentation
```

---

## 🔬 Практичне застосування

### Для дослідників:
```python
from core import CA1Population
from plasticity import SynapseManager

# Створення популяції CA1 нейронів
pop = CA1Population(N=1000, layers=4, params=params)
syn = SynapseManager(connectivity, weights, params)
# ... симуляція
```

### Для AI-розробників:
```python
from ai_integration import LLMWithCA1Memory

# Інтеграція з LLM
memory = LLMWithCA1Memory(params)
memory.process_step(hidden_state, value, position)
retrieved = memory.retrieve_and_fuse(query)
```

---

**Версія / Version**: 2.0  
**Статус / Status**: Production-Ready ✓  
**Дата / Date**: December 2025

---

*"Від біологічної структури до обчислювальної точності та інтеграції ШІ — все на основі рецензованих наукових даних."*
