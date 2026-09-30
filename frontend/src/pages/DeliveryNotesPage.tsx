import { useEffect, useMemo, useState } from 'react';

import DeliveryNoteForm from '../components/DeliveryNoteForm';
import {
  cancelDeliveryNote,
  confirmDeliveryNote,
  getDeliveryNotes,
} from '../services/deliveryNote';
import { getOrders } from '../services/order';
import type { DeliveryNote, DeliveryNoteStatus } from '../types/deliveryNote';
import type { Order } from '../types/order';

function DeliveryNotesPage() {
  const [deliveryNotes, setDeliveryNotes] = useState<DeliveryNote[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);

  const [editingDeliveryNote, setEditingDeliveryNote] =
    useState<DeliveryNote | null>(null);

  const [actionDeliveryNoteId, setActionDeliveryNoteId] = useState<
    number | null
  >(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [deliveryNotesData, ordersData] = await Promise.all([
          getDeliveryNotes(),
          getOrders(),
        ]);

        setDeliveryNotes(deliveryNotesData);

        setOrders(ordersData);
      } catch {
        setError('No se pudieron cargar los albaranes');
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

  const ordersById = useMemo(
    () => new Map(orders.map((order) => [order.id, order])),
    [orders],
  );

  function handleNewDeliveryNote() {
    setEditingDeliveryNote(null);
    setShowForm(true);
  }

  function handleEditDeliveryNote(deliveryNote: DeliveryNote) {
    setEditingDeliveryNote(deliveryNote);

    setShowForm(true);
  }

  function handleCancelForm() {
    setEditingDeliveryNote(null);
    setShowForm(false);
  }

  function handleDeliveryNoteSaved(savedDeliveryNote: DeliveryNote) {
    setDeliveryNotes((current) => {
      const exists = current.some(
        (deliveryNote) => deliveryNote.id === savedDeliveryNote.id,
      );

      if (exists) {
        return current.map((deliveryNote) =>
          deliveryNote.id === savedDeliveryNote.id
            ? savedDeliveryNote
            : deliveryNote,
        );
      }

      return [...current, savedDeliveryNote];
    });

    setEditingDeliveryNote(null);
    setShowForm(false);
  }

  async function handleConfirmDeliveryNote(deliveryNote: DeliveryNote) {
    setError('');
    setActionDeliveryNoteId(deliveryNote.id);

    try {
      const updatedDeliveryNote = await confirmDeliveryNote(deliveryNote.id);

      setDeliveryNotes((current) =>
        current.map((currentDeliveryNote) =>
          currentDeliveryNote.id === updatedDeliveryNote.id
            ? updatedDeliveryNote
            : currentDeliveryNote,
        ),
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : 'No se pudo confirmar el albarán',
      );
    } finally {
      setActionDeliveryNoteId(null);
    }
  }

  async function handleCancelDeliveryNote(deliveryNote: DeliveryNote) {
    setError('');
    setActionDeliveryNoteId(deliveryNote.id);

    try {
      const updatedDeliveryNote = await cancelDeliveryNote(deliveryNote.id);

      setDeliveryNotes((current) =>
        current.map((currentDeliveryNote) =>
          currentDeliveryNote.id === updatedDeliveryNote.id
            ? updatedDeliveryNote
            : currentDeliveryNote,
        ),
      );

      if (editingDeliveryNote?.id === updatedDeliveryNote.id) {
        setEditingDeliveryNote(null);

        setShowForm(false);
      }
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : 'No se pudo cancelar el albarán',
      );
    } finally {
      setActionDeliveryNoteId(null);
    }
  }

  function getOrderLabel(orderId: number) {
    const order = ordersById.get(orderId);

    if (!order) {
      return `Pedido #${orderId}`;
    }

    return `Pedido #${order.id}`;
  }

  function getOrderedLinesCount(orderId: number) {
    return ordersById.get(orderId)?.lines.length ?? null;
  }

  function formatDeliveryDate(value: string) {
    const [year, month, day] = value.split('-');

    if (!year || !month || !day) {
      return value;
    }

    return `${day}/${month}/${year}`;
  }

  function formatDateTime(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return new Intl.DateTimeFormat('es-ES', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(date);
  }

  function getStatusLabel(status: DeliveryNoteStatus) {
    switch (status) {
      case 'DRAFT':
        return 'Borrador';

      case 'CONFIRMED':
        return 'Confirmado';

      case 'CANCELLED':
        return 'Cancelado';
    }
  }

  function getStatusClassName(status: DeliveryNoteStatus) {
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

            <h1 className='mt-2 text-3xl font-bold'>Albaranes</h1>

            <p className='mt-2 text-slate-400'>
              Gestión de entregas asociadas a pedidos confirmados.
            </p>
          </div>

          <button
            type='button'
            onClick={handleNewDeliveryNote}
            className='rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-emerald-400'
          >
            Nuevo albarán
          </button>
        </div>

        {(showForm || editingDeliveryNote) && (
          <DeliveryNoteForm
            deliveryNote={editingDeliveryNote}
            onSaved={handleDeliveryNoteSaved}
            onCancel={handleCancelForm}
          />
        )}

        {error && (
          <p className='mb-6 rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-red-300'>
            {error}
          </p>
        )}

        {isLoading && <p className='text-slate-400'>Cargando albaranes...</p>}

        {!isLoading && !error && deliveryNotes.length === 0 && (
          <section className='rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center'>
            <h2 className='text-xl font-semibold'>Todavía no hay albaranes</h2>

            <p className='mt-2 text-slate-400'>
              Crea un albarán desde un pedido confirmado para registrar una
              entrega.
            </p>
          </section>
        )}

        {deliveryNotes.length > 0 && (
          <div className='overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900'>
            <table className='w-full min-w-[1050px]'>
              <thead className='border-b border-slate-800 bg-slate-900/80 text-left text-sm text-slate-400'>
                <tr>
                  <th className='px-6 py-4'>Albarán</th>

                  <th className='px-6 py-4'>Pedido</th>

                  <th className='px-6 py-4'>Entrega</th>

                  <th className='px-6 py-4'>Líneas</th>

                  <th className='px-6 py-4'>Estado</th>

                  <th className='px-6 py-4'>Creado</th>

                  <th className='px-6 py-4'>Acciones</th>
                </tr>
              </thead>

              <tbody>
                {deliveryNotes.map((deliveryNote) => {
                  const isActionPending =
                    actionDeliveryNoteId === deliveryNote.id;

                  const orderLinesCount = getOrderedLinesCount(
                    deliveryNote.order_id,
                  );

                  return (
                    <tr
                      key={deliveryNote.id}
                      className='border-b border-slate-800 last:border-0'
                    >
                      <td className='px-6 py-4'>
                        <p className='font-medium'>#{deliveryNote.id}</p>

                        {deliveryNote.notes && (
                          <p className='mt-1 max-w-[220px] truncate text-sm text-slate-500'>
                            {deliveryNote.notes}
                          </p>
                        )}
                      </td>

                      <td className='px-6 py-4'>
                        <p className='font-medium text-slate-200'>
                          {getOrderLabel(deliveryNote.order_id)}
                        </p>

                        {orderLinesCount !== null && (
                          <p className='mt-1 text-xs text-slate-500'>
                            {orderLinesCount}{' '}
                            {orderLinesCount === 1
                              ? 'línea pedida'
                              : 'líneas pedidas'}
                          </p>
                        )}
                      </td>

                      <td className='px-6 py-4 text-slate-300'>
                        {formatDeliveryDate(deliveryNote.delivery_date)}
                      </td>

                      <td className='px-6 py-4'>
                        <p className='font-medium'>
                          {deliveryNote.lines.length}
                        </p>

                        <p className='mt-1 text-xs text-slate-500'>
                          {deliveryNote.lines
                            .map(
                              (line) => `${line.description}: ${line.quantity}`,
                            )
                            .join(' · ')}
                        </p>
                      </td>

                      <td className='px-6 py-4'>
                        <span
                          className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${getStatusClassName(
                            deliveryNote.status,
                          )}`}
                        >
                          {getStatusLabel(deliveryNote.status)}
                        </span>
                      </td>

                      <td className='px-6 py-4 text-sm text-slate-400'>
                        {formatDateTime(deliveryNote.created_at)}

                        {deliveryNote.confirmed_at && (
                          <p className='mt-1 text-xs text-slate-500'>
                            Confirmado:{' '}
                            {formatDateTime(deliveryNote.confirmed_at)}
                          </p>
                        )}
                      </td>

                      <td className='px-6 py-4'>
                        <div className='flex flex-wrap items-center gap-3'>
                          {deliveryNote.status === 'DRAFT' && (
                            <>
                              <button
                                type='button'
                                onClick={() =>
                                  handleEditDeliveryNote(deliveryNote)
                                }
                                disabled={isActionPending}
                                className='font-medium text-emerald-400 transition hover:text-emerald-300 disabled:opacity-50'
                              >
                                Editar
                              </button>

                              <button
                                type='button'
                                onClick={() =>
                                  handleConfirmDeliveryNote(deliveryNote)
                                }
                                disabled={isActionPending}
                                className='font-medium text-sky-400 transition hover:text-sky-300 disabled:opacity-50'
                              >
                                {isActionPending
                                  ? 'Procesando...'
                                  : 'Confirmar'}
                              </button>
                            </>
                          )}

                          {(deliveryNote.status === 'DRAFT' ||
                            deliveryNote.status === 'CONFIRMED') && (
                            <button
                              type='button'
                              onClick={() =>
                                handleCancelDeliveryNote(deliveryNote)
                              }
                              disabled={isActionPending}
                              className='font-medium text-red-400 transition hover:text-red-300 disabled:opacity-50'
                            >
                              {isActionPending ? 'Procesando...' : 'Cancelar'}
                            </button>
                          )}

                          {deliveryNote.status === 'CANCELLED' && (
                            <span className='text-sm text-slate-600'>
                              Sin acciones
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}

export default DeliveryNotesPage;
