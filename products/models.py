from django.db import models
from django.utils.text import slugify
import cloudinary.uploader


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    slug = models.SlugField(max_length=110, unique=True, blank=True, verbose_name='Slug')
    order = models.PositiveIntegerField(default=0, verbose_name='Orden', help_text='Orden en el catálogo (menor = primero)')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nombre')
    description = models.TextField(verbose_name='Descripción')

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Categoría',
    )

    image = models.URLField(blank=True, null=True, verbose_name='Imagen')
    image_file = models.ImageField(upload_to='temp/', blank=True, null=True, verbose_name='Archivo de imagen')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def save(self, *args, **kwargs):
        if self.image_file:
            uploaded = cloudinary.uploader.upload(self.image_file)
            self.image = uploaded.get('secure_url')
            self.image_file = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name='Producto')
    color = models.CharField(max_length=50, verbose_name='Color')
    size = models.CharField(max_length=50, verbose_name='Talle')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio')
    stock = models.IntegerField(default=0, verbose_name='Stock')

    class Meta:
        unique_together = ('product', 'color', 'size')
        verbose_name = 'Variante'
        verbose_name_plural = 'Variantes'

    def __str__(self):
        return f"{self.product.name} - {self.color}/{self.size}"


class Order(models.Model):

    STATUS_PENDIENTE = 'pendiente'
    STATUS_PAGADO = 'pagado'
    STATUS_PREPARACION = 'preparacion'
    STATUS_CANCELADO = 'cancelado'

    STATUS_CHOICES = [
        (STATUS_PENDIENTE, 'Pendiente'),
        (STATUS_PAGADO, 'Pagado'),
        (STATUS_PREPARACION, 'Preparación en curso'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    name = models.CharField(max_length=100, verbose_name='Nombre')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=30, verbose_name='Teléfono')

    document = models.CharField(max_length=50, blank=True, default='', verbose_name='Documento')

    address = models.CharField(max_length=255, verbose_name='Dirección')
    city = models.CharField(max_length=100, verbose_name='Ciudad')
    postal_code = models.CharField(max_length=20, verbose_name='Código postal')
    province = models.CharField(max_length=100, blank=True, default='', verbose_name='Provincia')

    shipping = models.CharField(max_length=50, blank=True, default='', verbose_name='Envío')
    payment_method = models.CharField(max_length=50, blank=True, default='', verbose_name='Método de pago')

    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDIENTE,
        verbose_name='Estado del pedido',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f"Pedido #{self.id} - {self.name}"

    def save(self, *args, **kwargs):
        previous_status = None

        if self.pk:
            previous_status = (
                Order.objects.filter(pk=self.pk)
                .values_list('status', flat=True)
                .first()
            )

        is_new_cancellation = (
            self.status == self.STATUS_CANCELADO
            and previous_status != self.STATUS_CANCELADO
        )

        super().save(*args, **kwargs)

        if is_new_cancellation:
            self._restore_stock()

    def _restore_stock(self):
        """Al cancelar un pedido, devuelve la cantidad de cada item al stock de su variante."""
        for item in self.items.all():
            variant = ProductVariant.objects.filter(
                product__name=item.product_name,
                color=item.color,
                size=item.size,
            ).first()

            if variant:
                variant.stock += item.quantity
                variant.save(update_fields=['stock'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Pedido')
    product_name = models.CharField(max_length=200, verbose_name='Producto')
    color = models.CharField(max_length=50, verbose_name='Color')
    size = models.CharField(max_length=50, verbose_name='Talle')
    quantity = models.IntegerField(verbose_name='Cantidad')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio')

    class Meta:
        verbose_name = 'Item del pedido'
        verbose_name_plural = 'Items del pedido'

    def __str__(self):
        return f"{self.product_name} ({self.color}/{self.size}) x{self.quantity}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Producto')

    image = models.URLField(blank=True, null=True, verbose_name='Imagen')
    image_file = models.ImageField(upload_to='temp/', blank=True, null=True, verbose_name='Archivo de imagen')

    color = models.CharField(max_length=50, blank=True, null=True, verbose_name='Color')

    class Meta:
        verbose_name = 'Imagen de producto'
        verbose_name_plural = 'Imágenes de producto'

    def save(self, *args, **kwargs):
        if self.image_file:
            uploaded = cloudinary.uploader.upload(self.image_file)
            self.image = uploaded.get('secure_url')
            self.image_file = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.color}"

class HeroSection(models.Model):

    title = models.CharField(max_length=100, verbose_name='Título')
    subtitle = models.CharField(max_length=255, verbose_name='Subtítulo')

    button_text = models.CharField(
        max_length=50,
        default='Ver colección',
        verbose_name='Texto del botón',
    )

    image = models.URLField(
        blank=True,
        null=True,
        verbose_name='Imagen',
    )

    image_file = models.ImageField(
        upload_to='hero/',
        blank=True,
        null=True,
        verbose_name='Archivo de imagen',
    )

    active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Portada'
        verbose_name_plural = 'Portada'

    def save(self, *args, **kwargs):

        if self.image_file:

            uploaded = cloudinary.uploader.upload(self.image_file)

            self.image = uploaded.get('secure_url')

            self.image_file = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title