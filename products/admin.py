from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductVariant, Order, OrderItem, ProductImage

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

    fields = (
        'color',
        'size',
        'price',
        'stock',
    )

    classes = ('collapse',)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

    readonly_fields = ('image_preview',)

    fields = (
        'color',
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
        'image_preview',
        'created_at',
    )

    search_fields = (
        'name',
    )

    readonly_fields = (
        'image_preview_large',
    )

    list_filter = (
        'created_at',
    )

    fieldsets = (

        ("📦 Producto", {
            'fields': (
                'name',
                'description',
            )
        }),

        ("🖼️ Imagen", {
            'fields': (
                'image_preview_large',
            )
        }),
    )

    def image_preview(self, obj):

        if obj.image:
            return format_html(
                '<img src="{}" width="60" style="border-radius:8px;" />',
                obj.image
            )

        return "Sin imagen"

    image_preview.short_description = 'Imagen'

    def image_preview_large(self, obj):

        if obj.image:
            return format_html(
                '<img src="{}" width="250" style="border-radius:12px;" />',
                obj.image
            )

        return "Sin imagen"

    image_preview_large.short_description = 'Vista previa'





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
        'is_paid',
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