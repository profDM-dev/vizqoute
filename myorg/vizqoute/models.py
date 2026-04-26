from django.db import models


class VizqouteUser(models.Model):
    ROLE_CHOICES = [
        ('contractor', 'Contractor'),
        ('client', 'Client'),
    ]
    # Common fields for both contractors and clients
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20)
    companyname = models.CharField(max_length=255, null=True, blank=True)
    createdat = models.DateTimeField(auto_now_add=True)
    updatedat = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class VizqouteClient(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True)
    createdat = models.DateTimeField(auto_now_add=True)
    updatedat = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class VizqouteQuotation(models.Model):
    # Status choices for the quotation lifecycle
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    # Foreign keys to link quotations to contractors and clients
    contractorid = models.ForeignKey(
        VizqouteUser,
        on_delete=models.CASCADE,
        related_name='quotations'
    )
    clientid = models.ForeignKey(
        VizqouteClient,
        on_delete=models.CASCADE,
        related_name='quotations'
    )
    # Location fields for the job site
    latitude = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    createdat = models.DateTimeField(auto_now_add=True)
    updatedat = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quotation {self.id}"


class VizqouteQuoteItem(models.Model):
    # Each quote item is linked to a specific quotation
    quotationid = models.ForeignKey(
        VizqouteQuotation,
        on_delete=models.CASCADE,
        related_name='items'
    )

    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50)
    unitprice = models.DecimalField(max_digits=10, decimal_places=2)
    totalprice = models.DecimalField(max_digits=10, decimal_places=2)

    createdat = models.DateTimeField(auto_now_add=True)
    updatedat = models.DateTimeField(auto_now=True)


class VizqouteRoofingSpec(models.Model):
    quotationid = models.ForeignKey(
        VizqouteQuotation,
        on_delete=models.CASCADE,
        related_name='roofingspecs'
    )
    # Fields to capture roofing specifications
    roofarea = models.DecimalField(max_digits=10, decimal_places=2)
    pitchangle = models.DecimalField(max_digits=5, decimal_places=2)
    materialtype = models.CharField(max_length=100)
    laborhours = models.DecimalField(max_digits=10, decimal_places=2)
    wastefactor = models.DecimalField(max_digits=5, decimal_places=3)

    createdat = models.DateTimeField(auto_now_add=True)
    updatedat = models.DateTimeField(auto_now=True)


class VizqoutePreview(models.Model):
    quotationid = models.ForeignKey(
        VizqouteQuotation,
        on_delete=models.CASCADE,
        related_name='previews'
    )

    sharelink = models.CharField(max_length=255)
    expirydate = models.DateTimeField()
    accesscount = models.IntegerField(default=0)

    createdat = models.DateTimeField(auto_now_add=True)
