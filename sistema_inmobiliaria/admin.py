from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models

from sistema_inmobiliaria.models import Propiedad, Vendedor, Categoria, Entrada, Consulta, SolicitudVisita, SuscriptorNewsletter

# Register your models here.

admin.site.register(Propiedad)


@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'telefono', 'email', 'foto_preview']
    list_filter = ['nombre', 'apellido']
    search_fields = ['nombre', 'apellido', 'telefono', 'email']
    fields = ['nombre', 'apellido', 'telefono', 'email', 'foto', 'foto_preview']
    readonly_fields = ['foto_preview']
    
    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = 'Nombre Completo'
    
    def foto_preview(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 50%; border: 2px solid #ddd;" />',
                obj.foto.url
            )
        return format_html(
            '<div style="width: 60px; height: 60px; background-color: #007bff; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px;">'
            '<i class="fas fa-user"></i>'
            '</div>'
        )
    foto_preview.short_description = 'Foto'


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion_corta', 'slug', 'creado']
    list_filter = ['creado']
    search_fields = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    ordering = ['nombre']
    
    def descripcion_corta(self, obj):
        if obj.descripcion:
            return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
        return '-'
    descripcion_corta.short_description = 'Descripción'


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 
        'autor', 
        'categoria', 
        'estado_badge', 
        'destacado_icon',
        'fecha_publicacion', 
        'tiempo_lectura',
        'imagen_preview'
    ]
    list_filter = [
        'estado', 
        'categoria', 
        'destacado', 
        'fecha_publicacion',
        'autor'
    ]
    search_fields = ['titulo', 'contenido', 'resumen', 'autor']
    prepopulated_fields = {'slug': ('titulo',)}
    ordering = ['-fecha_publicacion']
    date_hierarchy = 'fecha_publicacion'
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('titulo', 'slug', 'autor', 'categoria')
        }),
        ('Contenido', {
            'fields': ('resumen', 'contenido'),
            'classes': ('wide',)
        }),
        ('Imagen', {
            'fields': ('imagen', 'imagen_alt'),
        }),
        ('Configuración', {
            'fields': ('estado', 'destacado', 'tiempo_lectura', 'fecha_publicacion'),
            'classes': ('wide',)
        }),
        ('SEO', {
            'fields': ('meta_descripcion', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    # Forzar widget de archivo para el campo imagen
    formfield_overrides = {
        models.ImageField: {'widget': admin.widgets.AdminFileWidget},
    }
    
    def estado_badge(self, obj):
        colors = {
            'borrador': '#6c757d',
            'publicado': '#28a745', 
            'archivado': '#dc3545'
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def destacado_icon(self, obj):
        if obj.destacado:
            return format_html('<span style="color: #ffc107; font-size: 16px;">⭐</span>')
        return '-'
    destacado_icon.short_description = 'Destacado'
    
    def imagen_preview(self, obj):
        """Muestra una miniatura segura incluso para rutas antiguas almacenadas como cadena."""
        if not obj.imagen:
            return '-'

        # Si es un FieldFile moderno
        if hasattr(obj.imagen, 'url'):
            try:
                return format_html(
                    '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:4px;" />',
                    obj.imagen.url
                )
            except (ValueError, FileNotFoundError):
                # La imagen no existe físicamente
                return '-'

        # Soporte legado: obj.imagen es str con ruta relativa como 'blog/foo.jpg'
        from django.conf import settings
        ruta = obj.imagen
        # Si ya es URL absoluta, úsala tal cual; si no, préfix MEDIA_URL
        if not ruta.startswith(('http://', 'https://', '/')):
            ruta = settings.MEDIA_URL.rstrip('/') + '/' + ruta.lstrip('/')
        return format_html('<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:4px;" />', ruta)
    imagen_preview.short_description = 'Imagen'
    
    actions = ['marcar_como_publicado', 'marcar_como_borrador', 'marcar_como_destacado']
    
    def marcar_como_publicado(self, request, queryset):
        updated = queryset.update(estado='publicado')
        self.message_user(request, f'{updated} entrada(s) marcada(s) como publicada(s).')
    marcar_como_publicado.short_description = "Marcar como publicado"
    
    def marcar_como_borrador(self, request, queryset):
        updated = queryset.update(estado='borrador')
        self.message_user(request, f'{updated} entrada(s) marcada(s) como borrador.')
    marcar_como_borrador.short_description = "Marcar como borrador"
    
    def marcar_como_destacado(self, request, queryset):
        updated = queryset.update(destacado=True)
        self.message_user(request, f'{updated} entrada(s) marcada(s) como destacada(s).')
    marcar_como_destacado.short_description = "Marcar como destacado"


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 
        'email', 
        'origen_badge',
        'tipo_badge',
        'propiedad_link', 
        'prioridad_badge',
        'respondida_icon',
        'fecha_consulta'
    ]
    
    list_filter = [
        'origen', 
        'tipo', 
        'prioridad',
        'respondida', 
        'fecha_consulta',
        'propiedad'
    ]
    
    search_fields = [
        'nombre', 
        'email', 
        'mensaje', 
        'asunto',
        'propiedad__titulo'
    ]
    
    readonly_fields = ['fecha_consulta']
    
    fieldsets = (
        ('Información del Consultante', {
            'fields': ('nombre', 'email', 'telefono')
        }),
        ('Detalles de la Consulta', {
            'fields': ('origen', 'tipo', 'asunto', 'mensaje', 'propiedad', 'presupuesto')
        }),
        ('Gestión y Seguimiento', {
            'fields': ('prioridad', 'respondida', 'respuesta', 'fecha_respuesta', 'notas_internas')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_consulta',),
            'classes': ('collapse',)
        }),
    )
    
    def origen_badge(self, obj):
        colors = {
            'propiedad': 'primary',
            'general': 'secondary', 
            'contacto': 'info',
            'home': 'success',
            'newsletter': 'warning'
        }
        color = colors.get(obj.origen, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_origen_display()
        )
    origen_badge.short_description = 'Origen'
    
    def tipo_badge(self, obj):
        colors = {
            'compra': 'success',
            'venta': 'warning',
            'alquiler': 'info',
            'informacion': 'secondary',
            'general': 'light',
            'otro': 'dark'
        }
        color = colors.get(obj.tipo, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def prioridad_badge(self, obj):
        colors = {
            'baja': 'secondary',
            'media': 'primary',
            'alta': 'warning',
            'urgente': 'danger'
        }
        color = colors.get(obj.prioridad, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_prioridad_display()
        )
    prioridad_badge.short_description = 'Prioridad'
    
    def respondida_icon(self, obj):
        if obj.respondida:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Respondida</span>'
            )
        return format_html(
            '<span style="color: #ffc107; font-weight: bold;">⏳ Pendiente</span>'
        )
    respondida_icon.short_description = 'Estado'
    
    def propiedad_link(self, obj):
        if obj.propiedad:
            url = reverse('admin:sistema_inmobiliaria_propiedad_change', args=[obj.propiedad.id])
            return format_html('<a href="{}">{}</a>', url, obj.propiedad.titulo[:30])
        return '-'
    propiedad_link.short_description = 'Propiedad'


@admin.register(SolicitudVisita)
class SolicitudVisitaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email', 'propiedad', 'fecha_preferida', 'hora_preferida', 'estado', 'fecha_solicitud']
    list_filter = ['estado', 'fecha_solicitud', 'fecha_preferida', 'propiedad']
    search_fields = ['nombre', 'email', 'mensaje']
    readonly_fields = ['fecha_solicitud']
    ordering = ['-fecha_solicitud']
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('nombre', 'email', 'telefono')
        }),
        ('Detalles de la Visita', {
            'fields': ('propiedad', 'fecha_preferida', 'hora_preferida', 'mensaje')
        }),
        ('Estado y Respuesta', {
            'fields': ('estado', 'respuesta_agente')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_solicitud',),
            'classes': ('collapse',)
        }),
    )





@admin.register(SuscriptorNewsletter)
class SuscriptorNewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'nombre', 'fecha_suscripcion', 'activo', 'confirmado']
    list_filter = ['activo', 'confirmado', 'fecha_suscripcion']
    search_fields = ['email', 'nombre']
    readonly_fields = ['fecha_suscripcion', 'token_confirmacion']
    ordering = ['-fecha_suscripcion']


# Personalización del admin
admin.site.site_header = "Sistema Inmobiliaria - Administración"
admin.site.site_title = "Admin Sistema Inmobiliaria"
admin.site.index_title = "Panel de Administración"