from django.shortcuts import render, redirect
import pandas as pd


def clean_price(price):
    return float(price.replace('\xa0', '').replace(' ', '').replace('₴', ''))


def clean_rating(rating):
    return float(rating) if rating else 0


def analyze_data(request):
    products = request.session.get('products', [])

    if not products:
        return redirect('my_simple_form')

    cleaned_products = [(title, clean_price(price), image, clean_rating(rating)) for title, price, image, rating in
                        products]

    df = pd.DataFrame(cleaned_products, columns=['title', 'price', 'image', 'rating'])

    cheapest_products = None
    most_expensive_products = None
    sorted_products = None

    num_items = 5

    if request.method == 'POST':
        action = request.POST.get('action')
        num_items = int(request.POST.get('num_items', 5))

        if action == 'min':
            cheapest_products = df.nsmallest(num_items, 'price')
        elif action == 'max':
            most_expensive_products = df.nlargest(num_items, 'price')

    sort_by = request.GET.get('sort_by')
    if sort_by == 'rating_desc':
        sorted_products = df.sort_values(by='rating', ascending=False)
    elif sort_by == 'rating_asc':
        sorted_products = df.sort_values(by='rating', ascending=True)
    elif sort_by == 'price_desc':
        sorted_products = df.sort_values(by='price', ascending=False)
    elif sort_by == 'price_asc':
        sorted_products = df.sort_values(by='price', ascending=True)

    total_products = len(df)
    average_price = df['price'].mean()

    return render(request, 'analyzer_app/analysis.html', {
        'total_products': total_products,
        'average_price': average_price,
        'cheapest_products': cheapest_products if cheapest_products is not None and not cheapest_products.empty else None,
        'most_expensive_products': most_expensive_products if most_expensive_products is not None and not most_expensive_products.empty else None,
        'sorted_products': sorted_products.to_dict('records') if sorted_products is not None else df.to_dict('records')
    })
