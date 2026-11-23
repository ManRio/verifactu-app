import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';

import { createDeliveryNote, getDeliveryNotes, updateDeliveryNote } from '../services/deliveryNote';
import { getOrders } from '../services/order';
import type { DeliveryNote } from '../types/deliveryNote';
import type { Order } from '../types/order';
import { todayLocal } from '../utils/format';

type Props = { deliveryNote?: DeliveryNote | null; onSaved: (note: DeliveryNote) => void; onCancel: () => void };

/** Los albaranes confirmados consumen unidades; los borradores, no. */
export default function DeliveryNoteForm({ deliveryNote = null, onSaved, onCancel }: Props) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [existingNotes, setExistingNotes] = useState<DeliveryNote[]>([]);
  const [orderId, setOrderId] = useState(deliveryNote ? String(deliveryNote.order_id) : '');
  const [deliveryDate, setDeliveryDate] = useState(deliveryNote?.delivery_date ?? todayLocal());
  const [notes, setNotes] = useState(deliveryNote?.notes ?? '');
  const [selected, setSelected] = useState<Record<number, string>>(() =>
    Object.fromEntries((deliveryNote?.lines ?? []).map((line) => [line.order_line_id, String(Number(line.quantity))])),
  );
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const editable = !deliveryNote || deliveryNote.status === 'DRAFT';

  useEffect(() => {
    let active = true;
    void Promise.all([getOrders(), getDeliveryNotes()]).then(([orderData, noteData]) => {
      if (!active) return;
      setOrders(orderData.filter((order) => order.status === 'CONFIRMED' || order.id === deliveryNote?.order_id));
      setExistingNotes(noteData);
    }).catch((err: unknown) => {
      if (active) setError(err instanceof Error ? err.message : 'No se pudieron cargar pedidos y entregas.');
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [deliveryNote]);

  const order = useMemo(() => orders.find((item) => String(item.id) === orderId) ?? null, [orders, orderId]);
  const lines = useMemo(() => {
    if (!order) return [];
    return order.lines.map((line) => {
    const confirmed = existingNotes
      .filter((note) => note.order_id === order.id && note.status === 'CONFIRMED' && note.id !== deliveryNote?.id)
      .flatMap((note) => note.lines)
      .filter((entry) => entry.order_line_id === line.id)
      .reduce((sum, entry) => sum + Number(entry.quantity), 0);
    const remaining = Math.max(0, Number(line.quantity) - confirmed);
    return { line, confirmed, remaining };
    });
  }, [order, existingNotes, deliveryNote?.id]);

  function updateOrder(value: string) {
    setOrderId(value);
    setSelected({});
    setError('');
  }

  function toggle(id: number, available: number, checked: boolean) {
    setSelected((current) => {
      const next = { ...current };
      if (!checked) delete next[id];
      else next[id] = String(Math.min(available, 1));
      return next;
    });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving || !editable) return;
    setError('');
    if (!order || !deliveryDate) { setError('Selecciona un pedido confirmado y una fecha.'); return; }
    const selectedLines = lines.filter(({ line }) => Object.prototype.hasOwnProperty.call(selected, line.id));
    if (!selectedLines.length) { setError('Marca al menos una línea de pedido.'); return; }
    const invalid = selectedLines.some(({ line, remaining }) => {
      const value = Number(selected[line.id]);
      return !Number.isSafeInteger(value) || value < 1 || value > remaining;
    });
    if (invalid) { setError('Revisa las cantidades: deben ser enteros entre 1 y las unidades pendientes.'); return; }
    const payload = {
      delivery_date: deliveryDate,
      notes: notes.trim() || null,
      lines: selectedLines.map(({ line }, index) => ({
        order_line_id: line.id,
        quantity: String(Number(selected[line.id])),
        position: index + 1,
      })),
    };
    setSaving(true);
    try {
      const result = deliveryNote
        ? await updateDeliveryNote(deliveryNote.id, payload)
        : await createDeliveryNote({ order_id: order.id, ...payload });
      onSaved(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el albarán.');
    } finally { setSaving(false); }
  }

  return (
    <section className='mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 text-white'>
      <h2 className='text-xl font-bold'>{deliveryNote ? `Editar albarán #${deliveryNote.id}` : 'Nuevo albarán'}</h2>
      <p className='mt-2 text-sm text-slate-400'>Marca cada producto que vas a entregar y escribe las unidades. Solo se consideran consumidas las entregas confirmadas.</p>
      {error && <p role='alert' className='mt-5 rounded-xl border border-rose-600/40 bg-rose-950/40 p-4 text-sm text-rose-200'>{error}</p>}
      {loading ? <p className='mt-6 text-slate-400'>Cargando pedidos y entregas...</p> : (
        <form onSubmit={(event) => void submit(event)} className='mt-6 space-y-6'>
          <div className='grid gap-4 sm:grid-cols-2'>
            <label className='text-sm text-slate-300'>Pedido confirmado
              <select className='mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-white' value={orderId}
                disabled={!editable || saving || Boolean(deliveryNote)} onChange={(event) => updateOrder(event.target.value)} required>
                <option value=''>Selecciona un pedido</option>
                {orders.map((item) => <option key={item.id} value={item.id}>Pedido #{item.id} · {item.lines.length} líneas</option>)}
              </select>
            </label>
            <label className='text-sm text-slate-300'>Fecha de entrega
              <input type='date' className='mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-white'
                value={deliveryDate} onChange={(event) => setDeliveryDate(event.target.value)} disabled={!editable || saving} required />
            </label>
          </div>
          {order && <fieldset>
            <legend className='mb-3 font-semibold'>Líneas disponibles del pedido</legend>
            <div className='space-y-3'>
              {lines.map(({ line, confirmed, remaining }) => {
                const checked = Object.prototype.hasOwnProperty.call(selected, line.id);
                const disabled = !editable || saving || remaining < 1;
                return <div key={line.id} className={`grid gap-3 rounded-xl border border-slate-700 p-4 sm:grid-cols-[1fr_160px] ${remaining < 1 ? 'opacity-50' : 'bg-slate-950/40'}`}>
                  <label className='flex items-start gap-3'>
                    <input type='checkbox' className='mt-1 h-4 w-4 accent-emerald-400' checked={checked}
                      onChange={(event) => toggle(line.id, remaining, event.target.checked)} disabled={disabled} />
                    <span><span className='block font-medium'>{line.description}</span>
                      <span className='mt-1 block text-xs text-slate-400'>Pedido: {Number(line.quantity)} · Confirmado: {confirmed} · <strong className='text-emerald-300'>Pendiente: {remaining}</strong></span>
                    </span>
                  </label>
                  <label className='text-xs text-slate-300'>Unidades a entregar
                    <input type='number' min={1} max={remaining} step={1} required={checked} value={checked ? selected[line.id] : ''}
                      onChange={(event) => setSelected((current) => ({ ...current, [line.id]: event.target.value }))}
                      disabled={disabled || !checked} placeholder={remaining > 0 ? '1' : 'Sin unidades'}
                      className='mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white disabled:opacity-50' />
                  </label>
                </div>;
              })}
            </div>
            {lines.every(({ remaining }) => remaining < 1) && <p className='mt-3 text-sm text-amber-300'>Este pedido ya está completamente entregado.</p>}
          </fieldset>}
          <label className='block text-sm text-slate-300'>Notas de entrega
            <textarea value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={1000} rows={3}
              disabled={!editable || saving} placeholder='Observaciones...' className='mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-white'/>
          </label>
          <div className='flex justify-end gap-3'>
            <button type='button' onClick={onCancel} disabled={saving} className='rounded-lg border border-slate-700 px-4 py-2 text-slate-200'>Cancelar</button>
            {editable && <button type='submit' disabled={saving || !order || lines.every(({ remaining }) => remaining < 1)}
              className='rounded-lg bg-emerald-400 px-4 py-2 font-bold text-slate-950 disabled:opacity-50'>{saving ? 'Guardando...' : deliveryNote ? 'Guardar cambios' : 'Crear albarán'}</button>}
          </div>
        </form>
      )}
    </section>
  );
}
