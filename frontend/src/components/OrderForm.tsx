import { useEffect, useState } from 'react';

import { getCustomers } from '../services/customer';
import { createOrder, updateOrder } from '../services/order';
import { getProducts } from '../services/product';
import type { Customer } from '../types/customer';
import type { Order } from '../types/order';
import type { Product } from '../types/product';

type OrderFormProps = {
  order?: Order | null;
  onSaved: (order: Order) => void;
  onCancel: () => void;
};

type EditableLine = {
  product_id: string;
  quantity: string;
};

function OrderForm({ order = null, onSaved, onCancel }: OrderFormProps) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  const [customerId, setCustomerId] = useState(
    order ? String(order.customer_id) : '',
  );

  const [notes, setNotes] = useState(order?.notes ?? '');

  const [lines, setLines] = useState<EditableLine[]>(
    order
      ? order.lines.map((line) => ({
          product_id: String(line.product_id),
          quantity: line.quantity,
        }))
      : [
          {
            product_id: '',
            quantity: '1.000',
          },
        ],
  );

  const [isLoadingOptions, setIsLoadingOptions] = useState(true);

  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadOptions() {
      try {
        const [customersData, productsData] = await Promise.all([
          getCustomers(),
          getProducts(),
        ]);

        setCustomers(
          customersData.filter(
            (customer) =>
              customer.is_active || customer.id === order?.customer_id,
          ),
        );

        const orderProductIds = new Set(
          order?.lines.map((line) => line.product_id) ?? [],
        );

        setProducts(
          productsData.filter(
            (product) => product.is_active || orderProductIds.has(product.id),
          ),
        );
      } catch {
        setError('No se pudieron cargar los clientes o productos');
      } finally {
        setIsLoadingOptions(false);
      }
    }

    loadOptions();
  }, [order]);

  function handleLineChange(
    index: number,
    field: keyof EditableLine,
    value: string,
  ) {
    setLines((current) =>
      current.map((line, lineIndex) =>
        lineIndex === index
          ? {
              ...line,
              [field]: value,
            }
          : line,
      ),
    );
  }

  function handleAddLine() {
    setLines((current) => [
      ...current,
      {
        product_id: '',
        quantity: '1.000',
      },
    ]);
  }

  function handleRemoveLine(index: number) {
    setLines((current) => {
      if (current.length === 1) {
        return current;
      }

      return current.filter((_, lineIndex) => lineIndex !== index);
    });
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError('');

    if (!customerId) {
      setError('Selecciona un cliente');
      return;
    }

    if (
      lines.some(
        (line) =>
          !line.product_id || !line.quantity || Number(line.quantity) <= 0,
      )
    ) {
      setError('Todas las líneas deben tener producto y una cantidad válida');
      return;
    }

    const payload = {
      customer_id: Number(customerId),
      notes: notes.trim() || null,
      lines: lines.map((line, index) => ({
        product_id: Number(line.product_id),
        quantity: line.quantity,
        position: index + 1,
      })),
    };

    setIsSaving(true);

    try {
      const savedOrder = order
        ? await updateOrder(order.id, payload)
        : await createOrder(payload);

      onSaved(savedOrder);
    } catch (error) {
      setError(
        error instanceof Error ? error.message : 'No se pudo guardar el pedido',
      );
    } finally {
      setIsSaving(false);
    }
  }

  const canEdit = !order || order.status === 'DRAFT';

  return (
    <section className='mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-6'>
      <div className='mb-6'>
        <h2 className='text-xl font-semibold'>
          {order ? `Editar pedido #${order.id}` : 'Nuevo pedido'}
        </h2>

        <p className='mt-1 text-sm text-slate-400'>
          Selecciona el cliente y los productos incluidos en el pedido.
        </p>
      </div>

      {error && (
        <p className='mb-6 rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-red-300'>
          {error}
        </p>
      )}

      {isLoadingOptions ? (
        <p className='text-slate-400'>Cargando clientes y productos...</p>
      ) : (
        <form onSubmit={handleSubmit} className='space-y-6'>
          <div>
            <label
              htmlFor='order-customer'
              className='mb-2 block text-sm font-medium text-slate-300'
            >
              Cliente
            </label>

            <select
              id='order-customer'
              value={customerId}
              onChange={(event) => setCustomerId(event.target.value)}
              disabled={!canEdit || isSaving}
              className='w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-60'
            >
              <option value=''>Selecciona un cliente</option>

              {customers.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.legal_name}
                  {customer.tax_id ? ` · ${customer.tax_id}` : ''}
                </option>
              ))}
            </select>

            {customers.length === 0 && (
              <p className='mt-2 text-sm text-amber-400'>
                No hay clientes activos disponibles.
              </p>
            )}
          </div>

          <div>
            <div className='mb-3 flex items-center justify-between'>
              <div>
                <h3 className='font-semibold'>Líneas del pedido</h3>

                <p className='mt-1 text-sm text-slate-400'>
                  El precio, IVA y los importes definitivos los calcula el
                  backend.
                </p>
              </div>

              {canEdit && (
                <button
                  type='button'
                  onClick={handleAddLine}
                  disabled={isSaving}
                  className='rounded-lg border border-emerald-500/50 px-3 py-2 text-sm font-medium text-emerald-400 transition hover:bg-emerald-500/10 disabled:opacity-60'
                >
                  Añadir línea
                </button>
              )}
            </div>

            <div className='space-y-3'>
              {lines.map((line, index) => {
                const selectedProduct = products.find(
                  (product) => product.id === Number(line.product_id),
                );

                return (
                  <div
                    key={index}
                    className='grid gap-3 rounded-xl border border-slate-800 bg-slate-950/50 p-4 md:grid-cols-[minmax(0,1fr)_180px_auto]'
                  >
                    <div>
                      <label
                        htmlFor={`order-product-${index}`}
                        className='mb-2 block text-sm text-slate-400'
                      >
                        Producto
                      </label>

                      <select
                        id={`order-product-${index}`}
                        value={line.product_id}
                        onChange={(event) =>
                          handleLineChange(
                            index,
                            'product_id',
                            event.target.value,
                          )
                        }
                        disabled={!canEdit || isSaving}
                        className='w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white outline-none transition focus:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-60'
                      >
                        <option value=''>Selecciona un producto</option>

                        {products.map((product) => (
                          <option key={product.id} value={product.id}>
                            {product.name}
                            {product.sku ? ` · ${product.sku}` : ''}
                          </option>
                        ))}
                      </select>

                      {selectedProduct && (
                        <p className='mt-2 text-xs text-slate-500'>
                          Precio actual: {selectedProduct.unit_price} € · IVA{' '}
                          {selectedProduct.tax_rate}%
                        </p>
                      )}
                    </div>

                    <div>
                      <label
                        htmlFor={`order-quantity-${index}`}
                        className='mb-2 block text-sm text-slate-400'
                      >
                        Cantidad
                      </label>

                      <input
                        id={`order-quantity-${index}`}
                        type='number'
                        min='0.001'
                        step='0.001'
                        value={line.quantity}
                        onChange={(event) =>
                          handleLineChange(
                            index,
                            'quantity',
                            event.target.value,
                          )
                        }
                        disabled={!canEdit || isSaving}
                        className='w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white outline-none transition focus:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-60'
                      />
                    </div>

                    <div className='flex items-end'>
                      {canEdit && lines.length > 1 && (
                        <button
                          type='button'
                          onClick={() => handleRemoveLine(index)}
                          disabled={isSaving}
                          className='rounded-lg px-3 py-2.5 font-medium text-red-400 transition hover:bg-red-500/10 hover:text-red-300 disabled:opacity-60'
                        >
                          Quitar
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {products.length === 0 && (
              <p className='mt-3 text-sm text-amber-400'>
                No hay productos activos disponibles.
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor='order-notes'
              className='mb-2 block text-sm font-medium text-slate-300'
            >
              Notas
            </label>

            <textarea
              id='order-notes'
              rows={4}
              maxLength={1000}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              disabled={!canEdit || isSaving}
              placeholder='Observaciones, instrucciones de entrega...'
              className='w-full resize-y rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-60'
            />
          </div>

          <div className='flex justify-end gap-3'>
            <button
              type='button'
              onClick={onCancel}
              disabled={isSaving}
              className='rounded-lg border border-slate-700 px-4 py-2 font-medium text-slate-300 transition hover:bg-slate-800 disabled:opacity-60'
            >
              Cancelar
            </button>

            {canEdit && (
              <button
                type='submit'
                disabled={
                  isSaving || customers.length === 0 || products.length === 0
                }
                className='rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50'
              >
                {isSaving
                  ? 'Guardando...'
                  : order
                    ? 'Guardar cambios'
                    : 'Crear pedido'}
              </button>
            )}
          </div>
        </form>
      )}
    </section>
  );
}

export default OrderForm;
