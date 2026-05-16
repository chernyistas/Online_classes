from rest_framework.exceptions import ValidationError


def validate_youtube_link(value):
    """Проверяет, что ссылка ведёт на YouTube"""
    if not value:
        return value

    if not (value.startswith("https://www.youtube.com") or value.startswith("https://youtu.be/")):
        raise ValidationError("Можно использовать только ссылки на YouTube")
    return value
