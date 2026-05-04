from django.db import models
import cloudinary.uploader


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    image = models.URLField(blank=True, null=True)
    image_file = models.ImageField(upload_to='temp/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image_file:
            uploaded = cloudinary.uploader.upload(self.image_file)
            self.image = uploaded.get('secure_url')
            self.image_file = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

    class Meta:
        unique_together = ('product', 'color', 'size')

class Order(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30)

    document = models.CharField(max_length=50, blank=True, default='')

    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    province = models.CharField(max_length=100, blank=True, default='')

    shipping = models.CharField(max_length=50, blank=True, default='')
    payment_method = models.CharField(max_length=50, blank=True, default='')

    total = models.DecimalField(max_digits=10, decimal_places=2)

    is_paid = models.BooleanField(default=False)  # 👈 CLAVE

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')

    image = models.URLField(blank=True, null=True)
    image_file = models.ImageField(upload_to='temp/', blank=True, null=True)

    color = models.CharField(max_length=50, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.image_file:
            uploaded = cloudinary.uploader.upload(self.image_file)
            self.image = uploaded.get('secure_url')
            self.image_file = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.color}"

