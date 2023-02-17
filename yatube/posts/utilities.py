from django.core.paginator import Paginator


POSTS_ON_PAGES = 10


def get_paginator(posts, request):
    paginator = Paginator(posts, POSTS_ON_PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
