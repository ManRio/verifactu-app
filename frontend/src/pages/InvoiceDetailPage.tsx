import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import { downloadDocumentPdf } from '../services/documentPdf';

import { getInvoice, issueInvoice } from '../services/invoice';
import type { Invoice } from '../types/invoice';
import { formatDate, formatDateTime, formatMoney, todayLocal } from '../utils/format';

function InvoiceDetailPage() {
  const { invoiceId } = useParams<{ invoiceId: string }>();
  const id = Number(invoiceId);
  const validId = Number.isSafeInteger(id) && id > 0;

  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [pdfDownloading, setPdfDownloading] = useState(false);
  const [pdfError, setPdfError] = useState('');
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [isIssuing, setIsIssuing] = useState(false);
  const [showIssueForm, setShowIssueForm] = useState(false);
  const [seriesCode, setSeriesCode] = useState('F');
  const [issueDate, setIssueDate] = useState(todayLocal());

  useEffect(() => {
    if (!validId) return;
    let active = true;
    async function load() {
      try {
        const data = await getInvoice(id);
        if (active) setInvoice(data);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'No se pudo cargar la factura');
      } finally {
        if (active) setIsLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [id, validId]);

  async function handleIssue(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!invoice || invoice.status !== 'DRAFT' || isIssuing) return;

    const code = seriesCode.trim().toUpperCase();
    if (!code || code.length > 20 || !issueDate) {
      setActionError('Introduce una serie válida (hasta 20 caracteres) y una fecha de emisión.');
      return;
    }

    // La emisión asigna numeración definitiva y no puede deshacerse en esta versión.
    const confirmed = window.confirm(
      `¿Emitir definitivamente el borrador #${invoice.id} con serie ${code} y fecha ${formatDate(issueDate)}? ` +
        'La factura emitida no podrá editarse desde esta aplicación.',
    );
    if (!confirmed) return;

    setIsIssuing(true);
    setActionError('');
    try {
      const updated = await issueInvoice(invoice.id, {
        series_code: code,
        issue_date: issueDate,
      });
      setInvoice(updated);
      setShowIssueForm(false);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'No se pudo emitir la factura');
    } finally {
      setIsIssuing(false);
    }
  }

  async function handleDownloadPdf() {
    if (!invoice || pdfDownloading) return;
    setPdfDownloading(true);
    setPdfError('');
    try {
      await downloadDocumentPdf('invoice', invoice.id);
    } catch (err) {
      setPdfError(err instanceof Error ? err.message : 'No se pudo descargar el PDF');
    } finally {
      setPdfDownloading(false);
    }
  }

  return (
    <main className='min-h-screen bg-slate-950 px-4 py-8 text-white sm:px-6 lg:px-8'>
      <div className='mx-auto max-w-5xl'>
        <Link className='text-sm text-emerald-400 hover:underline' to='/invoices'>← Volver a facturas</Link>
        {!validId && <p role='alert' className='mt-8 text-red-300'>Identificador de factura no válido.</p>}
        {validId && isLoading && <p role='status' className='mt-8 text-slate-400'>Cargando factura...</p>}
        {error && <p role='alert' className='mt-8 rounded-xl border border-red-900 bg-red-950/40 p-5 text-red-300'>{error}</p>}

        {validId && !isLoading && !error && invoice && (
          <>
            <header className='my-8 flex flex-wrap items-start justify-between gap-4'>
              <div>
                <p className='text-sm font-semibold uppercase tracking-widest text-emerald-400'>Detalle de factura</p>
                <h1 className='mt-2 text-3xl font-bold'>
                  {invoice.full_number ?? `Borrador #${invoice.id}`}
                </h1>
                <p className='mt-2 text-slate-400'>Creado el {formatDateTime(invoice.created_at)}</p>
              </div>
              {invoice.status === 'ISSUED' && (
              <button
                type='button'
                onClick={() => void handleDownloadPdf()}
                disabled={pdfDownloading}
                className='rounded-lg border border-emerald-500/60 px-4 py-2 text-sm font-semibold text-emerald-300 transition hover:bg-emerald-500/10 disabled:opacity-50'
              >
                {pdfDownloading ? 'Generando PDF...' : 'Descargar PDF'}
              </button>
              )}
              <span className={`rounded-full border px-4 py-2 text-sm font-semibold ${invoice.status === 'ISSUED'
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                : 'border-amber-500/30 bg-amber-500/10 text-amber-300'}`}>
                {invoice.status === 'ISSUED' ? 'Emitida' : 'Borrador'}
              </span>
            </header>

            {pdfError && (
              <p role='alert' className='mb-5 rounded-lg border border-red-900 bg-red-950/40 p-4 text-sm text-red-300'>
                {pdfError}
              </p>
            )}
            <section className='mb-6 grid gap-4 sm:grid-cols-2'>
              <div className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
                <h2 className='mb-3 text-lg font-semibold'>Emisor (datos históricos)</h2>
                <p className='font-medium'>{invoice.issuer_legal_name}</p>
                <p className='mt-1 text-sm text-slate-300'>NIF: {invoice.issuer_tax_id}</p>
                <p className='mt-2 text-sm text-slate-400'>{invoice.issuer_address}</p>
                <p className='text-sm text-slate-400'>{invoice.issuer_postal_code} {invoice.issuer_city}</p>
                <p className='text-sm text-slate-400'>{invoice.issuer_province}</p>
              </div>
              <div className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
                <h2 className='mb-3 text-lg font-semibold'>Cliente (datos históricos)</h2>
                <p className='font-medium'>{invoice.customer_legal_name}</p>
                {invoice.customer_tax_id && <p className='mt-1 text-sm text-slate-300'>NIF: {invoice.customer_tax_id}</p>}
                {invoice.customer_address && <p className='mt-2 text-sm text-slate-400'>{invoice.customer_address}</p>}
                <p className='text-sm text-slate-400'>
                  {invoice.customer_postal_code ?? ''} {invoice.customer_city ?? ''}
                </p>
                {invoice.customer_province && <p className='text-sm text-slate-400'>{invoice.customer_province}</p>}
              </div>
            </section>

            <section className='mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-6'>
              <h2 className='mb-3 text-lg font-semibold'>Fechas</h2>
              <p className='text-sm text-slate-300'>Operación: {formatDate(invoice.operation_date)}</p>
              <p className='mt-2 text-sm text-slate-300'>Emisión: {formatDate(invoice.issue_date)}</p>
              {invoice.issued_at && <p className='mt-2 text-sm text-slate-300'>Registrada: {formatDateTime(invoice.issued_at)}</p>}
            </section>

            <section className='mb-6 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900'>
              <h2 className='border-b border-slate-800 p-6 text-xl font-semibold'>Líneas de factura</h2>
              <div className='overflow-x-auto'>
                <table className='w-full min-w-[700px] text-left'>
                  <thead className='bg-slate-950/50 text-sm text-slate-400'>
                    <tr>
                      <th scope='col' className='px-6 py-4'>Descripción</th>
                      <th scope='col' className='px-6 py-4 text-right'>Cantidad</th>
                      <th scope='col' className='px-6 py-4 text-right'>Precio</th>
                      <th scope='col' className='px-6 py-4 text-right'>IVA</th>
                      <th scope='col' className='px-6 py-4 text-right'>Total</th>
                    </tr>
                  </thead>
                  <tbody className='divide-y divide-slate-800'>
                    {invoice.lines.map((line) => (
                      <tr key={line.id}>
                        <td className='px-6 py-4'>{line.description}</td>
                        <td className='px-6 py-4 text-right'>{line.quantity}</td>
                        <td className='px-6 py-4 text-right'>{formatMoney(line.unit_price)}</td>
                        <td className='px-6 py-4 text-right'>{line.tax_rate}%</td>
                        <td className='px-6 py-4 text-right font-medium'>{formatMoney(line.total_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className='mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-6'>
              <h2 className='mb-3 text-lg font-semibold'>Totales</h2>
              <div className='ml-auto max-w-sm space-y-3'>
                <div className='flex justify-between text-slate-300'><span>Base imponible</span><span>{formatMoney(invoice.subtotal)}</span></div>
                <div className='flex justify-between text-slate-300'><span>Impuestos</span><span>{formatMoney(invoice.tax_total)}</span></div>
                <div className='flex justify-between border-t border-slate-700 pt-3 text-xl font-bold'>
                  <span>Total</span><span className='text-emerald-400'>{formatMoney(invoice.total_amount)}</span>
                </div>
              </div>
              {invoice.notes && (
                <div className='mt-6 border-t border-slate-800 pt-5'>
                  <h3 className='font-semibold'>Observaciones</h3>
                  <p className='mt-2 whitespace-pre-wrap text-sm text-slate-300'>{invoice.notes}</p>
                </div>
              )}
            </section>

            <section className='mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-6'>
              <h2 className='mb-3 text-lg font-semibold'>Albaranes incluidos</h2>
              {invoice.delivery_notes.length === 0 ? (
                <p className='text-sm text-slate-400'>Sin albaranes vinculados.</p>
              ) : (
                <ul className='space-y-2'>
                  {invoice.delivery_notes.map((link) => (
                    <li key={link.id}>
                      <Link to={`/delivery-notes/${link.delivery_note_id}`} className='text-emerald-400 hover:underline'>
                        Albarán #{link.delivery_note_id}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {invoice.status === 'DRAFT' && (
              <section className='rounded-2xl border border-amber-500/30 bg-slate-900 p-6'>
                <div className='flex flex-wrap items-center justify-between gap-3'>
                  <div>
                    <h2 className='text-lg font-semibold'>Emitir factura</h2>
                    <p className='mt-1 text-sm text-slate-400'>
                      Asignará número definitivo y bloqueará la edición del documento.
                    </p>
                  </div>
                  {!showIssueForm && (
                    <button type='button' onClick={() => setShowIssueForm(true)}
                      className='rounded-lg bg-amber-400 px-4 py-2 font-semibold text-slate-950 hover:bg-amber-300'>
                      Preparar emisión
                    </button>
                  )}
                </div>

                {showIssueForm && (
                  <form onSubmit={handleIssue} className='mt-5 space-y-4'>
                    <div className='grid gap-4 sm:grid-cols-2'>
                      <label className='block text-sm text-slate-300'>
                        Serie
                        <input value={seriesCode} maxLength={20} required
                          onChange={(event) => setSeriesCode(event.target.value)}
                          className='mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white' />
                      </label>
                      <label className='block text-sm text-slate-300'>
                        Fecha de emisión
                        <input type='date' value={issueDate} required
                          onChange={(event) => setIssueDate(event.target.value)}
                          className='mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white' />
                      </label>
                    </div>
                    {actionError && <p role='alert' className='text-sm text-red-300'>{actionError}</p>}
                    <div className='flex flex-wrap gap-3'>
                      <button type='submit' disabled={isIssuing}
                        className='rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50'>
                        {isIssuing ? 'Emitiendo...' : 'Emitir definitivamente'}
                      </button>
                      <button type='button' disabled={isIssuing}
                        onClick={() => { setShowIssueForm(false); setActionError(''); }}
                        className='rounded-lg border border-slate-700 px-4 py-2 text-slate-300'>
                        Cancelar
                      </button>
                    </div>
                  </form>
                )}
              </section>
            )}

            <p className='mt-6 text-xs text-slate-500'>
              Prototipo en desarrollo: la emisión actual no acredita conformidad con VERI*FACTU.
            </p>
          </>
        )}
      </div>
    </main>
  );
}

export default InvoiceDetailPage;
