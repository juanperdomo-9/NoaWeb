from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductVariant, Order, OrderItem, ProductImage

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

    readonly_fields = ('image_preview',)

    fields = (
        'image',
        'image_preview',
    )

    def image_preview(self, obj):

        if obj.image:
            return format_html(
                '<img src="{}" width="80" style="border-radius:10px;" />',
                obj.image.url
            )

        return "Sin imagen"

    image_preview.short_description = 'Preview'



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):


    inlines = [ProductVariantInline, ProductImageInline]

    list_display = (
        'name',
        'price',
        'stock_status',
        'active',
    )

    search_fields = (
        'name',
    )

    list_filter = (
        'active',
    )

    list_editable = (
        'active',
    )

    fieldsets = (

        ("📦 Producto", {
            'fields': (
                'name',
                'description',
            )
        }),

        ("💰 Precio y stock", {
            'fields': (
                'price',
                'stock',
                'active',
            )
        }),
    )

    def stock_status(self, obj):

        if obj.stock <= 0:
            return format_html(
                '<span style="color:red;font-weight:bold;">❌ Sin stock</span>'
            )

        elif obj.stock < 5:
            return format_html(
                '<span style="color:orange;font-weight:bold;">⚠️ Poco stock</span>'
            )

        return format_html(
            '<span style="color:green;font-weight:bold;">✅ En stock</span>'
        )

    stock_status.short_description = 'Estado stock'



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False

    
    readonly_fields = (
        'product_name',
        'color',
        'size',
        'quantity',
        'price',
    )
    

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'city',
        'total',
        'payment_method',
        'payment_status',
        'created_at',
    )

    list_filter = (
        'payment_method',
        'is_paid',
        'created_at',
    )

    search_fields = (
        'name',
        'email',
        'phone',
    )

    list_editable = (
        'is_paid',
    )

    inlines = [OrderItemInline]

    def payment_status(self, obj):

        if obj.is_paid:
            return format_html(
                '<span style="color:green;font-weight:bold;">✅ Pagado</span>'
            )

        return format_html(
            '<span style="color:red;font-weight:bold;">❌ Pendiente</span>'
        )

    payment_status.short_description = 'Estado pago'



admin.site.register(ProductImage)
admin.site.register(ProductVariant)
admin.site.register(OrderItem)