import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { getCustomers } from '../services/customer';
import { getDeliveryNote } from '../services/deliveryNote';
import { getOrder } from '../services/order';
import type { DeliveryNote, DeliveryNoteStatus } from '../types/deliveryNote';
import type { Order } from '../types/order';
import { formatDate, formatDateTime, formatMoney } from '../utils/format';

const statusLabels: Record<DeliveryNoteStatus, string> = {
  DRAFT: 'Borrador',
  CONFIRMED: 'Confirmado',
  CANCELLED: 'Cancelado',
};

function DeliveryNoteDetailPage() {
  const { deliveryNoteId } = useParams<{ deliveryNoteId: string }>();
  const id = Number(deliveryNoteId);
  const validId = Number.isSafeInteger(id) && id > 0;
  const [note, setNote] = useState<DeliveryNote | null>(null);
  const [order, setOrder] = useState<Order | null>(null);
  const [customerName, setCustomerName] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!validId) return;
    let active = true;

    async function load() {
      try {
        const noteData = await getDeliveryNote(id);
        const [orderData, customers] = await Promise.all([
          getOrder(noteData.order_id),
          getCustomers(),
        ]);
        if (!active) return;
        setNote(noteData);
        setOrder(orderData);
        setCustomerName(
          customers.find((customer) => customer.id === orderData.customer_id)
            ?.legal_name ?? `Cliente #${orderData.customer_id}`,
        );
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'No se pudo cargar el albarán');
      } finally {
        if (active) setIsLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [id, validId]);

  return (
    <main className='min-h-screen bg-slate-950 px-4 py-8 text-white sm:px-6 lg:px-8'>
      <div className='mx-auto max-w-5xl'>
        <Link className='text-sm text-emerald-400 hover:underline' to='/delivery-notes'>
          ← Volver a albaranes
        </Link>
        {!validId && <p role='alert' className='mt-8 text-red-300'>Identificador de albarán no válido.</p>}
        {validId && isLoading && <p role='status' className='mt-8 text-slate-400'>Cargando albarán...</p>}
        {error && <p role='alert' className='mt-8 rounded-xl border border-red-900 bg-red-950/40 p-5 text-red-300'>{error}</p>}

        {validId && !isLoading && !error && note && order && (
          <>
            <header className='my-8 flex flex-wrap items-start justify-between gap-4'>
              <div>
                <p className='text-sm font-semibold uppercase tracking-widest text-emerald-400'>Detalle de entrega</p>
                <h1 className='mt-2 text-3xl font-bold'>Albarán #{note.id}</h1>
                <p className='mt-2 text-slate-400'>Creado el {formatDateTime(note.created_at)}</p>
              </div>
              <span className='rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold'>
                {statusLabels[note.status]}
              </span>
            </header>

            <section className='mb-6 grid gap-4 sm:grid-cols-2'>
              <div className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
                <h2 className='mb-3 text-lg font-semibold'>Pedido de origen</h2>
                <Link className='font-medium text-emerald-400 hover:underline' to={`/orders/${note.order_id}`}>
                  Pedido #{note.order_id}
                </Link>
                <p className='mt-3 text-sm text-slate-300'>Cliente: {customerName}</p>
              </div>
              <div className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
                <h2 className='mb-3 text-lg font-semibold'>Información de entrega</h2>
                <p className='text-sm text-slate-300'>Fecha: {formatDate(note.delivery_date)}</p>
                <p className='mt-2 text-sm text-slate-300'>Estado: {statusLabels[note.status]}</p>
                <p className='mt-2 text-sm text-slate-300'>Confirmación: {formatDateTime(note.confirmed_at)}</p>
              </div>
            </section>

            <section className='mb-6 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900'>
              <h2 className='border-b border-slate-800 p-6 text-xl font-semibold'>Líneas entregadas</h2>
              <div className='overflow-x-auto'>
                <table className='w-full min-w-[700px] text-left'>
                  <thead className='bg-slate-950/50 text-sm text-slate-400'>
                    <tr>
                      <th scope='col' className='px-6 py-4'>Descripción</th>
                      <th scope='col' className='px-6 py-4 text-right'>Cantidad</th>
                      <th scope='col' className='px-6 py-4 text-right'>Precio unitario</th>
                      <th scope='col' className='px-6 py-4 text-right'>IVA</th>
                    </tr>
                  </thead>
                  <tbody className='divide-y divide-slate-800'>
                    {note.lines.map((line) => (
                      <tr key={line.id}>
                        <td className='px-6 py-4'>{line.description}</td>
                        <td className='px-6 py-4 text-right'>{line.quantity}</td>
                        <td className='px-6 py-4 text-right'>{formatMoney(line.unit_price)}</td>
                        <td className='px-6 py-4 text-right'>{line.tax_rate}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {note.notes && (
              <section className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
                <h2 className='font-semibold'>Observaciones</h2>
                <p className='mt-3 whitespace-pre-wrap text-sm text-slate-300'>{note.notes}</p>
              </section>
            )}
          </>
        )}
      </div>
    </main>
  );
}

export default DeliveryNoteDetailPage;
