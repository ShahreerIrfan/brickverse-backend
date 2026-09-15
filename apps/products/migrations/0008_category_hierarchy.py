from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_category_mega_menu_order_category_show_in_mega_menu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='id',
            field=models.CharField(max_length=100, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='category',
            name='label',
            field=models.CharField(max_length=150),
        ),
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='category',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='children',
                to='products.category',
            ),
        ),
    ]
