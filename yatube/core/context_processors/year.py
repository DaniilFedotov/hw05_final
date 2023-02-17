from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    date = datetime.now().year
    return {
        'year': date
    }
