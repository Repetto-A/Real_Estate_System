from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone

from .models import SolicitudVisita, Consulta
from .email_utils import enviar_notificacion_visita_confirmada, enviar_notificacion_visita_rechazada


@receiver(pre_save, sender=SolicitudVisita)
def solicitud_visita_pre_save(sender, instance, **kwargs):
    """
    Guarda el estado anterior de la solicitud de visita antes de guardar
    """
    if instance.pk:
        try:
            instance._estado_anterior = SolicitudVisita.objects.get(pk=instance.pk).estado
        except SolicitudVisita.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=SolicitudVisita)
def solicitud_visita_post_save(sender, instance, created, **kwargs):
    """
    Envía notificación por email cuando cambia el estado de una solicitud de visita
    """
    if not created and hasattr(instance, '_estado_anterior'):
        estado_anterior = instance._estado_anterior
        estado_actual = instance.estado
        
        # Solo enviar email si el estado cambió y no es 'pendiente'
        if estado_anterior != estado_actual and estado_actual != 'pendiente':
            if estado_actual == 'confirmada':
                enviar_notificacion_visita_confirmada(instance)
            elif estado_actual == 'rechazada':
                enviar_notificacion_visita_rechazada(instance)


@receiver(pre_save, sender=Consulta)
def consulta_pre_save(sender, instance, **kwargs):
    """
    Guarda el estado anterior de la consulta antes de guardar
    """
    if instance.pk:
        try:
            consulta_anterior = Consulta.objects.get(pk=instance.pk)
            instance._respondida_anterior = consulta_anterior.respondida
            instance._respuesta_anterior = consulta_anterior.respuesta
        except Consulta.DoesNotExist:
            instance._respondida_anterior = None
            instance._respuesta_anterior = ""
    else:
        instance._respondida_anterior = None
        instance._respuesta_anterior = ""


@receiver(post_save, sender=Consulta)
def consulta_post_save(sender, instance, created, **kwargs):
    """
    Envía notificación por email cuando se responde una consulta
    """
    print(f"DEBUG: consulta_post_save called - created: {created}, id: {instance.pk}")
    
    if not created and hasattr(instance, '_respondida_anterior'):
        respondida_anterior = instance._respondida_anterior
        respuesta_anterior = instance._respuesta_anterior
        
        print(f"DEBUG: respondida_anterior: {respondida_anterior}, instance.respondida: {instance.respondida}")
        print(f"DEBUG: respuesta_anterior: '{respuesta_anterior}', instance.respuesta: '{instance.respuesta}'")
        
        # Condiciones más flexibles para enviar email
        enviar_email = False
        
        # Caso 1: Se marcó como respondida por primera vez y hay respuesta
        if not respondida_anterior and instance.respondida and instance.respuesta:
            enviar_email = True
            print("DEBUG: Caso 1 - Primera vez respondida")
        
        # Caso 2: Ya estaba respondida pero se cambió la respuesta
        elif (respondida_anterior and instance.respondida and 
              instance.respuesta and instance.respuesta.strip() != respuesta_anterior.strip()):
            enviar_email = True
            print("DEBUG: Caso 2 - Respuesta actualizada")
        
        # Caso 3: Se agregó respuesta sin marcar como respondida
        elif (instance.respuesta and instance.respuesta.strip() != respuesta_anterior.strip() and 
              len(instance.respuesta.strip()) > 0):
            enviar_email = True
            # Auto-marcar como respondida
            instance.respondida = True
            print("DEBUG: Caso 3 - Auto-marcando como respondida")
        
        if enviar_email:
            print("DEBUG: Enviando email de consulta respondida")
            # Actualizar fecha de respuesta si no está establecida
            if not instance.fecha_respuesta:
                instance.fecha_respuesta = timezone.now()
                instance.save(update_fields=['fecha_respuesta'])
            
            enviar_notificacion_consulta_respondida(instance)
        else:
            print("DEBUG: No se cumplieron las condiciones para enviar email")


def enviar_notificacion_consulta_respondida(consulta):
    """
    Envía email al cliente informando que su consulta fue respondida
    """
    print(f"DEBUG: Iniciando envío de email para consulta ID: {consulta.pk}")
    print(f"DEBUG: Email destinatario: {consulta.email}")
    print(f"DEBUG: Nombre: {consulta.nombre}")
    
    asunto = f"Respuesta a tu consulta - {consulta.asunto or 'Consulta General'}"
    print(f"DEBUG: Asunto del email: {asunto}")
    
    # Contexto para el template
    context = {
        'consulta': consulta,
        'propiedad': consulta.propiedad,
    }
    
    try:
        # Renderizar template HTML
        print("DEBUG: Renderizando template HTML")
        html_content = render_to_string('emails/consulta_respondida.html', context)
        text_content = strip_tags(html_content)
        print("DEBUG: Template renderizado correctamente")
        
        print("DEBUG: Creando mensaje de email")
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[consulta.email],
        )
        msg.attach_alternative(html_content, "text/html")
        
        print("DEBUG: Enviando email...")
        msg.send()
        print("DEBUG: Email enviado exitosamente")
        return True
    except Exception as e:
        print(f"ERROR enviando email de consulta respondida: {e}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        return False
