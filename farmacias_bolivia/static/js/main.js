// ======================================================
// SCRIPT PRINCIPAL - FARMACIAS BOLIVIA
// ======================================================

$(document).ready(function() {
    console.log('🚀 Farmacias Bolivia - Sistema de Gestión Integral');
    
    // ======================================================
    // MANEJO DEL CARRITO
    // ======================================================
    
    // Agregar al carrito
    $('.agregar-carrito').click(function(e) {
        e.preventDefault();
        
        const button = $(this);
        const productoId = button.data('id');
        const nombre = button.data('nombre');
        const precio = button.data('precio');
        const cantidad = button.data('cantidad') || 1;
        
        mostrarLoading();
        
        $.ajax({
            url: '/api/carrito/agregar',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                producto_id: productoId,
                nombre: nombre,
                cantidad: cantidad,
                precio: precio
            }),
            success: function(response) {
                if (response.success) {
                    actualizarContadorCarrito(response.carrito_items);
                    mostrarNotificacion('Producto agregado al carrito', 'success');
                    
                    // Animación del botón
                    button.html('<i class="fas fa-check"></i> Agregado');
                    setTimeout(() => {
                        button.html('<i class="fas fa-cart-plus"></i> Agregar');
                    }, 2000);
                }
            },
            error: function() {
                mostrarNotificacion('Error al agregar producto', 'danger');
            },
            complete: function() {
                ocultarLoading();
            }
        });
    });
    
    // Actualizar cantidad en carrito
    $('.actualizar-cantidad').on('change', function() {
        const productoId = $(this).data('id');
        const cantidad = $(this).val();
        
        if (cantidad < 1) {
            eliminarDelCarrito(productoId);
            return;
        }
        
        $.ajax({
            url: '/api/carrito/actualizar',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                producto_id: productoId,
                cantidad: cantidad
            }),
            success: function(response) {
                if (response.success) {
                    location.reload();
                }
            }
        });
    });
    
    // Eliminar del carrito
    $('.eliminar-carrito').click(function() {
        const productoId = $(this).data('id');
        eliminarDelCarrito(productoId);
    });
    
    function eliminarDelCarrito(productoId) {
        mostrarLoading();
        
        $.ajax({
            url: '/api/carrito/eliminar',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                producto_id: productoId
            }),
            success: function(response) {
                if (response.success) {
                    actualizarContadorCarrito(response.carrito_items);
                    location.reload();
                }
            },
            complete: function() {
                ocultarLoading();
            }
        });
    }
    
    function actualizarContadorCarrito(total) {
        $('#carrito-count').text(total);
        if (total === 0) {
            $('#carrito-count').hide();
        } else {
            $('#carrito-count').show();
        }
    }
    
    // ======================================================
    // BÚSQUEDA DE PRODUCTOS (con debounce)
    // ======================================================
    
    let timeoutId;
    $('#search-producto').on('input', function() {
        clearTimeout(timeoutId);
        const termino = $(this).val();
        
        timeoutId = setTimeout(() => {
            if (termino.length >= 2) {
                buscarProductos(termino);
            } else if (termino.length === 0) {
                cargarProductosDefault();
            }
        }, 500);
    });
    
    function buscarProductos(termino) {
        mostrarLoading();
        
        $.ajax({
            url: `/api/medicamentos/buscar/${termino}`,
            method: 'GET',
            success: function(response) {
                if (response.resultados) {
                    mostrarResultadosBusqueda(response.resultados);
                }
            },
            complete: function() {
                ocultarLoading();
            }
        });
    }
    
    function mostrarResultadosBusqueda(resultados) {
        const container = $('#productos-container');
        container.empty();
        
        if (resultados.length === 0) {
            container.html(`
                <div class="col-12 text-center py-5">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <p>No se encontraron productos</p>
                </div>
            `);
            return;
        }
        
        resultados.forEach(producto => {
            container.append(`
                <div class="col-md-3 mb-4 fade-in">
                    <div class="card product-card h-100">
                        <div class="card-body text-center">
                            <i class="fas fa-pills fa-3x text-primary mb-3"></i>
                            <h6 class="card-title">${producto.nombre_comercial}</h6>
                            <p class="text-muted small">${producto.nombre_generico || ''}</p>
                            <div class="product-price">Bs. ${producto.precio.toFixed(2)}</div>
                            ${producto.stock > 0 ? 
                                `<button class="btn btn-primary btn-sm mt-2 agregar-carrito"
                                    data-id="${producto.id_medicamento}"
                                    data-nombre="${producto.nombre_comercial}"
                                    data-precio="${producto.precio}">
                                    <i class="fas fa-cart-plus"></i> Agregar
                                </button>` :
                                `<button class="btn btn-secondary btn-sm mt-2" disabled>
                                    <i class="fas fa-times"></i> Sin Stock
                                </button>`
                            }
                        </div>
                    </div>
                </div>
            `);
        });
        
        // Rebind eventos
        $('.agregar-carrito').click(function(e) {
            e.preventDefault();
            // Lógica de agregar al carrito
        });
    }
    
    // ======================================================
    // VALIDACIÓN DE FORMULARIOS
    // ======================================================
    
    $('form.validar-form').on('submit', function(e) {
        let isValid = true;
        $(this).find('[required]').each(function() {
            if (!$(this).val()) {
                $(this).addClass('is-invalid');
                isValid = false;
            } else {
                $(this).removeClass('is-invalid');
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            mostrarNotificacion('Por favor complete todos los campos requeridos', 'warning');
        }
    });
    
    // ======================================================
    // SUBIDA DE RECETA MÉDICA
    // ======================================================
    
    $('#receta-input').on('change', function() {
        const file = this.files[0];
        const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
        const maxSize = 5 * 1024 * 1024; // 5MB
        
        if (file) {
            if (!allowedTypes.includes(file.type)) {
                mostrarNotificacion('Formato no permitido. Use JPG, PNG o PDF', 'danger');
                $(this).val('');
                return;
            }
            
            if (file.size > maxSize) {
                mostrarNotificacion('El archivo es demasiado grande. Máximo 5MB', 'danger');
                $(this).val('');
                return;
            }
            
            mostrarNotificacion('Archivo subido correctamente', 'success');
            $('#receta-nombre').text(file.name);
        }
    });
    
    // ======================================================
    // ACTUALIZACIÓN DE ESTADO DE PEDIDO (FARMACÉUTICO)
    // ======================================================
    
    $('.cambiar-estado-pedido').on('change', function() {
        const pedidoId = $(this).data('id');
        const nuevoEstado = $(this).val();
        
        if (confirm(`¿Cambiar estado del pedido #${pedidoId} a "${nuevoEstado}"?`)) {
            mostrarLoading();
            
            $.ajax({
                url: '/api/pedidos/cambiar-estado',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    pedido_id: pedidoId,
                    estado: nuevoEstado
                }),
                success: function(response) {
                    if (response.success) {
                        mostrarNotificacion('Estado actualizado correctamente', 'success');
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        mostrarNotificacion(response.error || 'Error al actualizar', 'danger');
                    }
                },
                error: function() {
                    mostrarNotificacion('Error al actualizar estado', 'danger');
                },
                complete: function() {
                    ocultarLoading();
                }
            });
        } else {
            // Revertir select
            $(this).val($(this).data('original'));
        }
    });
    
    // ======================================================
    // GENERACIÓN DE REPORTES
    // ======================================================
    
    $('#generar-reporte').click(function() {
        const fechaInicio = $('#fecha-inicio').val();
        const fechaFin = $('#fecha-fin').val();
        
        if (!fechaInicio || !fechaFin) {
            mostrarNotificacion('Seleccione un rango de fechas', 'warning');
            return;
        }
        
        mostrarLoading();
        
        $.ajax({
            url: '/api/reportes/ventas',
            method: 'GET',
            data: {
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin
            },
            success: function(response) {
                if (response.data) {
                    $('#reporte-contenido').html(generarTablaReporte(response.data));
                    $('#reporte-modal').modal('show');
                }
            },
            complete: function() {
                ocultarLoading();
            }
        });
    });
    
    // ======================================================
    // FUNCIONES AUXILIARES
    // ======================================================
    
    function mostrarNotificacion(mensaje, tipo = 'info') {
        const alertHtml = `
            <div class="alert alert-${tipo} alert-dismissible fade show position-fixed top-0 end-0 m-3" 
                 style="z-index: 9999; min-width: 300px;" role="alert">
                <i class="fas fa-${tipo === 'success' ? 'check-circle' : tipo === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                ${mensaje}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('body').append(alertHtml);
        
        setTimeout(() => {
            $('.alert').fadeOut('slow', function() {
                $(this).remove();
            });
        }, 3000);
    }
    
    function mostrarLoading() {
        if ($('.spinner-overlay').length === 0) {
            $('body').append(`
                <div class="spinner-overlay">
                    <div class="spinner-border text-light" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                </div>
            `);
        }
    }
    
    function ocultarLoading() {
        $('.spinner-overlay').fadeOut('fast', function() {
            $(this).remove();
        });
    }
    
    // ======================================================
    // ACTUALIZACIÓN EN TIEMPO REAL (WebSocket simulado)
    // ======================================================
    
    function actualizarEstadoSistema() {
        $.ajax({
            url: '/api/estructuras/estado',
            method: 'GET',
            success: function(data) {
                $('#estado-carrito').text(data.carrito_items || 0);
                $('#estado-cola').text(data.cola_pedidos || 0);
                $('#estado-historial').text(data.historial_acciones || 0);
            }
        });
    }
    
    // Actualizar cada 30 segundos si estamos en dashboard
    if (window.location.pathname.includes('/dashboard')) {
        setInterval(actualizarEstadoSistema, 30000);
    }
    
    // ======================================================
    // INICIALIZACIÓN DE TOOLTIPS
    // ======================================================
    
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // ======================================================
    // LOG DEL SISTEMA
    // ======================================================
    
    console.log('✅ Sistema inicializado correctamente');
    console.log('📊 Estructuras de datos: Lista Enlazada, Cola, Pila, Árbol BB, Tabla Hash');
});