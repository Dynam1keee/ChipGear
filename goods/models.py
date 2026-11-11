import os
from django.db import models
from django.urls import reverse
from users.models import User

def category_image_path(instance, filename):
    return os.path.join('categories', instance.slug, '_category_image.jpg')

class Category(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Name")
    slug = models.SlugField(max_length=150, unique=True, verbose_name='URL')
    image = models.ImageField(upload_to=category_image_path, default='images/image_not_found.jpg', blank=True, null=False, verbose_name='Image')
    model_name = models.CharField(max_length=150, unique=False, verbose_name="Model name")

    class Meta:
        db_table = 'category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

def product_image_path(instance, filename):
    return os.path.join('categories', instance.category.slug, f'{instance.id:07}.jpg')

class Product(models.Model):
    name = models.CharField(max_length=150, unique=True, null=False, verbose_name="Name")
    slug = models.SlugField(max_length=150, unique=True, null=False, verbose_name='URL')
    manufacturer = models.CharField(max_length=150, null=False, verbose_name="Manufacturer")
    description = models.CharField(max_length=150, blank=True, null=False, default='-', verbose_name='Description')
    image = models.ImageField(upload_to=product_image_path, default='images/image_not_found.jpg', blank=True, null=False, verbose_name='Image')
    price = models.DecimalField(default=0.00, max_digits=7, decimal_places=2, verbose_name='Price')
    discount = models.PositiveIntegerField(default=0, verbose_name='Discount (percentage)')
    quantity = models.PositiveIntegerField(default=0, verbose_name='Quantity')
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE, verbose_name='Category')

    class Meta:
        db_table = 'product'
        verbose_name = 'Product'
        verbose_name_plural = 'All products'
        ordering = ['id']
    
    def __str__(self):
        return self.name
    
    def display_id(self):
        return f'{self.id:07}'
    display_id.short_description = 'ID'
    
    def get_values_dict(self):
        for rel in self._meta.get_fields():
            if isinstance(rel, models.OneToOneRel):
                if hasattr(self, rel.get_accessor_name()):
                    obj_from_category = getattr(self, rel.get_accessor_name())

                    prod_attrs_dict = {field.name: field.verbose_name for field in Product._meta.fields}
                    specs_attrs_dict = {field.name: field.verbose_name for field in obj_from_category._meta.fields}

                    values_dict = {}
                    for k, v in specs_attrs_dict.items():
                        if not k in prod_attrs_dict.keys() and not k.endswith('_ptr'):
                            values_dict[v] = getattr(obj_from_category, k)
                    return values_dict
    
    
    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"category_slug": self.category.slug, "product_slug": self.slug})
    
    def sell_price(self):
        if self.discount:
            return round(self.price - self.price * self.discount / 100, 2)
        return self.price


class RecentlyViewed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    search_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} searched for "{self.query}" at {self.search_time}'

### CATEGORIES

class Case(Product):
    form_factor = models.CharField(max_length=50, verbose_name="Form factor")
    material = models.CharField(max_length=50, verbose_name="Material")
    front_panel_ports = models.CharField(max_length=100, verbose_name="Front panel ports")
    expansion_slots = models.PositiveSmallIntegerField(verbose_name="Expansion slots")
    drive_bays = models.PositiveSmallIntegerField(verbose_name="Drive bays")
    cooling_system = models.CharField(max_length=100, verbose_name="Cooling system")
    side_panel_window = models.BooleanField(default=False, verbose_name="Side panel window")
    rgb_lighting = models.BooleanField(default=False, verbose_name="RGB lighting")
    dimensions = models.CharField(max_length=50, verbose_name="Dimensions")
    weight = models.DecimalField(default=0.00, max_digits=5, decimal_places=2, verbose_name="Weight")

    class Meta:
        db_table = 'case'
        verbose_name = 'Case'
        verbose_name_plural = 'Cases'

    def __str__(self):
        return self.name


class PowerSupply(Product):
    power = models.PositiveSmallIntegerField(verbose_name="Power, W")
    efficiency = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Efficiency, %")
    modular_cables = models.BooleanField(default=False, verbose_name="Modular cables")
    form_factor = models.CharField(max_length=50, verbose_name="Form factor")
    fan_size = models.CharField(max_length=10, verbose_name="Fan size")
    connectors = models.CharField(max_length=100, verbose_name="Connectors")
    protections = models.CharField(max_length=100, verbose_name="Protections")
    dimensions = models.CharField(max_length=50, verbose_name="Dimensions")
    weight = models.DecimalField(default=0.00, max_digits=5, decimal_places=2, verbose_name="Weight")
    certification = models.CharField(max_length=50, verbose_name="Certification")

    class Meta:
        db_table = 'power_supply'
        verbose_name = 'Power supply'
        verbose_name_plural = 'Power supplies'

    def __str__(self):
        return self.name


class Motherboard(Product):
    socket = models.CharField(max_length=50, verbose_name="CPU socket")
    chipset = models.CharField(max_length=50, verbose_name="Chipset")
    form_factor = models.CharField(max_length=50, verbose_name="Form factor")
    memory_slots = models.PositiveSmallIntegerField(verbose_name="Memory slots")
    max_memory = models.CharField(max_length=50, verbose_name="Max memory")
    memory_type = models.CharField(max_length=50, verbose_name="Memory type")
    expansion_slots = models.PositiveSmallIntegerField(verbose_name="Expansion slots")
    storage_interfaces = models.CharField(max_length=100, verbose_name="Storage interfaces")
    onboard_graphics = models.BooleanField(default=False, verbose_name="Onboard graphics")
    rear_panel_ports = models.CharField(max_length=100, verbose_name="Rear panel ports")

    class Meta:
        db_table = 'motherboard'
        verbose_name = 'Motherboard'
        verbose_name_plural = 'Motherboards'

    def __str__(self):
        return self.name


class CPU(Product):
    socket = models.CharField(max_length=50, verbose_name="Socket")
    cores = models.PositiveSmallIntegerField(verbose_name="Cores")
    threads = models.PositiveSmallIntegerField(verbose_name="Threads")
    base_clock = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Base clock, GHz")
    boost_clock = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Boost clock, GHz")
    cache = models.CharField(max_length=50, verbose_name="Cache")
    lithography = models.CharField(max_length=50, verbose_name="Lithography")
    thermal_design_power = models.PositiveSmallIntegerField(verbose_name="Thermal Design Power, W")
    integrated_graphics = models.BooleanField(default=False, verbose_name="Integrated graphics")
    hyperthreading = models.BooleanField(default=False, verbose_name="Hyper-threading")

    class Meta:
        db_table = 'cpu'
        verbose_name = 'CPU'
        verbose_name_plural = 'CPUs'

    def __str__(self):
        return self.name


class GraphicsCard(Product):
    chipset = models.CharField(max_length=50, verbose_name="Chipset")
    memory = models.CharField(max_length=50, verbose_name="Memory capacity")
    memory_type = models.CharField(max_length=50, verbose_name="Memory type")
    memory_bus = models.PositiveSmallIntegerField(verbose_name="Memory bus, bits")
    core_clock = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Core clock, MHz")
    boost_clock = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Boost clock, MHz")
    cuda_cores = models.PositiveIntegerField(verbose_name="CUDA cores")
    interfaces = models.CharField(max_length=100, verbose_name="Interfaces")
    power_connector = models.CharField(max_length=50, verbose_name="Power connector")
    dimensions = models.CharField(max_length=50, verbose_name="Dimensions")
    weight = models.DecimalField(default=0.00, max_digits=5, decimal_places=2, verbose_name="Weight")

    class Meta:
        db_table = 'graphics_card'
        verbose_name = 'Graphics card'
        verbose_name_plural = 'Graphics cards'

    def __str__(self):
        return self.name


class RAM(Product):
    capacity = models.CharField(max_length=50, verbose_name="Capacity")
    type = models.CharField(max_length=50, verbose_name="Memory type")
    speed = models.PositiveSmallIntegerField(verbose_name="Speed, MHz")
    modules = models.PositiveSmallIntegerField(verbose_name="Modules")
    voltage = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Voltage, V")
    latency = models.CharField(max_length=50, verbose_name="Latency")
    heat_spreader = models.BooleanField(default=False, verbose_name="Heat spreader")
    ecc = models.BooleanField(default=False, verbose_name="ECC support")
    rgb = models.BooleanField(default=False, verbose_name="RGB lighting")
    dimensions = models.CharField(max_length=50, verbose_name="Dimensions")

    class Meta:
        db_table = 'ram'
        verbose_name = "RAM"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SoundCard(Product):
    interface = models.CharField(max_length=50, verbose_name="Interface")
    channels = models.PositiveSmallIntegerField(verbose_name="Channels")
    sample_rate = models.PositiveIntegerField(verbose_name="Sample rate, Hz")
    signal_to_noise_ratio = models.PositiveSmallIntegerField(verbose_name="Signal-to-noise ratio, dB")
    audio_formats = models.CharField(max_length=100, verbose_name="Supported audio formats")
    features = models.CharField(max_length=100, verbose_name="Features")
    inputs = models.CharField(max_length=100, verbose_name="Inputs")
    outputs = models.CharField(max_length=100, verbose_name="Outputs")
    dimensions = models.CharField(max_length=50, verbose_name="Dimensions")
    weight = models.DecimalField(default=0.00, max_digits=5, decimal_places=2, verbose_name="Weight")

    class Meta:
        db_table = 'sound_card'
        verbose_name = 'Sound card'
        verbose_name_plural = 'Sound cards'

    def __str__(self):
        return self.name


class HardDrive(Product):
    interface = models.CharField(max_length=50, verbose_name="Interface")
    capacity = models.CharField(max_length=50, verbose_name="Capacity")
    form_factor = models.CharField(max_length=50, verbose_name="Form factor")
    rpm = models.PositiveSmallIntegerField(verbose_name="RPM")
    cache = models.CharField(max_length=50, verbose_name="Cache")
    read_speed = models.PositiveIntegerField(verbose_name="Read speed, MB/s")
    write_speed = models.PositiveIntegerField(verbose_name="Write speed, MB/s")
    average_seek_time = models.CharField(max_length=50, verbose_name="Average seek time")
    interface_speed = models.CharField(max_length=50, verbose_name="Interface speed")
    dimensions = models.CharField(max_length=50, verbose_name="Dimensions")

    class Meta:
        db_table = 'hard_drive'
        verbose_name = 'Hard drive'
        verbose_name_plural = 'Hard drives'

    def __str__(self):
        return self.name


class Keyboard(Product):
    layout = models.CharField(max_length=50, verbose_name="Layout")
    key_switches = models.CharField(max_length=50, verbose_name="Key switches")
    backlighting = models.BooleanField(default=False, verbose_name="Backlighting")
    connectivity = models.CharField(max_length=50, verbose_name="Connectivity")
    interface = models.CharField(max_length=50, verbose_name="Interface")
    multimedia_keys = models.BooleanField(default=False, verbose_name="Multimedia keys")
    programmable_keys = models.BooleanField(default=False, verbose_name="Programmable keys")
    wrist_rest = models.BooleanField(default=False, verbose_name="Wrist rest")
    dimensions = models.CharField(max_length=50, verbose_name="Dimensions")
    weight = models.DecimalField(default=0.00, max_digits=5, decimal_places=2, verbose_name="Weight")

    class Meta:
        db_table = 'keyboard'
        verbose_name = 'Keyboard'
        verbose_name_plural = 'Keyboards'

    def __str__(self):
        return self.name


class Mouse(Product):
    sensor_type = models.CharField(max_length=50, verbose_name="Sensor type")
    dpi = models.PositiveIntegerField(verbose_name="DPI")
    programmable_buttons = models.PositiveSmallIntegerField(verbose_name="Programmable buttons")
    polling_rate = models.PositiveSmallIntegerField(verbose_name="Polling rate, Hz")
    connection_type = models.CharField(max_length=50, verbose_name="Connection type")
    grip_style = models.CharField(max_length=50, verbose_name="Grip style")
    weight = models.DecimalField(default=0.00, max_digits=5, decimal_places=2, verbose_name="Weight")
    cable_length = models.DecimalField(default=0.00, max_digits=5, decimal_places=2, verbose_name="Cable length, m")
    dimensions = models.CharField(max_length=50, verbose_name="Dimensions")
    rgb_lighting = models.BooleanField(default=False, verbose_name="RGB lighting")

    class Meta:
        db_table = 'mouse'
        verbose_name = 'Mouse'
        verbose_name_plural = 'Mice'

    def __str__(self):
        return self.name


class CoolingSystem(Product):
    type = models.CharField(max_length=50, verbose_name="Cooling system type")
    fan_size = models.PositiveSmallIntegerField(verbose_name="Fan size, mm")
    bearing_type = models.CharField(max_length=50, verbose_name="Bearing type")
    airflow = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Airflow, CFM")
    noise_level = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Noise level, dB")
    speed_control = models.BooleanField(default=False, verbose_name="Speed control")
    rgb_lighting = models.BooleanField(default=False, verbose_name="RGB lighting")
    dimensions = models.CharField(max_length=50, verbose_name="Dimensions")
    weight = models.DecimalField(default=0.00, max_digits=6, decimal_places=2, verbose_name="Weight")
    compatibility = models.CharField(max_length=100, verbose_name="Compatibility")

    class Meta:
        db_table = 'cooling_system'
        verbose_name = 'Cooling system'
        verbose_name_plural = 'Cooling systems'

    def __str__(self):
        return self.name


class Monitor(Product):
    panel_type = models.CharField(max_length=50, verbose_name="Panel type")
    resolution = models.CharField(max_length=20, verbose_name="Resolution")
    refresh_rate = models.PositiveSmallIntegerField(verbose_name="Refresh rate, Hz")
    response_time = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Response time, ms")
    aspect_ratio = models.CharField(max_length=10, verbose_name="Aspect ratio")
    brightness = models.PositiveSmallIntegerField(verbose_name="Brightness, cd/m²")
    contrast_ratio = models.CharField(max_length=20, verbose_name="Contrast ratio")
    color_gamut = models.CharField(max_length=50, verbose_name="Color gamut")
    inputs = models.CharField(max_length=100, verbose_name="Inputs")
    dimensions = models.CharField(max_length=50, verbose_name="Dimensions")

    class Meta:
        db_table = 'monitor'
        verbose_name = 'Monitor'
        verbose_name_plural = 'Monitors'

    def __str__(self):
        return self.name