from django.db import models


class SocialLink(models.Model):
    """
    Social media link managed by the admin.
    Active links appear as clickable icons in the footer.
    Inactive/empty links appear as greyed-out icons.
    """

    PLATFORM_CHOICES = [
        ('facebook',  'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter',   'Twitter / X'),
        ('youtube',   'YouTube'),
        ('tiktok',    'TikTok'),
    ]

    ICON_MAP = {
        'facebook':  'ti ti-brand-facebook',
        'instagram': 'ti ti-brand-instagram',
        'twitter':   'ti ti-brand-x',
        'youtube':   'ti ti-brand-youtube',
        'tiktok':    'ti ti-brand-tiktok',
    }

    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        unique=True,
        verbose_name='Platform',
    )
    url = models.URLField(
        blank=True,
        default='',
        verbose_name='Profile URL',
        help_text='Paste the full URL (e.g. https://facebook.com/yourpage). Leave blank to hide the link.',
    )

    class Meta:
        verbose_name = 'Social Link'
        verbose_name_plural = 'Social Links'
        ordering = ['platform']

    def __str__(self):
        return f"{self.get_platform_display()} — {'active' if self.url else 'inactive'}"

    @property
    def icon(self):
        return self.ICON_MAP.get(self.platform, 'ti ti-world')

    @property
    def is_active(self):
        return bool(self.url)

    @property
    def name(self):
        return self.get_platform_display()
