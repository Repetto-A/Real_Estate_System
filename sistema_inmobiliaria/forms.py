from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, time
from .models import Consulta, SolicitudVisita, SuscriptorNewsletter


class ConsultaForm(forms.ModelForm):
    """
    Formulario unificado para todas las consultas
    """
    class Meta:
        model = Consulta
        fields = ['nombre', 'email', 'telefono', 'mensaje', 'asunto', 'tipo', 'presupuesto']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+54 9 11 1234-5678'
            }),
            'asunto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Asunto de tu consulta'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'presupuesto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: $50,000 - $100,000'
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu consulta aquí...'
            })
        }
        labels = {
            'nombre': 'Nombre completo',
            'email': 'Email',
            'telefono': 'Teléfono',
            'asunto': 'Asunto',
            'tipo': 'Tipo de consulta',
            'presupuesto': 'Presupuesto estimado',
            'mensaje': 'Mensaje'
        }


# Formulario simplificado para compatibilidad con modals existentes
class ContactoPropiedadForm(forms.ModelForm):
    """
    Formulario simplificado para contactar desde propiedades (compatibilidad)
    """
    class Meta:
        model = Consulta
        fields = ['nombre', 'email', 'telefono', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+54 9 11 1234-5678'
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu consulta aquí...'
            })
        }
        labels = {
            'nombre': 'Nombre completo',
            'email': 'Email',
            'telefono': 'Teléfono',
            'mensaje': 'Mensaje'
        }


class SolicitudVisitaForm(forms.ModelForm):
    """
    Formulario para solicitar una visita a una propiedad
    """
    class Meta:
        model = SolicitudVisita
        fields = ['nombre', 'email', 'telefono', 'fecha_preferida', 'hora_preferida', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+54 9 11 1234-5678'
            }),
            'fecha_preferida': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': date.today().strftime('%Y-%m-%d')
            }),
            'hora_preferida': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mensaje adicional (opcional)...'
            })
        }
        labels = {
            'nombre': 'Nombre completo',
            'email': 'Email de contacto',
            'telefono': 'Teléfono de contacto',
            'fecha_preferida': 'Fecha preferida',
            'hora_preferida': 'Hora preferida',
            'mensaje': 'Mensaje adicional'
        }

    def clean_fecha_preferida(self):
        fecha = self.cleaned_data.get('fecha_preferida')
        if fecha and fecha < date.today():
            raise ValidationError('La fecha no puede ser anterior a hoy.')
        return fecha

    def clean_hora_preferida(self):
        hora = self.cleaned_data.get('hora_preferida')
        if hora:
            # Validar horario comercial (9:00 - 18:00)
            if hora < time(9, 0) or hora > time(18, 0):
                raise ValidationError('El horario debe estar entre 9:00 y 18:00.')
        return hora


class ContactoGeneralForm(forms.ModelForm):
    """
    Formulario para consultas generales del sitio web (compatibilidad)
    """
    class Meta:
        model = Consulta
        fields = ['nombre', 'email', 'telefono', 'asunto', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+54 9 11 1234-5678 (opcional)'
            }),
            'asunto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Asunto de tu consulta'
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe tu consulta o comentario...'
            })
        }
        labels = {
            'nombre': 'Nombre completo',
            'email': 'Email de contacto',
            'telefono': 'Teléfono',
            'asunto': 'Asunto',
            'mensaje': 'Mensaje'
        }


class NewsletterForm(forms.ModelForm):
    """
    Formulario para suscripción al newsletter
    """
    class Meta:
        model = SuscriptorNewsletter
        fields = ['email', 'nombre']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre (opcional)'
            })
        }
        labels = {
            'email': 'Email',
            'nombre': 'Nombre'
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Verificar si ya existe un suscriptor activo con este email
            if SuscriptorNewsletter.objects.filter(email=email, activo=True).exists():
                raise ValidationError('Este email ya está suscrito a nuestro newsletter.')
        return email


class NewsletterSimpleForm(forms.Form):
    """
    Formulario simple para suscripción rápida al newsletter (solo email)
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com'
        }),
        label='Email'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Verificar si ya existe un suscriptor activo con este email
            if SuscriptorNewsletter.objects.filter(email=email, activo=True).exists():
                raise ValidationError('Este email ya está suscrito a nuestro newsletter.')
        return email
