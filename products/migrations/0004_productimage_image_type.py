# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_alter_category_code_alter_category_icon_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productimage',
            name='image_type',
            field=models.CharField(choices=[('primary', '대표 이미지'), ('gallery', '갤러리 이미지'), ('detail', '상세 이미지')], default='gallery', max_length=20, verbose_name='이미지 타입'),
        ),
    ]