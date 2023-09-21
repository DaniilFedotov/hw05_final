# Yatube
### Описание
Социальная сеть для блогеров.
Учебный проект, представляющий собой социальную сеть для блогеров, где можно размещать
свои посты, которые могут содержать картинки или относиться к существующим сообществам.

### Как запустить проект
Клонировать репозиторий и перейти в него в командной строке:
```sh
git clone https://github.com/DaniilFedotov/hw05_final.git
```
```sh
cd hw05_final
```

Cоздать и активировать виртуальное окружение:
```sh
python3 -m venv venv
```
```sh
source venv/bin/activate
```

Установить зависимости из файла requirements.txt:
```sh
python3 -m pip install --upgrade pip
```
```sh
pip install -r requirements.txt
```

Далее нужно перейти в папку проекта и выполнить миграции:
```sh
cd yatube
```
```sh
python3 manage.py makemigrations
```
```sh
python3 manage.py migrate
```

После этого необходимо создать файл .env и заполнить его в соответствии с примером .env.example.
Затем запустить проект локально:
```sh
python3 manage.py runserver
```

Для демонстрации работы сайта в директории предусмотрена тестовая база данных.