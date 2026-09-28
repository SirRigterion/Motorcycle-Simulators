[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-2E8B57?style=flat-square)](https://docs.python.org/3/library/tkinter.html)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=flat-square)](#требования)

# Motorcycle Simulator

> Два настольных симулятора мотоцикла на Python и Tkinter: обычная версия и Crazy Edition с нитро, лазером и противниками.

## Версии

| Файл | Описание |
| --- | --- |
| `moto.py` | Симулятор Kawasaki Ninja 400: управление мотоциклом, передачи, скорость, топливо, температура, дистанция и визуальные эффекты. |
| `motoCRAZY.py` | Crazy Edition: отдельная версия с нитроускорением, лазерным выстрелом, противниками и дополнительными эффектами. |

Обе версии запускаются независимо друг от друга. Это локальное развлекательное приложение, не связанное с производителем мотоциклов.

## Требования

- Python 3
- Tkinter (обычно входит в установщик Python; в некоторых дистрибутивах Linux устанавливается отдельно)
- Для сборки `.exe`: Windows и PyInstaller

Сторонние Python-пакеты не требуются. Для проверки Tkinter можно выполнить:

```bash
python -m tkinter
```

Если в Linux команда сообщает, что Tkinter отсутствует, установите пакет Tkinter средствами своего дистрибутива и повторите проверку.

## Сборка Windows-приложений

Готовые Windows-сборки находятся в `dist/` после сборки. Чтобы запустить их, откройте соответствующий файл:

- `dist/MotorcycleSimulator.exe` — обычная версия.
- `dist/MotorcycleSimulatorCrazy.exe` — Crazy Edition.

Чтобы пересобрать приложения на Windows, откройте PowerShell в корне проекта и выполните:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name MotorcycleSimulator --distpath dist --workpath build moto.py
python -m PyInstaller --noconfirm --onefile --windowed --name MotorcycleSimulatorCrazy --distpath dist --workpath build motoCRAZY.py
```

PyInstaller собирает автономные приложения без консольного окна. Сборку `.exe` нужно выполнять в Windows: PyInstaller формирует приложение для текущей операционной системы и архитектуры, поэтому Windows-сборки не запускаются как приложения Linux или macOS.

## Запуск

Откройте терминал в папке проекта и запустите одну из версий:

```bash
python moto.py
```

```bash
python motoCRAZY.py
```

В Linux или macOS вместо `python` может потребоваться команда `python3`. На Windows также можно использовать `py moto.py` или `py motoCRAZY.py`.

## Управление

### Обычная версия

| Клавиши | Действие |
| --- | --- |
| `W` / `стрелка вверх` | Газ |
| `S` / `стрелка вниз` | Тормоз |
| `A` / `D` или стрелки влево / вправо | Руление |
| `Q` / `E` | Понизить / повысить передачу |
| `Space` | Включить или выключить двигатель |
| `R` | Сбросить симуляцию |

### Crazy Edition

| Клавиши | Действие |
| --- | --- |
| `W` / `стрелка вверх` | Газ |
| `S` / `стрелка вниз` | Тормоз |
| `A` / `D` или стрелки влево / вправо | Руление |
| `Q` / `E` | Понизить / повысить передачу |
| `Space` | Включить или выключить двигатель |
| `F` или `X` + газ | Нитроускорение |
| `Shift` | Лазерный выстрел |
| `R` | Сбросить симуляцию |

## Структура проекта

```text
.
├── moto.py
├── motoCRAZY.py
├── README.md
├── .gitignore
└── dist/  # готовые .exe
```

## Лицензия

Проект распространяется по лицензии [PolyForm Noncommercial 1.0.0](LICENSE). Она разрешает использование в некоммерческих целях и не предоставляет разрешения на коммерческое использование. Перед использованием ознакомьтесь с полным текстом лицензии.

Это source-available проект, а не Open Source по определению OSI: лицензии Open Source не могут запрещать коммерческое использование.