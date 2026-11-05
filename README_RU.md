# AVNI Genesis Kit 0.1

**Verified Agent Handoff** — локальный CLI-инструмент для упаковки, восстановления, проверки и ведения истории происхождения Python-агентов.

Это экспериментальный MVP. Он **не** обещает автономное самоулучшение, безопасное исполнение недоверенного кода, побитовое совпадение сборок на любых платформах или эквивалентность ответов произвольных LLM.

## Что уже реализовано

- `genome.json`: формальное описание агента и allowlist файлов.
- Проверка SHA-256 для каждого разрешённого артефакта.
- Проверка типовых признаков секретов и запрет на упаковку контрольных директорий.
- Детерминированный ZIP-пакет с манифестом и историей lineage.
- Восстановление/репликация в новую директорию без сети и без установки зависимостей.
- Новый `organism_id` для потомка, тот же `genome_id`, ссылка на родителя.
- Acceptance-тесты в отдельном Python-процессе с timeout.
- Сравнение фактических результатов потомка и родителя.
- Локальная hash-chain история поколений.
- Необязательная подпись отчётов Ed25519.
- Команда `avni status` с определением drift allowlisted-файлов.
- Автоматические тесты и GitHub Actions workflow.

## Требования

- Python 3.11 или новее.
- Для основного ядра сторонние библиотеки не нужны.
- Для Ed25519-подписи нужен пакет `cryptography`.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[signing,dev]"
```

## Первый запуск

```bash
avni init hello-agent
cd hello-agent
avni validate
avni status
avni verify
avni build
```

Ожидаемый результат `avni verify` для демонстрационного агента: **3 passed, 0 failed**.

## Команды

```text
avni init NAME [--path DIR]
avni validate [DIR]
avni status [DIR]
avni seal [DIR] [--note TEXT]
avni build [DIR] [--output FILE]
avni replicate PACKAGE --dest DIR
avni restore PACKAGE --dest DIR
avni verify [DIR] [--against PARENT_DIR] [--timeout SECONDS] [--sign]
avni lineage [DIR]
avni keygen [DIR]
avni verify-report REPORT [--signature FILE]
```

Подробная спецификация: `docs/SPECIFICATION.md`. Позиционирование: `docs/PRODUCT_POSITIONING.md`.
