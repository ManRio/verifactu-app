import { useEffect, useState } from 'react';

import CustomerForm from '../components/CustomerForm';
import {
  activateCustomer,
  deactivateCustomer,
  getCustomers,
} from '../services/customer';
import type { Customer } from '../types/customer';

function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);

  useEffect(() => {
    async function loadCustomers() {
      try {
        const data = await getCustomers();
        setCustomers(data);
      } catch {
        setError('No se pudieron cargar los clientes');
      } finally {
        setIsLoading(false);
      }
    }

    loadCustomers();
  }, []);

  function handleNewCustomer() {
    setEditingCustomer(null);
    setShowForm(true);
  }

  function handleEditCustomer(customer: Customer) {
    setEditingCustomer(customer);
    setShowForm(false);
  }

  function handleCancelForm() {
    setShowForm(false);
    setEditingCustomer(null);
  }

  function handleCustomerSaved(savedCustomer: Customer) {
    if (editingCustomer) {
      setCustomers((current) =>
        current.map((customer) =>
          customer.id === savedCustomer.id ? savedCustomer : customer,
        ),
      );
    } else {
      setCustomers((current) => [...current, savedCustomer]);
    }

    setShowForm(false);
    setEditingCustomer(null);
  }

  async function handleToggleStatus(customer: Customer) {
    setError('');

    try {
      const updatedCustomer = customer.is_active
        ? await deactivateCustomer(customer.id)
        : await activateCustomer(customer.id);

      setCustomers((current) =>
        current.map((currentCustomer) =>
          currentCustomer.id === updatedCustomer.id
            ? updatedCustomer
            : currentCustomer,
        ),
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : 'No se pudo cambiar el estado del cliente',
      );
    }
  }

  return (
    <main className='min-h-screen bg-slate-950 px-6 py-10 text-white'>
      <div className='mx-auto max-w-7xl'>
        <div className='mb-8 flex items-center justify-between'>
          <div>
            <p className='text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400'>
              VeriFactu App
            </p>

            <h1 className='mt-2 text-3xl font-bold'>Clientes</h1>

            <p className='mt-2 text-slate-400'>
              Gestión de clientes del negocio.
            </p>
          </div>

          <button
            type='button'
            onClick={handleNewCustomer}
            className='rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-emerald-400'
          >
            Nuevo cliente
          </button>
        </div>

        {(showForm || editingCustomer) && (
          <CustomerForm
            customer={editingCustomer}
            onSaved={handleCustomerSaved}
            onCancel={handleCancelForm}
          />
        )}

        {isLoading && <p className='text-slate-400'>Cargando clientes...</p>}

        {error && (
          <p className='mb-6 rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-red-300'>
            {error}
          </p>
        )}

        {!isLoading && !error && customers.length === 0 && (
          <section className='rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center'>
            <h2 className='text-xl font-semibold'>Todavía no hay clientes</h2>

            <p className='mt-2 text-slate-400'>
              Crea tu primer cliente para empezar.
            </p>
          </section>
        )}

        {customers.length > 0 && (
          <div className='overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900'>
            <table className='w-full min-w-[900px]'>
              <thead className='border-b border-slate-800 bg-slate-900/80 text-left text-sm text-slate-400'>
                <tr>
                  <th className='px-6 py-4'>Cliente</th>
                  <th className='px-6 py-4'>NIF/CIF</th>
                  <th className='px-6 py-4'>Localidad</th>
                  <th className='px-6 py-4'>Contacto</th>
                  <th className='px-6 py-4'>Estado</th>
                  <th className='px-6 py-4'>Acciones</th>
                </tr>
              </thead>

              <tbody>
                {customers.map((customer) => (
                  <tr
                    key={customer.id}
                    className='border-b border-slate-800 last:border-0'
                  >
                    <td className='px-6 py-4'>
                      <p className='font-medium'>{customer.legal_name}</p>

                      {customer.trade_name && (
                        <p className='mt-1 text-sm text-slate-400'>
                          {customer.trade_name}
                        </p>
                      )}
                    </td>

                    <td className='px-6 py-4 text-slate-300'>
                      {customer.tax_id ?? '—'}
                    </td>

                    <td className='px-6 py-4 text-slate-300'>
                      {customer.city ?? '—'}

                      {customer.province && (
                        <p className='mt-1 text-sm text-slate-500'>
                          {customer.province}
                        </p>
                      )}
                    </td>

                    <td className='px-6 py-4'>
                      <p className='text-slate-300'>{customer.email ?? '—'}</p>

                      {customer.phone && (
                        <p className='mt-1 text-sm text-slate-500'>
                          {customer.phone}
                        </p>
                      )}
                    </td>

                    <td className='px-6 py-4'>
                      {customer.is_active ? (
                        <span className='text-emerald-400'>Activo</span>
                      ) : (
                        <span className='text-slate-500'>Inactivo</span>
                      )}
                    </td>

                    <td className='px-6 py-4'>
                      <div className='flex items-center gap-4'>
                        <button
                          type='button'
                          onClick={() => handleEditCustomer(customer)}
                          className='font-medium text-emerald-400 transition hover:text-emerald-300'
                        >
                          Editar
                        </button>

                        <button
                          type='button'
                          onClick={() => handleToggleStatus(customer)}
                          className={
                            customer.is_active
                              ? 'font-medium text-red-400 transition hover:text-red-300'
                              : 'font-medium text-emerald-400 transition hover:text-emerald-300'
                          }
                        >
                          {customer.is_active ? 'Desactivar' : 'Activar'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}

export default CustomersPage;
