from django.db import models
import re
from datetime import date, time, datetime
import datetime
import io
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils import timezone

from reportlab.pdfgen import canvas
from django.utils.text import slugify


class Vendedor(models.Model):

    nombre = models.CharField(max_length=255, null=False, blank=False)
    apellido = models.CharField(max_length=255, null=False, blank=False)
    telefono = models.CharField(max_length=10, null=False, blank=False)
    email = models.EmailField(max_length=255, blank=True, default="")
    foto = models.ImageField(upload_to='vendedores/', blank=True, null=True, help_text="Foto del vendedor")

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
        
    def validar(self):
        if not self.nombre:
            return ["El nombre del vendedor es obligatorio."]
        
        if not self.apellido:
            return ["El apellido del vendedor es obligatorio."]
        
        if not self.telefono:
            return ["El teléfono del vendedor es obligatorio."]
        
        if not re.match(r'^\d{10}$', self.telefono):
            return ["Formato del teléfono no válido, debe tener 10 dígitos."]
        
        return []

class Propiedad(models.Model):

    # Atributos
    titulo = models.CharField(max_length=255)
    precio = models.IntegerField()
    imagen = models.ImageField(upload_to='propiedades/')
    descripcion = models.TextField()
    habitaciones = models.IntegerField()
    bano = models.IntegerField()
    estacionamiento = models.IntegerField()
    creado = models.DateField(default=date.today)
    vendedor_id = models.ForeignKey(Vendedor, on_delete=models.SET_NULL, null=True)

    # Validación
    def validar(self):
        if not self.titulo:
            return "El título de la propiedad es obligatorio."
        if not self.precio:
            return "El precio de la propiedad es obligatorio."
        if len(self.descripcion) < 50:
            return "La descripción de la propiedad es obligatoria y debe tener al menos 50 caracteres."
        if not self.habitaciones:
            return "La cantidad de habitaciones es obligatoria."
        if not self.bano:
            return "La cantidad de baños es obligatoria."
        if not self.estacionamiento:
            return "La cantidad de lugares de estacionamiento es obligatoria."
        if not self.vendedor_id:
            return "Se debe elegir un vendedor."
        if not self.imagen:
            return "La imagen es obligatoria."
        return None
    

    def save(self, *args, **kwargs):
        self.validar()  # Llama al método validar al guardar
        super().save(*args, **kwargs)  # Guarda la propiedad

    
    def __str__(self):
        return self.titulo


    class Meta:
        verbose_name_plural = "propiedades"









class Categoria(models.Model):
    """
    Modelo para las categorías de las entradas del blog
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class Entrada(models.Model):
    """
    Modelo para las entradas del blog
    """
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('archivado', 'Archivado'),
    ]
    
    titulo = models.CharField(max_length=200, help_text="Título del artículo")
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL amigable (se genera automáticamente)")
    contenido = models.TextField(help_text="Contenido completo del artículo (HTML permitido)")
    resumen = models.TextField(max_length=300, blank=True, help_text="Resumen corto para mostrar en listados")
    
    # Metadatos
    autor = models.CharField(max_length=100, default="Admin")
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_publicacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Imagen
    imagen = models.ImageField(upload_to='blog/', blank=True, null=True, help_text="Imagen destacada del artículo")
    imagen_alt = models.CharField(max_length=200, blank=True, help_text="Texto alternativo para la imagen")
    
    # Configuración
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    tiempo_lectura = models.PositiveIntegerField(default=5, help_text="Tiempo estimado de lectura en minutos")
    destacado = models.BooleanField(default=False, help_text="Marcar como artículo destacado")
    
    # SEO
    meta_descripcion = models.CharField(max_length=160, blank=True, help_text="Descripción para motores de búsqueda")
    meta_keywords = models.CharField(max_length=200, blank=True, help_text="Palabras clave separadas por comas")
    
    class Meta:
        verbose_name = "Entrada"
        verbose_name_plural = "Entradas"
        ordering = ['-fecha_publicacion']
        indexes = [
            models.Index(fields=['estado', 'fecha_publicacion']),
            models.Index(fields=['categoria', 'estado']),
            models.Index(fields=['destacado', 'estado']),
        ]
    
    def __str__(self):
        return self.titulo
    
    def save(self, *args, **kwargs):
        # Generar slug automáticamente si no existe
        if not self.slug:
            self.slug = slugify(self.titulo)
            
        # Generar resumen automáticamente si no existe
        if not self.resumen and self.contenido:
            # Remover tags HTML básicos y truncar
            import re
            texto_limpio = re.sub(r'<[^>]+>', '', self.contenido)
            self.resumen = texto_limpio[:297] + '...' if len(texto_limpio) > 300 else texto_limpio
            
        # Generar meta_descripcion si no existe
        if not self.meta_descripcion and self.resumen:
            self.meta_descripcion = self.resumen[:157] + '...' if len(self.resumen) > 160 else self.resumen
            
        # Generar imagen_alt si no existe
        if not self.imagen_alt and self.imagen:
            self.imagen_alt = f"Imagen del artículo: {self.titulo}"
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """
        Retorna la URL absoluta de la entrada
        """
        from django.urls import reverse
        return reverse('entrada_detalle', kwargs={'slug': self.slug})
    
    @property
    def es_publicado(self):
        """
        Verifica si la entrada está publicada
        """
        return self.estado == 'publicado'
    
    @property
    def palabras_clave_lista(self):
        """
        Retorna las palabras clave como lista
        """
        if self.meta_keywords:
            return [keyword.strip() for keyword in self.meta_keywords.split(',')]
        return []
    
    @classmethod
    def publicadas(cls):
        """
        Manager personalizado para obtener solo entradas publicadas
        """
        return cls.objects.filter(estado='publicado', fecha_publicacion__lte=timezone.now())
    
    @classmethod
    def destacadas(cls):
        """
        Manager personalizado para obtener entradas destacadas
        """
        return cls.publicadas().filter(destacado=True)


class Consulta(models.Model):
    """
    Modelo unificado para todas las consultas del sitio web
    """
    ORIGEN_CHOICES = [
        ('propiedad', 'Consulta desde Propiedad'),
        ('general', 'Consulta General'),
        ('contacto', 'Página de Contacto'),
        ('home', 'Página Principal'),
        ('newsletter', 'Newsletter'),
    ]
    
    TIPO_CHOICES = [
        ('compra', 'Interés en Compra'),
        ('venta', 'Interés en Venta'),
        ('alquiler', 'Interés en Alquiler'),
        ('informacion', 'Solicitud de Información'),
        ('general', 'Consulta General'),
        ('otro', 'Otro'),
    ]
    
    # Campos básicos (siempre requeridos)
    nombre = models.CharField(max_length=100, help_text="Nombre del consultante")
    email = models.EmailField(help_text="Email de contacto")
    telefono = models.CharField(max_length=15, blank=True, help_text="Teléfono opcional")
    mensaje = models.TextField(help_text="Mensaje o consulta")
    
    # Campos de clasificación
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES, help_text="Desde dónde se hizo la consulta")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='general', help_text="Tipo de consulta")
    
    # Campos opcionales según el contexto
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, null=True, blank=True, 
                                related_name='consultas', help_text="Propiedad relacionada (si aplica)")
    asunto = models.CharField(max_length=200, blank=True, help_text="Asunto específico")
    presupuesto = models.CharField(max_length=50, blank=True, help_text="Presupuesto estimado")
    
    # Campos de gestión
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    respondida = models.BooleanField(default=False, help_text="Marca si ya fue respondida")
    respuesta = models.TextField(blank=True, help_text="Respuesta del agente")
    fecha_respuesta = models.DateTimeField(null=True, blank=True, help_text="Fecha de respuesta")
    
    # Campos de seguimiento
    prioridad = models.CharField(max_length=10, choices=[
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ], default='media')
    
    notas_internas = models.TextField(blank=True, help_text="Notas internas del equipo")
    
    class Meta:
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"
        ordering = ['-fecha_consulta']
        indexes = [
            models.Index(fields=['origen', 'fecha_consulta']),
            models.Index(fields=['respondida', 'prioridad']),
            models.Index(fields=['propiedad', 'fecha_consulta']),
        ]
    
    def __str__(self):
        if self.propiedad:
            return f"Consulta de {self.nombre} - {self.propiedad.titulo} ({self.get_origen_display()})"
        return f"Consulta de {self.nombre} - {self.get_tipo_display()} ({self.get_origen_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-asignar prioridad basada en el tipo
        if self.tipo in ['compra', 'venta'] and self.propiedad:
            self.prioridad = 'alta'
        elif self.tipo == 'alquiler':
            self.prioridad = 'media'
        
        super().save(*args, **kwargs)
    
    @property
    def es_sobre_propiedad(self):
        return self.propiedad is not None
    
    @property
    def tiempo_sin_responder(self):
        if self.respondida:
            return None
        from django.utils import timezone
        return timezone.now() - self.fecha_consulta


class SolicitudVisita(models.Model):
    """
    Modelo para solicitudes de visita a propiedades
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('rechazada', 'Rechazada'),
        ('completada', 'Completada'),
    ]
    
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='solicitudes_visita')
    nombre = models.CharField(max_length=100, help_text="Nombre del interesado")
    email = models.EmailField(help_text="Email de contacto")
    telefono = models.CharField(max_length=15, help_text="Teléfono de contacto")
    fecha_preferida = models.DateField(help_text="Fecha preferida para la visita")
    hora_preferida = models.TimeField(help_text="Hora preferida para la visita")
    mensaje = models.TextField(blank=True, help_text="Mensaje adicional")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    respuesta_agente = models.TextField(blank=True, help_text="Respuesta del agente")
    
    class Meta:
        verbose_name = "Solicitud de Visita"
        verbose_name_plural = "Solicitudes de Visita"
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"Visita {self.nombre} - {self.propiedad.titulo} ({self.get_estado_display()})"





class SuscriptorNewsletter(models.Model):
    """
    Modelo para suscriptores del newsletter
    """
    email = models.EmailField(unique=True, help_text="Email del suscriptor")
    nombre = models.CharField(max_length=100, blank=True, help_text="Nombre opcional")
    fecha_suscripcion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True, help_text="Suscripción activa")
    confirmado = models.BooleanField(default=False, help_text="Email confirmado")
    token_confirmacion = models.CharField(max_length=100, blank=True, help_text="Token para confirmar email")
    
    class Meta:
        verbose_name = "Suscriptor Newsletter"
        verbose_name_plural = "Suscriptores Newsletter"
        ordering = ['-fecha_suscripcion']
    
    def __str__(self):
        return f"{self.email} ({'Activo' if self.activo else 'Inactivo'})"
