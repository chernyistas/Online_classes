import os

import stripe


def create_stripe_product(name, description):
    stripe.api_key = os.getenv("STRIPE_API_KEY")
    product = stripe.Product.create(name=name, description=description)
    return product


def create_stripe_price(product_id, amount):
    stripe.api_key = os.getenv("STRIPE_API_KEY")
    price = stripe.Price.create(
        currency="rub",
        unit_amount=int(amount * 100),
        product=product_id,
    )

    return price


def create_checkout_session(price_id, success_url, cancel_url):
    stripe.api_key = os.getenv("STRIPE_API_KEY")
    session = stripe.checkout.Session.create(
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{"price": price_id, "quantity": 1}],
        mode="payment",
    )
    return session.id, session.url
