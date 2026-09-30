import { useEffect, useMemo, useState } from 'react';

import {
  createDeliveryNote,
  updateDeliveryNote,
} from '../services/deliveryNote';
import { getOrders } from '../services/order';
import type { DeliveryNote } from '../types/deliveryNote';
import type { Order } from '../types/order';

type DeliveryNoteFormProps = {
  deliveryNote?: DeliveryNote | null;
  onSaved: (deliveryNote: DeliveryNote) => void;
  onCancel: () => void;
};

type EditableLine = {
  order_line_id: string;
  quantity: string;
};

function getTodayValue() {
  const now = new Date();

  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
}

function DeliveryNoteForm({
  deliveryNote = null,
  onSaved,
  onCancel,
}: DeliveryNoteFormProps) {
  const [orders, setOrders] = useState<Order[]>([]);

  const [orderId, setOrderId] = useState(
    deliveryNote ? String(deliveryNote.order_id) : '',
  );

  const [deliveryDate, setDeliveryDate] = useState(
    deliveryNote?.delivery_date ?? getTodayValue(),
  );

  const [notes, setNotes] = useState(deliveryNote?.notes ?? '');

  const [lines, setLines] = useState<EditableLine[]>(
    deliveryNote
      ? deliveryNote.lines.map((line) => ({
          order_line_id: String(line.order_line_id),
          quantity: line.quantity,
        }))
      : [
          {
            order_line_id: '',
            quantity: '1.000',
          },
        ],
  );

  const [isLoadingOptions, setIsLoadingOptions] = useState(true);

  const [isSaving, setIsSaving] = useState(false);

  const [error, setError] = useState('');

  useEffect(() => {
    async function loadOrders() {
      try {
        const ordersData = await getOrders();

        setOrders(
          ordersData.filter(
            (order) =>
              order.status === 'CONFIRMED' ||
              order.id === deliveryNote?.order_id,
          ),
        );
      } catch {
        setError('No se pudieron cargar los pedidos');
      } finally {
        setIsLoadingOptions(false);
      }
    }

    loadOrders();
  }, [deliveryNote]);

  const selectedOrder = useMemo(
    () => orders.find((order) => order.id === Number(orderId)) ?? null,
    [orders, orderId],
  );

  const canEdit = !deliveryNote || deliveryNote.status === 'DRAFT';

  function handleOrderChange(value: string) {
    setOrderId(value);

    setLines([
      {
        order_line_id: '',
        quantity: '1.000',
      },
    ]);
  }

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
        order_line_id: '',
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

    if (!orderId) {
      setError('Selecciona un pedido');
      return;
    }

    if (!deliveryDate) {
      setError('Selecciona una fecha de entrega');
      return;
    }

    if (
      lines.some(
        (line) =>
          !line.order_line_id || !line.quantity || Number(line.quantity) <= 0,
      )
    ) {
      setError(
        'Todas las líneas deben tener una línea de pedido y una cantidad válida',
      );
      return;
    }

    const orderLineIds = lines.map((line) => Number(line.order_line_id));

    if (new Set(orderLineIds).size !== orderLineIds.length) {
      setError('No puedes añadir dos veces la misma línea del pedido');
      return;
    }

    const payload = {
      delivery_date: deliveryDate,
      notes: notes.trim() || null,
      lines: lines.map((line, index) => ({
        order_line_id: Number(line.order_line_id),
        quantity: line.quantity,
        position: index + 1,
      })),
    };

    setIsSaving(true);

    try {
      const savedDeliveryNote = deliveryNote
        ? await updateDeliveryNote(deliveryNote.id, payload)
        : await createDeliveryNote({
            order_id: Number(orderId),
            ...payload,
          });

      onSaved(savedDeliveryNote);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : 'No se pudo guardar el albarán',
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className='mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-6'>
      <div className='mb-6'>
        <h2 className='text-xl font-semibold'>
          {deliveryNote
            ? `Editar albarán #${deliveryNote.id}`
            : 'Nuevo albarán'}
        </h2>

        <p className='mt-1 text-sm text-slate-400'>
          Selecciona un pedido confirmado y las cantidades que se entregan.
        </p>
      </div>

      {error && (
        <p className='mb-6 rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-red-300'>
          {error}
        </p>
      )}

      {isLoadingOptions ? (
        <p className='text-slate-400'>Cargando pedidos...</p>
      ) : (
        <form onSubmit={handleSubmit} className='space-y-6'>
          <div className='grid gap-6 md:grid-cols-2'>
            <div>
              <label
                htmlFor='delivery-note-order'
                className='mb-2 block text-sm font-medium text-slate-300'
              >
                Pedido
              </label>

              <select
                id='delivery-note-order'
                value={orderId}
                onChange={(event) => handleOrderChange(event.target.value)}
                disabled={!canEdit || isSaving || Boolean(deliveryNote)}
                className='w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-60'
              >
                <option value=''>Selecciona un pedido confirmado</option>

                {orders.map((order) => (
                  <option key={order.id} value={order.id}>
                    Pedido #{order.id} · {order.lines.length}{' '}
                    {order.lines.length === 1 ? 'línea' : 'líneas'}
                  </option>
                ))}
              </select>

              {orders.length === 0 && (
                <p className='mt-2 text-sm text-amber-400'>
                  No hay pedidos confirmados disponibles.
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor='delivery-note-date'
                className='mb-2 block text-sm font-medium text-slate-300'
              >
                Fecha de entrega
              </label>

              <input
                id='delivery-note-date'
                type='date'
                value={deliveryDate}
                onChange={(event) => setDeliveryDate(event.target.value)}
                disabled={!canEdit || isSaving}
                className='w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-60'
              />
            </div>
          </div>

          <div>
            <div className='mb-3 flex items-center justify-between gap-4'>
              <div>
                <h3 className='font-semibold'>Líneas entregadas</h3>

                <p className='mt-1 text-sm text-slate-400'>
                  Indica qué líneas del pedido se entregan y en qué cantidad.
                </p>
              </div>

              {canEdit && selectedOrder && (
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

            {!selectedOrder ? (
              <p className='rounded-xl border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-500'>
                Selecciona primero un pedido para ver sus líneas.
              </p>
            ) : (
              <div className='space-y-3'>
                {lines.map((line, index) => {
                  const selectedOrderLine = selectedOrder.lines.find(
                    (orderLine) => orderLine.id === Number(line.order_line_id),
                  );

                  return (
                    <div
                      key={index}
                      className='grid gap-3 rounded-xl border border-slate-800 bg-slate-950/50 p-4 md:grid-cols-[minmax(0,1fr)_180px_auto]'
                    >
                      <div>
                        <label
                          htmlFor={`delivery-note-line-${index}`}
                          className='mb-2 block text-sm text-slate-400'
                        >
                          Línea del pedido
                        </label>

                        <select
                          id={`delivery-note-line-${index}`}
                          value={line.order_line_id}
                          onChange={(event) =>
                            handleLineChange(
                              index,
                              'order_line_id',
                              event.target.value,
                            )
                          }
                          disabled={!canEdit || isSaving}
                          className='w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white outline-none transition focus:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-60'
                        >
                          <option value=''>Selecciona una línea</option>

                          {selectedOrder.lines.map((orderLine) => (
                            <option key={orderLine.id} value={orderLine.id}>
                              {orderLine.description} · Pedido:{' '}
                              {orderLine.quantity}
                            </option>
                          ))}
                        </select>

                        {selectedOrderLine && (
                          <p className='mt-2 text-xs text-slate-500'>
                            Pedido: {selectedOrderLine.quantity} · Precio:{' '}
                            {selectedOrderLine.unit_price} € · IVA{' '}
                            {selectedOrderLine.tax_rate}%
                          </p>
                        )}
                      </div>

                      <div>
                        <label
                          htmlFor={`delivery-note-quantity-${index}`}
                          className='mb-2 block text-sm text-slate-400'
                        >
                          Cantidad entregada
                        </label>

                        <input
                          id={`delivery-note-quantity-${index}`}
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
            )}
          </div>

          <div>
            <label
              htmlFor='delivery-note-notes'
              className='mb-2 block text-sm font-medium text-slate-300'
            >
              Notas
            </label>

            <textarea
              id='delivery-note-notes'
              rows={4}
              maxLength={1000}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              disabled={!canEdit || isSaving}
              placeholder='Observaciones sobre la entrega...'
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
                disabled={isSaving || orders.length === 0 || !selectedOrder}
                className='rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50'
              >
                {isSaving
                  ? 'Guardando...'
                  : deliveryNote
                    ? 'Guardar cambios'
                    : 'Crear albarán'}
              </button>
            )}
          </div>
        </form>
      )}
    </section>
  );
}

export default DeliveryNoteForm;
