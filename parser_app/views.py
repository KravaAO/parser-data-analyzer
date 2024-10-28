from django.shortcuts import render
import requests
from urllib3 import Retry
from requests.adapters import HTTPAdapter
from .forms import URLForm
from django.http import JsonResponse, HttpResponse
from openpyxl import Workbook
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re
import random
from bs4 import BeautifulSoup
import json
from django import forms


class URLForm(forms.Form):
    url_field = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control styled-input',  # додаємо власний CSS клас
            'placeholder': 'Введіть URL посилання'  # додати підказку для зручності
        })
    )


# Create your views here.

def parse_url_view(request):
    if request.method == 'POST':
        url = request.POST.get('url_field')  # отримуємо URL з форми
        try:
            response = requests.get(url)
            response.raise_for_status()  # перевірка на помилки
            html_content = response.text
        except requests.RequestException as e:
            return render(request, 'parser_app/error.html', {'error': str(e)})

        return render(request, 'parser_app/success.html', {'html_content': html_content})

    return render(request, 'parser_app/my_form.html', {'form': URLForm})


def parse_selected_blocks_view(request):
    if request.method == 'POST':
        selected_blocks = request.POST.getlist('selected_blocks')

        # Process selected blocks
        parsed_content = [block for block in selected_blocks]

        return render(request, 'parser_app/parsed_blocks.html', {'parsed_content': parsed_content})


def export_to_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    products = request.session.get('products', [])
    writer = csv.writer(response)
    writer.writerow(['Назва товару', 'Ціна (грн)', 'Зображення'])

    for product in products:
        writer.writerow(product)

    return response


def export_to_json(request):
    products = request.session.get('products', [])
    data = [{'title': title, 'price': price, 'image': image} for title, price, image in products]

    return JsonResponse(data, safe=False)


def export_to_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Товари"
    ws.append(['Назва товару', 'Ціна (грн)', 'Рейтинг', 'Зображення'])
    products = request.session.get('products', [])
    for title, price, image, rating in products:
        ws.append([title, price, rating, image])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="products.xlsx"'
    wb.save(response)

    return response
