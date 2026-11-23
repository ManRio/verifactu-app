import { useEffect, useMemo, useState } from 'react';

import { getAccountingSummary } from '../services/reports';
import type { AccountingSummary } from '../services/reports';
import { formatMoney } from '../utils/format';

const presentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
};
const integer = (value: string) => new Intl.NumberFormat('es-ES', { maximumFractionDigits: 0 }).format(Number(value));

export default function AccountingSummaryPage() {
  const [month, setMonth] = useState(presentMonth);
  const [summary, setSummary] = useState<AccountingSummary | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    void getAccountingSummary(month)
      .then(data => { if (active) { setSummary(data); setError(''); setLoading(false); } })
      .catch(err => { if (active) { setError(err instanceof Error ? err.message : 'No se pudo cargar el resumen'); setLoading(false); } });
    return () => { active = false; };
  }, [month]);

  const maxTrend = useMemo(() => Math.max(1, ...((summary?.trend ?? []).flatMap(item => [Number(item.invoiced), Number(item.received)]))), [summary]);
  const monthLabel = (value: string) => new Intl.DateTimeFormat('es-ES', { month: 'short' }).format(new Date(`${value}-01T12:00:00`));
  function changeMonth(value: string) { if (value) { setLoading(true); setMonth(value); } }

  return <main className='min-h-screen bg-slate-950 px-4 py-8 text-white sm:px-6'>
    <div className='mx-auto max-w-7xl space-y-8'>
      <header className='flex flex-wrap items-end justify-between gap-5'>
        <div>
          <p className='text-xs font-bold uppercase tracking-[0.2em] text-emerald-400'>Superusuario · Demostración</p>
          <h1 className='mt-2 text-3xl font-extrabold'>Panorama económico</h1>
          <p className='mt-2 max-w-2xl text-slate-400'>Facturación, cobros, saldos pendientes y artículos destacados. Cifras informativas, no contabilidad oficial.</p>
        </div>
        <label className='text-sm font-medium text-slate-300'>Mes del análisis
          <input type='month' value={month} max={presentMonth()} onChange={event => changeMonth(event.target.value)}
            className='mt-2 block rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white focus:border-emerald-500 focus:outline-none'/>
        </label>
      </header>
      {error && <div role='alert' className='rounded-xl border border-rose-800 bg-rose-950/30 p-5 text-rose-200'>{error}</div>}
      {loading && <p role='status' className='text-slate-400'>Actualizando cifras...</p>}
      {summary && !loading && !error && <>
        <section className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4' aria-label='Indicadores del mes'>
          {[
            { title: 'Ventas facturadas', value: formatMoney(summary.total_invoiced), detail: `${summary.issued_invoice_count} facturas emitidas en el mes` },
            { title: 'Cobrado en el mes', value: formatMoney(summary.cash_received_month), detail: 'Cobros vigentes por fecha de pago' },
            { title: 'Pendiente del mes', value: formatMoney(summary.outstanding_month_invoices), detail: 'Saldo actual de las facturas de ese mes' },
            { title: 'Pendiente total', value: formatMoney(summary.total_outstanding), detail: 'Todas las facturas emitidas sin liquidar' },
          ].map(card => <article key={card.title} className='rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg shadow-black/10'>
            <h2 className='text-sm font-semibold text-slate-400'>{card.title}</h2>
            <p className='mt-3 text-3xl font-extrabold tabular-nums tracking-tight'>{card.value}</p>
            <p className='mt-3 text-xs leading-5 text-slate-500'>{card.detail}</p>
          </article>)}
        </section>
        <section className='grid gap-5 xl:grid-cols-[1.6fr_1fr]'>
          <div className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
            <div className='flex flex-wrap items-center justify-between gap-3'>
              <div><h2 className='text-lg font-bold'>Evolución de facturación y cobros</h2><p className='mt-1 text-sm text-slate-400'>Últimos seis meses hasta el período elegido</p></div>
              <div className='flex flex-wrap gap-4 text-xs text-slate-400'><span><span className='mr-2 inline-block h-2.5 w-2.5 rounded-sm bg-emerald-400'/>Facturado</span><span><span className='mr-2 inline-block h-2.5 w-2.5 rounded-sm bg-sky-400'/>Cobrado</span></div>
            </div>
            <div className='mt-8 flex h-56 items-end gap-3 border-b border-slate-700 pb-2 sm:gap-5'>
              {summary.trend.map(item => <div key={item.month} className='flex h-full min-w-0 flex-1 flex-col justify-end gap-2'>
                <div className='flex h-full items-end justify-center gap-1.5'>
                  <div title={`Facturado ${item.month}: ${formatMoney(item.invoiced)}`} className='w-1/3 max-w-8 rounded-t-md bg-emerald-400' style={{height: `${(Number(item.invoiced) ? Math.max(3, Number(item.invoiced) / maxTrend * 100) : 0)}%`}} />
                  <div title={`Cobrado ${item.month}: ${formatMoney(item.received)}`} className='w-1/3 max-w-8 rounded-t-md bg-sky-400' style={{height: `${(Number(item.received) ? Math.max(3, Number(item.received) / maxTrend * 100) : 0)}%`}} />
                </div>
                <span className='text-center text-xs capitalize text-slate-400'>{monthLabel(item.month)}</span>
              </div>)}
            </div>
            <p className='mt-4 text-xs leading-5 text-slate-500'>El dinero cobrado en un mes puede corresponder a facturas anteriores. Los cobros anulados no cuentan.</p>
          </div>
          <div className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
            <h2 className='text-lg font-bold'>Estado de cobro de las facturas del mes</h2>
            <p className='mt-2 text-sm text-slate-400'>Porcentaje ya cobrado de las facturas emitidas en el período elegido.</p>
            <p className='mt-7 text-4xl font-extrabold tabular-nums'>{integer(summary.collection_rate)} %</p>
            <div role='progressbar' aria-valuenow={Number(summary.collection_rate)} aria-valuemin={0} aria-valuemax={100} aria-label='Porcentaje cobrado' className='mt-5 h-3 overflow-hidden rounded-full bg-slate-800'>
              <div className='h-full rounded-full bg-emerald-400' style={{width: `${Math.min(100, Math.max(0, Number(summary.collection_rate)))}%`}}/>
            </div>
            <div className='mt-7 grid grid-cols-2 gap-3'>
              <div><p className='text-xs text-slate-400'>Cobrado sobre esas facturas</p><p className='mt-1 font-bold tabular-nums'>{formatMoney(summary.paid_for_month_invoices)}</p></div>
              <div><p className='text-xs text-slate-400'>Aún pendiente</p><p className='mt-1 font-bold tabular-nums text-amber-300'>{formatMoney(summary.outstanding_month_invoices)}</p></div>
            </div>
            <div className='mt-6 border-t border-slate-700 pt-5'><p className='text-xs text-slate-400'>Diferencia facturado – cobrado en el mes</p><p className='mt-1 text-xl font-bold tabular-nums'>{formatMoney(summary.cash_gap)}</p><p className='mt-2 text-xs leading-5 text-slate-500'>Esta diferencia no equivale necesariamente al saldo deudor: el cobro mensual puede incluir facturas antiguas.</p></div>
          </div>
        </section>
        <section className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
          <h2 className='text-lg font-bold'>Productos más vendidos</h2>
          <p className='mt-1 text-sm text-slate-400'>Unidades de artículos incluidas en facturas emitidas durante el mes seleccionado.</p>
          {summary.top_products.length === 0 ? <p className='mt-6 rounded-xl border border-slate-800 p-5 text-sm text-slate-500'>Sin productos facturados en este período.</p> :
            <div className='mt-6 space-y-5'>{summary.top_products.map((product, index) => {
              const maxUnits = Math.max(1, ...summary.top_products.map(p => Number(p.units)));
              return <div key={product.product_id} className='flex items-center gap-4'>
                <span className='w-6 shrink-0 text-sm font-bold text-slate-500'>{index + 1}.</span>
                <div className='min-w-0 flex-1'><div className='mb-2 flex flex-wrap justify-between gap-2 text-sm'><span className='truncate font-medium'>{product.name}</span><span className='tabular-nums text-slate-300'>{integer(product.units)} uds · {formatMoney(product.total_amount)}</span></div>
                <div className='h-2 rounded-full bg-slate-800'><div className='h-2 rounded-full bg-emerald-400' style={{width:`${Number(product.units)/maxUnits*100}%`}}/></div></div>
              </div>;
            })}</div>}
        </section>
      </>}
      <p className='text-xs leading-5 text-slate-500'>Las ventas se reconocen aquí cuando se emite la factura, no cuando se crea el pedido. Los cobros son registros manuales de la aplicación, no movimientos bancarios conciliados. Todos los importes incluyen IVA.</p>
    </div>
  </main>;
}
