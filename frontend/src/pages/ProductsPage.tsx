import { useEffect, useState } from 'react';
import ProductForm from '../components/ProductForm';

import { getProducts } from '../services/product';
import type { Product } from '../types/product';

function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

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
    }

    setShowForm(false);
    setEditingProduct(null);
  }

  return (
    <main className='min-h-screen bg-slate-950 px-6 py-10 text-white'>
      <div className='mx-auto max-w-6xl'>
        <div className='mb-8 flex items-center justify-between'>
          <div>
            <p className='text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400'>
              VeriFactu App
            </p>

            <h1 className='mt-2 text-3xl font-bold'>Productos</h1>

            <p className='mt-2 text-slate-400'>
              Gestión de productos del negocio.
            </p>
          </div>

          <button
            type='button'
            onClick={handleNewProduct}
            className='rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-emerald-400'
          >
            Nuevo producto
          </button>
        </div>

        {(showForm || editingProduct) && (
          <ProductForm
            product={editingProduct}
            onSaved={handleProductSaved}
            onCancel={handleCancelForm}
          />
        )}

        {isLoading && <p className='text-slate-400'>Cargando productos...</p>}

        {error && (
          <p className='rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-red-300'>
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

        {products.length > 0 && (
          <div className='overflow-hidden rounded-2xl border border-slate-800 bg-slate-900'>
            <table className='w-full'>
              <thead className='border-b border-slate-800 bg-slate-900/80 text-left text-sm text-slate-400'>
                <tr>
                  <th className='px-6 py-4'>Producto</th>
                  <th className='px-6 py-4'>SKU</th>
                  <th className='px-6 py-4'>Precio</th>
                  <th className='px-6 py-4'>IVA</th>
                  <th className='px-6 py-4'>Estado</th>
                  <th className='px-6 py-4'>Editar</th>
                </tr>
              </thead>

              <tbody>
                {products.map((product) => (
                  <tr
                    key={product.id}
                    className='border-b border-slate-800 last:border-0'
                  >
                    <td className='px-6 py-4 font-medium'>{product.name}</td>

                    <td className='px-6 py-4 text-slate-400'>
                      {product.sku ?? '—'}
                    </td>

                    <td className='px-6 py-4'>{product.unit_price} €</td>

                    <td className='px-6 py-4'>{product.tax_rate} %</td>

                    <td className='px-6 py-4'>
                      {product.is_active ? (
                        <span className='text-emerald-400'>Activo</span>
                      ) : (
                        <span className='text-slate-500'>Inactivo</span>
                      )}
                    </td>

                    <td className='px-6 py-4'>
                      <button
                        type='button'
                        onClick={() => handleEditProduct(product)}
                        className='font-medium text-emerald-400 transition hover:text-emerald-300'
                      >
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}

export default ProductsPage;
