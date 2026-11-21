import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';

import { getCustomers } from '../services/customer';
import { getDeliveryNotes } from '../services/deliveryNote';
import { createInvoice, getInvoices, updateInvoice } from '../services/invoice';
import { getOrders } from '../services/order';
import type { Customer } from '../types/customer';
import type { DeliveryNote } from '../types/deliveryNote';
import type { Invoice } from '../types/invoice';
import type { Order } from '../types/order';
import { formatDate } from '../utils/format';

type InvoiceFormProps = {
  invoice?: Invoice | null;
  onSaved: (invoice: Invoice) => void;
  onCancel: () => void;
};

function InvoiceForm({ invoice = null, onSaved, onCancel }: InvoiceFormProps) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [deliveryNotes, setDeliveryNotes] = useState<DeliveryNote[]>([]);
  const [usedIds, setUsedIds] = useState<Set<number>>(new Set());

  const [customerId, setCustomerId] = useState(invoice ? String(invoice.customer_id) : '');
  const [selectedIds, setSelectedIds] = useState<number[]>(
    invoice?.delivery_notes.map((link) => link.delivery_note_id) ?? [],
  );
  const [operationDate, setOperationDate] = useState(invoice?.operation_date ?? '');
  const [notes, setNotes] = useState(invoice?.notes ?? '');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    async function loadOptions() {
      try {
        const [customerData, orderData, noteData, invoiceData] = await Promise.all([
          getCustomers(), getOrders(), getDeliveryNotes(), getInvoices(),
        ]);
        if (!active) return;

        // Un albarán queda reservado incluso si forma parte de un borrador.
        const occupied = new Set<number>();
        for (const existing of invoiceData) {
          if (existing.id === invoice?.id) continue;
          for (const link of existing.delivery_notes) {
            occupied.add(link.delivery_note_id);
          }
        }

        setCustomers(customerData);
        setOrders(orderData);
        setDeliveryNotes(noteData);
        setUsedIds(occupied);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'No se pudieron cargar los datos del formulario');
      } finally {
        if (active) setIsLoading(false);
      }
    }

    void loadOptions();
    return () => {
      active = false;
    };
  }, [invoice]);

  const ordersById = useMemo(
    () => new Map(orders.map((order) => [order.id, order])),
    [orders],
  );

  const availableNotes = useMemo(
    () => deliveryNotes.filter(
      (note) => note.status === 'CONFIRMED' && !usedIds.has(note.id)
        && ordersById.has(note.order_id),
    ),
    [deliveryNotes, usedIds, ordersById],
  );

  const customerIds = useMemo(
    () => new Set(availableNotes.map((note) => ordersById.get(note.order_id)!.customer_id)),
    [availableNotes, ordersById],
  );

  const selectableCustomers = customers.filter((customer) => customerIds.has(customer.id));
  const matchingNotes = availableNotes.filter(
    (note) => ordersById.get(note.order_id)?.customer_id === Number(customerId),
  );

  function handleCustomerChange(value: string) {
    setCustomerId(value);
    setSelectedIds([]);
    setError('');
  }

  function toggleNote(noteId: number) {
    setSelectedIds((current) => current.includes(noteId)
      ? current.filter((id) => id !== noteId)
      : [...current, noteId],
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSaving) return;

    if (selectedIds.length === 0) {
      setError('Selecciona al menos un albarán confirmado.');
      return;
    }

    if (selectedIds.some((id) => !matchingNotes.some((note) => note.id === id))) {
      setError('La selección contiene albaranes no disponibles para el cliente elegido.');
      return;
    }

    setIsSaving(true);
    setError('');
    try {
      const payload = {
        delivery_note_ids: selectedIds,
        operation_date: operationDate || null,
        notes: notes.trim() || null,
      };
      const saved = invoice
        ? await updateInvoice(invoice.id, payload)
        : await createInvoice(payload);
      onSaved(saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar la factura');
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className='mb-8 rounded-2xl border border-emerald-500/20 bg-slate-900 p-6 text-white'>
      <div className='mb-5 flex flex-wrap items-center justify-between gap-3'>
        <div>
          <h2 className='text-xl font-semibold'>
            {invoice ? `Editar borrador #${invoice.id}` : 'Nueva factura (borrador)'}
          </h2>
          <p className='mt-1 text-sm text-slate-400'>
            Elige un cliente y sus albaranes confirmados disponibles.
          </p>
        </div>
        <button type='button' onClick={onCancel}
          className='rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-slate-500'>
          Cerrar
        </button>
      </div>

      {isLoading && <p role='status' className='text-slate-400'>Cargando clientes y albaranes...</p>}
      {error && <p role='alert' className='mb-5 rounded-lg border border-red-900 bg-red-950/40 p-4 text-sm text-red-300'>{error}</p>}

      {!isLoading && (
        <form onSubmit={handleSubmit} className='space-y-6'>
          <div>
            <label htmlFor='invoice-customer' className='mb-2 block text-sm font-medium text-slate-200'>Cliente</label>
            <select id='invoice-customer' value={customerId} required
              onChange={(event) => handleCustomerChange(event.target.value)}
              className='w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white'>
              <option value=''>Seleccionar cliente...</option>
              {selectableCustomers.map((customer) => (
                <option key={customer.id} value={customer.id}>{customer.legal_name}</option>
              ))}
            </select>
            {selectableCustomers.length === 0 && (
              <p className='mt-3 text-sm text-amber-300'>
                No hay albaranes confirmados disponibles para facturar.{' '}
                <Link className='underline' to='/delivery-notes'>Ir a Albaranes</Link>
              </p>
            )}
          </div>

          {customerId && (
            <fieldset className='rounded-xl border border-slate-800 p-4'>
              <legend className='px-2 text-sm font-semibold text-slate-200'>Albaranes disponibles</legend>
              {matchingNotes.length === 0 ? (
                <p className='text-sm text-slate-400'>No hay albaranes confirmados disponibles para este cliente.</p>
              ) : (
                <div className='space-y-3'>
                  {matchingNotes.map((note) => (
                    <label key={note.id} className='flex cursor-pointer items-start gap-3 rounded-lg border border-slate-800 bg-slate-950/50 p-3 hover:border-slate-600'>
                      <input type='checkbox' className='mt-1 accent-emerald-500'
                        checked={selectedIds.includes(note.id)} onChange={() => toggleNote(note.id)} />
                      <span className='flex-1'>
                        <span className='block font-medium'>Albarán #{note.id} · Pedido #{note.order_id}</span>
                        <span className='block text-xs text-slate-400'>
                          Entrega {formatDate(note.delivery_date)} · {note.lines.length} líneas
                        </span>
                        <span className='mt-1 block text-xs text-slate-500'>
                          {note.lines.map((line) => `${line.description} (${line.quantity})`).join(' · ')}
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </fieldset>
          )}

          <div className='grid gap-4 md:grid-cols-2'>
            <label className='block text-sm font-medium text-slate-200'>
              Fecha de operación (opcional)
              <input type='date' value={operationDate}
                onChange={(event) => setOperationDate(event.target.value)}
                className='mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white' />
            </label>
            <div className='flex items-end text-sm text-slate-400'>
              La serie y la numeración se asignarán al emitir, no al guardar el borrador.
            </div>
          </div>

          <label className='block text-sm font-medium text-slate-200'>
            Observaciones (opcional)
            <textarea value={notes} maxLength={1000} rows={3}
              onChange={(event) => setNotes(event.target.value)}
              className='mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white' />
          </label>

          <div className='flex flex-wrap justify-end gap-3'>
            <button type='button' disabled={isSaving} onClick={onCancel}
              className='rounded-lg border border-slate-700 px-4 py-2 font-medium text-slate-200 disabled:opacity-50'>
              Cancelar
            </button>
            <button type='submit' disabled={isSaving || !customerId || selectedIds.length === 0}
              className='rounded-lg bg-emerald-500 px-5 py-2 font-semibold text-slate-950 hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50'>
              {isSaving ? 'Guardando...' : 'Guardar borrador'}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}

export default InvoiceForm;
