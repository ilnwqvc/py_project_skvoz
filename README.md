Запуск setup_env.bat
Для запуска, в консоли cmd/терминал windows/VS Code необходимо написать комманду cd <ваш путь к папке с прокетом>/scripts.

 - Далее для cmd написать комманду setup_env.bat.
 - Для терминал windows/терминал VS Code написать комманду .\setup_env.bat. 

Произойдет запуск файла, установка окружения и зависимостей, сам smoke test с итоговым результатом.

## Extract — запуск (Windows)

1. Установить зависимости:

pip install -r requirements.txt

2. Запуск:

python src/extract.py

3. Результат:

В папке data/raw/JP_TYO/ появится JSON-файл с датой и временем загрузки.