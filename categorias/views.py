from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Categoria


# =========================
# LISTAR CATEGORÍAS
# =========================
def lista_categorias(request):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    categorias = Categoria.objects.filter(estado=True)
    
    # Enviar rol al template
    es_cajero = request.session.get('rol') == 'cajero'
    es_admin = request.session.get('rol') == 'administrador'
    
    return render(request, 'categorias/lista.html', {
        'categorias': categorias,
        'es_cajero': es_cajero,
        'es_admin': es_admin,
    })


# =========================
# CREAR CATEGORÍA
# =========================
def crear_categoria(request):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Solo administrador puede crear
    if request.session.get('rol') != 'administrador':
        messages.error(request, '❌ Acceso denegado. Solo el administrador puede crear categorías.')
        return redirect('categorias:lista')
    
    if request.method == 'POST':
        nombre = request.POST.get('nomCategoria').strip()

        if not nombre:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('categorias:crear')

        # VALIDACIÓN DE DUPLICADO
        if Categoria.objects.filter(nomCategoria__iexact=nombre).exists():
            messages.error(request, 'Esa categoría ya existe')
            return redirect('categorias:crear')

        Categoria.objects.create(
            nomCategoria=nombre,
            estado=True
        )

        messages.success(request, f'Categoría "{nombre}" creada')
        return redirect('categorias:lista')

    return render(request, 'categorias/crear.html')


# =========================
# EDITAR CATEGORÍA
# =========================
def editar_categoria(request, id_categoria):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Solo administrador puede editar
    if request.session.get('rol') != 'administrador':
        messages.error(request, '❌ Acceso denegado. Solo el administrador puede editar categorías.')
        return redirect('categorias:lista')
    
    categoria = get_object_or_404(Categoria, id=id_categoria)

    if request.method == 'POST':
        nombre = request.POST.get('nomCategoria').strip()

        if not nombre:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('categorias:editar', id_categoria=id_categoria)

        # VALIDAR DUPLICADO EXCLUYENDO EL MISMO REGISTRO
        if Categoria.objects.filter(nomCategoria__iexact=nombre)\
                            .exclude(id=categoria.id).exists():
            messages.error(request, 'Ya existe otra categoría con ese nombre')
            return redirect('categorias:editar', id_categoria=id_categoria)

        categoria.nomCategoria = nombre
        categoria.save()

        messages.success(request, 'Categoría actualizada')
        return redirect('categorias:lista')

    return render(request, 'categorias/editar.html', {'categoria': categoria})


# =========================
# ELIMINAR (INACTIVAR)
# =========================
def eliminar_categoria(request, id_categoria):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Solo administrador puede eliminar
    if request.session.get('rol') != 'administrador':
        messages.error(request, '❌ Acceso denegado. Solo el administrador puede eliminar categorías.')
        return redirect('categorias:lista')
    
    categoria = get_object_or_404(Categoria, id=id_categoria)

    if request.method == 'POST':
        categoria.estado = False
        categoria.save()
        messages.success(request, 'Categoría eliminada')
        return redirect('categorias:lista')

    return render(request, 'categorias/eliminar.html', {'categoria': categoria})


# =========================
# RECUPERAR (OPCIONAL) - SOLO ADMIN
# =========================
def lista_inactivas(request):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Solo administrador puede ver inactivas
    if request.session.get('rol') != 'administrador':
        messages.error(request, '❌ Acceso denegado. Solo el administrador puede recuperar categorías.')
        return redirect('categorias:lista')
    
    categorias = Categoria.objects.filter(estado=False)
    return render(request, 'categorias/recuperar.html', {'categorias': categorias})


def recuperar_categoria(request, id_categoria):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Solo administrador puede recuperar
    if request.session.get('rol') != 'administrador':
        messages.error(request, '❌ Acceso denegado. Solo el administrador puede recuperar categorías.')
        return redirect('categorias:lista')
    
    categoria = get_object_or_404(Categoria, id=id_categoria)
    categoria.estado = True
    categoria.save()
    messages.success(request, 'Categoría recuperada')
    return redirect('categorias:inactivas')