from django import template
from django.db.models import Count
from ..models import Category

register = template.Library()


@register.simple_tag
def get_top_categories(count=5):
    """Возвращает топ категорий по количеству транзакций"""
    return Category.objects.annotate(
        transaction_count=Count('transactions')
    ).order_by('-transaction_count')[:count]


@register.inclusion_tag('blog/tags/category_list.html')
def show_categories(limit=10):
    """Отображает список категорий (шаблонный тег включения)"""
    categories = Category.objects.annotate(
        transaction_count=Count('transactions')
    ).order_by('-transaction_count')[:limit]
    return {'categories': categories}


@register.simple_tag
def get_user_categories(limit=10):
    """Возвращает QuerySet категорий пользователя"""
    return Category.objects.annotate(
        transaction_count=Count('transactions')
    ).order_by('-transaction_count')[:limit]


@register.inclusion_tag('blog/tags/user_categories.html', takes_context=True)
def show_user_categories(context, limit=10):
    """
    Шаблонный тег с контекстными переменными. Получает доступ к request.user через контекст.
    """
    request = context.get('request')
    
    if request and request.user.is_authenticated:
        categories = Category.objects.filter(
            user=request.user
        ).annotate(
            transaction_count=Count('transactions')
        ).order_by('-transaction_count')[:limit]
    else:
        categories = Category.objects.none()
    
    return {
        'categories': categories,
        'user': request.user if request else None,
    }

