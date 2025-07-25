from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
import uuid


def enviar_email_contacto_propiedad(contacto):
    """
    Envía email al agente cuando alguien contacta sobre una propiedad
    """
    propiedad = contacto.propiedad
    agente = propiedad.vendedor_id
    
    if not agente or not agente.email:
        return False
    
    asunto = f"Nueva consulta sobre {propiedad.titulo}"
    
    # Contexto para el template
    context = {
        'contacto': contacto,
        'propiedad': propiedad,
        'agente': agente,
    }
    
    # Renderizar template HTML
    html_content = render_to_string('emails/contacto_propiedad_agente.html', context)
    text_content = strip_tags(html_content)
    
    try:
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[agente.email],
            reply_to=[contacto.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False


def enviar_email_solicitud_visita(solicitud):
    """
    Envía email al agente cuando alguien solicita una visita
    """
    print(f"=== DEBUG: enviar_email_solicitud_visita ===")
    print(f"Solicitud ID: {solicitud.id}")
    
    propiedad = solicitud.propiedad
    print(f"Propiedad: {propiedad.titulo}")
    
    agente = propiedad.vendedor_id
    print(f"Agente: {agente}")
    print(f"Agente email: {agente.email if agente else 'No agente'}")
    
    if not agente or not agente.email:
        print(f"ERROR: No hay agente o email para la propiedad {propiedad.titulo}")
        return False
    
    asunto = f"Nueva solicitud de visita para {propiedad.titulo}"
    
    # Contexto para el template
    context = {
        'solicitud': solicitud,
        'propiedad': propiedad,
        'agente': agente,
    }
    
    # Renderizar template HTML
    print(f"Renderizando template con contexto...")
    try:
        html_content = render_to_string('emails/solicitud_visita_agente.html', context)
        text_content = strip_tags(html_content)
        print(f"Template renderizado exitosamente")
    except Exception as e:
        print(f"ERROR renderizando template: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"Enviando email a: {agente.email}")
    print(f"Asunto: {asunto}")
    
    try:
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[agente.email],
            reply_to=[solicitud.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        print(f"Email enviado exitosamente a {agente.email}")
        return True
    except Exception as e:
        print(f"ERROR enviando email: {e}")
        import traceback
        traceback.print_exc()
        return False


def enviar_email_contacto_general(contacto):
    """
    Envía email a administración por consulta general
    """
    asunto = f"Nueva consulta general de {contacto.nombre}"
    
    # Contexto para el template
    context = {
        'contacto': contacto,
    }
    
    # Renderizar template HTML
    html_content = render_to_string('emails/contacto_general_admin.html', context)
    text_content = strip_tags(html_content)
    
    try:
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[settings.EMAIL_HOST_USER],  # Enviar a la misma cuenta admin
            reply_to=[contacto.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False


def enviar_confirmacion_newsletter(suscriptor, request):
    """
    Envía email de confirmación para suscripción al newsletter
    """
    # Generar token único para confirmación
    token = str(uuid.uuid4())
    suscriptor.token_confirmacion = token
    suscriptor.save()
    
    asunto = "Confirma tu suscripción al newsletter"
    
    # URL de confirmación
    confirm_url = request.build_absolute_uri(
        reverse('confirmar_newsletter', kwargs={'token': token})
    )
    
    # Contexto para el template
    context = {
        'suscriptor': suscriptor,
        'confirm_url': confirm_url,
    }
    
    # Renderizar template HTML
    html_content = render_to_string('emails/confirmacion_newsletter.html', context)
    text_content = strip_tags(html_content)
    
    try:
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[suscriptor.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False


def enviar_notificacion_visita_confirmada(solicitud):
    """
    Envía email al cliente confirmando la visita
    """
    asunto = f"Visita confirmada - {solicitud.propiedad.titulo}"
    
    # Contexto para el template
    context = {
        'solicitud': solicitud,
        'propiedad': solicitud.propiedad,
        'agente': solicitud.propiedad.vendedor_id,
    }
    
    # Renderizar template HTML
    html_content = render_to_string('emails/visita_confirmada_cliente.html', context)
    text_content = strip_tags(html_content)
    
    try:
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[solicitud.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False


def enviar_notificacion_visita_rechazada(solicitud):
    """
    Envía email al cliente informando que la visita fue rechazada
    """
    asunto = f"Solicitud de visita - {solicitud.propiedad.titulo}"
    
    # Contexto para el template
    context = {
        'solicitud': solicitud,
        'propiedad': solicitud.propiedad,
        'agente': solicitud.propiedad.vendedor_id,
    }
    
    # Renderizar template HTML
    html_content = render_to_string('emails/visita_rechazada_cliente.html', context)
    text_content = strip_tags(html_content)
    
    try:
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[solicitud.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False
