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


# Create your views here.

def parse_rozetka(session, url):
    all_titles = []
    all_prices = []
    all_images = []
    all_ratings = []

    response = session.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    pagination_items = soup.select('a.pagination__link')
    last_page = max([int(item.get_text()) for item in pagination_items if item.get_text().isdigit()])

    # (перші 4)
    for page in range(1, min(5, last_page + 1)):
        paginated_url = f"{url}?page={page}"
        response = session.get(paginated_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        product_elements = soup.select('div.goods-tile__inner')

        for product in product_elements:
            title_elem = product.select_one('span.goods-tile__title')
            title = title_elem.get_text(strip=True) if title_elem else "Назва вiдсутня"
            all_titles.append(title)

            price_elem = product.select_one('span.goods-tile__price-value')
            price = price_elem.get_text(strip=True) if price_elem else "Цiна вiдсутня"
            all_prices.append(price)

            images = [img['src'] for img in soup.find_all('img', class_='ng-lazyloaded')]
            all_images.extend(images)

            rating = random.randint(0, 5)
            all_ratings.append(rating)

    products = list(zip(all_titles, all_prices, all_images, all_ratings))
    return products


def setup_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[503, 500, 502, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        "DNT": "1"  # Do Not Track
    })
    return session


def parse_hotline(session, url):
    response = session.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    all_titles = []
    all_prices = []
    all_images = []
    all_ratings = []

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        products = soup.select("div.list-item__info")

        for index, product in enumerate(products):
            title = product.find("a", class_="item-title").text.strip() if product.find("a",
                                                                                        class_="item-title") else "Назва відсутня"
            all_titles.append(title)

            try:
                price_elements = driver.find_elements(By.CLASS_NAME, "list-item__value-price")
                if index < len(price_elements):
                    price_text = price_elements[index].text
                    price_match = re.search(r'\d[\d\s]*', price_text)
                    if price_match:
                        price = price_match.group(0).replace("\xa0", "").strip()
                    else:
                        price = "Ціна відсутня"
                    all_prices.append(price)
                else:
                    all_prices.append("Ціна відсутня")

            except Exception as e:
                print(f"Помилка парсингу ціни: {e}")
                all_prices.append("Ціна відсутня")

            image_tag = product.find_previous("img", class_="rounded-border--sm")
            image_url = "https://hotline.ua" + image_tag["src"] if image_tag else "Зображення відсутнє"
            all_images.append(image_url)

            rating = random.randint(0, 5)
            all_ratings.append(rating)

    finally:
        driver.quit()

    products = list(zip(all_titles, all_prices, all_images, all_ratings))
    return products


def parse_url_view(request):
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url_field']
            try:
                session = setup_session()

                if 'rozetka' in url:
                    products = parse_rozetka(session, url)
                    request.session['products'] = products
                    return render(request, 'parser_app/success.html', {'products': products})

                elif 'hotline' in url:
                    products = parse_hotline(session, url)
                    request.session['products'] = products
                    return render(request, 'parser_app/success.html', {'products': products})
                else:
                    return render(request, 'parser_app/error.html', {'error': 'Unsupported URL'})

            except requests.exceptions.RequestException as e:
                return render(request, 'parser_app/error.html', {'error': str(e)})
    else:
        form = URLForm()

    return render(request, 'parser_app/my_form.html', {'form': form})


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


def other_functionality(request):
    return redirect('my_simple_form')
