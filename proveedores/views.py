from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Proveedor


# LISTAR
def lista_proveedores(request):
    proveedores = Proveedor.objects.filter(estado=True)
    return render(request, 'proveedores/lista.html', {'proveedores': proveedores})


# CREAR
def crear_proveedor(request):
    if request.method == 'POST':
        nombre = request.POST.get('nomProv').strip()
        direccion = request.POST.get('direccion').strip()
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')

        if not nombre or not direccion:
            messages.error(request, 'Nombre y dirección son obligatorios')
            return redirect('proveedores:crear')

        # VALIDAR DIRECCIÓN DUPLICADA
        if Proveedor.objects.filter(direccion__iexact=direccion).exists():
            messages.error(request, 'Ya existe un proveedor con esa dirección')
            return redirect('proveedores:crear')

        # VALIDAR MISMO NOMBRE PERO OTRA DIRECCIÓN
        if Proveedor.objects.filter(nomProv__iexact=nombre).exists():
            messages.warning(request, 'Ya existe un proveedor con ese nombre, verifica si es el mismo con otra dirección')

        Proveedor.objects.create(
            nomProv=nombre,
            direccion=direccion,
            email=email,
            telefono=telefono,
            estado=True
        )

        messages.success(request, 'Proveedor creado correctamente')
        return redirect('proveedores:lista')

    return render(request, 'proveedores/crear.html')
# EDITAR
def editar_proveedor(request, id_proveedor):
    proveedor = get_object_or_404(Proveedor, id=id_proveedor)

    if request.method == 'POST':
        nombre = request.POST.get('nomProv').strip()

        if not nombre:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('proveedores:editar', id_proveedor=id_proveedor)

        if Proveedor.objects.filter(nomProv__iexact=nombre).exclude(id=proveedor.id).exists():
            messages.error(request, 'Ya existe ese proveedor')
            return redirect('proveedores:editar', id_proveedor=id_proveedor)

        proveedor.nomProv = nombre
        proveedor.email = request.POST.get('email')
        proveedor.telefono = request.POST.get('telefono')
        proveedor.direccion = request.POST.get('direccion')
        proveedor.save()

        messages.success(request, 'Proveedor actualizado')
        return redirect('proveedores:lista')

    return render(request, 'proveedores/editar.html', {'proveedor': proveedor})


# ELIMINAR (SOFT)
def eliminar_proveedor(request, id_proveedor):
    proveedor = get_object_or_404(Proveedor, id=id_proveedor)

    if request.method == 'POST':
        proveedor.estado = False
        proveedor.save()
        messages.success(request, 'Proveedor eliminado')
        return redirect('proveedores:lista')

    return render(request, 'proveedores/eliminar.html', {'proveedor': proveedor})