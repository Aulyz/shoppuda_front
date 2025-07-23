from django.db import models
from django.conf import settings


class Wishlist(models.Model):
    """위시리스트(찜하기)"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlists',
        verbose_name='사용자'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='wishlists',
        verbose_name='상품'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='추가일시'
    )
    
    class Meta:
        db_table = 'shop_wishlists'
        verbose_name = '위시리스트'
        verbose_name_plural = '위시리스트'
        unique_together = ['user', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
