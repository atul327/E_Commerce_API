from utils.razorpay_client import client

order = client.order.create(
    {
        "amount":50000,
        "currency":"INR",
        "receipt":"test_order_1"
    }
)

print(order)