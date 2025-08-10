# models.py
from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField
from django.contrib.auth import get_user_model

User = get_user_model()

class SiteSettings(models.Model):
    logo = models.ImageField(upload_to='settings/', null=True, blank=True)
    email = models.EmailField(blank=True)
    twitter_url = models.URLField("Twitter", blank=True)
    github_url = models.URLField("GitHub", blank=True)
    linkedin_url = models.URLField("LinkedIn", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Site Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "0.Site Settings"
        verbose_name_plural = "0. Site Settings"

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    is_published = models.BooleanField(default=True)

    class Meta:
        abstract = True

class LandingContent(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    background_video = models.FileField(upload_to='landing_videos/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='landing_created'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='landing_updated'
    )

    is_published = models.BooleanField(default=True)

    def __str__(self):
        return f"Landing: {self.title} ({'Published' if self.is_published else 'Draft'})"
    
    class Meta:
        verbose_name = "1. Main Content"
        verbose_name_plural = "1. Main Content"
    
class LandingSlider(models.Model):
    title = models.CharField(max_length=100 , verbose_name="Name" , null=True)
    image = models.ImageField(upload_to='landing_slider/')
    is_published = models.BooleanField(default=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "3. Main Slider"
        verbose_name_plural = "3. Main Sliders"
        ordering = ['-time_create']

    def __str__(self):
        return self.title
        
class Feature(BaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "4. Feature"
        verbose_name_plural = "4. Features"
        ordering = ['-created_at']

class TeamService(models.Model):
    TEAM_CHOICES = [
        ('blue', 'Blue Team'),
        ('red', 'Red Team'),
        ('purple', 'Purple Team'),
    ]

    team = models.CharField(max_length=10, choices=TEAM_CHOICES, unique=True)
    title = models.CharField(max_length=255 , null=True)
    description = models.TextField()
    icon = models.ImageField(upload_to='team_icons/', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_team_display()

    class Meta:
        verbose_name = "Team Service"
        verbose_name_plural = "Team Service"

class Banner(models.Model):
    title = models.CharField(max_length=255)
    descriptions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banner"

class Benefit(models.Model):
    ICON_CHOICES = [
        ('lock', 'FaLock'),
        ('bolt', 'FaBolt'),
        ('secret', 'FaUserSecret'),
    ]

    icon_key = models.CharField(max_length=20, choices=ICON_CHOICES)
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='whychooseus/')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='benefits_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='benefits_updated')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class Statistic(models.Model):
    title = models.CharField(max_length=255)
    value = models.PositiveIntegerField()
    suffix = models.CharField("Enter Suffix ex % , + :", null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='statistics_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='statistics_updated')

    class Meta:
        verbose_name = "8. Statistic"
        verbose_name_plural = "8. Statistics"
        ordering = ['id']

    def __str__(self):
        return f"{self.title} ({self.value})"
    
class Plan(models.Model):
    BILLING_CYCLE_CHOICES = [
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.billing_cycle})"

class PlanFeature(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='features')
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.text} for {self.plan.name}"

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} at {self.purchased_at}"
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(("Enter Description") , null=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "5. Category"
        verbose_name_plural = "5. Categories"
        ordering = ["id"]


class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name="subcategories", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    class Meta:
        verbose_name = "6. Subategory"
        verbose_name_plural = "6. Subategories"
        ordering = ["id"]

class ToolPage(models.Model):
    subcategory = models.ForeignKey('SubCategory', related_name="tools", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    command = models.CharField(max_length=255 , null=True)
    description = models.CharField("Description", max_length=150, null=True)
    image = models.ImageField(upload_to='tools_images/', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, editable=False)
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def _generate_unique_slug(self):
        base = slugify(self.title, allow_unicode=True) or "tool"
        slug = base
        i = 2
        Model = self.__class__
        while Model.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{i}"
            i += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def get_price_for_plan(self, plan):
        access = self.plan_accesses.filter(plan=plan).first()
        return access.extra_price if access else None

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "7. Add Tools"
        verbose_name_plural = "7. Add Tools"
        ordering = ["id"]
    
class ToolBlock(models.Model):
    tool = models.ForeignKey(ToolPage, related_name='blocks', on_delete=models.CASCADE)
    title = models.TextField()
    content = RichTextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.tool.title} - {self.title}"
    
class Research(models.Model):
    title = models.CharField(max_length=255)
    description = RichTextField()
    image = models.ImageField(upload_to='research_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Research"
        verbose_name_plural = "Research"

class PrivacyPolicy(models.Model):
    title = models.CharField(max_length=255, default="Privacy Policy")
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Privacy Policy"
        verbose_name_plural = "Privacy Policies"

    def __str__(self):
        return self.title


class TermsAndConditions(models.Model):
    title = models.CharField(max_length=255, default="Terms and Conditions")
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Terms and Conditions"
        verbose_name_plural = "Terms and Conditions"

    def __str__(self):
        return self.title


class SecurityPolicy(models.Model):
    title = models.CharField(max_length=255, default="Security Policy")
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Security Policy"
        verbose_name_plural = "Security Policies"

    def __str__(self):
        return self.title

class About(models.Model):
    title = models.CharField(max_length=255, default="About Us")
    content = RichTextField()  # rich text editor
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "About Page"
        verbose_name_plural = "About Pages"

    def __str__(self):
        return self.title
    
class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} ({self.email})"
    

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email