import { useEffect, useMemo, useState } from 'react';

import OrderForm from '../components/OrderForm';
import { getCustomers } from '../services/customer';
import {
  cancelOrder,
  confirmOrder,
  getOrders,
} from '../services/order';
import type { Customer } from '../types/customer';
import type { Order, OrderStatus } from '../types/order';

function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [actionOrderId, setActionOrderId] = useState<number | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [
          ordersData,
          customersData,
        ] = await Promise.all([
          getOrders(),
          getCustomers(),
        ]);

        setOrders(ordersData);
        setCustomers(customersData);
      } catch {
        setError(
          'No se pudieron cargar los pedidos',
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

  const customersById = useMemo(
    () =>
      new Map(
        customers.map(
          (customer) => [
            customer.id,
            customer,
          ],
        ),
      ),
    [customers],
  );

  function handleNewOrder() {
    setEditingOrder(null);
    setShowForm(true);
  }

  function handleEditOrder(
    order: Order,
  ) {
    setEditingOrder(order);
    setShowForm(true);
  }

  function handleCancelForm() {
    setEditingOrder(null);
    setShowForm(false);
  }

  function handleOrderSaved(
    savedOrder: Order,
  ) {
    setOrders((current) => {
      const exists = current.some(
        (order) =>
          order.id === savedOrder.id,
      );

      if (exists) {
        return current.map(
          (order) =>
            order.id === savedOrder.id
              ? savedOrder
              : order,
        );
      }

      return [
        ...current,
        savedOrder,
      ];
    });

    setEditingOrder(null);
    setShowForm(false);
  }

  async function handleConfirmOrder(
    order: Order,
  ) {
    setError('');
    setActionOrderId(order.id);

    try {
      const updatedOrder =
        await confirmOrder(order.id);

      setOrders((current) =>
        current.map(
          (currentOrder) =>
            currentOrder.id ===
            updatedOrder.id
              ? updatedOrder
              : currentOrder,
        ),
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : 'No se pudo confirmar el pedido',
      );
    } finally {
      setActionOrderId(null);
    }
  }

  async function handleCancelOrder(
    order: Order,
  ) {
    setError('');
    setActionOrderId(order.id);

    try {
      const updatedOrder =
        await cancelOrder(order.id);

      setOrders((current) =>
        current.map(
          (currentOrder) =>
            currentOrder.id ===
            updatedOrder.id
              ? updatedOrder
              : currentOrder,
        ),
      );

      if (
        editingOrder?.id ===
        updatedOrder.id
      ) {
        setEditingOrder(null);
        setShowForm(false);
      }
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : 'No se pudo cancelar el pedido',
      );
    } finally {
      setActionOrderId(null);
    }
  }

  function getCustomerName(
    customerId: number,
  ) {
    const customer =
      customersById.get(customerId);

    if (!customer) {
      return `Cliente #${customerId}`;
    }

    return customer.trade_name
      ? `${customer.legal_name} · ${customer.trade_name}`
      : customer.legal_name;
  }

  function formatMoney(
    value: string,
  ) {
    const amount = Number(value);

    if (
      Number.isNaN(amount)
    ) {
      return `${value} €`;
    }

    return new Intl.NumberFormat(
      'es-ES',
      {
        style: 'currency',
        currency: 'EUR',
      },
    ).format(amount);
  }

  function formatDate(
    value: string,
  ) {
    const date = new Date(value);

    if (
      Number.isNaN(date.getTime())
    ) {
      return value;
    }

    return new Intl.DateTimeFormat(
      'es-ES',
      {
        dateStyle: 'short',
        timeStyle: 'short',
      },
    ).format(date);
  }

  function getStatusLabel(
    status: OrderStatus,
  ) {
    switch (status) {
      case 'DRAFT':
        return 'Borrador';

      case 'CONFIRMED':
        return 'Confirmado';

      case 'CANCELLED':
        return 'Cancelado';
    }
  }

  function getStatusClassName(
    status: OrderStatus,
  ) {
    switch (status) {
      case 'DRAFT':
        return 'border-amber-500/30 bg-amber-500/10 text-amber-300';

      case 'CONFIRMED':
        return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';

      case 'CANCELLED':
        return 'border-slate-600 bg-slate-800 text-slate-400';
    }
  }

  return (
    <main className='min-h-screen bg-slate-950 px-6 py-10 text-white'>
      <div className='mx-auto max-w-7xl'>
        <div className='mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between'>
          <div>
            <p className='text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400'>
              VeriFactu App
            </p>

            <h1 className='mt-2 text-3xl font-bold'>
              Pedidos
            </h1>

            <p className='mt-2 text-slate-400'>
              Gestión del ciclo comercial previo
              a entrega y facturación.
            </p>
          </div>

          <button
            type='button'
            onClick={handleNewOrder}
            className='rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-emerald-400'
          >
            Nuevo pedido
          </button>
        </div>

        {(showForm ||
          editingOrder) && (
          <OrderForm
            order={editingOrder}
            onSaved={handleOrderSaved}
            onCancel={handleCancelForm}
          />
        )}

        {error && (
          <p className='mb-6 rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-red-300'>
            {error}
          </p>
        )}

        {isLoading && (
          <p className='text-slate-400'>
            Cargando pedidos...
          </p>
        )}

        {!isLoading &&
          !error &&
          orders.length === 0 && (
            <section className='rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center'>
              <h2 className='text-xl font-semibold'>
                Todavía no hay pedidos
              </h2>

              <p className='mt-2 text-slate-400'>
                Crea tu primer pedido para
                comenzar el flujo comercial.
              </p>
            </section>
          )}

        {orders.length > 0 && (
          <div className='overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900'>
            <table className='w-full min-w-[1100px]'>
              <thead className='border-b border-slate-800 bg-slate-900/80 text-left text-sm text-slate-400'>
                <tr>
                  <th className='px-6 py-4'>
                    Pedido
                  </th>

                  <th className='px-6 py-4'>
                    Cliente
                  </th>

                  <th className='px-6 py-4'>
                    Líneas
                  </th>

                  <th className='px-6 py-4'>
                    Total
                  </th>

                  <th className='px-6 py-4'>
                    Estado
                  </th>

                  <th className='px-6 py-4'>
                    Fecha
                  </th>

                  <th className='px-6 py-4'>
                    Acciones
                  </th>
                </tr>
              </thead>

              <tbody>
                {orders.map(
                  (order) => {
                    const isActionPending =
                      actionOrderId ===
                      order.id;

                    return (
                      <tr
                        key={order.id}
                        className='border-b border-slate-800 last:border-0'
                      >
                        <td className='px-6 py-4'>
                          <p className='font-medium'>
                            #{order.id}
                          </p>

                          {order.notes && (
                            <p className='mt-1 max-w-[220px] truncate text-sm text-slate-500'>
                              {
                                order.notes
                              }
                            </p>
                          )}
                        </td>

                        <td className='px-6 py-4'>
                          <p className='font-medium text-slate-200'>
                            {getCustomerName(
                              order.customer_id,
                            )}
                          </p>
                        </td>

                        <td className='px-6 py-4 text-slate-300'>
                          {
                            order.lines
                              .length
                          }
                        </td>

                        <td className='px-6 py-4'>
                          <p className='font-semibold'>
                            {formatMoney(
                              order.total_amount,
                            )}
                          </p>

                          <p className='mt-1 text-xs text-slate-500'>
                            Base:{' '}
                            {formatMoney(
                              order.subtotal,
                            )}
                          </p>

                          <p className='mt-1 text-xs text-slate-500'>
                            Impuestos:{' '}
                            {formatMoney(
                              order.tax_total,
                            )}
                          </p>
                        </td>

                        <td className='px-6 py-4'>
                          <span
                            className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${getStatusClassName(
                              order.status,
                            )}`}
                          >
                            {getStatusLabel(
                              order.status,
                            )}
                          </span>
                        </td>

                        <td className='px-6 py-4 text-sm text-slate-400'>
                          {formatDate(
                            order.created_at,
                          )}

                          {order.confirmed_at && (
                            <p className='mt-1 text-xs text-slate-500'>
                              Confirmado:{' '}
                              {formatDate(
                                order.confirmed_at,
                              )}
                            </p>
                          )}
                        </td>

                        <td className='px-6 py-4'>
                          <div className='flex flex-wrap items-center gap-3'>
                            {order.status ===
                              'DRAFT' && (
                              <>
                                <button
                                  type='button'
                                  onClick={() =>
                                    handleEditOrder(
                                      order,
                                    )
                                  }
                                  disabled={
                                    isActionPending
                                  }
                                  className='font-medium text-emerald-400 transition hover:text-emerald-300 disabled:opacity-50'
                                >
                                  Editar
                                </button>

                                <button
                                  type='button'
                                  onClick={() =>
                                    handleConfirmOrder(
                                      order,
                                    )
                                  }
                                  disabled={
                                    isActionPending
                                  }
                                  className='font-medium text-sky-400 transition hover:text-sky-300 disabled:opacity-50'
                                >
                                  {isActionPending
                                    ? 'Procesando...'
                                    : 'Confirmar'}
                                </button>
                              </>
                            )}

                            {(order.status ===
                              'DRAFT' ||
                              order.status ===
                                'CONFIRMED') && (
                              <button
                                type='button'
                                onClick={() =>
                                  handleCancelOrder(
                                    order,
                                  )
                                }
                                disabled={
                                  isActionPending
                                }
                                className='font-medium text-red-400 transition hover:text-red-300 disabled:opacity-50'
                              >
                                {isActionPending
                                  ? 'Procesando...'
                                  : 'Cancelar'}
                              </button>
                            )}

                            {order.status ===
                              'CANCELLED' && (
                              <span className='text-sm text-slate-600'>
                                Sin acciones
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  },
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}

export default OrdersPage;