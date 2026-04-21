from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Categoria


# =========================
# LISTAR CATEGORÍAS
# =========================
def lista_categorias(request):
    categorias = Categoria.objects.filter(estado=True)
    return render(request, 'categorias/lista.html', {'categorias': categorias})


# =========================
# CREAR CATEGORÍA
# =========================
def crear_categoria(request):
    if request.method == 'POST':
        nombre = request.POST.get('nomCategoria').strip()

        if not nombre:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('categorias:crear')

        #  VALIDACIÓN DE DUPLICADO
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
    categoria = get_object_or_404(Categoria, id=id_categoria)

    if request.method == 'POST':
        categoria.estado = False
        categoria.save()
        messages.success(request, 'Categoría eliminada')
        return redirect('categorias:lista')

    return render(request, 'categorias/eliminar.html', {'categoria': categoria})


# =========================
# RECUPERAR (OPCIONAL)
# =========================
def lista_inactivas(request):
    categorias = Categoria.objects.filter(estado=False)
    return render(request, 'categorias/recuperar.html', {'categorias': categorias})


def recuperar_categoria(request, id_categoria):
    categoria = get_object_or_404(Categoria, id=id_categoria)
    categoria.estado = True
    categoria.save()
    messages.success(request, 'Categoría recuperada')
    return redirect('categorias:inactivas')