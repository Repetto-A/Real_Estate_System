from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Propiedad, Vendedor, Entrada, Categoria, Consulta, SolicitudVisita, SuscriptorNewsletter
from .forms import ConsultaForm, ContactoPropiedadForm, SolicitudVisitaForm, ContactoGeneralForm, NewsletterForm, NewsletterSimpleForm
from .email_utils import enviar_email_contacto_propiedad, enviar_email_solicitud_visita, enviar_email_contacto_general, enviar_confirmacion_newsletter
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.

def home(request):

    propiedades = Propiedad.objects.all()
    return render(request, 'sistema_inmobiliaria/home.html', {'propiedades': propiedades})

def login(request):

    return render(request, 'sistema_inmobiliaria/login.html')

def blog(request):
    from datetime import datetime, timedelta
    
    # Obtener solo entradas publicadas
    entradas_list = Entrada.publicadas().select_related('categoria')
    
    # Filtrar por categoría si se especifica
    categoria_slug = request.GET.get('categoria')
    categoria_obj = None
    if categoria_slug:
        categoria_obj = Categoria.objects.filter(slug=categoria_slug).first()
        entradas_list = entradas_list.filter(categoria__slug=categoria_slug)
    
    # Búsqueda por término
    search = request.GET.get('search')
    if search:
        entradas_list = entradas_list.filter(
            Q(titulo__icontains=search) | 
            Q(contenido__icontains=search) |
            Q(resumen__icontains=search) |
            Q(autor__icontains=search)
        )
    
    # Filtro por fecha
    fecha_filtro = request.GET.get('fecha')
    if fecha_filtro:
        hoy = datetime.now().date()
        if fecha_filtro == 'ultima_semana':
            fecha_inicio = hoy - timedelta(days=7)
            entradas_list = entradas_list.filter(fecha_publicacion__gte=fecha_inicio)
        elif fecha_filtro == 'ultimo_mes':
            fecha_inicio = hoy - timedelta(days=30)
            entradas_list = entradas_list.filter(fecha_publicacion__gte=fecha_inicio)
        elif fecha_filtro == 'ultimo_ano':
            fecha_inicio = hoy - timedelta(days=365)
            entradas_list = entradas_list.filter(fecha_publicacion__gte=fecha_inicio)
    
    # Filtro por entradas destacadas
    solo_destacadas = request.GET.get('destacadas')
    if solo_destacadas == 'si':
        entradas_list = entradas_list.filter(destacado=True)
    
    # Ordenamiento
    orden = request.GET.get('orden', 'reciente')
    if orden == 'reciente':
        entradas_list = entradas_list.order_by('-fecha_publicacion')
    elif orden == 'antiguo':
        entradas_list = entradas_list.order_by('fecha_publicacion')
    elif orden == 'titulo':
        entradas_list = entradas_list.order_by('titulo')
    elif orden == 'lectura':
        entradas_list = entradas_list.order_by('tiempo_lectura')
    
    # Paginación
    paginator = Paginator(entradas_list, 6)  # 6 entradas por página
    page_number = request.GET.get('page')
    entradas = paginator.get_page(page_number)
    
    # Obtener categorías para el filtro
    categorias = Categoria.objects.all()
    
    # Entradas destacadas para el sidebar
    entradas_destacadas = Entrada.destacadas()[:3]
    
    # Obtener autores únicos para el filtro
    autores = Entrada.publicadas().values_list('autor', flat=True).distinct().order_by('autor')
    
    context = {
        'entradas': entradas,
        'categorias': categorias,
        'entradas_destacadas': entradas_destacadas,
        'autores': autores,
        'categoria_actual': categoria_slug,
        'categoria_obj': categoria_obj,
        'search_query': search,
        'fecha_filtro': fecha_filtro,
        'solo_destacadas': solo_destacadas,
        'orden_actual': orden,
        'total_entradas': entradas_list.count(),
    }
    
    return render(request, 'sistema_inmobiliaria/blog.html', context)

def contacto(request):
    if request.method == "POST":
        try:
            print("=== DEBUG: Formulario de contacto recibido ===")
            
            # Obtener datos del formulario (simplificado sin preferencias)
            nombre = request.POST.get("nombre", "")
            email_cliente = request.POST.get("email", "")
            mensaje = request.POST.get("mensaje", "")
            tipo = request.POST.get("tipo", "")
            precio = request.POST.get("precio", "")
            telefono = request.POST.get("telefono", "")
            propiedad_id = request.POST.get("propiedad_id", "")
            
            # Datos específicos para solicitudes de visita
            fecha_visita = request.POST.get("fecha_visita", "")
            hora_visita = request.POST.get("hora_visita", "")
            
            print(f"Datos: {nombre}, {email_cliente}, {tipo}, {precio}, {telefono}, propiedad_id: {propiedad_id}")
            if tipo == "Visita":
                print(f"Solicitud de visita - Fecha: {fecha_visita}, Hora: {hora_visita}")
            
            # Obtener información de la propiedad si se proporciona ID
            propiedad_info = ""
            if propiedad_id:
                try:
                    propiedad = Propiedad.objects.get(id=propiedad_id)
                    propiedad_info = f"""

=== INFORMACIÓN DE LA PROPIEDAD ===
Propiedad: {propiedad.titulo}
Precio: ${propiedad.precio:,.0f}
Habitaciones: {propiedad.habitaciones}
Baños: {propiedad.bano}
Estacionamiento: {propiedad.estacionamiento}
Vendedor: {propiedad.vendedor_id.nombre if propiedad.vendedor_id else 'No asignado'} {propiedad.vendedor_id.apellido if propiedad.vendedor_id else ''}
URL: {request.build_absolute_uri(reverse('Propiedad', args=[propiedad.id]))}
"""
                    print(f"Propiedad encontrada: {propiedad.titulo}")
                except Propiedad.DoesNotExist:
                    print(f"Propiedad con ID {propiedad_id} no encontrada")
                    propiedad_info = f"""

=== INFORMACIÓN DE LA PROPIEDAD ===
Propiedad ID: {propiedad_id} (Propiedad no encontrada)
"""
            
            # Guardar la consulta en el modelo unificado Consulta
            try:
                propiedad_obj = None
                if propiedad_id:
                    try:
                        propiedad_obj = Propiedad.objects.get(id=propiedad_id)
                    except Propiedad.DoesNotExist:
                        print(f"Propiedad con ID {propiedad_id} no encontrada")
                
                # Determinar origen y tipo de consulta
                origen = 'propiedad' if propiedad_obj else 'general'
                tipo_consulta = tipo.lower() if tipo else 'general'
                
                # Mapear tipos de consulta
                tipo_mapping = {
                    'compra': 'compra',
                    'venta': 'venta', 
                    'alquiler': 'alquiler',
                    'visita': 'informacion',  # Las visitas son solicitudes de información
                    'general': 'general'
                }
                tipo_final = tipo_mapping.get(tipo_consulta, 'general')
                
                # Crear la consulta unificada
                consulta = Consulta.objects.create(
                    nombre=nombre,
                    email=email_cliente,
                    telefono=telefono,
                    mensaje=mensaje,
                    origen=origen,
                    tipo=tipo_final,
                    propiedad=propiedad_obj,
                    presupuesto=precio if precio else '',
                    # Guardar información del agente si es una consulta de propiedad
                    notas_internas=f"Agente: {propiedad_obj.vendedor_id.nombre} ({propiedad_obj.vendedor_id.email})" if propiedad_obj and propiedad_obj.vendedor_id else ''
                )
                
                print(f"Consulta guardada con ID: {consulta.id} - Origen: {origen}, Tipo: {tipo_final}")
                
            except Exception as e:
                print(f"Error guardando consulta: {e}")
                import traceback
                traceback.print_exc()
            
            # Si es una solicitud de visita, también guardarla en SolicitudVisita
            if tipo == "Visita" and propiedad_id and fecha_visita and hora_visita:
                try:
                    from datetime import datetime
                    propiedad_obj = Propiedad.objects.get(id=propiedad_id)
                    
                    # Convertir fecha y hora a los formatos correctos
                    fecha_obj = datetime.strptime(fecha_visita, '%Y-%m-%d').date()
                    hora_obj = datetime.strptime(hora_visita, '%H:%M').time()
                    
                    # Crear la solicitud de visita
                    solicitud_visita = SolicitudVisita.objects.create(
                        propiedad=propiedad_obj,
                        nombre=nombre,
                        email=email_cliente,
                        telefono=telefono,
                        fecha_preferida=fecha_obj,
                        hora_preferida=hora_obj,
                        mensaje=mensaje,
                        estado='pendiente'
                    )
                    
                    print(f"Solicitud de visita guardada con ID: {solicitud_visita.id}")
                    
                    # Enviar email específico para solicitud de visita
                    from .email_utils import enviar_email_solicitud_visita
                    email_enviado = enviar_email_solicitud_visita(solicitud_visita)
                    print(f"Email de solicitud de visita enviado: {email_enviado}")
                    
                    # Marcar que ya se envió un email específico
                    if email_enviado:
                        email_ya_enviado = True
                    
                except Exception as e:
                    print(f"Error guardando solicitud de visita: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Crear mensaje completo con teléfono y propiedad
            mensaje_completo = f"""NUEVA CONSULTA DE CONTACTO
            
Nombre: {nombre}
Email: {email_cliente}
Teléfono: {telefono}
Tipo de operación: {tipo}
Presupuesto: ${precio}{propiedad_info}

Mensaje:
{mensaje}"""
            
            # Variable para controlar si ya se envió un email específico
            email_ya_enviado = False
            
            # Verificar configuración de email
            print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
            print(f"EMAIL_HOST_PASSWORD configurado: {'Sí' if settings.EMAIL_HOST_PASSWORD else 'No'}")
            
            # Enviar email específico según el tipo de consulta (solo si no se envió ya uno)
            if not email_ya_enviado:
                try:
                    print("Enviando email específico...")
                    email_enviado = False
                    
                    # Si es una consulta de propiedad (no visita), usar email específico
                    if propiedad_id and tipo != "Visita":
                        try:
                            propiedad_obj = Propiedad.objects.get(id=propiedad_id)
                            # Crear objeto temporal para el email (compatible con el template)
                            class ContactoTemp:
                                def __init__(self, nombre, email, telefono, mensaje, propiedad):
                                    self.nombre = nombre
                                    self.email = email
                                    self.telefono = telefono
                                    self.mensaje = mensaje
                                    self.propiedad = propiedad
                            
                            contacto_temp = ContactoTemp(nombre, email_cliente, telefono, mensaje, propiedad_obj)
                            from .email_utils import enviar_email_contacto_propiedad
                            email_enviado = enviar_email_contacto_propiedad(contacto_temp)
                            print(f"Email de contacto de propiedad enviado: {email_enviado}")
                        except Propiedad.DoesNotExist:
                            print(f"Propiedad con ID {propiedad_id} no encontrada para email")
                    
                    # Si es una consulta general, usar email general
                    elif not propiedad_id or tipo != "Visita":
                        # Crear objeto temporal para el email general
                        class ContactoGeneralTemp:
                            def __init__(self, nombre, email, telefono, asunto, mensaje):
                                self.nombre = nombre
                                self.email = email
                                self.telefono = telefono
                                self.asunto = asunto or "Consulta general"
                                self.mensaje = mensaje
                        
                        contacto_temp = ContactoGeneralTemp(nombre, email_cliente, telefono, tipo or "Consulta general", mensaje)
                        from .email_utils import enviar_email_contacto_general
                        email_enviado = enviar_email_contacto_general(contacto_temp)
                        print(f"Email de contacto general enviado: {email_enviado}")
                    
                    # Fallback al email genérico si los específicos fallan
                    if not email_enviado:
                        print("Usando email genérico como fallback...")
                        subject = f"Consulta de {nombre}"
                        from_email = settings.EMAIL_HOST_USER
                        recipient_list = ["alerepettosac@gmail.com"]
                        
                        send_mail(subject, mensaje_completo, from_email, recipient_list)
                        email_enviado = True
                    
                    print(f"Email enviado exitosamente: {email_enviado}")
                    
                except Exception as e:
                    print(f"Error enviando email: {e}")
                    import traceback
                    traceback.print_exc()
                    email_enviado = False
            
            # Respuesta al usuario (tanto para emails específicos como para visitas)
            try:
                # Si es una petición AJAX (desde el modal), devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    if email_ya_enviado or email_enviado:
                        return JsonResponse({'success': True, 'message': '¡Gracias por contactarnos! Hemos recibido tu mensaje y nos pondremos en contacto contigo en breve.'})
                    else:
                        return JsonResponse({'success': False, 'message': 'Hubo un problema enviando el email. Por favor intenta nuevamente.'}, status=500)
                
                # Para requests normales (no AJAX)
                if email_ya_enviado or email_enviado:
                    messages.success(request, '¡Gracias por contactarnos! Hemos recibido tu mensaje y nos pondremos en contacto contigo en breve.')
                else:
                    messages.error(request, 'Hubo un problema enviando el email. Por favor intenta nuevamente.')
                return redirect('Contacto')
                
            except Exception as e:
                print(f"Error en respuesta: {e}")
                # Si es una petición AJAX, devolver error JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Hubo un problema procesando tu solicitud.'}, status=500)
                
                messages.error(request, 'Hubo un problema enviando el email. Por favor intenta nuevamente.')
            
        except Exception as e:
            print(f"Error general en contacto: {e}")
            import traceback
            traceback.print_exc()
            
            # Si es una petición AJAX, devolver error JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Hubo un error procesando tu mensaje. Por favor intenta nuevamente.'}, status=500)
            
            messages.error(request, 'Hubo un error procesando tu mensaje. Por favor intenta nuevamente.')
    
    return render(request, 'sistema_inmobiliaria/contacto.html')

def entrada(request, slug):
    # Obtener la entrada por slug, solo si está publicada
    entrada = get_object_or_404(
        Entrada.publicadas().select_related('categoria'), 
        slug=slug
    )
    
    # Obtener entradas relacionadas (misma categoría, excluyendo la actual)
    entradas_relacionadas = []
    if entrada.categoria:
        entradas_relacionadas = Entrada.publicadas().filter(
            categoria=entrada.categoria
        ).exclude(id=entrada.id)[:3]
    
    # Si no hay suficientes entradas relacionadas, completar con otras entradas
    if len(entradas_relacionadas) < 3:
        otras_entradas = Entrada.publicadas().exclude(
            id=entrada.id
        ).exclude(
            id__in=[e.id for e in entradas_relacionadas]
        )[:3 - len(entradas_relacionadas)]
        entradas_relacionadas = list(entradas_relacionadas) + list(otras_entradas)
    
    # Obtener todas las categorías con conteo de entradas para el sidebar
    from django.db.models import Count, Q
    categorias_con_conteo = Categoria.objects.annotate(
        entradas_count=Count('entrada', filter=Q(entrada__estado='publicado'))
    ).filter(entradas_count__gt=0)
    
    context = {
        'entrada': entrada,
        'entradas_relacionadas': entradas_relacionadas,
        'categorias_con_conteo': categorias_con_conteo,
    }
    
    return render(request, 'sistema_inmobiliaria/entrada.html', context)


def nosotros(request):

    return render(request, 'sistema_inmobiliaria/nosotros.html')

def propiedad(request, id):
    propiedad = get_object_or_404(Propiedad, id=id)
    propiedades_relacionadas = Propiedad.objects.exclude(id=id).order_by('?')[:3]
    
    context = {
        'propiedad': propiedad,
        'propiedades_relacionadas': propiedades_relacionadas
    }
    return render(request, 'sistema_inmobiliaria/propiedad.html', context)

def propiedades(request):
    propiedades = Propiedad.objects.all()
    
    # Filtros de búsqueda
    search = request.GET.get('search')
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')
    habitaciones = request.GET.get('habitaciones')
    banos = request.GET.get('banos')
    estacionamiento = request.GET.get('estacionamiento')
    
    if search:
        propiedades = propiedades.filter(
            Q(titulo__icontains=search) | 
            Q(descripcion__icontains=search)
        )
    
    if precio_min:
        propiedades = propiedades.filter(precio__gte=precio_min)
    
    if precio_max:
        propiedades = propiedades.filter(precio__lte=precio_max)
    
    if habitaciones:
        propiedades = propiedades.filter(habitaciones__gte=habitaciones)
    
    if banos:
        propiedades = propiedades.filter(bano__gte=banos)
    
    if estacionamiento:
        propiedades = propiedades.filter(estacionamiento__gte=estacionamiento)
    
    context = {
        'propiedades': propiedades,
        'search': search or '',
        'precio_min': precio_min or '',
        'precio_max': precio_max or '',
        'habitaciones': habitaciones or '',
        'banos': banos or '',
        'estacionamiento': estacionamiento or '',
        'total_propiedades': propiedades.count()
    }
    
    return render(request, 'sistema_inmobiliaria/propiedades.html', context)


# ============ NUEVAS VISTAS PARA CONTACTO Y NEWSLETTER ============

def contacto_propiedad(request, propiedad_id):
    """
    Vista para manejar el formulario de contacto desde una propiedad específica
    """
    print(f"=== DEBUG: contacto_propiedad llamada - Propiedad ID: {propiedad_id} ===")
    print(f"Método: {request.method}")
    
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)
    
    if request.method == 'POST':
        print(f"POST data: {dict(request.POST)}")
        form = ContactoPropiedadForm(request.POST)
        print(f"Formulario válido: {form.is_valid()}")
        
        if form.is_valid():
            print("Formulario válido - guardando contacto")
            contacto = form.save(commit=False)
            contacto.propiedad = propiedad
            contacto.save()
            print(f"Contacto guardado con ID: {contacto.id}")
            
            # Enviar email al agente
            try:
                print("Intentando enviar email al agente...")
                if enviar_email_contacto_propiedad(contacto):
                    print("Email enviado exitosamente")
                    messages.success(request, 
                        f'Tu consulta ha sido enviada al agente. Te contactaremos pronto.')
                else:
                    print("Error enviando email")
                    messages.warning(request, 
                        'Tu consulta fue guardada pero hubo un problema enviando el email. Te contactaremos pronto.')
            except Exception as e:
                print(f"Excepción enviando email: {e}")
                messages.warning(request, 
                    'Tu consulta fue guardada pero hubo un problema enviando el email. Te contactaremos pronto.')
            
            return redirect('Propiedad', id=propiedad_id)
        else:
            print(f"Errores del formulario: {form.errors}")
    else:
        print("Método GET - creando formulario vacío")
        form = ContactoPropiedadForm()
    
    return render(request, 'sistema_inmobiliaria/contacto_propiedad.html', {
        'form': form,
        'propiedad': propiedad
    })


def solicitar_visita(request, propiedad_id):
    """
    Vista para manejar el formulario de solicitud de visita
    """
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)
    
    if request.method == 'POST':
        form = SolicitudVisitaForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.propiedad = propiedad
            solicitud.save()
            
            # Enviar email al agente
            if enviar_email_solicitud_visita(solicitud):
                messages.success(request, 
                    f'Tu solicitud de visita ha sido enviada al agente. Te contactaremos para confirmar.')
            else:
                messages.warning(request, 
                    'Tu solicitud fue guardada pero hubo un problema enviando el email. Te contactaremos pronto.')
            
            return redirect('Propiedad', id=propiedad_id)
    else:
        form = SolicitudVisitaForm()
    
    return render(request, 'sistema_inmobiliaria/solicitar_visita.html', {
        'form': form,
        'propiedad': propiedad
    })


def contacto_general(request):
    """
    Vista mejorada para el formulario de contacto general
    """
    if request.method == 'POST':
        form = ContactoGeneralForm(request.POST)
        if form.is_valid():
            contacto = form.save()
            
            # Enviar email a administración
            if enviar_email_contacto_general(contacto):
                messages.success(request, 
                    'Tu consulta ha sido enviada correctamente. Te responderemos pronto.')
            else:
                messages.warning(request, 
                    'Tu consulta fue guardada pero hubo un problema enviando el email. Te contactaremos pronto.')
            
            return redirect('contacto_general')
    else:
        form = ContactoGeneralForm()
    
    return render(request, 'sistema_inmobiliaria/contacto_general.html', {
        'form': form
    })


@require_POST
def suscribir_newsletter(request):
    """
    Vista AJAX para suscripción rápida al newsletter
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email requerido'})
        
        # Verificar si ya existe
        if SuscriptorNewsletter.objects.filter(email=email, activo=True).exists():
            return JsonResponse({
                'success': False, 
                'message': 'Este email ya está suscrito a nuestro newsletter'
            })
        
        # Crear suscriptor
        suscriptor = SuscriptorNewsletter.objects.create(email=email)
        
        # Enviar email de confirmación
        if enviar_confirmacion_newsletter(suscriptor, request):
            return JsonResponse({
                'success': True, 
                'message': 'Te hemos enviado un email de confirmación. Revisa tu bandeja de entrada.'
            })
        else:
            return JsonResponse({
                'success': True, 
                'message': 'Suscripción registrada. Te contactaremos pronto.'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': 'Hubo un error procesando tu solicitud. Inténtalo de nuevo.'
        })


def confirmar_newsletter(request, token):
    """
    Vista para confirmar suscripción al newsletter
    """
    try:
        suscriptor = SuscriptorNewsletter.objects.get(token_confirmacion=token)
        suscriptor.confirmado = True
        suscriptor.token_confirmacion = ''  # Limpiar token
        suscriptor.save()
        
        messages.success(request, 
            '¡Gracias! Tu suscripción al newsletter ha sido confirmada.')
        
    except SuscriptorNewsletter.DoesNotExist:
        messages.error(request, 
            'Token de confirmación inválido o expirado.')
    
    return redirect('Home')


def newsletter_completo(request):
    """
    Vista para formulario completo de newsletter (con nombre)
    """
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            suscriptor = form.save()
            
            # Enviar email de confirmación
            if enviar_confirmacion_newsletter(suscriptor, request):
                messages.success(request, 
                    'Te hemos enviado un email de confirmación. Revisa tu bandeja de entrada.')
            else:
                messages.success(request, 
                    'Suscripción registrada. Te contactaremos pronto.')
            
            return redirect('newsletter_completo')
    else:
        form = NewsletterForm()
    
    return render(request, 'sistema_inmobiliaria/newsletter.html', {
        'form': form
    })