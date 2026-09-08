from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set.')
        email = self.normalize_email(email)
        extra_fields.setdefault('role', User.ROLE_CUSTOMER)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ROLE_ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class AdminManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(role=User.ROLE_ADMIN)

    def create(self, **kwargs):
        kwargs.update({'role': User.ROLE_ADMIN, 'is_staff': True})
        return super().create(**kwargs)


class CustomerManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(role=User.ROLE_CUSTOMER)

    def create(self, **kwargs):
        kwargs.update({'role': User.ROLE_CUSTOMER, 'is_staff': False})
        return super().create(**kwargs)


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_CUSTOMER = 'customer'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_CUSTOMER, 'Customer'),
    ]

    username = None
    email = models.EmailField('email address', unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    phone = models.CharField(max_length=50, blank=True)
    avatar = models.CharField(max_length=255, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_customer_role(self):
        return self.role == self.ROLE_CUSTOMER

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


class AdminUser(User):
    objects = AdminManager()

    class Meta:
        proxy = True
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'

    def save(self, *args, **kwargs):
        self.role = User.ROLE_ADMIN
        self.is_staff = True
        super().save(*args, **kwargs)


class CustomerUser(User):
    objects = CustomerManager()

    class Meta:
        proxy = True
        verbose_name = 'Customer User'
        verbose_name_plural = 'Customer Users'

    def save(self, *args, **kwargs):
        self.role = User.ROLE_CUSTOMER
        super().save(*args, **kwargs)


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    loyalty_points = models.IntegerField(default=0)
    tier = models.CharField(max_length=50, default="Bronze")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Customer Profile for {self.user.email}"


@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.ROLE_CUSTOMER:
        CustomerProfile.objects.get_or_create(user=instance)
