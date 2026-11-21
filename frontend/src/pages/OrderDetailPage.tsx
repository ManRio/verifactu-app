import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { getCustomers } from '../services/customer';
import { getDeliveryNotes } from '../services/deliveryNote';
import { getOrder } from '../services/order';
import type { DeliveryNote } from '../types/deliveryNote';
import type { Order, OrderStatus } from '../types/order';
import { formatDateTime, formatMoney } from '../utils/format';

const statusLabels: Record<OrderStatus, string> = {
  DRAFT: 'Borrador',
  CONFIRMED: 'Confirmado',
  CANCELLED: 'Cancelado',
};

function OrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [customerName, setCustomerName] = useState('');
  const [deliveryNotes, setDeliveryNotes] = useState<DeliveryNote[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const id = Number(orderId);

    if (!Number.isSafeInteger(id) || id <= 0) {
      // Evita llamar a la API con identificadores inválidos.
      return () => {
        active = false;
      };
    }

    async function load() {
      try {
        const [orderData, customers, notes] = await Promise.all([
          getOrder(id),
          getCustomers(),
          getDeliveryNotes(),
        ]);
        if (!active) return;

        setOrder(orderData);
        setCustomerName(
          customers.find((customer) => customer.id === orderData.customer_id)
            ?.legal_name ?? `Cliente #${orderData.customer_id}`,
        );
        setDeliveryNotes(notes.filter((note) => note.order_id === id));
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'No se pudo cargar el pedido');
      } finally {
        if (active) setIsLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [orderId]);

  if (!Number.isSafeInteger(Number(orderId)) || Number(orderId) <= 0) {
    return (
      <main className='p-8 text-white'>
        <p role='alert'>Identificador de pedido no válido.</p>
        <Link className='text-emerald-400' to='/orders'>Volver a pedidos</Link>
      </main>
    );
  }

  return (
    <main className='min-h-screen bg-slate-950 px-4 py-8 text-white sm:px-6 lg:px-8'>
      <div className='mx-auto max-w-5xl'>
        <Link to='/orders' className='text-sm text-emerald-400 hover:underline'>
          ← Volver a pedidos
        </Link>

        {isLoading && <p role='status' className='mt-8 text-slate-400'>Cargando pedido...</p>}
        {error && (
          <p role='alert' className='mt-8 rounded-xl border border-red-900 bg-red-950/40 p-5 text-red-300'>
            {error}
          </p>
        )}

        {!isLoading && !error && order && (
          <>
            <header className='my-8 flex flex-wrap items-start justify-between gap-4'>
              <div>
                <p className='text-sm font-semibold uppercase tracking-widest text-emerald-400'>Detalle del pedido</p>
                <h1 className='mt-2 text-3xl font-bold'>Pedido #{order.id}</h1>
                <p className='mt-2 text-slate-400'>Creado el {formatDateTime(order.created_at)}</p>
              </div>
              <span className='rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold'>
                {statusLabels[order.status]}
              </span>
            </header>

            <section className='mb-6 grid gap-4 sm:grid-cols-2'>
              <div className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
                <h2 className='mb-3 text-lg font-semibold'>Cliente</h2>
                <p>{customerName}</p>
                <p className='mt-2 text-sm text-slate-400'>Referencia #{order.customer_id}</p>
              </div>
              <div className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
                <h2 className='mb-3 text-lg font-semibold'>Información</h2>
                <p className='text-sm text-slate-300'>Estado: {statusLabels[order.status]}</p>
                <p className='mt-2 text-sm text-slate-300'>Confirmación: {formatDateTime(order.confirmed_at)}</p>
              </div>
            </section>

            <section className='mb-6 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900'>
              <h2 className='border-b border-slate-800 p-6 text-xl font-semibold'>Líneas del pedido</h2>
              <div className='overflow-x-auto'>
                <table className='w-full min-w-[700px] text-left'>
                  <thead className='bg-slate-950/50 text-sm text-slate-400'>
                    <tr>
                      <th scope='col' className='px-6 py-4'>Producto</th>
                      <th scope='col' className='px-6 py-4 text-right'>Cantidad</th>
                      <th scope='col' className='px-6 py-4 text-right'>Precio</th>
                      <th scope='col' className='px-6 py-4 text-right'>IVA</th>
                      <th scope='col' className='px-6 py-4 text-right'>Total</th>
                    </tr>
                  </thead>
                  <tbody className='divide-y divide-slate-800'>
                    {order.lines.map((line) => (
                      <tr key={line.id}>
                        <td className='px-6 py-4'>{line.description}</td>
                        <td className='px-6 py-4 text-right'>{line.quantity}</td>
                        <td className='px-6 py-4 text-right'>{formatMoney(line.unit_price)}</td>
                        <td className='px-6 py-4 text-right'>{line.tax_rate}%</td>
                        <td className='px-6 py-4 text-right font-semibold'>{formatMoney(line.total_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className='mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-6'>
              <h2 className='mb-4 text-lg font-semibold'>Totales</h2>
              <div className='ml-auto max-w-sm space-y-3'>
                <div className='flex justify-between text-slate-300'>
                  <span>Base imponible</span><span>{formatMoney(order.subtotal)}</span>
                </div>
                <div className='flex justify-between text-slate-300'>
                  <span>Impuestos</span><span>{formatMoney(order.tax_total)}</span>
                </div>
                <div className='flex justify-between border-t border-slate-700 pt-3 text-xl font-bold'>
                  <span>Total</span><span className='text-emerald-400'>{formatMoney(order.total_amount)}</span>
                </div>
              </div>
              {order.notes && (
                <div className='mt-6 border-t border-slate-800 pt-5'>
                  <h3 className='font-semibold'>Observaciones</h3>
                  <p className='mt-2 whitespace-pre-wrap text-sm text-slate-300'>{order.notes}</p>
                </div>
              )}
            </section>

            <section className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
              <h2 className='mb-3 text-lg font-semibold'>Albaranes asociados</h2>
              {deliveryNotes.length === 0 ? (
                <p className='text-sm text-slate-400'>No hay entregas registradas para este pedido.</p>
              ) : (
                <ul className='space-y-2'>
                  {deliveryNotes.map((note) => (
                    <li key={note.id}>
                      <Link className='text-emerald-400 hover:underline' to={`/delivery-notes/${note.id}`}>
                        Albarán #{note.id}
                      </Link>
                      <span className='ml-3 text-sm text-slate-400'>{note.status}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}

export default OrderDetailPage;
