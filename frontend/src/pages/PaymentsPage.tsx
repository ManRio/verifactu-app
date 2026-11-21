import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import InvoicePaymentsPanel from '../components/InvoicePaymentsPanel';
import { getPaymentBalances } from '../services/payment';
import type { BalanceStatus, InvoiceBalance } from '../types/payment';
import { formatDate, formatMoney } from '../utils/format';

const labels: Record<BalanceStatus, string> = {
  UNPAID: 'Pendiente',
  PARTIAL: 'Parcial',
  PAID: 'Cobrado',
};

type Filter = 'ALL' | BalanceStatus;

export default function PaymentsPage() {
  const [balances, setBalances] = useState<InvoiceBalance[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null);
  const [filter, setFilter] = useState<Filter>('ALL');
  const [search, setSearch] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const results = await getPaymentBalances();
        if (active) { setBalances(results); setError(''); }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'No se pudieron cargar los cobros');
      } finally {
        if (active) setIsLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [reloadKey]);

  const visible = useMemo(() => balances.filter((item) => {
    const matchesFilter = filter === 'ALL' || item.payment_status === filter;
    const query = search.trim().toLowerCase();
    const matchesSearch = !query || `${item.full_number} ${item.customer_legal_name}`.toLowerCase().includes(query);
    return matchesFilter && matchesSearch;
  }), [balances, filter, search]);

  const totalOutstanding = balances.reduce((sum, item) => sum + Number(item.outstanding_amount), 0);
  const totalPaid = balances.reduce((sum, item) => sum + Number(item.paid_amount), 0);
  const pendingCount = balances.filter((item) => item.payment_status !== 'PAID').length;

  return (
    <main className='min-h-screen bg-slate-950 px-4 py-8 text-white sm:px-6 lg:px-8'>
      <div className='mx-auto max-w-7xl'>
        <header className='mb-8'>
          <p className='text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400'>VeriFactu App</p>
          <h1 className='mt-2 text-3xl font-bold'>Cobros de facturas</h1>
          <p className='mt-2 text-slate-400'>Control manual de importes recibidos y pendientes. Los planes mensuales del SaaS son independientes.</p>
        </header>
        <div className='mb-8 grid gap-4 sm:grid-cols-3'>
          {[
            { title: 'Facturas emitidas', value: String(balances.length) },
            { title: 'Total cobrado', value: formatMoney(totalPaid.toFixed(2)) },
            { title: `Pendiente (${pendingCount})`, value: formatMoney(totalOutstanding.toFixed(2)) },
          ].map((card) => (
            <div key={card.title} className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
              <p className='text-sm text-slate-400'>{card.title}</p>
              <p className='mt-3 text-2xl font-bold'>{card.value}</p>
            </div>
          ))}
        </div>
        <div className='mb-5 flex flex-wrap items-end justify-between gap-4'>
          <div>
            <h2 className='text-xl font-semibold'>Saldos por factura</h2>
            <p className='mt-1 text-sm text-slate-400'>Selecciona una factura para registrar o revisar sus cobros.</p>
          </div>
          <div className='flex flex-wrap gap-2'>
            <label className='text-sm text-slate-300'>Buscar
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder='Factura o cliente'
                className='mt-1 block rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white' />
            </label>
            <label className='text-sm text-slate-300'>Estado
              <select value={filter} onChange={(e) => setFilter(e.target.value as Filter)}
                className='mt-1 block rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white'>
                <option value='ALL'>Todos</option><option value='UNPAID'>Pendientes</option>
                <option value='PARTIAL'>Parciales</option><option value='PAID'>Cobrados</option>
              </select>
            </label>
            <button type='button' onClick={() => {setIsLoading(true);setReloadKey((n) => n + 1);}}
              className='self-end rounded-lg border border-slate-700 px-4 py-2 text-sm text-white'>Actualizar</button>
          </div>
        </div>
        {isLoading && <p role='status' className='text-slate-400'>Cargando facturas...</p>}
        {error && <p role='alert' className='rounded-lg border border-red-800 bg-red-950/40 p-4 text-red-300'>{error}</p>}
        {!isLoading && !error && balances.length === 0 && (
          <p className='rounded-xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-400'>Todavía no hay facturas emitidas. <Link to='/invoices' className='text-emerald-400 hover:underline'>Ir a Facturas</Link></p>
        )}
        {!isLoading && !error && balances.length > 0 && (
          <div className='overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900'>
            <table className='w-full min-w-[830px] text-left'>
              <thead className='border-b border-slate-800 text-sm text-slate-400'><tr>
                <th className='px-5 py-4'>Factura</th><th className='px-5 py-4'>Cliente</th>
                <th className='px-5 py-4'>Emisión</th><th className='px-5 py-4 text-right'>Total</th>
                <th className='px-5 py-4 text-right'>Cobrado</th><th className='px-5 py-4 text-right'>Pendiente</th>
                <th className='px-5 py-4'>Estado</th><th className='px-5 py-4'>Acción</th>
              </tr></thead>
              <tbody className='divide-y divide-slate-800'>
                {visible.map((item) => (
                  <tr key={item.invoice_id} className={selectedInvoiceId === item.invoice_id ? 'bg-emerald-500/5' : ''}>
                    <td className='px-5 py-4'><Link to={`/invoices/${item.invoice_id}`} className='font-semibold text-emerald-300 hover:underline'>{item.full_number}</Link></td>
                    <td className='px-5 py-4 text-sm text-slate-300'>{item.customer_legal_name}</td>
                    <td className='px-5 py-4 text-sm text-slate-400'>{formatDate(item.issue_date)}</td>
                    <td className='px-5 py-4 text-right'>{formatMoney(item.total_amount)}</td>
                    <td className='px-5 py-4 text-right text-emerald-300'>{formatMoney(item.paid_amount)}</td>
                    <td className='px-5 py-4 text-right text-amber-300'>{formatMoney(item.outstanding_amount)}</td>
                    <td className='px-5 py-4 text-sm'>{labels[item.payment_status]}</td>
                    <td className='px-5 py-4'><button type='button' onClick={() => setSelectedInvoiceId(item.invoice_id)} className='text-sm font-medium text-emerald-400 hover:underline'>Ver cobros</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {visible.length === 0 && <p className='p-6 text-center text-slate-400'>Sin resultados para estos filtros.</p>}
          </div>
        )}
        {selectedInvoiceId !== null && (
          <div className='mt-8' id='payments-detail'>
            <div className='mb-3 flex items-center justify-between'>
              <h2 className='text-lg font-semibold'>Gestión de cobros</h2>
              <button type='button' onClick={() => setSelectedInvoiceId(null)} className='text-sm text-slate-400 hover:text-white'>Cerrar detalle</button>
            </div>
            <InvoicePaymentsPanel key={selectedInvoiceId} invoiceId={selectedInvoiceId} onChanged={() => setReloadKey((n) => n + 1)} />
          </div>
        )}
        <p className='mt-8 text-xs text-slate-500'>Entorno de demostración. No existe integración bancaria, conciliación automática, ni cobro a través de tarjeta.</p>
      </div>
    </main>
  );
}
