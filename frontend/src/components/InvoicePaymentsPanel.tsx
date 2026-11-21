import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import { getInvoicePayments, registerPayment, voidPayment } from '../services/payment';
import type { InvoicePayments, PaymentMethod } from '../types/payment';
import { formatDate, formatDateTime, formatMoney, todayLocal } from '../utils/format';

type Props = { invoiceId: number; onChanged?: () => void };

const methods: Record<PaymentMethod, string> = {
  TRANSFER: 'Transferencia',
  CASH: 'Efectivo',
  CARD: 'Tarjeta (cobro externo)',
  OTHER: 'Otro medio',
};

export default function InvoicePaymentsPanel({ invoiceId, onChanged }: Props) {
  const [data, setData] = useState<InvoicePayments | null>(null);
  const [loadError, setLoadError] = useState('');
  const [actionError, setActionError] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [amount, setAmount] = useState('');
  const [paymentDate, setPaymentDate] = useState(todayLocal());
  const [method, setMethod] = useState<PaymentMethod>('TRANSFER');
  const [reference, setReference] = useState('');
  const [notes, setNotes] = useState('');
  const [voidingId, setVoidingId] = useState<number | null>(null);
  const [voidReason, setVoidReason] = useState('');

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setLoadError('');
      try {
        const result = await getInvoicePayments(invoiceId);
        if (active) setData(result);
      } catch (err) {
        if (active) setLoadError(err instanceof Error ? err.message : 'Error al consultar cobros');
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [invoiceId, reloadKey]);

  function notifyChanged() {
    setReloadKey((current) => current + 1);
    onChanged?.();
  }

  async function submitPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!data || saving || Number(data.balance.outstanding_amount) <= 0) return;
    setActionError('');
    const parsed = Number(amount);
    if (!Number.isFinite(parsed) || parsed <= 0 || parsed > Number(data.balance.outstanding_amount)) {
      setActionError('El importe debe ser mayor que cero y no superar el saldo pendiente.');
      return;
    }
    if (!window.confirm(`¿Registrar el cobro de ${formatMoney(parsed.toFixed(2))} como recibido? No se realiza ningún cargo real.`)) return;
    setSaving(true);
    try {
      await registerPayment({
        invoice_id: invoiceId,
        amount: parsed.toFixed(2),
        payment_date: paymentDate,
        method,
        reference: reference.trim() || null,
        notes: notes.trim() || null,
      });
      setAmount('');
      setReference('');
      setNotes('');
      notifyChanged();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'No se pudo registrar el cobro');
    } finally {
      setSaving(false);
    }
  }

  async function confirmVoid(paymentId: number) {
    if (saving) return;
    if (voidReason.trim().length < 3) {
      setActionError('Especifica un motivo de anulación de al menos 3 caracteres.');
      return;
    }
    if (!window.confirm('¿Anular este registro de cobro? Quedará guardado en el historial.')) return;
    setSaving(true);
    setActionError('');
    try {
      await voidPayment(paymentId, voidReason.trim());
      setVoidingId(null);
      setVoidReason('');
      notifyChanged();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'No se pudo anular el cobro');
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className='rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6'>
      <h2 className='text-xl font-bold text-white'>Cobros de la factura</h2>
      <p className='mt-1 text-sm text-slate-400'>Registro manual de importes ya recibidos. No realiza pagos bancarios ni modifica la factura.</p>
      {loading && <p role='status' className='mt-4 text-slate-400'>Cargando cobros...</p>}
      {loadError && <p role='alert' className='mt-4 rounded-lg border border-red-800 bg-red-950/40 p-3 text-sm text-red-300'>{loadError}</p>}
      {data && !loading && (
        <>
          <div className='mt-6 grid gap-3 sm:grid-cols-3'>
            <div className='rounded-xl border border-slate-800 bg-slate-950 p-4'>
              <p className='text-sm text-slate-400'>Total factura</p>
              <p className='mt-2 text-xl font-bold text-white'>{formatMoney(data.balance.total_amount)}</p>
            </div>
            <div className='rounded-xl border border-slate-800 bg-slate-950 p-4'>
              <p className='text-sm text-slate-400'>Cobrado</p>
              <p className='mt-2 text-xl font-bold text-emerald-300'>{formatMoney(data.balance.paid_amount)}</p>
            </div>
            <div className='rounded-xl border border-slate-800 bg-slate-950 p-4'>
              <p className='text-sm text-slate-400'>Pendiente</p>
              <p className='mt-2 text-xl font-bold text-amber-300'>{formatMoney(data.balance.outstanding_amount)}</p>
            </div>
          </div>
          {Number(data.balance.outstanding_amount) > 0 && (
            <form className='mt-6 space-y-4 rounded-xl border border-slate-700 p-4' onSubmit={(e) => void submitPayment(e)}>
              <h3 className='font-semibold text-white'>Registrar un cobro recibido</h3>
              <div className='grid gap-4 sm:grid-cols-3'>
                <label className='block text-sm text-slate-300'>Importe (€)
                  <input type='number' required min='0.01' step='0.01' max={data.balance.outstanding_amount} value={amount} onChange={(e) => setAmount(e.target.value)}
                    className='mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white' />
                </label>
                <label className='block text-sm text-slate-300'>Fecha de cobro
                  <input type='date' required value={paymentDate} onChange={(e) => setPaymentDate(e.target.value)}
                    className='mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white' />
                </label>
                <label className='block text-sm text-slate-300'>Medio de cobro
                  <select value={method} onChange={(e) => setMethod(e.target.value as PaymentMethod)}
                    className='mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white'>
                    {Object.entries(methods).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
                  </select>
                </label>
              </div>
              <div className='grid gap-4 sm:grid-cols-2'>
                <label className='block text-sm text-slate-300'>Referencia (opcional)
                  <input value={reference} maxLength={100} onChange={(e) => setReference(e.target.value)} placeholder='Transferencia, recibo...'
                    className='mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white' />
                </label>
                <label className='block text-sm text-slate-300'>Observaciones (opcional)
                  <input value={notes} maxLength={500} onChange={(e) => setNotes(e.target.value)}
                    className='mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white' />
                </label>
              </div>
              <button type='submit' disabled={saving} className='rounded-lg bg-emerald-500 px-4 py-2.5 font-semibold text-slate-950 disabled:opacity-50'>
                {saving ? 'Guardando...' : 'Registrar cobro'}
              </button>
            </form>
          )}
          <h3 className='mt-7 text-lg font-semibold text-white'>Historial de movimientos</h3>
          {data.payments.length === 0 ? (
            <p className='mt-3 text-sm text-slate-400'>Esta factura todavía no tiene cobros registrados.</p>
          ) : (
            <div className='mt-3 space-y-3'>
              {data.payments.map((payment) => (
                <div key={payment.id} className='rounded-xl border border-slate-700/80 bg-slate-950/60 p-4'>
                  <div className='flex flex-wrap items-start justify-between gap-3'>
                    <div>
                      <p className={`font-semibold ${payment.status === 'VOIDED' ? 'text-slate-500 line-through' : 'text-emerald-300'}`}>
                        {formatMoney(payment.amount)}
                      </p>
                      <p className='mt-1 text-sm text-slate-300'>{methods[payment.method]} · {formatDate(payment.payment_date)}</p>
                      {payment.reference && <p className='text-xs text-slate-400'>Referencia: {payment.reference}</p>}
                      {payment.notes && <p className='text-xs text-slate-400'>{payment.notes}</p>}
                      <p className='mt-1 text-xs text-slate-500'>Registrado: {formatDateTime(payment.created_at)}</p>
                    </div>
                    <div className='text-right'>
                      <span className={`rounded-full px-3 py-1 text-xs ${payment.status === 'VOIDED' ? 'bg-slate-700 text-slate-300' : 'bg-emerald-500/10 text-emerald-300'}`}>
                        {payment.status === 'VOIDED' ? 'Anulado' : 'Registrado'}
                      </span>
                      {payment.status === 'RECORDED' && (
                        <button type='button' disabled={saving} onClick={() => {setVoidingId(payment.id);setVoidReason('');setActionError('');}}
                          className='ml-3 text-xs text-red-300 hover:underline disabled:opacity-50'>Anular registro</button>
                      )}
                    </div>
                  </div>
                  {payment.status === 'VOIDED' && (
                    <p className='mt-3 border-t border-slate-800 pt-3 text-xs text-amber-300'>Anulado: {payment.void_reason} · {formatDateTime(payment.voided_at)}</p>
                  )}
                  {voidingId === payment.id && payment.status === 'RECORDED' && (
                    <div className='mt-4 flex flex-wrap items-end gap-2 border-t border-slate-800 pt-4'>
                      <label className='min-w-[220px] flex-1 text-sm text-slate-300'>Motivo de anulación
                        <input autoFocus value={voidReason} maxLength={500} onChange={(e) => setVoidReason(e.target.value)}
                          className='mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white' />
                      </label>
                      <button type='button' disabled={saving} onClick={() => void confirmVoid(payment.id)} className='rounded-lg bg-red-700 px-3 py-2 text-sm text-white disabled:opacity-50'>Confirmar anulación</button>
                      <button type='button' onClick={() => setVoidingId(null)} className='rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-300'>Cancelar</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
      {actionError && <p role='alert' className='mt-4 rounded-lg border border-red-800 bg-red-950/40 p-3 text-sm text-red-300'>{actionError}</p>}
    </section>
  );
}
