### Инструкция для старта локальной разработки

1. Создайте локальное окружение
```bash
python3 -m venv venv
```
2. Активируйте созданное окружение 

<br>для MacOS</br>
```bash
source venv/bin/activate
```
<br>для Windows</br>
```bash
venv\Scripts\activate
```

3. Установите необходимые зависимости
```bash
pip3 -r deploy/requirements.txt 
```

4. Поднимите контейнеры с помощью Makefile
```bash
make local-start
```
