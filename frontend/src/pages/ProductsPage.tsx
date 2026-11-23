import { useEffect, useState } from 'react';

import ProductForm from '../components/ProductForm';

import {
  getProducts,
  activateProduct,
  deactivateProduct,
} from '../services/product';

import type { Product } from '../types/product';

const PAGE_SIZE = 10;

function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [hideInactive, setHideInactive] = useState(false);

  useEffect(() => {
    async function loadProducts() {
      try {
        const data = await getProducts();
        setProducts(data);
      } catch {
        setError('No se pudieron cargar los productos');
      } finally {
        setIsLoading(false);
      }
    }

    loadProducts();
  }, []);

  function handleNewProduct() {
    setEditingProduct(null);
    setShowForm(true);
  }

  function handleEditProduct(product: Product) {
    setEditingProduct(product);
    setShowForm(false);
  }

  function handleCancelForm() {
    setShowForm(false);
    setEditingProduct(null);
  }

  function handleProductSaved(savedProduct: Product) {
    if (editingProduct) {
      setProducts((current) =>
        current.map((product) =>
          product.id === savedProduct.id ? savedProduct : product,
        ),
      );
    } else {
      setProducts((current) => [...current, savedProduct]);
      setCurrentPage(Math.ceil((products.length + 1) / PAGE_SIZE));
    }

    setShowForm(false);
    setEditingProduct(null);
  }

  async function handleToggleStatus(product: Product) {
    setError('');

    try {
      const updatedProduct = product.is_active
        ? await deactivateProduct(product.id)
        : await activateProduct(product.id);

      setProducts((current) =>
        current.map((currentProduct) =>
          currentProduct.id === updatedProduct.id
            ? updatedProduct
            : currentProduct,
        ),
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : 'No se pudo cambiar el estado del producto',
      );
    }
  }

  const query = searchQuery.trim().toLowerCase();
  const filteredProducts = products.filter((product) => (!hideInactive || product.is_active)
    && (!query || `${product.name} ${product.sku ?? ''}`.toLowerCase().includes(query)));
  const totalPages = Math.max(1, Math.ceil(filteredProducts.length / PAGE_SIZE));

  const safePage = Math.min(currentPage, totalPages);

  const startIndex = (safePage - 1) * PAGE_SIZE;
  const endIndex = startIndex + PAGE_SIZE;

  const visibleProducts = filteredProducts.slice(startIndex, endIndex);

  function goToPage(page: number) {
    if (page < 1 || page > totalPages) return;

    setCurrentPage(page);
  }

  return (
    <main className='min-h-screen bg-slate-950 px-4 py-8 text-white sm:px-6 lg:px-8'>
      <div className='mx-auto max-w-7xl'>
        {/* Encabezado */}
        <div className='mb-8 flex flex-wrap items-center justify-between gap-4'>
          <div>
            <p className='text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400'>
              VeriFactu App
            </p>

            <h1 className='mt-2 text-3xl font-bold'>Productos</h1>

            <p className='mt-2 text-slate-400'>
              Gestión del catálogo de productos del negocio.
            </p>
          </div>

          <button
            type='button'
            onClick={handleNewProduct}
            className='rounded-lg bg-emerald-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-400'
          >
            + Nuevo producto
          </button>
        </div>

        {/* Formulario */}
        {(showForm || editingProduct) && (
          <div className='mb-6'>
            <ProductForm
              product={editingProduct}
              onSaved={handleProductSaved}
              onCancel={handleCancelForm}
            />
          </div>
        )}

        {isLoading && <p className='text-slate-400'>Cargando productos...</p>}

        {error && (
          <p className='mb-6 rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-red-300'>
            {error}
          </p>
        )}

        {!isLoading && !error && products.length === 0 && (
          <section className='rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center'>
            <h2 className='text-xl font-semibold'>Todavía no hay productos</h2>

            <p className='mt-2 text-slate-400'>
              Crea tu primer producto para empezar.
            </p>
          </section>
        )}

        <section aria-label='Buscar y filtrar productos' className='mb-5 flex flex-wrap items-center gap-4 rounded-xl border border-slate-800 bg-slate-900 p-4'>
          <label className='flex-1 text-sm text-slate-300'>Buscar producto
            <input type='search' value={searchQuery} onChange={(event) => {setSearchQuery(event.target.value);setCurrentPage(1);}}
              placeholder='Nombre o SKU' className='mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white'/>
          </label>
          <label className='flex items-center gap-2 text-sm text-slate-300'><input type='checkbox' checked={hideInactive} onChange={(event) => {setHideInactive(event.target.checked);setCurrentPage(1);}}/> Ocultar inactivos</label>
        </section>
        {/* Tabla */}
        {products.length > 0 && (
          <section className='overflow-hidden rounded-2xl border border-slate-800 bg-slate-900'>
            <div className='flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-6 py-4'>
              <div>
                <h2 className='font-semibold'>Catálogo de productos</h2>

                <p className='mt-1 text-sm text-slate-400'>
                  {products.length} productos registrados
                </p>
              </div>

              <span className='rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300'>
                {products.filter((p) => p.is_active).length} activos
              </span>
            </div>

            <div className='overflow-x-auto'>
              <table className='w-full min-w-[760px]'>
                <thead className='border-b border-slate-800 bg-slate-950/30 text-left text-sm text-slate-400'>
                  <tr>
                    <th className='px-6 py-4'>Producto</th>
                    <th className='px-6 py-4'>SKU</th>
                    <th className='px-6 py-4'>Precio</th>
                    <th className='px-6 py-4'>IVA</th>
                    <th className='px-6 py-4'>Estado</th>
                    <th className='px-6 py-4'>Acciones</th>
                  </tr>
                </thead>

                <tbody>
                  {visibleProducts.map((product) => (
                    <tr
                      key={product.id}
                      className='border-b border-slate-800 transition last:border-0 hover:bg-slate-800/40'
                    >
                      <td className='px-6 py-4 font-medium'>{product.name}</td>

                      <td className='px-6 py-4 text-sm text-slate-400'>
                        {product.sku ?? '—'}
                      </td>

                      <td className='px-6 py-4 font-medium'>
                        {new Intl.NumberFormat('es-ES', {
                          style: 'currency',
                          currency: 'EUR',
                        }).format(Number(product.unit_price))}
                      </td>

                      <td className='px-6 py-4 text-slate-300'>
                        {product.tax_rate} %
                      </td>

                      <td className='px-6 py-4'>
                        <span
                          className={
                            product.is_active
                              ? 'rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300'
                              : 'rounded-full bg-slate-700/40 px-3 py-1 text-xs font-medium text-slate-400'
                          }
                        >
                          {product.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>

                      <td className='px-6 py-4'>
                        <div className='flex items-center gap-4'>
                          <button
                            type='button'
                            onClick={() => handleEditProduct(product)}
                            className='font-medium text-emerald-400 hover:text-emerald-300'
                          >
                            Editar
                          </button>

                          <button
                            type='button'
                            onClick={() => handleToggleStatus(product)}
                            className={
                              product.is_active
                                ? 'font-medium text-red-400 hover:text-red-300'
                                : 'font-medium text-emerald-400 hover:text-emerald-300'
                            }
                          >
                            {product.is_active ? 'Desactivar' : 'Activar'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Paginación */}
            <div className='flex flex-wrap items-center justify-between gap-4 border-t border-slate-800 px-6 py-5'>
              <p className='text-sm text-slate-400'>
                Mostrando{' '}
                <span className='font-medium text-white'>
                  {startIndex + 1}–{Math.min(endIndex, products.length)}
                </span>{' '}
                de{' '}
                <span className='font-medium text-white'>
                  {products.length}
                </span>{' '}
                productos
              </p>

              <nav
                aria-label='Paginación de productos'
                className='flex flex-wrap items-center gap-2'
              >
                <button
                  type='button'
                  disabled={safePage === 1}
                  onClick={() => goToPage(safePage - 1)}
                  className='rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40'
                >
                  Anterior
                </button>

                {Array.from(
                  { length: totalPages },
                  (_, index) => index + 1,
                ).map((page) => (
                  <button
                    key={page}
                    type='button'
                    onClick={() => goToPage(page)}
                    aria-label={`Ir a la página ${page}`}
                    aria-current={safePage === page ? 'page' : undefined}
                    className={
                      safePage === page
                        ? 'min-w-10 rounded-lg bg-emerald-500 px-3 py-2 text-sm font-bold text-slate-950'
                        : 'min-w-10 rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 transition hover:bg-slate-800'
                    }
                  >
                    {page}
                  </button>
                ))}

                <button
                  type='button'
                  disabled={safePage === totalPages}
                  onClick={() => goToPage(safePage + 1)}
                  className='rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40'
                >
                  Siguiente
                </button>
              </nav>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

export default ProductsPage;
