from django.contrib import admin
from .models import Order, OrderProduct, Payment


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'full_name',
        'phone',
        'email',
        'order_total',
        'tax',
        'status',
        'is_ordered',
        'created_at',
    )
    list_filter = ('status', 'is_ordered')
    search_fields = ('order_number', 'first_name', 'last_name', 'phone', 'email')
    list_per_page = 20


class OrderProductAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'product',
        'quantity',
        'product_price',
        'ordered',
    )


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)
admin.site.register(Payment)
