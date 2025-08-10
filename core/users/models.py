from django.db import models, transaction
from django.db.models import F
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import PermissionDenied

from main.models import ToolPage


class Plan(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    monthly_attempts_limit = models.PositiveIntegerField(default=0)
    yearly_attempts_limit = models.PositiveIntegerField(default=0)

    monthly_features = models.TextField(blank=True)
    yearly_features = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} (${self.monthly_price}/mo)"

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Plans"
        ordering = ['monthly_price']


class Scanner(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    command = models.CharField(max_length=255, help_text="Command or script path")

    def __str__(self):
        return self.name


class PlanScannerAccess(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='scanner_accesses')
    scanner = models.ForeignKey(Scanner, on_delete=models.CASCADE, related_name='plan_accesses')
    included = models.BooleanField(default=True)
    extra_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('plan', 'scanner')
        verbose_name = "Scanner Access in Plan"
        verbose_name_plural = "Scanner Accesses in Plans"

    def __str__(self):
        return f"{self.scanner.name} in {self.plan.name} — {'Included' if self.included else f'${self.extra_price}'}"


class PlanToolAccess(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='tool_accesses')
    tool = models.ForeignKey(ToolPage, on_delete=models.CASCADE, related_name='plan_accesses')
    included = models.BooleanField(default=True)
    extra_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('plan', 'tool')
        verbose_name = "Tool Access in Plan"
        verbose_name_plural = "Tool Accesses in Plans"

    def __str__(self):
        return f"{self.tool.title} in {self.plan.name} — {'Included' if self.included else f'${self.extra_price}'}"


class ScanFolder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="folders")
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.name}"


# ===== Coupons / Discounts =====

class Coupon(models.Model):
    PERCENT = 'percent'
    FIXED = 'fixed'
    DISCOUNT_TYPE = [(PERCENT, 'Percent'), (FIXED, 'Fixed amount')]

    code = models.CharField(max_length=40, unique=True, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE)
    value = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    # applicability scopes (empty = all)
    plans = models.ManyToManyField(Plan, blank=True, related_name='coupons')
    tools = models.ManyToManyField(ToolPage, blank=True, related_name='coupons')

    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)   # global limit
    per_user_limit = models.PositiveIntegerField(default=1)         # per-user limit
    stackable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_valid_now(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if self.max_uses is not None and self.usage_count >= self.max_uses:
            return False
        return True

    def __str__(self):
        return f"{self.code} ({self.discount_type}:{self.value})"


class CouponRedemption(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='redemptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, null=True, blank=True)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    amount_discounted = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'coupon'])]

    def __str__(self):
        return f"{self.user} used {self.coupon.code} (-{self.amount_discounted})"


# ===== Integrations with partners =====

class IntegrationPartner(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    settings = models.JSONField(default=dict, blank=True)  # base URLs, scopes, etc.
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PlanIntegration(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='integrations')
    partner = models.ForeignKey(IntegrationPartner, on_delete=models.CASCADE, related_name='plan_bindings')
    included = models.BooleanField(default=True)
    monthly_limit = models.PositiveIntegerField(default=0)          # 0 = unlimited (or ignore if included=False)
    overage_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('plan', 'partner')

    def __str__(self):
        return f"{self.partner.name} in {self.plan.name} ({'incl.' if self.included else 'paid'})"


# ===== Per-tool usage limits & counters =====

class ToolUsageLimit(models.Model):
    PERIOD_MONTH = 'month'
    PERIOD_YEAR = 'year'
    PERIOD_CHOICES = [(PERIOD_MONTH, 'Monthly'), (PERIOD_YEAR, 'Yearly')]

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='tool_limits')
    tool = models.ForeignKey(ToolPage, on_delete=models.CASCADE, related_name='plan_limits')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default=PERIOD_MONTH)
    limit = models.PositiveIntegerField(default=0)  # 0 = unlimited
    overage_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('plan', 'tool', 'period')

    def __str__(self):
        return f"{self.plan.name} / {self.tool.title} [{self.period}] limit={self.limit}"


class ToolUsageCounter(models.Model):
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, related_name='usage_counters')
    tool = models.ForeignKey(ToolPage, on_delete=models.CASCADE)
    period = models.CharField(max_length=10, choices=ToolUsageLimit.PERIOD_CHOICES, default=ToolUsageLimit.PERIOD_MONTH)
    window_started_at = models.DateTimeField(default=timezone.now)
    used = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('subscription', 'tool', 'period')

    def increment(self, n=1):
        self.used = F('used') + n
        self.save(update_fields=['used'])
        self.refresh_from_db(fields=['used'])

    def __str__(self):
        return f"{self.subscription} / {self.tool.slug} [{self.period}] used={self.used}"


class Subscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('trial', 'Trial'),
        ('paused', 'Paused'),
    )

    PAYMENT_METHODS = (
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('manual', 'Manual'),
        ('internal', 'Internal'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    cancelled_at = models.DateTimeField(blank=True, null=True)
    renewed_at = models.DateTimeField(blank=True, null=True)

    attempts_left = models.PositiveIntegerField(default=0)
    times_renewed = models.PositiveIntegerField(default=0)

    notified_expiration = models.BooleanField(default=False)
    is_trial = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True, null=True)

    # ---- Attempts (global) ----
    def reset_attempts(self):
        if self.plan and self.start_date and self.end_date:
            duration = self.end_date - self.start_date
            if duration.days >= 365:
                self.attempts_left = self.plan.yearly_attempts_limit
            else:
                self.attempts_left = self.plan.monthly_attempts_limit
            self.save(update_fields=['attempts_left'])

    def use_attempt(self):
        updated = (Subscription.objects
                   .filter(pk=self.pk, attempts_left__gt=0)
                   .update(attempts_left=F('attempts_left') - 1))
        if updated:
            self.refresh_from_db(fields=['attempts_left'])
            return True
        return False

    # ---- Tool usage checks ----
    def _get_limit_for_tool(self, tool: ToolPage):
        # prefer monthly, fall back to yearly
        limit = self.plan.tool_limits.filter(tool=tool, period=ToolUsageLimit.PERIOD_MONTH).first()
        if not limit:
            limit = self.plan.tool_limits.filter(tool=tool, period=ToolUsageLimit.PERIOD_YEAR).first()
        return limit

    def can_use_tool(self, tool: ToolPage, raise_if_denied=False):
        # 1) included in plan?
        included = self.plan.tool_accesses.filter(tool=tool, included=True).exists()
        if not included:
            if raise_if_denied:
                raise PermissionDenied("Tool is not included in your plan.")
            return False

        # 2) limits
        limit = self._get_limit_for_tool(tool)
        if not limit or limit.limit == 0:
            return True  # unlimited

        # 3) counter
        counter, _ = ToolUsageCounter.objects.get_or_create(
            subscription=self, tool=tool, period=limit.period,
            defaults={'window_started_at': timezone.now(), 'used': 0}
        )
        allowed = counter.used < limit.limit
        if not allowed and raise_if_denied:
            raise PermissionDenied("Usage limit exceeded for this tool.")
        return allowed

    @transaction.atomic
    def consume_tool_usage(self, tool: ToolPage, units=1):
        limit = self._get_limit_for_tool(tool)
        if limit and limit.limit == 0:
            return  # unlimited

        if not self.can_use_tool(tool, raise_if_denied=True):
            # will raise if denied
            return

        counter, _ = ToolUsageCounter.objects.select_for_update().get_or_create(
            subscription=self, tool=tool, period=(limit.period if limit else ToolUsageLimit.PERIOD_MONTH),
            defaults={'window_started_at': timezone.now(), 'used': 0}
        )
        counter.used = F('used') + units
        counter.save(update_fields=['used'])

    def reset_usage_counters(self, period='month'):
        now = timezone.now()
        self.usage_counters.filter(period=period).update(used=0, window_started_at=now)

    # ---- Status helpers ----
    def is_active(self):
        return self.status == 'active' and self.end_date > timezone.now()

    def expire_if_needed(self):
        if self.end_date <= timezone.now() and self.status != 'expired':
            self.status = 'expired'
            self.save(update_fields=['status'])

    @property
    def is_expired(self):
        return self.end_date <= timezone.now()

    @property
    def remaining_days(self):
        if not self.end_date:
            return 0
        return max((self.end_date - timezone.now()).days, 0)

    @property
    def is_cancelled(self):
        return self.status == 'cancelled'

    @property
    def is_trial_active(self):
        return self.is_trial and self.is_active()

    def __str__(self):
        return f"{self.user.username} | {self.plan.name} | {self.status} | Ends {self.end_date.strftime('%Y-%m-%d')}"
