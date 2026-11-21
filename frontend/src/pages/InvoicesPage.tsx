import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import InvoiceForm from '../components/InvoiceForm';
import { getInvoices } from '../services/invoice';
import type { Invoice, InvoiceStatus } from '../types/invoice';
import { formatDate, formatMoney } from '../utils/format';

type StatusFilter = 'ALL' | InvoiceStatus;
type LoadStatus = 'loading' | 'ready' | 'error';

function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>('loading');
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL');
  const [reloadKey, setReloadKey] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const [editingInvoice, setEditingInvoice] = useState<Invoice | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const data = await getInvoices();
        if (!active) return;
        setInvoices(data);
        setError('');
        setLoadStatus('ready');
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'No se pudieron cargar las facturas');
        setLoadStatus('error');
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [reloadKey]);

  function refresh() {
    setLoadStatus('loading');
    setReloadKey((current) => current + 1);
  }

  function handleNew() {
    setEditingInvoice(null);
    setShowForm(true);
  }

  function handleEdit(invoice: Invoice) {
    if (invoice.status !== 'DRAFT') return;
    setEditingInvoice(invoice);
    setShowForm(true);
  }

  function handleSaved(saved: Invoice) {
    setInvoices((current) => current.some((invoice) => invoice.id === saved.id)
      ? current.map((invoice) => invoice.id === saved.id ? saved : invoice)
      : [...current, saved],
    );
    setStatusFilter('ALL');
    setShowForm(false);
    setEditingInvoice(null);
    setError('');
  }

  const draftCount = invoices.filter((invoice) => invoice.status === 'DRAFT').length;
  const issuedCount = invoices.filter((invoice) => invoice.status === 'ISSUED').length;
  const visibleInvoices = invoices
    .filter((invoice) => statusFilter === 'ALL' || invoice.status === statusFilter)
    .sort((a, b) => b.created_at.localeCompare(a.created_at));

  return (
    <main className='min-h-screen bg-slate-950 px-4 py-8 text-white sm:px-6 lg:px-8'>
      <div className='mx-auto max-w-7xl'>
        <header className='mb-8 flex flex-wrap items-start justify-between gap-4'>
          <div>
            <p className='text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400'>VeriFactu App</p>
            <h1 className='mt-2 text-3xl font-bold'>Facturas</h1>
            <p className='mt-2 text-slate-400'>Gestión de borradores y consulta de facturas emitidas.</p>
          </div>
          <button type='button' onClick={handleNew}
            className='rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 hover:bg-emerald-400'>
            + Nueva factura
          </button>
        </header>

        {showForm && (
          <InvoiceForm key={editingInvoice?.id ?? 'new'} invoice={editingInvoice}
            onSaved={handleSaved}
            onCancel={() => { setShowForm(false); setEditingInvoice(null); }} />
        )}

        <section className='mb-8 grid gap-4 sm:grid-cols-3' aria-label='Resumen de facturación'>
          {[
            { label: 'Total de facturas', value: invoices.length },
            { label: 'Borradores', value: draftCount },
            { label: 'Emitidas', value: issuedCount },
          ].map((item) => (
            <div key={item.label} className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
              <p className='text-sm text-slate-400'>{item.label}</p>
              <p className='mt-3 text-3xl font-bold'>{item.value}</p>
            </div>
          ))}
        </section>

        <div className='mb-6 flex flex-wrap items-center justify-between gap-4'>
          <div>
            <h2 className='text-xl font-semibold'>Listado de facturas</h2>
            <p className='mt-1 text-sm text-slate-400'>{visibleInvoices.length} facturas en el listado</p>
          </div>
          <div className='flex flex-wrap items-center gap-3'>
            <button type='button' onClick={refresh}
              className='rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-slate-500'>
              Actualizar
            </button>
            <label htmlFor='invoice-status-filter' className='text-sm text-slate-400'>Estado</label>
            <select id='invoice-status-filter' value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
              className='rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-white'>
              <option value='ALL'>Todas</option>
              <option value='DRAFT'>Borradores</option>
              <option value='ISSUED'>Emitidas</option>
            </select>
          </div>
        </div>

        {loadStatus === 'loading' && <p role='status' className='py-8 text-slate-400'>Cargando facturas...</p>}
        {loadStatus === 'error' && (
          <div role='alert' className='rounded-xl border border-red-900 bg-red-950/40 p-6'>
            <p className='text-red-300'>{error}</p>
            <button type='button' onClick={refresh}
              className='mt-4 rounded-lg border border-red-500/40 px-4 py-2 text-red-200'>
              Reintentar
            </button>
          </div>
        )}
        {loadStatus === 'ready' && visibleInvoices.length === 0 && (
          <div className='rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center'>
            <h3 className='text-lg font-semibold'>
              {invoices.length === 0 ? 'Todavía no hay facturas' : 'No hay facturas con este estado'}
            </h3>
            <p className='mt-2 text-sm text-slate-400'>
              {invoices.length === 0
                ? 'Usa «Nueva factura» para seleccionar albaranes confirmados.'
                : 'Prueba con otro filtro.'}
            </p>
          </div>
        )}
        {loadStatus === 'ready' && visibleInvoices.length > 0 && (
          <section className='overflow-hidden rounded-2xl border border-slate-800 bg-slate-900'>
            <div className='overflow-x-auto'>
              <table className='w-full min-w-[900px] text-left'>
                <thead className='border-b border-slate-800 bg-slate-950/30 text-sm text-slate-400'>
                  <tr>
                    <th scope='col' className='px-6 py-4'>Factura</th>
                    <th scope='col' className='px-6 py-4'>Cliente</th>
                    <th scope='col' className='px-6 py-4'>Fecha</th>
                    <th scope='col' className='px-6 py-4'>Estado</th>
                    <th scope='col' className='px-6 py-4 text-right'>Importe</th>
                    <th scope='col' className='px-6 py-4'>Acciones</th>
                  </tr>
                </thead>
                <tbody className='divide-y divide-slate-800'>
                  {visibleInvoices.map((invoice) => (
                    <tr key={invoice.id} className='hover:bg-slate-800/40'>
                      <td className='px-6 py-5 font-semibold'>
                        <Link to={`/invoices/${invoice.id}`} className='text-emerald-400 hover:underline'>
                          {invoice.full_number ?? `Borrador #${invoice.id}`}
                        </Link>
                      </td>
                      <td className='px-6 py-5 text-sm text-slate-300'>{invoice.customer_legal_name}</td>
                      <td className='px-6 py-5 text-sm text-slate-400'>{formatDate(invoice.issue_date ?? invoice.created_at)}</td>
                      <td className='px-6 py-5'>
                        <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${
                          invoice.status === 'ISSUED'
                            ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                            : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
                        }`}>
                          {invoice.status === 'ISSUED' ? 'Emitida' : 'Borrador'}
                        </span>
                      </td>
                      <td className='px-6 py-5 text-right font-semibold tabular-nums'>{formatMoney(invoice.total_amount)}</td>
                      <td className='px-6 py-5'>
                        <div className='flex flex-wrap gap-3 text-sm font-medium'>
                          <Link to={`/invoices/${invoice.id}`} className='text-sky-400 hover:underline'>Ver detalle</Link>
                          {invoice.status === 'DRAFT' && (
                            <button type='button' className='text-emerald-400 hover:underline' onClick={() => handleEdit(invoice)}>
                              Editar
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

export default InvoicesPage;
